# Yapılacaklar

İşaretleme: `[x]` doğrulanarak tamamlandı · `[~]` kısmen · `[ ]` yapılmadı

---

## 1. Kanal kurulumu — TAMAMLANDI

- [x] Kanal adı araştırması (12+ isim YouTube'da tarandı)
- [x] "Thumpy Meadow" seçildi, `@ThumpyMeadow` boş doğrulandı
- [x] YouTube kanalı oluşturuldu (`UC9_bFi-Pyp8hTlclZYkcz-Q`)
- [x] Kanal açıklaması yazıldı ve yayınlandı
- [x] 10 kanal anahtar kelimesi eklendi
- [x] **Audience: "made for kids"** ayarlandı (COPPA) — Studio'da doğrulandı
- [x] Banner üretildi (güvenli alan testi yapıldı) ve yüklendi
- [x] Profil resmi üretildi (daire kırpımı test edildi) ve yüklendi
- [x] Ülke ayarı yapıldı
- [x] Telefon doğrulaması (özel küçük resim izni) — Studio'da "Upload file" göründü
- [ ] Marka (ticari isim) araştırması: TÜRKPATENT / EUIPO / USPTO'da "Thumpy Meadow"

## 2. Üretim motoru — TAMAMLANDI

- [x] Dino karakteri (mutlu + heyecanlı ruh hali)
- [x] Katmanlı arka plan, kayan bulutlar
- [x] Obje kütüphanesi: balon(7), şekil(7×7), meyve(7), hayvan(6), sayma(1–10)
- [x] Obje doğrulama (beyaz liste) — bozuk prop testi yapıldı
- [x] 16:9 yatay düzen, 1920×1080, 24 fps
- [x] Kare kare çizim → ffmpeg borusu (diske PNG yazmıyor)
- [x] Altyazı kutusu, otomatik satır bölme
- [x] Karaoke görünümü (çalan kelime sarı, zıplıyor)
- [x] Fon müziği sentezi (marimba + pad, C-G-Am-F)
- [x] Seslendirme: `en-US-AnaNeural` seçildi (A/B testi yapıldı)
- [x] Gerçek ses süresine göre sahne zamanlaması
- [x] Meyve çizim hataları düzeltildi (elma, muz, çilek)

## 3. Otomasyon — TAMAMLANDI

- [x] Claude ile 3 fikir üretimi
- [x] Claude ile tam senaryo (bölümler, segmentler)
- [x] Çocuk güvenliği kuralları prompta gömüldü
- [x] SEO kuralları prompta gömüldü
- [x] Telegram botu `@thumpymeadow_bot`
- [x] Durum makinesi (idle/choosing/reviewing/done/error)
- [x] Senaryo onayı (.txt + Onayla/Yeniden yaz)
- [x] Hata durumu + "Tekrar dene" butonu
- [x] "video üret" her durumda sıfırlayıp yeni döngü başlatıyor
- [x] YouTube yükleme (gizli + zamanlanmış + made for kids + kategori 27)
- [x] GitHub Actions workflow'ları
- [x] State'in repoya yazılması
- [x] 6 GitHub Secret eklendi
- [x] YouTube OAuth — **doğru kanal doğrulanarak** alındı

## 4. SEO ve yayın — TAMAMLANDI

- [x] Başlık kuralları (anahtar kelime başta, ≤70 karakter, tık tuzağı yok)
- [x] Açıklama üretimi (ilk 150 karakter + öğrenilenler + chapters + kanal tanıtımı)
- [x] Bölüm başlıkları (YouTube chapter kurallarına uygun)
- [x] Etiket ve hashtag üretimi
- [x] Küçük resim: sunburst, sticker, heyecanlı karakter, renkli başlık, 3 varyasyon
- [x] Küçük resimde sadece senaryoda geçen objeler (yanıltıcı değil)
- [x] Öğrenen yayın saati planlayıcı (ABD Doğu, 4 aday saat)
- [x] 48 saatlik izlenme ölçümü + haftalık Telegram raporu
- [x] İlk videoya 3 varyasyonlu A/B testi kuruldu

## 5. İlk yayın — TAMAMLANDI

- [x] Uçtan uca ilk bölüm üretildi (10:41)
- [x] YouTube'a yüklendi ve zamanlandı (`WIEorW7zW10`)
- [x] Studio'da ayarlar doğrulandı
- [x] Küçük resimler elle yüklendi (A/B testi)
- [x] İlk gün analitiği alındı ve yorumlandı

## 6. Müzik molası vokal kalitesi — DEVAM EDİYOR

- [x] Telifsiz melodi şablonları (4 adet, 1929 öncesi kamu malı)
- [x] Hece sayacı (54/54 doğru) + kelime→nota eşleme
- [x] Davul, bas, akor düzenlemesi
- [x] Vokoder ile şarkı söyletme denemesi (A) — robotik, reddedildi
- [x] Ritmik anlatım denemesi (B) — ritim yok
- [x] Doğal satırdan kelime kesme (C) — cızırtılı
- [x] Hece bölme + ünlü hizalama (D) — **ritim onaylandı**
- [x] Perdeyi TTS motorunda üretme (E) — **ses beğenildi**, kayma var
- [x] Legato + küçük kelimeler (G) — sorun sürüyor
- [x] Cızırtı kaynakları giderildi (yumuşak geçişler, davul yumuşatma, R3 motoru)
- [x] Hece hizalaması ölçülerek doğrulandı (sapma ≤0,05 vuruş)
- [ ] **SIRADAKİ:** Cümleyi bütün söylet + kelimeyi bölme (`SPLIT_SYLLABLES=False`) testi
- [ ] Karar: yeterliyse sisteme bağla, değilse alternatiflerden birine geç
- [ ] Müzik molası görselini zenginleştir (objeler dans etsin, sadece yazı+Dino olmasın)
- [ ] Onaylanan yöntemi `episode.py`/`produce.py` içine entegre et

## 7. İzlenme süresi — SIRADA (hiçbiri yapılmadı)

- [ ] İlk 10 saniyede obje göster (şu an 29. saniye)
- [ ] Müzikli, hareketli 5–8 saniyelik açılış jeneriği
- [ ] Müzik molası sıklığını artır (anlatım bloklarını kısalt)
- [ ] Objelere hareket: zıplama, dönme, parıltıyla belirme
- [ ] Dino her yeni objede heyecanlansın (`mood="excited"`)
- [ ] Sahne çeşitliliği: çiftlik, deniz, gece, bahçe
- [ ] Audience retention grafiğini al, düşüş noktalarını tespit et

## 8. Büyüme — SONRA

- [ ] ABC / harf dersleri (harf çizimi kütüphaneye eklenecek)
- [ ] Her bölümden otomatik Shorts kesiti (dikey, 30–60 sn)
- [ ] Oynatma listeleri (YouTube yetkisi genişletilmeli)
- [ ] Yeni karakterler (tavşan, ayı, fil)
- [ ] Harici cron tetikleyici (cron-job.org) — GitHub cron gecikmesine karşı

## 9. Bakım ve güvenlik

- [ ] **Sohbette paylaşılan tüm anahtarları yenile** (Claude API, Telegram bot token,
      Google client secret, refresh token) ve GitHub Secrets'ı güncelle
- [ ] `astrologicalshorts` refresh token'ının doğru kanala ait olduğunu doğrula
      (`yt_oauth_exchange.py`'nin kanal yazdıran sürümüyle)
- [ ] Deneysel dosyaları temizle (karar verilince: `singer.py`, `sing_test.py`,
      `voice_test.py`, `sample_episode.py`, kullanılmayan `assets/`)
- [ ] `requirements.txt`'e `pyworld` ve `setuptools<81` eklensin (eğer şarkı sistemi
      ana akışa girerse)

---

## İnceleme

Tamamlanan işlerin sonucu ve kanıtı. (CLAUDE.md → Görev Yönetimi madde 4)

### Kanal kurulumu — 2026-11-02
**Sonuç:** Kanal tam yapılandırıldı.
**Kanıt:** YouTube Studio'da doğrulandı — Audience "made for kids" işaretli,
açıklama yayında ("Changes published"), 10 anahtar kelime kayıtlı ("Settings saved"),
`youtube.com/verify` "Phone number verified" döndü, Studio'da Thumbnail bölümünde
"Upload file" seçeneği göründü (telefon doğrulaması aktif).

### Üretim motoru — 2026-11-02
**Sonuç:** 16:9 video motoru, obje kütüphanesi ve müzik sentezi çalışıyor.
**Kanıt:** 36 obje tek sayfada çizilip gözle doğrulandı; hatalı çizimler (elma, muz,
çilek) düzeltilip yeniden kontrol edildi. Sayma/hayvan/meyve/şekil sahneleri gerçek
video karelerinden çıkarılıp incelendi. Küçük resimler telefon boyutunda (210×118)
okunabilirlik testinden geçti. Banner güvenli alan (1546×423) çizilerek doğrulandı.

### Otomasyon — 2026-11-02
**Sonuç:** Telegram → Claude → render → YouTube zinciri uçtan uca çalışıyor.
**Kanıt:** Taklit servislerle uçtan uca test yapıldı; bozuk obje (`{"kind":"dragon"}`)
`None`'a çevrildi, `"n": "3"` metni sayıya dönüştü, 9 kelimeden uzun şarkı satırı
kırpıldı, hashtag'lerden `#` ve boşluk temizlendi. Ardından gerçek çalıştırmada
fikirler → seçim → senaryo → onay → video → YouTube linki zinciri tamamlandı.

### Yayın saati planlayıcı — 2026-11-02
**Sonuç:** Öğrenen planlayıcı doğru çalışıyor.
**Kanıt:** 14 günlük benzetim yapıldı; sistem önce her adayı denedi, sonra daha iyi
performans gösteren saate yöneldi ve arada diğerini denemeye devam etti. Yaz/kış
saati geçişleri ayrı ayrı test edildi (Kasım: 13:00 ABD = 21:00 TR,
Temmuz: 13:00 ABD = 20:00 TR).

### İlk video — 2026-11-02
**Sonuç:** Yayınlandı.
**Kanıt:** `youtu.be/WIEorW7zW10`, 10:41, Studio'da made for kids + Scheduled +
7 chapter + 3 hashtag doğrulandı. Küçük resim A/B testi kuruldu.

### Müzik molası ritim hizalaması — 2026-11-03
**Sonuç:** Ritim hizalaması çözüldü (kullanıcı onayladı: "ritim tutması çok güzel").
**Kanıt:** Hece başlangıçları bağımsız yöntemle (perde + enerji analizi) ölçüldü;
dört farklı satırda hedef vuruşlardan sapma 0,01–0,05 vuruş çıktı. Hece bölme
("banana" → 3 parça) ve legato sonrası hizanın bozulmadığı ayrıca doğrulandı.
**Açık kalan:** Ses kalitesi ve anlaşılırlık (bkz. bölüm 6).
