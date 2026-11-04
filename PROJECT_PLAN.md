# Proje Planı ve Mevcut Durum

Son güncelleme: 2026-11-03

---

## Nerede duruyoruz?

Proje **"çalışır durumda, kalite iyileştirme aşamasında"**.

```
Faz 0  Fikir ve stil araştırması          ████████████ %100  ✔ bitti
Faz 1  Kanal kurulumu                     ████████████ %100  ✔ bitti
Faz 2  Video üretim motoru                ████████████ %100  ✔ bitti
Faz 3  Otomasyon (Claude + Telegram + YT) ████████████ %100  ✔ bitti
Faz 4  SEO + küçük resim + yayın saati    ████████████ %100  ✔ bitti
Faz 5  İlk yayın ve ölçüm                 ████████████ %100  ✔ bitti
Faz 6  Müzik molası vokal kalitesi        ████░░░░░░░░  %35  ⏳ DEVAM EDİYOR
Faz 7  İzlenme süresi iyileştirmeleri     ░░░░░░░░░░░░   %0  ⏸ sırada
Faz 8  Büyüme (Shorts, listeler, ABC)     ░░░░░░░░░░░░   %0  ⏸ sonra
```

---

## Faz 0 — Fikir ve stil araştırması ✔

**Hedef:** Hangi tarzda çocuk videosu üretilebilir, neyi gerçekten yapabiliriz?

Yapılanlar:
- SquareWheels TV (2,5M abone) kanalı incelendi → 3D animasyon, bizim için ulaşılamaz
- Pinkfong dinozor şarkıları incelendi → düz renkli 2D, ulaşılabilir hedef
- Ücretsiz + otomatik kısıtıyla 3D animasyonun mümkün olmadığı açıkça tespit edildi
- Pinkfong tarzında özgün karakter (Dino) tasarlandı ve örnek video üretildi

**Karar:** Düz renkli 2D, katmanlı arka plan, yuvarlak sevimli karakter.

---

## Faz 1 — Kanal kurulumu ✔

