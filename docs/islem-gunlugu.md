# İşlem Günlüğü

YouTube, GitHub, Google Cloud ve Telegram üzerinde yapılan **her işlem** tarihli
olarak buraya yazılır. Secret değerleri yazılmaz, yalnızca adları.

Format: `tarih · sistem · işlem · sonuç`

---

## 2026-11-02

### YouTube
- `11-02` · YouTube · **Kanal oluşturuldu**: "Thumpy Meadow", `@ThumpyMeadow`,
  ID `UC9_bFi-Pyp8hTlclZYkcz-Q`, sahibinin Google hesabı altında brand account
  → başarılı
- `11-02` · YouTube Studio · Profil resmi yüklendi (kanal oluşturma sırasında)
  → başarılı
- `11-02` · YouTube Studio · **Kanal açıklaması** yazıldı ve yayınlandı
  → "Changes published" doğrulandı
- `11-02` · YouTube Studio · **10 kanal anahtar kelimesi** eklendi (nursery rhymes,
  kids songs, songs for kids, toddler learning, preschool, learn colors,
  counting songs, dinosaur cartoon, cartoons for kids, baby songs) → kaydedildi
- `11-02` · YouTube Studio · **Audience: "made for kids"** seçildi (COPPA)
  → "Settings saved" doğrulandı. Sonuç: yorumlar, bildirimler ve kişiselleştirilmiş
  reklam kapandı (beklenen davranış)
- `11-02` · YouTube Studio · Banner yüklendi (kullanıcı) → başarılı
- `11-02` · YouTube Studio · Ülke ayarı yapıldı (kullanıcı) → başarılı
- `11-02` · YouTube · **Telefon doğrulaması** (`youtube.com/verify`) → "Phone number
  verified". Sonuç: özel küçük resim izni açıldı
- `11-02` · YouTube API · **İlk video yüklendi**: `WIEorW7zW10`,
  "Learn Fruit Names & Colors | Yummy Fruits for Kids | Thumpy Meadow", 10:41,
  `private` + `publishAt` 2026-11-02 18:00 UTC (21:00 TR), `madeForKids=true`,
  `categoryId=27` → başarılı
- `11-02` · YouTube API · Küçük resim yükleme **başarısız**: "The authenticated user
  doesn't have permissions to upload and set custom video thumbnails"
  → sebep: telefon doğrulaması o an yoktu; sonradan doğrulandı
- `11-02` · YouTube Studio · 3 küçük resim elle yüklendi ve **A/B testi** kuruldu
  ("Thumbnail only" modu) → başarılı

### GitHub
- `11-02` · GitHub · Repo oluşturuldu: `ufukkcan/thumpy-meadow-automation`,
  **public** → başarılı
- `11-02` · GitHub · 16 Python/metin dosyası yüklendi (kök dizine) → başarılı
- `11-02` · GitHub · `.github/workflows/check_and_produce.yml` oluşturuldu → başarılı
- `11-02` · GitHub · `.github/workflows/yt_oauth_exchange.yml` oluşturuldu → başarılı
- `11-02` · GitHub · Settings → Actions → **Read and write permissions** → ayarlandı
- `11-02` · GitHub Secrets · Eklendi: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`,
  `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ANTHROPIC_API_KEY`, `YT_REFRESH_TOKEN`
  → 6 secret
- `11-02` · GitHub Actions · İlk uçtan uca çalıştırma → başarılı (üretim 13 dk)
- `11-02` · GitHub · Küçük resim güncellemesi: 6 dosya yeniden yüklendi
  (`thumbnail.py`, `scene2d.py`, `props.py`, `generate_episode.py`, `produce.py`,
  `check_and_produce.py`) → başarılı

### Google Cloud
- `11-02` · Google Cloud · Mevcut `shorts-bot-web` (Web application) OAuth client
  kullanıldı; redirect URI `https://ufukkcan.github.io/tiktok-legal-pages/callback.html`
- `11-02` · Google OAuth · **1. yetkilendirme denemesi** → token **Interesthings**
  kanalına bağlandı → **KULLANILMADI** (kanal doğrulama kontrolü yakaladı)
- `11-02` · Google OAuth · **2. yetkilendirme denemesi** → kanal seçim ekranından
  "Thumpy Meadow" seçildi → token doğrulandı ("BU TOKEN SU KANALA AIT: Thumpy Meadow")
  → `YT_REFRESH_TOKEN` olarak kaydedildi

### Telegram
- `11-02` · BotFather · Bot oluşturuldu: `Thumpy Meadow Bot` / `@thumpymeadow_bot`
  → token alındı
- `11-02` · Telegram · Bota `/start` yazıldı → bot mesaj gönderebilir durumda
- `11-02` · Telegram · İlk akış test edildi: fikirler → seçim → senaryo → onay
  → tüm adımlar başarılı

---

## 2026-11-03

### YouTube
- `11-03` · YouTube Studio · İlk gün analitiği alındı: 509 gösterim, 12 izlenme,
  %2,2 CTR, 2:09 ortalama izlenme, trafik %100 "Suggested videos"

### GitHub
- `11-03` · GitHub · `.github/workflows/sing_test.yml` oluşturuldu (deneysel) → başarılı
- `11-03` · GitHub · Şarkı deneme dosyaları yüklendi: `songs.py`, `singer.py`,
  `sing_test.py`, `rhythmic.py` (birkaç kez güncellendi) → başarılı
- `11-03` · GitHub Actions · Şarkı testi çalıştırmaları:
  - 1. deneme → **hata**: `ModuleNotFoundError: pkg_resources` → `setuptools<81` eklendi
  - 2. deneme → **hata**: YAML yanlışlıkla `sing_test.py` içine yapıştırılmış
    → dosyalar düzeltildi
  - 3. deneme → başarılı, E/F versiyonları üretildi
  - 4. deneme → başarılı, G versiyonu üretildi
