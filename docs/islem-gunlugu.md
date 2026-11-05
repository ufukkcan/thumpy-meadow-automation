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
---

## Bekleyen işlemler

- [ ] Tüm secret'ların yenilenmesi (Anthropic, Telegram, Google client secret,
      refresh token) — `docs/secrets.md`
- [ ] `astrologicalshorts` refresh token'ının kanal doğrulaması
