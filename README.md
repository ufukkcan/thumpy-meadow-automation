# Thumpy Meadow — Proje Kurgusu

> Bu dosya projenin tamamını anlatır. Hiç bilmeyen biri bunu okuyunca ne yapıldığını,
> neden yapıldığını, nasıl çalıştığını ve nasıl kullanılacağını anlar.

---

## 1. Tek cümleyle

**Thumpy Meadow**, 2–6 yaş İngilizce konuşan çocuklar için özgün 2D çizgi film eğitim
videoları üreten ve bunları YouTube'a otomatik yükleyen bir sistemdir. Videoların
görüntüsü, müziği, sesi ve metni dahil her parçası kodla sıfırdan üretilir; telifli
hiçbir materyal kullanılmaz.

---

## 2. Neden var? (Problem)

Sahibi (Ufuk) birden fazla YouTube kanalı işletiyor ve her videoyu elle üretmek
mümkün değil. Hedef: günde bir bölüm, insan onayıyla ama insan emeği olmadan.

Çocuk içeriği seçilmesinin sebebi: YouTube'da okul öncesi içerik en çok izlenen
kategorilerden biri ve tekrar izlenme oranı çok yüksek (aynı çocuk aynı videoyu
defalarca izliyor).

---

## 3. Ne üretir? (Çıktı)

Her bölüm:

| Özellik | Değer |
|---|---|
| Format | Yatay 16:9, 1920×1080, 24 fps, H.264 + AAC |
| Süre | 10–13 dakika |
| Dil | İngilizce (anlatım ve ekran metinleri) |
| Ses | `en-US-AnaNeural` (çocuk sesi, Microsoft Edge TTS) |
| Yapı | Giriş → 4 ders bölümü → Tekrar → Kapanış |
| Müzik | Kodla üretilmiş telifsiz fon müziği + ders aralarında müzik molaları |
| Küçük resim | 1280×720 JPEG, 3 renk varyasyonu (A/B testi için) |
| Gizlilik | `private` + `publishAt` (zamanlanmış yayın) |
| COPPA | `selfDeclaredMadeForKids = true` |

Bir bölümün akışı:

```
Hello Friends!          (4–6 anlatım segmenti, karşılama)
Ders 1                  (12–16 anlatım segmenti + 1 müzik molası)
Ders 2                  (aynı)
Ders 3                  (aynı)
Ders 4                  (aynı)
Let's Remember!         (6–8 segment, hızlı tekrar)
Bye-Bye!                (3–4 segment, veda)
```

Segment iki türdür:
- **narration** — Dino bir cümle söyler, ekranda altta beyaz kutuda yazı, sağda isteğe
  bağlı bir obje (balon, meyve, hayvan, şekil, sayma) belirir.
- **music_break** — Dino hızlı dans eder, ekranda karaoke tarzı şarkı sözleri akar,
  çalan kelime sarı renkte zıplar.

---

## 4. Nasıl çalışır? (Günlük akış)

```
┌─ Her 5 dakikada bir GitHub Actions çalışır ──────────────────────────────┐
│                                                                           │
│  Durum: idle/done                                                         │
│     ↓ (Telegram'a "video üret" yazıldı VEYA saat 11:00 TR geldi)          │
│  Claude 3 bölüm fikri üretir  →  Telegram'a butonlu mesaj                  │
│                                                                           │
│  Durum: choosing                                                          │
│     ↓ (kullanıcı 1/2/3 butonuna bastı)                                    │
│  Claude tam senaryoyu yazar  →  Telegram'a .txt dosyası                   │
│  (anlatım cümleleri, şarkı sözleri, başlık, etiketler, küçük resim planı) │
│                                                                           │
│  Durum: reviewing                                                         │
│     ↓ (kullanıcı "Onayla" bastı)            ↓ ("Yeniden yaz" bastı)       │
│  ÜRETİM BAŞLAR                               Claude senaryoyu tekrar yazar │
│    1. Her anlatım cümlesi seslendirilir (edge-tts)                        │
│    2. Sahne süreleri gerçek ses uzunluğuna göre hesaplanır                │
│    3. Video kare kare çizilir, ffmpeg'e akıtılır                          │
│    4. Müzik + seslendirme karıştırılır                                    │
│    5. 3 küçük resim üretilir                                              │
│    6. Yayın saati hesaplanır (öğrenen planlayıcı)                         │
│    7. YouTube'a gizli + zamanlanmış yüklenir, küçük resim A set edilir    │
│    8. Telegram'a link, süre, yayın saati, 3 küçük resim gönderilir        │
│                                                                           │
│  Durum: done                                                              │
│                                                                           │
│  AYRICA her çalışmada: yayından 48 saat geçmiş videoların izlenmesi       │
│  ölçülür, haftada bir Telegram'a yayın saati raporu gönderilir.           │
└───────────────────────────────────────────────────────────────────────────┘
```

