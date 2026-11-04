# SEO ve Yayın Saati

---

## SEO kuralları

Claude bu kurallara göre üretir (`generate_episode.py` → `SCRIPT_PROMPT`):

### Başlık
- En güçlü arama ifadesi **en başta** (örn. "Learn Colors with Balloons")
- Sonra ikincil ifade, sonda ` | Thumpy Meadow`
- En fazla 70 karakter (sistem 100'e kırpar)
- ⛔ Abartı, tık tuzağı, yanıltıcı iddia yok

**Örnek:** `Learn Fruit Names & Colors | Yummy Fruits for Kids | Thumpy Meadow`

### Açıklama
Otomatik birleştirilir (`build_description`):
1. `description_intro` — 2 cümle, **ilk 150 karakterde** ana anahtar kelimeler
2. "In this video, little ones will:" + 3–5 madde
3. "Chapters:" + zaman damgalı bölüm listesi
4. Kanal tanıtımı (nursery rhymes, kids songs, toddler learning, preschool)
5. 3 hashtag

### Chapters (bölüm başlıkları)
YouTube kuralları koda gömülü (`episode.chapters`):
- İlki **00:00** olmalı
- En az **3 adet**
- Her biri en az **10 saniye** (daha kısa olanlar atlanır)

### Etiketler
- 12–16 etiket, toplam ≤480 karakter
- Ebeveynlerin **gerçekten aradığı** ifadeler
  (örn. "colors for toddlers", "learn colors", "preschool learning")
- ⛔ Alakasız popüler kelime yok

### Hashtag
Tam 3 tane, en alakalısı ilk sırada, `#` işareti olmadan üretilir
(açıklamanın sonuna eklenirken `#` konur).

### Küçük resim
- `thumbnail_text`: ≤14 karakter, BÜYÜK HARF, **merak uyandıran kısa soru ya da
  heyecan cümlesi** ("WHAT FRUIT?", "COUNT WITH ME!")
- `thumbnail_props`: bölümde **gerçekten geçen** 3–4 obje
  (kod bunu zorluyor — yanıltıcı küçük resim YouTube'da cezalandırılıyor)
- 3 renk varyasyonu üretilir: A sarı, B mavi, C pembe
- A otomatik yüklenir; B ve C Studio'da A/B testine eklenebilir

### Diğer sinyaller
- `categoryId = 27` (Education)
- `defaultLanguage` / `defaultAudioLanguage = "en"`
- `selfDeclaredMadeForKids = True`

---

## Yayın saati planlayıcı

**Mantık:** Hedef kitle İngilizce konuşan çocuklar; en büyük pazar ABD. Video,
izlenme yoğunluğundan **1–2 saat önce** yayına girmeli ki YouTube işleyip önermeye
başlayabilsin.

### Aday saatler (America/New_York)

| Gün tipi | Adaylar | Mantık |
|---|---|---|
| Hafta içi | 13:00, 15:30 | Öğleden sonra / kreş-okul sonrası |
| Hafta sonu | 07:00, 09:00 | Sabah yoğunluğu |

Yaz/kış saati otomatik hesaplanır (`zoneinfo`). Telegram mesajında hem ABD hem
Türkiye saati gösterilir.

### Öğrenme

1. Her aday en az **3 kez** denenir (keşif aşaması)
2. Sonra her yüklemede, **ilk 48 saat izlenmesinin medyanı** en yüksek olan seçilir
3. Her **5 yüklemede bir** diğer aday tekrar denenir (izleyici davranışı değişebilir)
4. Yayından 48 saat sonra izlenme otomatik ölçülür (`upload_youtube.view_count`)
5. Haftada bir Telegram'a rapor gelir

**Kayıt:** `state/publish_log.json`

```json
{"videos": [
  {"video_id": "...", "publish_at": "2026-11-02T18:00:00Z",
   "day_type": "weekday", "slot": "13:00", "views_48h": 412}
]}
```

**Not:** `MIN_LEAD = 1,5 saat` — üretim bittikten sonra en erken bu kadar sonraya
zamanlanır (YouTube'un işlemesi için pay).

### Önemli gözlem

Videonun **tarih damgası ilk yüklendiği anda sabitlenir**. Gizli yüklenip sonradan
açılan video "taze" görünmez. Bu yüzden onay ile yayın arası kısa tutulmalı.
