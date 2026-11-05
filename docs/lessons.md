# Dersler: Yaşanan Hatalar, Sorunlar ve Çözümleri

Bu dosya projede yaptığımız **tüm hataları** kaydeder — benim (asistan) hatalarım,
araçların tuzakları ve dış servislerin sürprizleri. Amaç aynı hataya ikinci kez
düşmemek. Yeni bir oturumda bu dosya mutlaka okunmalı.

---

## A. Benim (asistanın) yaptığı hatalar

### A1. ffmpeg hatasını gizlemek
**Hata:** `subprocess.run(..., capture_output=True)` kullanıp hata mesajını hiç
göstermedim. Kullanıcı sadece "exit code 254" gördü, saatlerce ne olduğunu anlayamadık.
**Çözüm:** `_run()` yardımcısı yazıldı; hata olursa ffmpeg'in kendi `stderr` çıktısının
son 25 satırını exception'a ekliyor.
**Kural:** Dış bir komut çalıştıran her yerde hata çıktısı kullanıcıya ulaşmalı.

### A2. Dosyayı eklemeyi unutup hatayı başka yerde aramak
**Hata:** `assets/tap_ring.png` dosyasını kullanıcıya hiç vermedim, kod onu arayınca
ffmpeg 254 ile çöktü. Sorunu kodda aradım.
**Çözüm:** Eksik dosya tespit edildi ve verildi.
**Kural:** Kod yeni bir dosyaya bağımlı hale geldiyse, o dosyanın kullanıcıya
verildiğinden emin ol.

### A3. Yanlış dosyaya yapıştırma talimatı
**Hata:** YAML içeriğini verirken hangi dosyaya gideceğini yeterince net söylemedim;
kullanıcı YAML'ı `sing_test.py` içine yapıştırdı, `SyntaxError` aldık.
**Çözüm:** Artık her kod bloğunun başında **tam dosya yolu** yazılıyor ve
`.py` → Python, `.yml` → YAML ayrımı açıkça belirtiliyor.

### A4. "Satırı bul" tarzı belirsiz talimatlar
**Hata:** "şu satırı bul ve değiştir" dedim; kullanıcı bulamadı, tüm dosyayı YAML ile
değiştirdi ve workflow bozuldu.
**Çözüm:** Kullanıcı açıkça "bana satır arattırma" dedi. Artık **dosyanın tamamı**
veriliyor ve adım adım tek iş söyleniyor.

### A5. Ölçerken müzik altyapısını çıkarmayı unutmak
**Hata:** Şarkı analizinde karışımı doğrudan ölçtüm; davul ve bas sesi vokal sanıldı,
sapmalar 2–6 vuruş gibi saçma çıktı.
**Çözüm:** Müzik kodla üretildiği için birebir yeniden üretilip karışımdan çıkarıldı;
geriye sadece vokal kaldı.
**Kural:** Ölçüm yaparken ölçtüğün şeyin gerçekten istediğin sinyal olduğunu doğrula.

### A6. Ana sesli test yapmadan "robotik" yorumunu kabul etmek
**Hata:** Kullanıcı "aşırı robotik" dediğinde hangi dosyayı dinlediğini sormadım;
meğer benim ürettiğim kaba yerel sesli (espeak) örneği dinlemiş, Ana sesli test hiç
çalışmamıştı.
**Çözüm:** Önce hangi dosyanın dinlendiği netleştirildi.
**Kural:** Geri bildirim geldiğinde neyin değerlendirildiğini doğrula.

### A7. Telifli şarkı sözü kullanmak
**Hata:** İlk örnek videoda "The wheels on the bus go round and round" sözlerini
kullandım. Bu şarkı 1939'da yazılmış, yani telifli olabilir.
**Çözüm:** Gerçek videolarda kullanılmadı; tüm sözler özgün yazılıyor, melodiler
1929 öncesi kamu malı eserlerden seçiliyor.

### A8. Kelime kelime seslendirmenin doğallığı bozduğunu geç fark etmek
**Hata:** Şarkı denemelerinde her kelimeyi ayrı seslendirdim. İnsan konuşmasında
kelimeler birbirine bağlanır (koartikülasyon); tek tek söylenince anlaşılırlık düşer.
Bunu 3 versiyon sonra fark ettim.
**Durum:** Düzeltme hazırlandı (`SPLIT_SYLLABLES = False`), test edilmedi.

---

## B. GitHub tuzakları

