# Kimlik Bilgileri Envanteri

⚠️ **Bu dosyada gizli değerler YOKTUR ve yazılmamalıdır.** Burada sadece hangi
bilginin nerede durduğu ve nasıl yenileneceği yazar.

---

## GitHub Secrets (repo: `thumpy-meadow-automation`)

Settings → Secrets and variables → Actions

| Secret adı | Ne | Nereden alınır | Yenileme |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API anahtarı | console.anthropic.com → Create Key (**Not linked**) | Eskisini sil, yenisini oluştur |
| `TELEGRAM_BOT_TOKEN` | Bot token | @BotFather → `/mybots` → API Token → Revoke | Revoke edip yenisini al |
| `TELEGRAM_CHAT_ID` | Sohbet kimliği | `getUpdates` | Değişmez |
| `YT_CLIENT_ID` | OAuth client kimliği | Google Cloud → Credentials | Gizli değil |
| `YT_CLIENT_SECRET` | OAuth client sırrı | Google Cloud → Credentials | Add secret / rotate |
| `YT_REFRESH_TOKEN` | Kanal yetkisi | `yt_oauth_exchange` workflow çıktısı | Yetkilendirmeyi tekrarla |

---

## Gizli olmayan tanımlayıcılar

Bunlar herkese açık ya da zararsız bilgilerdir:

| Bilgi | Değer |
|---|---|
| YouTube kanal ID | `UC9_bFi-Pyp8hTlclZYkcz-Q` |
| YouTube kullanıcı adı | `@ThumpyMeadow` |
| Google hesabı | Kanal sahibinin Gmail adresi (repo public olduğu için yazılmadı) |
| Telegram bot kullanıcı adı | `@thumpymeadow_bot` |
| GitHub repo | `ufukkcan/thumpy-meadow-automation` (public) |
| OAuth redirect URI | `https://ufukkcan.github.io/tiktok-legal-pages/callback.html` |
| OAuth client adı | `shorts-bot-web` (Web application) |

---

## ⚠️ Yenilenmesi gereken anahtarlar

Kurulum sırasında aşağıdaki gizli değerler sohbet ortamında paylaşıldı.
Güvenlik için **hepsi yenilenmeli** ve GitHub Secrets güncellenmelidir:

- [ ] Anthropic API anahtarı
- [ ] Telegram bot token (`@thumpymeadow_bot`)
- [ ] Google OAuth client secret
- [ ] YouTube refresh token (client secret yenilenince zaten geçersiz olur)

Yenileme sırası: client secret → refresh token (yeniden yetkilendirme) → diğerleri.

---

## Kural

Yeni bir anahtar üretildiğinde:
1. Doğrudan GitHub Secrets'a gir
2. Hiçbir dosyaya, koda ya da dokümana yazma
3. Mümkünse sohbet ortamına da yapıştırma
