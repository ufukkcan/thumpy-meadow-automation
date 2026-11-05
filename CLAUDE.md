# CLAUDE.md — Thumpy Meadow

## Proje

2–6 yaş İngilizce konuşan çocuklar için özgün 2D çizgi film eğitim videoları üretip
YouTube'a otomatik yükleyen sistem. Görüntü, müzik, ses ve metin dahil her parça
kodla sıfırdan üretilir; telifli hiçbir materyal kullanılmaz. Tek masraf Claude API.

Proje klasörü: `Documents\projeler\thumpy` (tam yolu kendi kullanıcı adınla tamamla)

---

## Oturum başı

1. Bu dosyayı oku ve uygula.
2. Aşağıdaki "MUTLAKA oku" listesini oku.
3. Diğer dosyaları yalnızca gerektiğinde, `INDEX.md`'ye bakarak aç.

### Oturum başında MUTLAKA oku

| Dosya | Niçin |
|---|---|
| `CLAUDE.md` (bu dosya) | Kurallar ve hızlı bağlam |
| `docs/lessons.md` | Aynı hatayı tekrarlamamak için |
| `todo.md` | Açık işler |
| `PROJECT_PLAN.md` | Hangi fazdayız |

Geri kalanı okuma. `INDEX.md` hangi soru için hangi dosyanın açılacağını söyler.

---

## Hızlı bağlam

**Durum (2026-11-04):** Çalışıyor. 2 video yayınlandı (`WIEorW7zW10`, `H9epa9bfhhI`).
Yeni müzik molası (CC0 enstrümanlar + Hanami DiffSinger vokali + BigVGAN) testte
**kullanıcı onaylı**, henüz üretime BAĞLI DEĞİL → sıradaki iş `todo.md` 6c (U1–U8).
Claude artık scratchpad klonundan push yapabiliyor (her push öncesi kullanıcı onayı).

**Kimlikler**
- Kanal: `@ThumpyMeadow` · `UC9_bFi-Pyp8hTlclZYkcz-Q` · made for kids · doğrulanmış
- Repo: `ufukkcan/thumpy-meadow-automation` (public, dosyalar kökte)
- Bot: `@thumpymeadow_bot` · Hesap: kanal sahibi Google hesabı (bkz. `docs/secrets.md`)

**Akış:** Telegram "video üret" (ya da 11:00 TR) → Claude 3 fikir → kullanıcı seçer →
Claude tam senaryo → **kullanıcı onaylar** → seslendirme + render (~15 dk) →
YouTube'a gizli+zamanlanmış yükleme → Telegram'a link.

**Yığın:** Python 3.12 · GitHub Actions · Claude API (`claude-sonnet-4-6`) ·
edge-tts (`en-US-AnaNeural`) · Pillow · ffmpeg · numpy · YouTube Data API v3 ·
Telegram Bot API

**Çıktı:** 16:9, 1920×1080, 24 fps, 10–13 dk. Giriş → 4 ders → tekrar → kapanış.

**Son video:** `youtu.be/WIEorW7zW10` — 10:41 — ilk gün: 509 gösterim, 12 izlenme,
%2,2 CTR, 2:09 ortalama izlenme (%20).

**Açık işler:** (1) müzik molası vokali, (2) izlenme süresi/açılış hızı,
(3) anahtar yenileme. Ayrıntı `todo.md`.

---

## Genel Talimatlar

1. **Token tasarrufu.** Kısa ve net yaz. Ne yaptığını ve ne yapılacağını söyle,
   istenmedikçe detay verme. Övgü ve güzelleme yok.

2. **Varsayım yok.** Doğrulanmış/doğrulanabilir yöntem kullan. Bilmediğin,
   anlamadığın, bulamadığın şeyi sor; birlikte karar verelim.

3. **Yazma yetkisi yalnızca proje klasöründe.** GitHub reposu, YouTube kanalı,
   Telegram botu ve Google Cloud'da yalnızca okuma/inceleme. Kod değişikliği
   önerilir, kullanıcı uygular. Okuma dışı her işlemde (kanal ayarı değiştirme,
   video silme, secret güncelleme) **işlem + gerekçe + etki** sun, onay bekle.

4. **Kullanıcının bilgisayarında script çalıştırılamaz** (kurumsal engel).
   Yerel çalıştırma gerektiren her iş GitHub Actions workflow'u olarak tasarlanır.
   Kullanıcıdan asla "şunu bilgisayarında çalıştır" isteme.

5. **Secret değeri hiçbir dosyaya yazılmaz** (API anahtarı, bot token, client secret,
   refresh token). Yazılabilecekler: secret'ın adı, nerede saklandığı, kanal ID,
   kullanıcı adı, redirect URI, tarih. Bkz. `docs/secrets.md`.

6. **Ustalık yol haritası.** Çalışılan her konuda dünya çapında uzmanlık için yol
   haritasını `docs/roadmap.md`'de tut. Maddeler tamamlandıkça işaretle.

7. **En iyi %1'in teknikleri.** Az paylaşılan teknikleri, gizli kaynakları ve
   alışılmadık yaklaşımları dahil et.

8. **Döngü engeli.** Bir sorun **en fazla 3 denemede** çözülmezse dur, denenenleri
   bildir, birlikte karar verelim.
   *(Bu kural müzik molası çalışmasında 7 denemeye çıkıldığı için eklendi.)*

9. **Kendini geliştirme.** Her düzeltmeden sonra `docs/lessons.md`'ye örüntüyü ve
   aynı hatayı önleyecek kuralı yaz. Oturum başında gözden geçir.