### B1. Web arayüzü klasör yapısını bozuyor
**Sorun:** "Upload files" ile klasör sürüklenince dosyalar ana dizine düz olarak
dökülüyor.
**Çözüm:** Ya her klasörü ayrı ayrı yükle, ya "Create new file" ile dosya adına
`klasor/dosya.py` yazarak klasörü oluştur, ya da GitHub Desktop kullan.
**Not:** Thumpy reposunda dosyalar bu yüzden kökte duruyor; sorun değil, hepsi aynı
klasörde olduğu için import'lar çalışıyor.

### B2. Gizli klasörler yüklenemiyor
**Sorun:** `.github` klasörü "this file is hidden" diyerek yüklenemedi.
**Çözüm:** `.github/workflows/dosya.yml` yolunu "Create new file" ile elle yazmak.

### B3. Ücretsiz Actions dakikası private repoda tükeniyor
**Sorun:** 5 dakikada bir çalışan cron, aylık 2000 dakikalık ücretsiz kotayı hızla
bitirdi; "recent account payments have failed or your spending limit needs to be
increased" hatası geldi, hem otomatik hem elle çalıştırma durdu.
**Çözüm:** Repo **public** yapıldı. Public repolarda Actions ücretsiz ve sınırsız.
**Kural:** Bu tarz sık çalışan otomasyonlar public repoda tutulmalı; gizli bilgi
zaten Secrets'ta, kodda değil.

### B4. Cron gecikiyor
**Sorun:** 5 dakikalık cron pratikte saatlerde bir çalışıyor (GitHub yoğunlukta
zamanlanmış işleri erteliyor).
**Geçici çözüm:** Butona bastıktan sonra elle "Run workflow".
**Kalıcı çözüm (yapılmadı):** cron-job.org gibi harici bir tetikleyici.

### B5. GitHub Actions kesintisi
**Sorun:** 2026-08-06'da GitHub'da genel Actions kesintisi oldu; işler "Queued"da
takıldı, "Failed to resolve action download info / Service Unavailable" hataları geldi.
**Çözüm:** Beklemek. `githubstatus.com` kontrol edildi, kesinti doğrulandı.
**Kural:** Tuhaf, açıklanamayan Actions hatalarında önce githubstatus.com'a bak.

### B6. Yarım kalan çalıştırma botu kilitliyor
**Sorun:** Kesinti sırasında iptal edilen çalıştırma Telegram mesajını "okundu"
işaretleyip işlemeden bitti; bot bir daha o mesajı görmedi, "video üret" çalışmaz oldu.
**Çözüm:** "video üret" artık **her durumda** mevcut durumu sıfırlayıp yeni döngü
başlatıyor (aktif/tıkanmış döngü olsa bile).

---

## C. Google / YouTube tuzakları

### C1. OAuth "Testing" modunda refresh token 7 günde ölüyor
**Sorun:** `invalid_grant: Bad Request`. Uygulama Google Cloud'da "Testing"
durumundaydı; bu moddaki refresh token'lar 7 gün sonra geçersiz oluyor.
**Çözüm:** Google Auth Platform → Audience → **Publish app** (In production).
Bunun için App name, support email, **homepage URL** ve **privacy policy URL** şart.
GitHub Pages'teki sayfalar bu amaçla kullanıldı.

### C2. Authorized domain eklemeden URL kabul edilmiyor
**Sorun:** "Missing domain: ufukkcan.github.io"
**Çözüm:** Branding sayfasında "Authorized domains" bölümüne `ufukkcan.github.io`
eklemek (başında `https://` olmadan).
**Ek tuzak:** Kopyala-yapıştır sonunda görünmez boşluk bırakıyor
("Invalid domain: cannot contain whitespace") → elle yazmak gerekti.

### C3. `urn:ietf:wg:oauth:2.0:oob` artık çalışmıyor
**Sorun:** Google eski "kodu ekranda göster" yöntemini kaldırdı: `Error 400: invalid_request`
**Çözüm:** "Desktop app" yerine **"Web application"** tipinde yeni OAuth client
oluşturup gerçek bir redirect URI vermek:
`https://ufukkcan.github.io/tiktok-legal-pages/callback.html`

