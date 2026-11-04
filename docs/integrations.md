# Entegrasyonlar

Her dış servisin nasıl bağlandığı, hangi kimlik bilgisini kullandığı ve tuzakları.

---

## 1. Anthropic Claude API

| | |
|---|---|
| Ne için | Bölüm fikirleri, tam senaryo, SEO metinleri |
| Model | `claude-sonnet-4-6` |
| Kütüphane | `anthropic==0.40.0` |
| Kimlik | GitHub Secret `ANTHROPIC_API_KEY` |
| Maliyet | Bölüm başına birkaç sent |

**Anahtar oluşturma:** console.anthropic.com → Settings → API Keys → Create Key.
Seçim ekranı çıkarsa **"Continue with API key"** ve **"Not linked"** seçilmeli.
"Linked" anahtarlar `anthropic-workspace-id` istiyor ve bu kodla çalışmıyor.

---

## 2. Microsoft Edge TTS (seslendirme)

| | |
|---|---|
| Ne için | Anlatım sesi |
| Kütüphane | `edge-tts==7.3.1` |
| Ses | `en-US-AnaNeural` (çocuk sesi) |
| Hız | `-10%` |
| Kimlik | Yok (anahtar gerektirmez) |

**Tuzak:** Microsoft güvenlik parametresini değiştirince eski sürümler `401/403`
veriyor. Böyle bir hata gelirse `edge-tts` sürümünü yükselt.

**Not:** Kelime zamanlamaları (`WordBoundary`) da alınabiliyor; şarkı denemelerinde
bu kullanılıyor.

---

## 3. YouTube Data API v3

| | |
|---|---|
| Ne için | Video yükleme, küçük resim, izlenme istatistiği |
| Kütüphane | `google-api-python-client==2.149.0`, `google-auth==2.35.0` |
| Yetki | `youtube.upload` + `youtube.readonly` |
| Kimlik | `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` |

### OAuth kurulumu (bir kez)

1. Google Cloud Console → Credentials → **Create OAuth client ID** →
   **Web application** (Desktop DEĞİL)
2. Authorized redirect URI: `https://ufukkcan.github.io/tiktok-legal-pages/callback.html`
3. Google Auth Platform → Branding: App name, support email, homepage URL,
   privacy policy URL, **Authorized domains → `ufukkcan.github.io`**
4. Audience → **Publish app** (Testing modunda token 7 günde ölür)
5. Yetkilendirme linki (gizli sekmede açılır):

```
https://accounts.google.com/o/oauth2/v2/auth
  ?client_id=<CLIENT_ID>
  &redirect_uri=https%3A%2F%2Fufukkcan.github.io%2Ftiktok-legal-pages%2Fcallback.html
  &response_type=code
  &scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube.upload+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube.readonly
  &access_type=offline
  &prompt=consent+select_account
```

6. ⚠️ **Giriş sırasında kanal seçim ekranında doğru kanalı seç.** Bir Google hesabı
   altında birden fazla kanal varsa token yanlış kanala bağlanabilir.
7. callback sayfası kodu gösterir → GitHub Actions'ta
   **"YouTube yetkilendirme (tek seferlik)"** workflow'una gir
8. Log'daki **"BU TOKEN SU KANALA AIT:"** satırını kontrol et. Beklenen kanal
   değilse token'ı KULLANMA, 5. adımdan tekrarla.
9. Doğruysa refresh token'ı `YT_REFRESH_TOKEN` secret'ına ekle

### Yükleme ayarları

```python
status = {
    "privacyStatus": "private",
    "publishAt": "<ISO8601 UTC>",
    "selfDeclaredMadeForKids": True,   # COPPA — zorunlu
    "embeddable": True,
}
snippet = {"categoryId": "27", "defaultLanguage": "en", "defaultAudioLanguage": "en"}
```

**Küçük resim:** Kanal telefonla doğrulanmamışsa yüklenemez
(`youtube.com/verify`, ilgili kanala geçerek).

---

## 4. Telegram Bot API

| | |
|---|---|
| Ne için | Fikir seçimi, senaryo onayı, bildirimler |
| Bağlantı | Düz HTTP (`requests`), kütüphane yok |
| Bot | `@thumpymeadow_bot` |
| Kimlik | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |

**Kurulum:** Telegram'da `@BotFather` → `/newbot` → isim ve kullanıcı adı →
token alınır. **Sonra bota `/start` yazılmalı**, yoksa bot mesaj gönderemez.

**Chat ID bulma:** `https://api.telegram.org/bot<TOKEN>/getUpdates` →
`message.chat.id`

**Limitler:** Gönderme 50 MB, indirme 20 MB. Bu yüzden 10 dakikalık video Telegram'a
gönderilmiyor; onay **senaryo metni** üzerinden yapılıyor.

---

## 5. GitHub Actions

| | |
|---|---|
| Ne için | Tüm sistemi çalıştırır |
| Runner | `ubuntu-latest`, Python 3.12 |
| Tetikleme | `cron` (5 dk) + `workflow_dispatch` (elle) |
| İzin | `contents: write` (state'i repoya yazmak için) |
| Maliyet | Public repoda ücretsiz ve sınırsız |

**Sistem paketleri:** `ffmpeg`, `fonts-dejavu-core` (+ şarkı testinde `rubberband-cli`)

**Tuzaklar:**
- Cron gecikir (saatlerde bir çalışabilir) → elle tetikleme
- Private repoda ücretsiz dakika tükenir → **public olmalı**
- Actions kesintisi olabilir → `githubstatus.com`

---

## 6. GitHub Pages (OAuth callback)

| | |
|---|---|
| Repo | `ufukkcan/tiktok-legal-pages` (public) |
| Sayfalar | `index.html`, `privacy.html`, `terms.html`, `callback.html` |
| Ne için | OAuth yönlendirme adresi + Google'ın istediği yasal sayfalar |

**Not:** Klasör adı TikTok denemesinden kalma; TikTok terk edildi ama sayfalar
YouTube OAuth için kullanılmaya devam ediyor. Adı değiştirmek Google Cloud'daki
redirect URI ve authorized domain ayarlarını da değiştirmeyi gerektirir.

`callback.html` yaptığı iş: adres çubuğundaki `?code=...` parametresini okuyup
ekranda büyük puntoyla gösterir ve "Kodu kopyala" butonu sunar.