**Kritik kural:** Senaryo asla otomatik onaylanmaz. İnsan onayı olmadan hiçbir video
üretilmez ve yüklenmez. Çocuk içeriğinde bu, sistemdeki tek ve en önemli güvenlik
kontrolüdür.

---

## 5. Nasıl kullanılır? (Operasyon)

Günlük kullanım tamamen Telegram üzerindendir:

1. **Fikir gelir** (11:00'de otomatik ya da "video üret" yazınca)
2. **Bir fikre bas** (1, 2 veya 3)
3. **Senaryo .txt gelir** — OKU. Çocuk içeriği için uygunsuz, yanlış ya da sıkıcı bir
   şey varsa "Yeniden yaz"a bas.
4. **"Onayla"ya bas** — üretim başlar (~15 dk)
5. **Link gelir** — YouTube Studio'da izle, beğenmezsen yayından önce sil
6. İstersen küçük resim B ve C'yi Studio'da A/B testine ekle

GitHub'ın zamanlayıcısı gecikebildiği için, butona bastıktan sonra cevap gelmezse
GitHub → Actions → "Thumpy Meadow - kontrol ve uretim" → **Run workflow** ile elle
tetiklenir.

---

## 6. Hangi teknolojiler? (Yığın)

| Katman | Teknoloji | Ne yapar | Maliyet |
|---|---|---|---|
| Çalışma ortamı | GitHub Actions (ubuntu-latest) | Her şeyi çalıştırır | Ücretsiz (public repo'da sınırsız) |
| Dil | Python 3.12 | Tüm kod | — |
| Senaryo | Anthropic Claude API (`claude-sonnet-4-6`) | Fikir, senaryo, SEO metni | ~birkaç sent/bölüm |
| Seslendirme | `edge-tts` (Microsoft Edge TTS) | Anlatım sesi | Ücretsiz |
| Çizim | `Pillow` | Her kareyi çizer | Ücretsiz |
| Video/Ses | `ffmpeg` | Kodlama, karıştırma, filtreler | Ücretsiz |
| Müzik | `numpy` (kendi sentezimiz) | Marimba, bas, davul, akor | Ücretsiz |
| Yükleme | YouTube Data API v3 | Video + küçük resim + istatistik | Ücretsiz (kota dahilinde) |
| Arayüz | Telegram Bot API | Fikir seçimi, onay, bildirim | Ücretsiz |
| Yasal sayfa | GitHub Pages | OAuth yönlendirme adresi | Ücretsiz |
| (Deneysel) | `pyworld`, `rubberband-cli` | Şarkı söyletme denemeleri | Ücretsiz |

**Hiçbir ücretli servis kullanılmaz.** Tek masraf Claude API çağrıları.

---

## 7. Telif ve güvenlik duruşu

**Telif:** Projedeki her görsel öğe (karakter, arka plan, objeler, küçük resimler,
banner, profil) Python koduyla geometrik şekillerden çizilir. Müzik `numpy` ile
sentezlenir. Melodi şablonları 1929 öncesi kamu malı eserlerdir (Twinkle Twinkle,
Mary Had a Little Lamb, London Bridge, Frère Jacques) ve düzenleme bize aittir.
Şarkı sözleri Claude tarafından özgün yazılır. Font: DejaVu Sans (açık kaynak).
**Hiçbir hazır varlık, stok görsel, hazır müzik ya da marka kullanılmaz.**

**Çocuk güvenliği:** `generate_episode.py` içindeki `SAFETY_RULES` bloğu Claude'a
verilen zorunlu kurallardır: korku/şiddet/tehlike yok, taklit edilebilecek riskli
davranış yok, marka/telifli eser adı yok, ticari yönlendirme yok, yanlış bilgi yok.
Ayrıca `props.validate_prop()` Claude'un ürettiği her objeyi beyaz listeye göre
doğrular; listede olmayan hiçbir şey çizilmez.

**COPPA:** Kanal ve her video "made for kids" işaretlidir. Bunun sonucu olarak
yorumlar ve bildirimler YouTube tarafından kapatılır, kişiselleştirilmiş reklam
gösterilmez. Bu değiştirilemez ve değiştirilmeye çalışılmamalıdır.

---

## 8. Entegrasyonlar ve nasıl bağlanırlar

Detaylı kurulum: `docs/setup.md` · Bağlantı detayları: `docs/integrations.md`

| Entegrasyon | Bağlanma şekli | Nerede saklanır |
|---|---|---|
| Claude API | API anahtarı | GitHub Secret `ANTHROPIC_API_KEY` |
| Telegram | Bot token + sabit chat id | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| YouTube | OAuth 2.0 (Web client) + refresh token | `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` |
| GitHub Pages | OAuth callback sayfası | `ufukkcan/tiktok-legal-pages` reposu (public) |

**En kritik tuzak:** YouTube refresh token'ı yetkilendirirken Google hesabı altında
birden fazla kanal olduğu için **doğru kanalı seçmek şarttır**. `yt_oauth_exchange.py`
token'ın hangi kanala ait olduğunu ekrana yazar; "Thumpy Meadow" yazmıyorsa o token
kullanılmaz.

---

## 9. Kardeş projeler (aynı mantık, farklı kanal)

Bu sistem daha önce kurulan üç kanalın deneyiminden doğdu. Hepsi aynı Google hesabı altında ayrı YouTube kanalları ve ayrı GitHub repoları:

| Kanal | Repo | İçerik | Format |
|---|---|---|---|
| interesthings | `youtube-shorts-automation` | İlginç bilgiler | Dikey Shorts |
| Historic Blink | (kod hazır, kurulum yapılmadı) | Tarih | Dikey Shorts |
| astrologicalshorts | `astrological-shorts-automation` | Astroloji (gerçek gök verisiyle) | Dikey Shorts |
| **Thumpy Meadow** | `thumpy-meadow-automation` | Çocuk eğitim | **Yatay uzun video** |

Thumpy Meadow diğerlerinden şu yönlerle ayrılır: yatay ve uzun format, obje çizim
kütüphanesi, müzik üretimi, küçük resim üretimi, öğrenen yayın saati, senaryo onayı
(diğerlerinde video önizleme onayı var).

---

## 10. Dosya haritası

Teknik detay: `docs/architecture.md`

```
repo kökü (thumpy-meadow-automation)
├── check_and_produce.py    ← ANA AKIŞ: durum makinesi, Telegram, onay, yükleme
├── generate_episode.py     ← Claude: fikir, senaryo, SEO + güvenlik kuralları
├── produce.py              ← seslendirme + render + küçük resim birleştirici
├── episode.py              ← video motoru: zaman çizelgesi, kare çizimi, chapters
├── scene2d.py              ← Dino karakteri, arka plan öğeleri
├── props.py                ← obje kütüphanesi + doğrulama (beyaz liste)
├── thumbnail.py            ← küçük resim üretimi (3 varyasyon)
├── music.py                ← fon müziği ve müzik molası sentezi
├── voice.py                ← edge-tts sarmalayıcı
├── scheduler.py            ← öğrenen yayın saati planlayıcı
├── telegram_bot.py         ← Telegram Bot API sarmalayıcı
├── upload_youtube.py       ← YouTube yükleme + küçük resim + istatistik
├── yt_oauth_exchange.py    ← TEK SEFERLİK: OAuth kodu → refresh token
├── songs.py                ← (deneysel) telifsiz melodiler, hece eşleme, düzenleme
├── singer.py               ← (deneysel) vokoder ile şarkı söyletme
├── rhythmic.py             ← (deneysel) doğal sesle ritmik söyleme
├── sing_test.py            ← (deneysel) şarkı testi üreteci
├── sample_episode.py       ← test için örnek bölüm
├── voice_test.py           ← ses testi
├── requirements.txt
├── assets/                 ← (şu an kullanılmıyor, Shorts projelerinden kalma)
├── state/                  ← bot hafızası (Actions tarafından repoya yazılır)
│   ├── pending.json        ← mevcut döngü durumu
│   ├── telegram_offset.json← işlenmiş son Telegram mesajı
│   ├── topics_used.json    ← tekrarı önlemek için kullanılmış konular
│   ├── publish_log.json    ← yayın saati öğrenme kayıtları
│   └── meta.json           ← son rapor tarihi
└── .github/workflows/
    ├── check_and_produce.yml   ← ana otomasyon (cron + elle)
    ├── yt_oauth_exchange.yml   ← tek seferlik yetkilendirme yardımcısı
    └── sing_test.yml           ← (deneysel) şarkı testi
```

---

## 11. Şu anki durum (özet)

- Kanal kuruldu, doğrulandı, COPPA ayarı yapıldı
- Sistem uçtan uca çalışıyor; **1 video üretildi ve yayınlandı**
- İlk video analitiği: 509 gösterim, 12 izlenme, %2,2 tıklanma, 2:09 ortalama izlenme
- **Açık iş:** müzik molalarındaki vokal kalitesi yetersiz (7 deneme yapıldı, devam ediyor)

Ayrıntı: `PROJECT_PLAN.md` · Geçmiş: `docs/changelog.md` · Yapılacaklar: `todo.md`
