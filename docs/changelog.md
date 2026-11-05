# Değişiklik Günlüğü (geçmişe dönük)

Bu dosya projede ne yapıldığını tarih/sıra ile kaydeder. Yeni bir oturumda
"daha önce ne yapılmıştı?" sorusunun cevabı buradadır.

Tarihler sohbetin geçtiği günlere göredir.

---

## 2026-11-05 — Pilot bölüm "Dino'nun Saklambacı" (7b, test, yükleme yok)

- **Araştırma:** `docs/arastirma-2d-kanallar.md`, `docs/arastirma-cocuk-izleme.md` → "Thumpy formülü".
- **Çizgi film stili** (`render2.py`): koyu kontur (Fluent nesnelere alfa genişletme ile bir kez),
  Dino ifadeleri (mutlu/şaşkın/dinliyor), iri gözler, kaş, düşme + baş dönmesi, çalı + bakan gözler,
  soru balonu (bekleme sayacı), gülen güneş, konturlu parıltı, satıra sığan yazı.
- **Bölüm** (`pilot.py`, `pilot.yml`): selam şarkısı 0. sn → soru + bekleme → 3 hayvan saklambaç
  (her biri farklı gag) → hareket molası → tekrar → ipucu → veda. Sert kamera kesmeleri.
  TTS baş/son sessizliği kırpılıyor; hayvan sesleri Ana sesinin perdesiyle.
- **Kanıt:** push `ef1968d`, run 42010325985 ilk denemede başarılı: 3:19 (198,7 sn), 69 segment,
  71 ms/kare (12 dk ≈ 20 dk render), ses hazırlığı 364 sn. 75 karenin 14'ü gözle kontrol edildi.

## 2026-11-04 — Yeni müzik molası: CC0 enstrümanlar + Hanami vokali (test, onaylı)