10. **Bitti demeden kanıt.** Çalıştığını kanıtlamadan tamamlandı işaretleme.
    Bu projede kanıt şu demek: kodu derle, YAML'ı doğrula, üretilen görseli `view`
    ile **gözle gör**, sesi/videoyu ölç (süre, hizalama, kırpma).
    "Kıdemli bir mühendis bunu onaylar mı?" diye sor.

11. **Dengeli zarafet.** Önemsiz olmayan değişikliklerde daha zarif bir yol var mı
    diye düşün. Çözüm yamalı duruyorsa doğru çözümü uygula. Basit işlerde aşırı
    mühendislik yapma. Sunmadan önce kendi işini sorgula.

12. **Otonom hata düzeltme.** Hata bildirildiğinde log/çıktı/hata mesajından kök
    nedeni bul ve proje klasöründe düzelt; elden tutulmayı bekleme. Düzeltme GitHub
    ya da YouTube tarafında uygulanacaksa madde 3'teki onay geçerli. Başarısız
    GitHub Actions çalıştırmalarını loglarından teşhis et.

13. **Aşırı mühendislik yok, istenmeyen özellik yok.**

14. **Tembellik yok.** Kök nedeni bul, geçici çözüm yok. Script sonucuna güvenme,
    her çalıştırmadan sonra sonucu kontrol et. Yönlendirilmedikçe örnek/kısmi veriyle
    değil tüm veriyle çalış. Ama hepsini birden okuma: gerekeni oku, karar için
    yetmezse daha fazlasını oku.

15. **Minimum etki.** Yalnızca gerekene dokun, yan etki yaratma.

16. **Soru sorulduğunda yalnızca düzyazı cevap ver.** Kod/komut vereceksen her
    dosyayı **tam** ve **tek blokta**, üstünde tam dosya yolu yazarak ver.

---

## Bu projeye özel çalışma tarzı

17. **Adım adım git.** "Şunu yap, yapınca söyle, sonrakine geçelim." Aynı anda
    birden fazla iş verme.

18. **Tam dosya ver, satır arattırma.** "Şu satırı bul ve değiştir" deme; dosyanın
    tamamını ver. Her kod bloğunun başında tam yol yaz
    (`props.py` mi, `.github/workflows/sing_test.yml` mi).

19. **Türkçe konuş.** Kod içi açıklamalar da Türkçe ama **ASCII** (Türkçe karakter
    kullanma; bazı ortamlarda sorun çıkarıyor).

20. **Test sınırını bil.**

| Yerelde test edilebilir | Yalnızca GitHub Actions'ta |
|---|---|
| Çizim, kare üretimi, video render | Gerçek seslendirme (Ana sesi) |
| Müzik sentezi, hece/hizalama ölçümü | Telegram akışı |
| Kod akışı (taklit servislerle) | YouTube yükleme |

Yerelde `espeak-ng` ile üretilen ses **kalite değerlendirmesi için kullanılmaz**,
sadece kod akışını doğrular. Kullanıcıya verilirken bu açıkça söylenir.

21. **Geri bildirimi doğrula.** Kullanıcı bir çıktıyı beğenmediğinde hangi dosyayı
    değerlendirdiğini sor. (Bir kez kaba yerel ses örneği, gerçek çıktı sanıldı.)

22. **Dürüstlük.** Yapılamayan bir şey varsa net söyle. Tahmin ile ölçümü ayır.
    Bir yaklaşımın tavanına gelindiyse alternatifleri sun, aynı şeyi tekrar deneme.

---

## Asla yapılmayacaklar

- ⛔ **"Made for kids" işaretini kaldırma** — yorumları açmak için bile.
  COPPA ihlali, kanal ve sahibi için yasal risk.
- ⛔ **Senaryoyu otomatik onaylama.** İnsan onayı bu sistemdeki tek ve en önemli
  çocuk güvenliği kontrolü.
- ⛔ **Telifli şarkı sözü/melodi kullanma.** 1929 öncesi kamu malı eserler serbest.
  ("Geleneksel" sanılan bazı şarkılar telifli: *The Wheels on the Bus* 1939.)
- ⛔ **OAuth token'ı kanal adı doğrulanmadan kullanma.** Bir Google hesabı altında
  birden fazla kanal var; token yanlış kanala bağlanabiliyor.
- ⛔ **Beyaz liste dışı obje kullanma.** Claude'un istediği her obje
  `props.validate_prop()` ile doğrulanır.

---

## Görev Yönetimi

1. **Önce plan.** Planı `todo.md`'ye işaretlenebilir maddelerle yaz.
2. **Planı onaylat.** Uygulamaya başlamadan danış.
3. **İlerlemeyi işle.** Maddeleri bittikçe işaretle (kanıtla, bkz. madde 10).
4. **Sonucu belgele.** `todo.md`'deki **İnceleme** bölümüne sonucu ve kanıtı yaz.
5. **Dersleri yakala.** Düzeltmelerden sonra `docs/lessons.md`'yi güncelle.
6. **Changelog.** Her geliştirme, iyileştirme ve önemli bulgudan sonra
   `docs/changelog.md`'ye ne yapıldığını ve nasıl çalıştığını yaz; tarih, video ID,
   kanal ID, secret **adı** (değeri değil) ekle.
7. **İşlem günlüğü.** YouTube, GitHub, Google Cloud ve Telegram üzerinde yapılan her
   işlemi `docs/islem-gunlugu.md`'ye tarihli yaz.
8. **Kararlar.** Mimari ve içerik kararlarını gerekçesiyle `docs/kararlar.md`'ye
   tarihli yaz.