### C4. ⚠️ Token yanlış kanala bağlanıyor — EN TEHLİKELİ TUZAK
**Sorun:** Bir Google hesabı altında birden fazla YouTube kanalı varsa, OAuth
sırasında kanal seçim ekranı atlanabiliyor ve token **ana kanala** bağlanıyor.
Thumpy Meadow için alınan ilk token Interesthings'e aitti. Fark edilmeseydi çocuk
videoları yanlış kanala yüklenecekti.
**Çözüm:** `yt_oauth_exchange.py` token aldıktan sonra `channels?mine=true` çağırıp
**kanal adını ekrana yazıyor**. Ad beklenen kanal değilse token kullanılmıyor.
**Kural:** Her yeni kanal yetkilendirmesinde kanal adı mutlaka doğrulanmalı.
**Açık risk:** `astrologicalshorts` token'ı bu kontrol eklenmeden alındı; kullanıcı
"sorun yok, çalışıyor" dedi ama resmen doğrulanmadı.

### C4b. ⚠️ Refresh token public repo loguna yazıldı (2026-11-05'te fark edildi)
**Hata (asistan, önceki oturumlar):** `yt_oauth_exchange.py` refresh token'ı `print` ile loga
yazıyordu. Repo public; kayıtlı secret olmayan değerler maskelenmez → Thumpy Meadow ve
Interesthings token'ları (run 41448523899, 41448204357) 3 gün açıkta kaldı.
**Çözüm:** Çalıştırmalar silindi (11-05, API ile doğrulandı). Token iptali kullanıcı kararıyla
genel anahtar yenilemesine ertelendi; yeni token OAuth Playground ile (tarayıcıda, loga/sohbete
düşmeden) alınacak.
**Kural:** Public repoda bir workflow ASLA secret niteliğinde değer yazdırmaz. Zorunluysa
önce `::add-mask::`; tercihen değer hiç workflow'a girmez. Yeni workflow yazarken loglarda
ne göründüğünü kontrol et.

### C5. Özel küçük resim telefon doğrulaması istiyor
**Sorun:** "The authenticated user doesn't have permissions to upload and set custom
video thumbnails"
**Çözüm:** İlgili kanala geçip `youtube.com/verify` adresinden telefon doğrulaması.
**Kural:** Yeni kanal kurulurken ilk videodan **önce** yapılmalı.

### C6. "Made for kids" yorumları ve bildirimleri kapatıyor
**Durum:** Bu bir hata değil, COPPA gereği. YouTube 2019'da FTC'ye 170 milyon dolar
ceza ödedi, o günden beri katı.
**Kural:** Yorumları açmak için "made for kids" işaretini kaldırmak **yapılmamalı**;
yanlış etiketleme kanalı ve sahibini cezai riske sokar.

### C7. Yayın tarihi ilk yüklemede sabitleniyor
**Gözlem:** Gizli yüklenen bir video sonradan herkese açık yapılınca tarih damgası
değişmiyor ("46 dakika önce" olarak kalıyor).
**Sonuç:** Videoyu günlerce gizli bekletmek, algoritmanın onu "taze" görmemesine yol
açabilir. Onaylandıktan sonra mümkün olduğunca çabuk yayına girmeli.

---

## D. TikTok denemesi (terk edildi)

Bir ara içerik TikTok'a yönlendirilmek istendi, sonra YouTube'a geri dönüldü.
Yaşananlar başka bir projede işe yarayabilir:

- **D1.** TikTok'un Sandbox ve Production ortamlarının **ayrı Client Key/Secret**'ı var.
  Production anahtarıyla Sandbox'a bağlanılmıyor (`client_key` hatası).
- **D2.** `localhost` redirect URI kabul edilmiyor ("localhost is not supported").
  GitHub Pages'te bir `callback.html` sayfası yazıldı (sonradan YouTube OAuth için de
  kullanıldı).
- **D3.** PKCE zorunlu (`code_challenge` + `code_challenge_method=S256`).
- **D4.** `video.upload` yetkisi Content Posting API için **yetmiyor**
  (`scope_not_authorized`); `video.publish` gerekiyor, o da "Direct Post" ayarını
  açmayı ve ağır inceleme formunu doldurmayı gerektiriyor.
- **D5.** `unaudited_client_can_only_post_to_private_accounts`: onaylanmamış uygulama
  sadece **gizli hesaplara** paylaşabiliyor. Gizli hesap da keşfete düşmediği için
  büyüme hedefiyle çelişiyor — bu yüzden TikTok terk edildi.

---

## E. Kütüphane ve araç tuzakları