- **Enstrümantal** (`samples.py`, `kidsong.py`, `music_test.yml`): CC0 kayıtlar (VCSL,
  FreePats ukulele, D. Smolken kontrbas, Karoryfer kick; commit'e sabit), kamu malı
  melodiler vuruş ızgarasında, ukulele tarama, el çırpma, "ta-da" girişi, durma + düdük,
  yankı/kompresör, -14 LUFS. Ölçüm: ritim sapması ort. ~2 ms. Kullanıcı: "gayet güzel".
- **Vokal** (`sing.py`, `vocal_test.yml`): DiffSinger "Hoshino Hanami ~AI❤dol~ v1.0"
  (Lotte V) akustik + perde modeli, CMU sözlüğü, BigVGAN-v2 vocoder (bankanın vocoder'ı
  CC BY-NC-SA olduğu için). 3 deneme: (1) mel dönüşüm hatası → kalite kötü, (2) düzeltildi,
  "biraz robotik", (3) doğal perde modeli + nefes → kullanıcı: "süper olmuş".
- Kararlar K-16/K-17/K-18; dersler E9–E13.
- GitHub: fine-grained token `thumpy-claude-push` (Contents/Workflows yazma, Actions okuma).
- Üretime bağlama ertelendi (todo 6c).

---
## 2026-11-02 — Kanal kuruldu, sistem yazıldı, ilk video yayınlandı

### Araştırma ve stil kararı
- SquareWheels TV (2,51M abone, 834 video) incelendi: 3D animasyon, klasik çocuk
  şarkıları, araç temalı. Bu kalite ücretsiz + otomatik kısıtıyla **ulaşılamaz** olarak
  değerlendirildi (3D modelleme, rigging, saatlerce render gerekiyor).
- Pinkfong dinozor şarkıları playlist'i incelendi: düz renkli 2D, kontursuz, katmanlı
  arka plan, yuvarlak karakter, büyük kapalı gözler, yanak lekeleri, sol üstte logo.
  Bu stil **ulaşılabilir** bulundu ve hedef alındı.
- İlk deneme: "Wheels on the Bus" temalı otobüs animasyonu üretildi (9 sn).
  Sorunlar: yazı ekrandan taşıyordu, otobüs küçüktü, üstte çok boşluk vardı. Düzeltildi.
- İkinci deneme: Pinkfong tarzında **özgün dinozor karakteri** tasarlandı. Kuyruk
  başta keskin üçgendi, yumuşak elips zincirine çevrildi. Karakter büyütüldü.

### İsim seçimi
- YouTube'da 12+ isim arandı: Bouncy Buddies, Dino Hop, Wobble World, Giggle Grove,
  Snugglesaurus, Peppy Pebbles, Puddlehop, Mumbleberry, Toodlemoo, Wigglewood,
  Dino Dilly, Plumpy Pals, Hoppy Hollow → **hepsi alınmış** (bu alan çok doymuş).
- Boş çıkanlar: Thumpy Meadow, Bumbly Meadow.
- `@thumpymeadow` ve `@bumblymeadow` kullanıcı adları 404 verdi (boş).
- **Thumpy Meadow** seçildi. (Not: "Thumpy" Disney'in Thumper karakterini çağrıştırıyor,
  marka araması kullanıcıya bırakıldı.)

### Kanal kurulumu
- Kanal, sahibinin Google hesabı altında brand account olarak oluşturuldu
- Kullanıcı adı: `@ThumpyMeadow`, kanal ID: `UC9_bFi-Pyp8hTlclZYkcz-Q`
- Banner (2560×1440, güvenli alana sığacak şekilde otomatik ölçeklenen başlıkla) ve
  profil resmi (800×800, daire kırpımına uygun) kodla üretildi, kullanıcı yükledi
- Açıklama yazıldı ve yayınlandı
- 10 anahtar kelime eklendi (nursery rhymes, kids songs, toddler learning, preschool,
  learn colors, counting songs, dinosaur cartoon, cartoons for kids, baby songs,
  songs for kids)
- **Audience: "Yes, set this channel as made for kids"** (COPPA uyumu)
- Ülke ayarı kullanıcı tarafından yapıldı

### Ses testi
- `en-US-AnaNeural` (çocuk sesi) ve `en-US-JennyNeural` (kadın anlatıcı) GitHub Actions
  üzerinden test edildi
- **Ana seçildi** ("child voice daha güzel, çok güzel oranlanmış")

### Üretim motoru
- `scene2d.py`: Dino karakteri, gökyüzü geçişi, tepeler, çalılar, bulutlar
- `props.py`: obje kütüphanesi (balon 7 renk, şekil 7×7, meyve 7, hayvan 6, sayma 1–10)
  + `validate_prop()` beyaz liste doğrulaması
- `episode.py`: 16:9 yatay düzen, zaman çizelgesi, kare kare çizim, ffmpeg borusu,
  altyazı kutusu, karaoke, chapters hesaplama
- `music.py`: marimba, pad akor, fon müziği, müzik molası melodisi
- `voice.py`: edge-tts sarmalayıcı
- Elma, muz, çilek çizimleri ilk denemede bozuktu (muz "gülümseme" gibi, çilek ters
  üçgen) → düzeltildi

### Otomasyon
- `generate_episode.py`: Claude ile 3 fikir + tam senaryo + SEO; çocuk güvenliği
  kuralları (`SAFETY_RULES`) ve anlatım stili (`STYLE_RULES`) promptlara gömüldü
- `telegram_bot.py`: mesaj, buton, dosya, fotoğraf gönderme; olay ayrıştırma
- `check_and_produce.py`: durum makinesi (idle → choosing → reviewing → done/error)
- `upload_youtube.py`: gizli + zamanlanmış yükleme, made for kids, kategori 27,
  dil "en", küçük resim, izlenme sayısı
- `scheduler.py`: öğrenen yayın saati (ABD Doğu, hafta içi 13:00/15:30,
  hafta sonu 07:00/09:00, en az 3 örnek sonra medyan, 5'te bir keşif)
- `produce.py`: seslendirme + render + küçük resim birleştirici
- GitHub Actions workflow'ları yazıldı

### Entegrasyon kurulumu
- GitHub reposu `thumpy-meadow-automation` açıldı (**public** — Actions sınırsız olsun diye)
- Yeni Telegram botu `@thumpymeadow_bot` oluşturuldu
- YouTube OAuth: ilk denemede token **yanlış kanala** (Interesthings) bağlandı, fark
  edildi ve kullanılmadı; ikinci denemede kanal seçim ekranından Thumpy Meadow seçilerek
  doğru token alındı
- 6 GitHub Secret eklendi

### İlk video
- Telegram akışı uçtan uca çalıştı: fikirler → seçim → senaryo → onay → üretim
- Üretim 13 dakika sürdü (tahminden çok hızlı)
- Video 10:41, `youtu.be/WIEorW7zW10`, 2 Kasım 21:00 TR'ye zamanlandı
- **Küçük resim yüklenemedi:** kanal telefonla doğrulanmamıştı → doğrulandı
- YouTube Studio'da kontrol: made for kids ✔, zamanlama ✔, 7 chapter ✔, 3 hashtag ✔

### Küçük resim yeniden tasarımı
- İlk tasarım "çok basit" bulundu
- Yeniden yazıldı: güneş ışını arka plan, sticker efekti (beyaz kenar + gölge),
  heyecanlı karakter (açık ağız, kollar havada, parlak gözler), 3–4 obje, her harfi
  farklı renkte eğik başlık, parıltı ve konfeti, 3 renk varyasyonu
- Claude artık merak uyandıran kısa soru üretiyor ("WHAT FRUIT?") ve küçük resimde
  **sadece senaryoda gerçekten geçen objeler** kullanılıyor (yanıltıcı olmaması için)
- Kullanıcı 3 varyasyonu YouTube'un A/B testine ekledi

---

## 2026-11-03 — İlk analitik ve müzik molası çalışması

### Analitik (ilk gün)
- 509 gösterim, 12 izlenme, %2,2 tıklanma, 2:09 ortalama izlenme, %100 önerilen videolar
- Teşhisler: giriş çok yavaş (ilk obje 29. sn), görsel tekdüze, müzik az

### Müzik molası vokal çalışması (7 versiyon)
- Kullanıcı geri bildirimi: "melodi akılda kalmıyor, kimse şarkı söylemiyor, görüntü tekdüze"
- `songs.py`: 4 telifsiz melodi şablonu (Twinkle, Mary, London Bridge, Frère Jacques),
  hece sayacı (54/54 doğru), kelime→nota eşleme, davul/bas/akor düzenlemesi
- `singer.py`: WORLD vokoder ile şarkı söyletme (A) → **aşırı robotik**
- Ritmik anlatım (B) → ses iyi ama ritim yok
- `rhythmic.py`: kelime sınırlarıyla doğal satırdan kesme (C) → cızırtılı
- Hece bölme + ünlü hizalama + yumuşak geçişler (D) → **ritim beğenildi**, ses kötü
- Perdeyi doğrudan TTS motorunda üretme (E) → **"çok güzel"**, ama kayma/anlaşılmazlık
- Legato + küçük kelimeler doğal (G) → sorun sürüyor
- Teşhis: kelime kelime seslendirme doğal akışı bozuyor; hece bölme kelimeyi parçalıyor
- `SPLIT_SYLLABLES = False` seçeneği eklendi (bütün kelime), **henüz test edilmedi**

### Ölçüm araçları
- Yüklenen mp3'ten müzik altyapısı çıkarılıp vokal ayrıştırıldı, hece başlangıçları
  vuruşlara göre ölçüldü (sapma 0,01–0,05 vuruş olduğu doğrulandı)
