# Operasyon El Kitabı

Günlük kullanım, sorun giderme ve acil durum adımları.

---

## Günlük kullanım

### Normal akış
1. Saat 11:00 (TR) civarı Telegram'a 3 fikir gelir — ya da istediğin zaman bota
   **"video üret"** yaz
2. Bir fikir butonuna bas (1, 2 veya 3)
3. Senaryo `.txt` olarak gelir → **oku**
4. **"Onayla"** ya da **"Yeniden yaz"**
5. ~15 dakika sonra link, süre, yayın saati ve 3 küçük resim gelir
6. İstersen YouTube Studio'da küçük resim A/B testi kur

### Cevap gelmiyorsa
GitHub cron gecikiyor olabilir:
**GitHub → Actions → "Thumpy Meadow - kontrol ve uretim" → Run workflow**

### Senaryoyu değerlendirirken nelere bak
- Çocuk için uygunsuz, korkutucu ya da riskli bir şey var mı?
- Bilgiler doğru mu? (hayvan sesleri, meyve renkleri, sayılar)
- Şarkı sözleri özgün mü, tanıdık bir şarkıya çok mu benziyor?
- Konu daha önce işlendi mi?

---

## Sorun giderme

### Telegram'a hiç mesaj gelmiyor
1. Actions'ta son çalıştırma yeşil mi? Kırmızıysa log'a bak
2. Bota daha önce `/start` yazıldı mı?
3. `TELEGRAM_BOT_TOKEN` ve `TELEGRAM_CHAT_ID` secret'ları doğru mu?
4. `state/pending.json` içeriği ne? `"status": "error"` ise "video üret" yaz

### Bot takıldı, butonlar çalışmıyor
Telegram'a **"video üret"** yaz — bu komut her durumda mevcut durumu sıfırlar.

### "Hata olustu: ..." mesajı geldi
- Mesajdaki hata metnini oku
- Senaryo onaylanmışsa **"Tekrar dene"** butonu çıkar, üretimi yeniden başlatır
- Çıkmazsa "video üret" ile baştan başla

### Video yüklenmedi: `invalid_grant`
Refresh token geçersiz olmuş. Olası sebepler: Google uygulaması "Testing" moduna
düşmüş, şifre değişmiş, yetki iptal edilmiş.
→ `docs/integrations.md` → YouTube OAuth kurulumunu tekrarla
→ **Kanal adını doğrulamayı unutma**

### Küçük resim yüklenmedi
"doesn't have permissions to upload and set custom video thumbnails" →
Thumpy Meadow kanalına geçip `youtube.com/verify` ile telefon doğrulaması yap.
Bu videonun küçük resmini Telegram'dan indirip Studio'dan elle yükle.

### ffmpeg hatası
Hata mesajının son satırlarına bak (artık gösteriliyor).
En sık sebep: eksik girdi dosyası (çıkış kodu 254).

### Actions "Queued"da takıldı / tuhaf hatalar
`githubstatus.com` → Actions satırı yeşil mi? Kesinti varsa beklemek gerekir.

### Actions "payments have failed" diyor
Repo private olmuş olabilir → **public** yap (Settings → Danger Zone →
Change repository visibility).

---

## Acil durum

### Yanlış/kötü bir video yüklendi
Video `private` + zamanlanmış olarak yüklendiği için **yayına girmeden** silinebilir:
YouTube Studio → Content → videonun üç noktası → **Delete forever**

### Sistemi tamamen durdur
`.github/workflows/check_and_produce.yml` dosyasında `schedule` bloğunu sil ya da
Actions sekmesinden workflow'u **Disable** et.

### Yanlış kanala yüklendi
`YT_REFRESH_TOKEN` yanlış kanala ait demektir. Videoyu o kanaldan sil, token'ı
doğru kanal için yeniden al (`docs/integrations.md`).

---

## Periyodik kontroller

| Sıklık | İş |
|---|---|
| Her bölümde | Senaryoyu oku, onayla |
| Haftalık | Telegram'a gelen yayın saati raporunu incele |
| Haftalık | YouTube Studio → Analytics: izlenme süresi, tıklanma oranı |
| Aylık | `state/topics_used.json` şişiyor mu (son 200 ile sınırlı, sorun olmamalı) |
| Gerekince | Anahtar yenileme (`todo.md` → bakım) |

---

## Ölçüm: neye bakmalı

| Metrik | Nerede | Hedef | İlk video |
|---|---|---|---|
| Gösterim | Analytics → Content | artıyor olmalı | 509 |
| Tıklanma oranı (CTR) | Analytics → Content | %4+ | %2,2 |
| Ortalama izlenme | Analytics → Content | %35+ | %20 (2:09) |
| Trafik kaynağı | "How viewers find" | önerilenler yüksek | %100 önerilen |

**En önemlisi ortalama izlenme süresi.** YouTube bir videoyu daha çok önerip
önermeyeceğine büyük ölçüde buna bakıyor.
