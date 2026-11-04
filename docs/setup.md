# Sıfırdan Kurulum

Bu sistemi yeni bir çocuk kanalı için baştan kurmak gerekirse izlenecek adımlar.
(Thumpy Meadow için bunların hepsi tamamlandı; burası referans ve yeni kanal içindir.)

---

## 1. YouTube kanalı

1. `youtube.com/channel_switcher` → **Create a channel**
2. Kanal adı ve `@kullanıcıadı` (önce YouTube aramasında ve
   `youtube.com/@isim` adresinde boş olduğunu doğrula)
3. YouTube Studio → **Customization → Profile**: açıklama, banner, profil resmi
4. **Settings → Channel → Basic info**: ülke + anahtar kelimeler
5. **Settings → Channel → Advanced settings → Audience**:
   **"Yes, set this channel as made for kids"**
6. İlgili kanala geçip `youtube.com/verify` → telefon doğrulaması
   (özel küçük resim için şart, ilk videodan önce yapılmalı)

## 2. GitHub reposu

1. **Public** repo aç (Actions ücretsiz ve sınırsız olsun diye)
2. Kod dosyalarını yükle (hepsi kökte olabilir)
3. `.github/workflows/check_and_produce.yml` ve `yt_oauth_exchange.yml` dosyalarını
   **"Create new file"** ile oluştur (klasör sürükleme çalışmaz)
4. Settings → Actions → General → **Read and write permissions**

## 3. Telegram botu

1. `@BotFather` → `/newbot` → isim + kullanıcı adı → token
2. Bota `/start` yaz
3. `https://api.telegram.org/bot<TOKEN>/getUpdates` → `chat.id`

## 4. Anthropic anahtarı

console.anthropic.com → Create Key → **"Not linked"** → anahtarı kopyala

## 5. Google OAuth

`docs/integrations.md` → YouTube bölümündeki adımlar.
Mevcut Web client (`shorts-bot-web`) tüm kanallar için kullanılabilir; sadece
**refresh token** kanal başına ayrı alınır.

## 6. GitHub Secrets

Settings → Secrets and variables → Actions → New repository secret:

| Ad | Kaynak |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `TELEGRAM_BOT_TOKEN` | BotFather |
| `TELEGRAM_CHAT_ID` | getUpdates |
| `YT_CLIENT_ID` | Google Cloud Credentials |
| `YT_CLIENT_SECRET` | Google Cloud Credentials |
| `YT_REFRESH_TOKEN` | `yt_oauth_exchange` workflow çıktısı (kanal doğrulanmış) |

## 7. İlk test

1. Telegram'a "video üret"
2. Actions → Run workflow
3. Fikir → seçim → senaryo → onay → video

---

## Workflow ayarları (env)

`check_and_produce.yml` içinde:

| Değişken | Değer | Anlamı |
|---|---|---|
| `TTS_VOICE` | `en-US-AnaNeural` | Anlatıcı ses |
| `AUTO_TRIGGER_TIME` | `11:00` | Günlük otomatik fikir saati (TR) |
| `MAX_REWRITES` | 5 (kod varsayılanı) | "Yeniden yaz" sınırı |

`scheduler.py` içinde yayın saati adayları:
```python
CANDIDATES = {
    "weekday": ["13:00", "15:30"],   # America/New_York
    "weekend": ["07:00", "09:00"],
}
```
