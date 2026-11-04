# Ortamlar ve Makineler

Projede rol oynayan her ortam, ne yapabildiği ve **güncel durumu**.
Durum değişince bu dosyadaki ilgili satır güncellenmeli.

Son güncelleme: 2026-11-03

---

## 1. Kullanıcının iş bilgisayarı (Windows)

| | |
|---|---|
| Rol | Tarayıcı işleri: GitHub web arayüzü, YouTube Studio, Google Cloud |
| **Durum** | ✅ Çalışıyor |
| **Kısıt** | ⛔ **Script/Python çalıştırılamıyor** (kurumsal engel) |

**Sonuç:** Yerel script gerektiren hiçbir adım tasarlanmamalı. OAuth kurulumu gibi
işler GitHub Actions üzerinden yapılıyor (`yt_oauth_exchange.yml`).

Kurulu ve kullanılan: Chrome (Claude eklentisi bağlı), GitHub Desktop (klasör yapısı
bozulduğunda kullanıldı).

---

## 2. Kullanıcının telefonu (iPhone)

| | |
|---|---|
| Rol | Telegram onayları, GitHub mobil uygulaması |
| **Durum** | ✅ Çalışıyor |
| Not | Mobil GitHub arayüzü tetikleyiciyi bazen yanlış etiketliyor (kozmetik) |

---

## 3. GitHub Actions runner (ubuntu-latest)

| | |
|---|---|
| Rol | **Tüm üretim burada çalışır** |
| **Durum** | ✅ Çalışıyor |
| Python | 3.12 |
| Sistem paketleri | `ffmpeg`, `fonts-dejavu-core` (şarkı testinde `rubberband-cli`) |
| Ağ | Tam internet erişimi (Microsoft TTS, Google, Anthropic, Telegram) |
| Süre sınırı | Workflow'da `timeout-minutes: 150` |
| Maliyet | Ücretsiz (public repo) |

**Bilinen davranışlar:**
- `schedule` (cron) gecikir — 5 dakikalık cron saatlerde bir çalışabilir
- Ubuntu sürümü zamanla değişiyor (24.04 → 26.04 gözlendi), paket sürümleri kayabilir
- Python 3.12'de `setuptools` varsayılan gelmiyor (pyworld için elle kurulmalı)

---

## 4. Asistan (Claude) çalışma ortamı

| | |
|---|---|
| Rol | Kod yazma, görsel üretimi, test, ölçüm |
| **Durum** | ✅ Çalışıyor |
| Python | 3.12, numpy/Pillow/ffmpeg mevcut |
| Ek araçlar | `espeak-ng` (kaba yerel ses), `rubberband`, `pyworld` |

**Ağ kısıtı (önemli):** Sadece belirli domainlere erişim var
(api.anthropic.com, github.com, pypi.org, npmjs.com, ubuntu arşivleri...).

⛔ **Erişilemeyen:** Microsoft Edge TTS, Telegram API, YouTube API, NASA efemeris.

**Sonuç:**
- Ana (gerçek) seslendirme burada üretilemez → gerçek ses testi mutlaka
  GitHub Actions'ta yapılmalı
- Yerelde `espeak-ng` ile sadece **akış ve kod** doğrulanır; kalite değerlendirmesi
  için kullanılmaz
- Dosya sistemi oturumlar arasında sıfırlanır — kalıcı bilgi bu dokümanlarda tutulmalı

---

## 5. Chrome tarayıcı bağlantısı (Claude in Chrome)

| | |
|---|---|
| Rol | YouTube/GitHub sayfalarını inceleme, kanal ayarlarını okuma/yazma |
| **Durum** | ⚠️ Aralıklı — bazen bağlı, bazen kopuk |

Çalıştığında yapılabilenler: sayfa okuma, ekran görüntüsü, form doldurma, tıklama.
⛔ **Dosya yükleme çalışmıyor** (banner, küçük resim gibi dosyaları kullanıcı yükler).

---

## 6. Barındırılan varlıklar

| Varlık | Yer | Durum |
|---|---|---|
| YouTube kanalı | `UC9_bFi-Pyp8hTlclZYkcz-Q` (@ThumpyMeadow) | ✅ Aktif, made for kids, doğrulanmış |
| GitHub repo | `ufukkcan/thumpy-meadow-automation` | ✅ Public, Actions çalışıyor |
| GitHub Pages | `ufukkcan/tiktok-legal-pages` | ✅ Yayında (OAuth callback + yasal sayfalar) |
| Telegram bot | `@thumpymeadow_bot` | ✅ Aktif |
| Google OAuth client | `shorts-bot-web` (Web application) | ✅ Production (published) |
| Anthropic anahtarı | "Not linked" tip | ✅ Çalışıyor |

---

## 7. Kardeş kanallar (bağlam)

| Kanal | Repo | Durum |
|---|---|---|
| interesthings | `youtube-shorts-automation` | ✅ Çalışıyor (İngilizce Shorts) |
| astrologicalshorts | `astrological-shorts-automation` | ✅ Çalışıyor (kullanıcı beyanı) |
| Historic Blink | — | ⏸ Kod hazır, kurulum yapılmadı |

**Not:** Üçü de aynı Google hesabı ve aynı OAuth client'ını kullanır, ama her birinin
**ayrı refresh token'ı** vardır. `astrologicalshorts` token'ının doğru kanala ait
olduğu resmen doğrulanmadı (bkz. `todo.md` → bakım).