| İş | Durum |
|---|---|
| İsim araştırması (12+ isim YouTube'da tarandı, çoğu alınmış) | ✔ |
| "Thumpy Meadow" seçildi, `@ThumpyMeadow` boş çıktı | ✔ |
| Kanal oluşturuldu (brand account) | ✔ |
| Açıklama + 10 anahtar kelime | ✔ |
| Banner (2560×1440) ve profil (800×800) üretildi ve yüklendi | ✔ |
| **Audience: "made for kids"** (COPPA) | ✔ |
| Ülke ayarı | ✔ |
| Telefon doğrulaması (özel küçük resim için şart) | ✔ |

---

## Faz 2 — Video üretim motoru ✔

| Bileşen | Durum | Not |
|---|---|---|
| Karakter (Dino) çizimi, 2 ruh hali | ✔ | `happy`, `excited` |
| Katmanlı arka plan | ✔ | gökyüzü geçişi, tepeler, çalılar, kayan bulutlar |
| Obje kütüphanesi | ✔ | 5 tür, 36 varyasyon (balon, şekil, meyve, hayvan, sayma) |
| Yatay 16:9 düzen | ✔ | 1920×1080, 24 fps |
| Kare kare çizim → ffmpeg borusu | ✔ | diske PNG yazmaz, hızlı |
| Fon müziği sentezi | ✔ | marimba arpej + pad akor, C-G-Am-F |
| Müzik molası (karaoke) | ✔ | görsel tamam, **vokal kalitesi açık iş** |
| Seslendirme entegrasyonu | ✔ | `en-US-AnaNeural`, test edilip seçildi |
| Gerçek ses süresine göre zamanlama | ✔ | |

---

## Faz 3 — Otomasyon ✔

| İş | Durum |
|---|---|
| Claude ile 3 fikir üretimi | ✔ |
| Claude ile tam senaryo + çocuk güvenliği kuralları | ✔ |
| Obje doğrulama (beyaz liste) | ✔ |
| Telegram botu (`@thumpymeadow_bot`) | ✔ |
| Durum makinesi: idle → choosing → reviewing → done | ✔ |
| Senaryo onayı (.txt dosyası + butonlar) | ✔ |
| Hata durumu + "Tekrar dene" butonu | ✔ |
| YouTube yükleme (gizli + zamanlanmış + made for kids) | ✔ |
| GitHub Actions (5 dk cron + elle tetikleme) | ✔ |
| State'in repoya yazılması | ✔ |

---

## Faz 4 — SEO, küçük resim, yayın saati ✔

| İş | Durum | Detay |
|---|---|---|
| SEO başlık kuralları | ✔ | güçlü anahtar kelime başta, ≤70 karakter, tık tuzağı yok |
| Açıklama üretimi | ✔ | ilk 150 karakterde anahtar kelimeler + öğrenilenler + chapters |
| Bölüm başlıkları (chapters) | ✔ | YouTube kurallarına uygun (00:00 başlangıç, ≥3 adet, ≥10 sn) |
| Etiketler ve hashtag'ler | ✔ | 12–16 etiket, 3 hashtag |
| Küçük resim üretimi | ✔ | sunburst, sticker efekti, renkli başlık, 3 varyasyon |
| Öğrenen yayın saati | ✔ | ABD Doğu saati, hafta içi/sonu ayrı, 48 saat ölçümü |
| Haftalık rapor | ✔ | Telegram'a |

---

## Faz 5 — İlk yayın ve ölçüm ✔

**Video:** "Learn Fruit Names & Colors | Yummy Fruits for Kids | Thumpy Meadow"
`youtu.be/WIEorW7zW10` · 10:41 · 2 Kasım 2026, 21:00 TR

**İlk gün analitiği:**

| Metrik | Değer | Yorum |
|---|---|---|
| Gösterim | 509 | YouTube videoyu test ediyor, iyi işaret |
| İzlenme | 12 | Yeni kanal için normal, karar vermek için çok az |
| Tıklanma oranı | %2,2 | Alt sınırda; A/B testi devam ediyor |
| Ortalama izlenme | 2:09 / 10:41 (%20) | **En kritik zayıflık** |
| Trafik kaynağı | %100 önerilen videolar | "Made for kids" işe yarıyor |

---

## Faz 6 — Müzik molası vokal kalitesi ⏳ DEVAM EDİYOR

**Problem:** Ücretsiz seslendirme (edge-tts) şarkı söyleyemiyor, sadece konuşuyor.
Konuşmayı şarkıya çevirme denemeleri yapılıyor.

**Denenen 7 versiyon:**

| Ver. | Yöntem | Sonuç |
|---|---|---|
| — | Rastgele melodi, vokal yok, sadece enstrüman | Reddedildi: "akılda kalmıyor, kimse şarkı söylemiyor" |
| A | WORLD vokoder, perde notaya zorlanıyor | Reddedildi: aşırı robotik |
| B | Ritmik anlatım, melodiyi enstrüman çalıyor | Kısmen: ses iyi, ritim yok |
| C | Doğal satır + kelime sınırları + Rubber Band | Cızırtılı, ritim tutmuyor |
| D | C + hece bölme + ünlü hizalama + yumuşak geçişler | **Ritim beğenildi**, ses kötü |
| E | Perde doğrudan TTS motorunda üretiliyor (kelime kelime) | **"Çok güzel"**, ama kayma + anlaşılmazlık |
| F | D + R3 motoru | (E seçildiği için değerlendirilmedi) |
| G | E + legato + küçük kelimeler doğal | Kayma ve anlaşılmazlık sürüyor |

**Son teşhis (henüz test edilmedi):** E ve G'de her kelime **ayrı ayrı** seslendiriliyor.
İnsan konuşmasında kelimeler birbirine bağlanır; tek tek söylenince doğal akış kaybolur.
Ayrıca çok heceli kelimeler hecelerine bölünüyor ve bölme noktaları sesin ortasına
denk gelince kelime parçalanıyor.

**Sıradaki deneme:** Cümleyi bütün söylet + kelimeyi bölme + legato + R3.
(`rhythmic.py` içinde `SPLIT_SYLLABLES = False` olarak hazırlandı, test edilmedi.)

**Eğer bu da yetersiz kalırsa — gerçekçi alternatifler:**
1. **Sözsüz dans molası:** vokal yok, Dino ve objeler müzikle dans eder, Ana sadece
   "Let's dance! Clap your hands!" gibi kısa doğal çağrılar yapar. Kalite riski sıfır.
2. **Elle kaydedilmiş şarkılar:** 8–10 konu için bir kez insan sesiyle kaydedilen
   şarkılar, bölümlerde tekrar tekrar kullanılır. Çocuklar tekrarı sever.
3. **Ücretli yapay zekâ şarkı servisi:** gerçek kalite, ama maliyet + ticari lisans
   kontrolü gerekir.

---

## Faz 7 — İzlenme süresi iyileştirmeleri ⏸ SIRADA

İlk videodan çıkan teşhisler (uygulanmadı):

1. **Giriş çok yavaş** — ilk obje 29. saniyede çıkıyor. İlk 10 saniyede obje olmalı,
   açılışta müzikli hareketli bir jenerik bulunmalı.
2. **Görsel tekdüzelik** — objeler duruyor. Zıplama, dönme, parıltıyla belirme olmalı;
   Dino her yeni objede heyecanlanmalı.
3. **Müzik az** — 10 dakikada 4 müzik molası. Daha kısa anlatım blokları, daha sık müzik.
4. **Sahne çeşitliliği** — her bölüm aynı çayır. Çiftlik, deniz, gece, bahçe eklenmeli.

**Öncelik sırası:** 1 → 3 → 2 → 4 (etkiye göre)

---

## Faz 8 — Büyüme ⏸ SONRA

| İş | Not |
|---|---|
| ABC / harf dersleri | "ABC song", "phonics" en çok aranan konulardan; harf çizimi kolay |
| Shorts kesitleri | Her bölümden otomatik 30–60 sn dikey kesit; keşfedilmeyi hızlandırır |
| Oynatma listeleri | Konu bazlı otomatik listeler; izlenme süresini artırır. YouTube yetkisi genişletilmeli |
| Yeni karakterler | Tavşan, ayı, fil — tekrar izlenmeyi artırır |
| Cron güvenilirliği | GitHub cron gecikiyor; cron-job.org gibi harici tetikleyici |

---

## Bilinen kısıtlar (değiştirilemez)

1. **Yorumlar ve bildirimler kapalı.** COPPA gereği, "made for kids" işaretli
   kanallarda YouTube bunu zorunlu kılıyor. Değiştirmeye çalışmak kanalı riske atar.
2. **Kişiselleştirilmiş reklam yok.** Aynı sebeple gelir diğer kanallardan düşük olur.
3. **GitHub cron gecikiyor.** 5 dakikalık cron pratikte saatlerde bir çalışabiliyor.
   Çözüm: elle tetikleme ya da harici tetikleyici.
4. **Seslendirme kalitesi tavanı.** edge-tts 24 kHz sıkıştırılmış ses veriyor;
   her işleme adımı bu kusuru büyütüyor.