### E1. libass `MarginV` ölçeklemesi
**Sorun:** Altyazı `MarginV=380` ile ekranın üstüne, görünmez bir noktaya itildi.
libass bu değeri büyük bir katsayıyla ölçeklediği için küçük değişiklikler konumu
çok değiştiriyor.
**Çözüm:** Deneysel olarak doğrulandı: 1080×1920 için `MarginV=40` doğru;
TikTok'un alt arayüzünden kaçmak için `170`.
**Kural:** Altyazı konumu değişirse gerçek kare çıkarıp **gözle** doğrula.

### E2. `edge-tts` sürümü eskiyince 401/403 veriyor
**Sorun:** Microsoft güvenlik parametresini değiştirince eski sürüm
`401/403 Invalid response status` alıyor.
**Çözüm:** Sürümü yükselt (6.1.19 → 7.2.8 → 7.3.1).

### E3. Telegram dosya limitleri
**Sorun:** Bot API ile **gönderme** limiti 50 MB, **indirme** limiti 20 MB.
Video 50 MB'ı aşınca `413 Request Entity Too Large`.
**Çözüm (Shorts projelerinde):** Süreye göre bitrate hesaplama (hedef 30 MB) ve
onaylanan videoyu Telegram'dan indirmek yerine **yeniden üretmek**.
**Thumpy'de:** 10 dk video zaten Telegram'a sığmaz; bu yüzden **senaryo onayı**
modeline geçildi.

### E4. `pyworld` için `setuptools<81` gerekiyor
**Sorun:** `ModuleNotFoundError: No module named 'pkg_resources'`. pyworld eski
`pkg_resources`'u kullanıyor, Python 3.12'de setuptools varsayılan gelmiyor.
**Çözüm:** `pip install "setuptools<81" pyworld==0.3.5`

### E5. Rubber Band'in iki motoru var
**Gözlem:** ffmpeg'in `rubberband` filtresi eski R2 motorunu kullanıyor ve insan
sesinde metalik tını bırakıyor. `rubberband-cli` paketindeki `-3` (R3/finer) motoru
çok daha temiz.
**Çözüm:** Perde/zaman işlemleri `rubberband -3 -F` ile komut satırından yapılıyor.

### E6. ffmpeg çıkış kodu 254 çoğunlukla "girdi dosyası yok" demek
**Gözlem:** Eksik dosya da, bozuk filtre de aynı kodu veriyor. Hata mesajı olmadan
ayırt edilemiyor (bkz. A1).

### E7. Anthropic "identity-linked" API anahtarı çalışmıyor
**Sorun:** `anthropic-workspace-id is required when authenticating with an
identity-linked API key`
**Çözüm:** Anahtar oluştururken **"Not linked"** seçilmeli ("Continue with API key"),
hesaba bağlı (linked) anahtar değil.

### E8. Hece sayma kuralları
**Gözlem:** Basit ünlü grubu sayımı `grapes` (1), `apples` (2), `counted` (2),
`jumped` (1) gibi kelimelerde yanılıyor.
**Çözüm:** Sessiz `-e`, `-es`, `-ed` kuralları + istisna sözlüğü (`triangle`, `lion`,
`dinosaur`...). 54 kelimelik testte 54/54 doğru.

---

### E9. Claude Code oturumunda git push kimlik penceresi açılmıyor
**Sorun:** `fatal: Cannot prompt because user interactivity has been disabled`.
Oturum `GCM_INTERACTIVE=never` ve `GIT_TERMINAL_PROMPT=0` ile başlıyor.
**Çözüm:** İlk push'ta yalnızca o komut için `GCM_INTERACTIVE=always` + `GIT_ASKPASS`
kaldırılır; kullanıcı açılan pencereye token'ı girer. Sonrası kayıtlı, pencere açılmaz.
**Kural:** Push, yerel çalışma klasöründen değil scratchpad'deki temiz klondan yapılır
(yerelde dal adı `master`, uzakta `main`; yerelde yüklenmemesi gereken kopya belgeler var).

### E10. onnxruntime C++ içinde çökünce Python yakalayamıyor, rapor kayboluyor
**Sorun:** `vocal_probe.py` bir DiffSinger modelini yüklerken onnxruntime 1.20.1
`Assertion '__n < this->size()' failed` → süreç `Aborted (core dumped)`, kod 134.
`try/except` işe yaramadı; rapor en sonda yazıldığı için hiçbir bilgi kalmadı.
**Çözüm:** Rapor adım adım diske yazılır; model yapısı `onnx` paketiyle (çalıştırmadan)
okunur; onnxruntime yüklemesi her model için ayrı alt süreçte denenir.
**Kural:** Native kütüphane (onnxruntime, ffmpeg, torch) ile keşif/toplu iş yaparken
her riskli adımı alt süreçte çalıştır ve sonucu anında diske yaz; artifact adımına
`if: always()` koy.