- `11-03` · GitHub Actions · `rubberband-cli` sistem paketi workflow'a eklendi
- `11-04` · GitHub · Kullanıcı fine-grained token `thumpy-claude-push` oluşturdu
  (yalnızca bu repo, Contents + Workflows yazma, 1 yıl). Değer yalnızca Windows
  Credential Manager'da. Kural: her push öncesi dosya listesi gösterilip onay alınır.
- `11-04` · GitHub · Claude ilk push'u yaptı (`eff0441`, main): `samples.py`, `kidsong.py`,
  `music_test.py`, `.github/workflows/music_test.yml`, `todo.md`, `docs/kararlar.md`
- `11-04` · GitHub Actions · Kullanıcı "Muzik molasi testi"ni çalıştırdı → başarılı,
  kullanıcı dinledi ve onayladı
- `11-04` · GitHub · Push `7d05e2a`: `vocal_probe.py`, `vocal_probe.yml`, `music_test.py`
  (TP -1.5), belge güncellemeleri
- `11-04` · GitHub Actions · "Vokal kesif" çalıştırması (run 41827925219) → **hata**:
  onnxruntime C++ assertion, kod 134 (bkz. lessons E10)
- `11-04` · GitHub · Kullanıcı `thumpy-claude-push` token'ına "Actions: Read-only" ekledi
  (Claude'un hata loglarını okuyabilmesi için)

- `11-05` · GitHub · Push `2d4ad73` (yeni dal `vocal-integration`) → `episode_test` run 41979380747 başarılı
- `11-05` · GitHub · Kullanıcı onayıyla `vocal-integration` → `main` birleştirildi (`fb231c2`): yeni vokalli müzik molası üretimde
- `11-05` · GitHub Actions · **Token sızıntısı bulundu**: `yt_oauth_exchange` run 41448523899 ve
  41448204357 loglarında refresh token maskesiz (public repo). Kullanıcı iki run'ı sildi →
  API doğruladı: run ve log 404, kalan run 0 (bkz. lessons C4b)
- `11-05` · Karar (kullanıcı) · Sızan token'lar **iptal edilmedi**; risk kabul edildi.
  Genel anahtar yenilemesinde (bekleyen işlemler) birlikte yenilenecek.
- `11-05` · GitHub · Push `52a8f68` + `7839e80` (yeni dal `visual-proto`): Skia motoru, Fluent nesneler,
  yeni Dino. Run 41987847621 hata (libEGL eksik) → apt paketleri eklendi → run 41989750327 başarılı:
  65 sn video, 79 ms/kare (12 dk bölüm ≈ 23 dk render)
- `11-05` · GitHub · Kullanıcı senaryoyu ("Dino'nun Saklambacı") ve push'u onayladı → push `ef1968d`
  (`visual-proto`): `pilot.py`, `pilot.yml`, çizgi film stili `render2.py`; `visual_proto.yml` yalnızca elle
- `11-05` · GitHub Actions · Pilot run 42010325985 başarılı (3:19). Kullanıcı tur 1 geri bildirimi verdi
- `11-05` · GitHub · Kullanıcı tur 2 senaryosunu ("Doğum Günü Saklambacı"), beyaz listeye cake + crown
  eklenmesini ve push'u onayladı (7c) → push `69212e6`; run 42016648248 başarılı (3:47, 65 ms/kare)
- `11-05` · GitHub · Kullanıcı 7d push'unu onayladı → push `40bfc43` (`visual-proto`): show.py motoru,
  yeni Claude şeması, SEO + localizations, thumbs.py, kanal doğrulaması, show_test.yml. main'e dokunulmadı
- `11-05` · GitHub Actions · show_test run 42022806206 hata: koyun sesinden çağrı kesilemedi (lessons E15)
- `11-05` · GitHub · Kullanıcı düzeltme push'unu onayladı ("pushla") → push `02e0625`; run 42023322949
  başarılı (7:23, 78 ms/kare); karelerde eski saklanma yerlerinin birikmesi bulundu
- `11-05` · GitHub · Kullanıcı son test push'unu onayladı ("tamam yapalim") → push `7c08a98`;
  run 42028706502 hata: Claude cevabı ayrıştırılamadı (lessons E17). Kural 8: durup soruldu
- `11-05` · GitHub · Kullanıcı öneriyle devam etti ("önerinle devam edelim") → push `ce3410c`;
  run 42029359003 başarılı (8:08 bölüm, 3 thumbnail)
- `11-05` · GitHub · Kullanıcı main'e birleştirmeyi onayladı → WALK düzeltmesi + `visual-proto` → `main`
  (`d91243f`); show_test 42034601443 başarılı (finalde eski ağaç yok, doğrulandı)
- `11-05` · GitHub Actions · Kullanıcı üretimi elle tetikledi; Telegram onayı → wfW6tyCYbz4 yüklendi
  (yayın 5 Kasım 18:00 UTC). Not: 5 dk'lık cron gerçekte günde 4–5 kez çalışıyor
- `11-06` · YouTube Studio · Kullanıcı analitik CSV verdi: H9epa9bfhhI 63 gösterim, %0 CTR, 0 izlenme
- `11-06` · GitHub · Kullanıcı Shorts planını ve test push'unu onayladı (7e)
---

## Bekleyen işlemler

- [ ] Tüm secret'ların yenilenmesi (Anthropic, Telegram, Google client secret,
      refresh token) — `docs/secrets.md`
- [ ] `astrologicalshorts` refresh token'ının kanal doğrulaması