### E11. GitHub Actions logu public repoda bile kimlik istiyor
**Sorun:** `actions/jobs/{id}/logs` → 403. Token'da "Actions: Read-only" yoktu.
**Çözüm:** Token'a Actions okuma izni eklendi (kullanıcı, 2026-11-04). Log okurken token
Credential Manager'dan `git credential fill` ile alınır (PowerShell'de girdi bir
ASCII dosyadan `cmd /c "git credential fill < dosya"` ile verilir; boru BOM ekliyor ve
"missing protocol field" hatası veriyor). Değer hiçbir zaman yazdırılmaz.

### E12. DiffSinger ses bankasının `dsdict-en.yaml`'ı tam sözlük değil
**Sorun:** "the", "a", "apple" dahil neredeyse hiçbir kelime bulunamadı. Dosya yalnızca
ek girişler içeriyor (isimler, semboller, sayılar); OpenUtau İngilizce telaffuzu kendi
CMUdict tabanlı G2P'siyle yapıyor.
**Çözüm:** CMU Pronouncing Dictionary (BSD, sabit commit) + ARPAbet → küçük harf,
vurgu rakamı atılır. Bankanın girişleri yalnızca CMU'da olmayan kelimeler için.
**Kural:** Bir dosyanın "sözlük" olduğunu adından varsayma; keşifte giriş sayısına ve
birkaç sıradan kelimeye bak (kural 2).

### E13. Ölçmeden eklenen "iyileştirme" sesi bozdu (vokal deneme 1)
**Hata (asistan):** DiffSinger mel'inin tabanının -6 olduğunu VARSAYIP, -4 altını sessizliğe
genişleten bir dönüşüm ekledim. Yüksek harmonikler o aralıktaydı → ses boğuk/bozuk.
Ölçüm (vocoder uyumu 2.1–2.4) bunu gösterdi; kullanıcı "ses kalitesi berbat" dedi.
**Çözüm:** Genişletme kaldırıldı; rapora gerçek mel dağılımı ve kopya sentez (gerçek
kayıt → mel → vocoder) tavan ölçümü eklendi.
**Kural:** Sinyal zincirine "temizlik/gürültü kapısı" gibi bir adım eklemeden önce değer
dağılımını ölç; her ara adım için kopya sentez gibi bir tavan testi koy (madde 2, 10).

### E14. Yerel kopyalar CRLF, repo LF → tüm dosya "değişmiş" görünüyor
**Sorun:** Proje klasöründeki eski dosyalar (episode.py vb.) Windows'ta CRLF; repoda LF.
Scratchpad klonuna kopyalayınca 3 satırlık değişiklik 277 satır göründü.
**Çözüm/Kural:** Push öncesi `git diff --cached --numstat` mutlaka kontrol; CRLF içeren
dosyalar LF'ye çevrilip yeniden eklenir (BOM'suz UTF-8).

---

## F. Kullanıcı ortamı kısıtları

### F1. İş bilgisayarı script çalıştırmayı engelliyor
**Sonuç:** Yerel Python ile yapılacak her iş (OAuth kurulumu gibi) GitHub Actions
üzerinden yapılacak şekilde yeniden tasarlandı (`yt_oauth_exchange.yml`).
**Kural:** Kullanıcıdan asla "bilgisayarında şu scripti çalıştır" isteme.

### F2. Benim çalışma ortamımın ağ kısıtları
**Gözlem:** Sandbox'ımdan Microsoft TTS sunucusuna, NASA efemeris sunucusuna ve
çoğu siteye erişim yok. Sadece belirli domainler açık (api.anthropic.com, github,
pypi, npm...).
**Sonuç:** Sesli çıktılar yerelde üretilemiyor; gerçek test GitHub Actions'ta yapılmalı.
Yerelde kaba bir yerel sesle (`espeak-ng`) sadece **akış/kod** doğrulanabilir.
**Kural:** Yerelde üretilen espeak örnekleri kalite değerlendirmesi için kullanılmaz.
