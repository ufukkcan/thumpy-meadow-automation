# Teknik Mimari

Her dosyanın ne yaptığı, önemli fonksiyonlar, veri yapıları ve ayarlar.

---

## Veri akışı

```
Telegram mesajı/buton
        ↓
check_and_produce.run()
        ↓
   durum makinesi
        ├─ start_cycle()      → generate_episode.generate_ideas()      → Claude
        ├─ send_script()      → generate_episode.generate_script()     → Claude
        │                     → normalize_episode()  → props.validate_prop()
        └─ produce_and_upload()
                ├─ produce.produce()
                │     ├─ voice.synthesize()        (her anlatım cümlesi)   → edge-tts
                │     ├─ episode.render()
                │     │     ├─ build_timeline()
                │     │     ├─ build_audio()  ← music.background_track()
                │     │     │                 ← music.music_break_track()
                │     │     ├─ build_background()  ← scene2d
                │     │     └─ kare döngüsü → scene2d._dino(), props.draw_prop()
                │     │                     → ffmpeg (stdin borusu)
                │     └─ thumbnail.make_variants()  → 3 JPEG
                ├─ generate_episode.build_description()
                ├─ scheduler.next_publish_time()
                ├─ upload_youtube.upload()          → YouTube Data API
                ├─ upload_youtube.set_thumbnail()
                └─ scheduler.record_upload()
```

---

## Senaryo veri yapısı

Claude'un ürettiği ve `normalize_episode()` tarafından doğrulanan yapı:

```python
{
  "title": "Learn Fruit Names & Colors | Yummy Fruits for Kids | Thumpy Meadow",
  "description_intro": "...",          # 2 cümle, ilk 150 karakterde anahtar kelimeler
  "learning_points": ["...", "..."],   # 3–5 madde
  "tags": ["learn colors", ...],       # ≤16, toplam ≤480 karakter
  "hashtags": ["learncolors", ...],    # tam 3, # işareti olmadan
  "thumbnail_text": "WHAT FRUIT?",     # ≤14 karakter, BÜYÜK HARF
  "thumbnail_props": [ {...}, ... ],   # 3–4 obje, SENARYODA GEÇENLERDEN
  "sections": [
    {
      "title": "Hello Friends!",       # YouTube chapter başlığı olur
      "segments": [
        {"type": "narration", "text": "...", "prop": {...} | None},
        {"type": "music_break", "lines": ["...", "..."]}
      ]
    }
  ]
}
```

`episode.flatten()` bunu düz segment listesine çevirir, her segmente `section` ekler.

---

## Obje (prop) formatları

`props.ALLOWED` beyaz listesi — Claude sadece bunları kullanabilir:

```python
{"kind": "balloon", "color": "red"}            # 7 renk
{"kind": "shape", "shape": "star", "color": "yellow"}   # 7 şekil × 7 renk
{"kind": "fruit", "fruit": "banana"}           # 7 meyve
{"kind": "animal", "animal": "duck"}           # 6 hayvan
{"kind": "count", "item": "apple", "n": 3}     # 5 nesne × 1–10
```

Renkler: red, blue, yellow, green, orange, purple, pink
Şekiller: circle, square, triangle, rectangle, star, heart, oval
Meyveler: apple, banana, orange, strawberry, grapes, pear, watermelon
Hayvanlar: duck, fish, bunny, cat, pig, frog
Sayma nesneleri: apple, orange, star, heart, balloon

`validate_prop()` geçersiz olanı `None` döndürür → o segment objesiz çizilir.

---

## Dosya dosya

### `check_and_produce.py` — ana akış
- `run()` — her Actions çalışmasının giriş noktası
- `handle(state, events)` — durum makinesi
- `start_cycle()`, `send_script()`, `produce_and_upload()`, `measure_and_report()`
- State dosyaları: `state/pending.json`, `telegram_offset.json`, `meta.json`
- Ayarlar (ortam değişkeni): `AUTO_TRIGGER_TIME` (11:00), `MAX_REWRITES` (5)
- Tetikleyici kelimeler: "video üret", "video uret", "/yeni", "yeni bölüm", "yeni bolum"

### `generate_episode.py` — Claude katmanı
- `generate_ideas()` → 3 fikir
- `generate_script(idea)` → tam senaryo (`normalize_episode` ile doğrulanmış)
- `build_description(ep, chapters)` → YouTube açıklaması
- `script_as_text(ep, minutes)` → Telegram'a gidecek .txt
- `SAFETY_RULES` — çocuk güvenliği (en kritik blok)
- `STYLE_RULES` — anlatım stili
- Model: `claude-sonnet-4-6`, senaryo için `max_tokens=12000`
- `state/topics_used.json` — son 200 konu, tekrarı önler

### `episode.py` — video motoru
- `W,H = 1920,1080`, `FPS = 24`
- `build_background()` — statik arka plan bir kez çizilir, her karede kopyalanır (hız)
- `build_timeline(segments)` — her segmentin başlangıç/süresi
- `chapters(timeline)` — YouTube chapter listesi (ilk 00:00, ≥3 adet, ≥10 sn)
- `build_audio()` — fon müziği (anlatımda %55, müzik molasında 0) + seslendirme
- `render()` — kare döngüsü, ffmpeg stdin borusu
- `NARRATION_LEAD_IN = 0.25`, `NARRATION_TAIL = 0.5`
- Obje konumu: `PROP_X=1300, PROP_Y=470, PROP_SIZE=330`; objeli sahnede Dino `x=560`

### `scene2d.py` — karakter ve arka plan
- `_dino(draw, cx, cy, scale, blink, arm_swing, mood)` — `mood`: "happy" | "excited"
- `_cloud()`, `_bush()`, renk sabitleri (SKY_TOP/BOT, HILL_*, TREE_*, GROUND*)

### `props.py` — obje kütüphanesi
- `draw_prop()`, `prop_label()`, `validate_prop()`, `ALLOWED`
- `draw_count()` — nesneleri sırayla belirir (sayma animasyonu), `step=0.45 sn`

### `thumbnail.py` — küçük resim
- `make_variants(text, props, prefix)` → 3 JPEG (A sarı, B mavi, C pembe)
- `_sunburst()`, `_sticker()` (beyaz kenar + gölge), `_title()` (her harf farklı renk)
- `CLUSTER` — 1–4 obje için konum/ölçek/açı şablonları

### `music.py` — müzik sentezi
- `SR = 44100`
- `background_track(duration, bpm=88)` — pad akor + bas + arpej
- `music_break_track(lines, bpm=100, seed)` → (ses, kelime zamanları, süre)
- `PROGRESSION` = C-G-Am-F, `PENTATONIC` dizi
- `write_wav()` — tepe değerine göre normalize eder (kırpma olmaz)

### `voice.py` — seslendirme
- `synthesize(text, voice, mp3_path, rate="-10%")` → numpy dizisi
- `-10%` hız: küçük çocuklar için biraz yavaş ve net

### `scheduler.py` — öğrenen yayın saati
- Aday saatler (America/New_York): hafta içi `13:00`, `15:30`; hafta sonu `07:00`, `09:00`
- `MIN_SAMPLES = 3` — her aday en az 3 kez denenir
- Sonra medyanı en yüksek olan seçilir; `EXPLORE_EVERY = 5` ile arada diğeri denenir
- `MIN_LEAD = 1.5 saat` — YouTube'un işlemesi için pay
- Yaz/kış saati otomatik (zoneinfo)
- `state/publish_log.json` — her yükleme + 48 saatlik izlenme

### `upload_youtube.py`
- `upload()` — `privacyStatus=private`, `publishAt`, `selfDeclaredMadeForKids=True`,
  `categoryId=27` (Education), `defaultLanguage/defaultAudioLanguage="en"`
- `set_thumbnail()` — hata durumunda çökmez, mesaj döndürür
- `view_count()` — 48 saatlik ölçüm için

### `telegram_bot.py`
- `send_message(text, buttons)`, `edit_message()`, `send_document()`, `send_photo()`
- `get_updates(offset)`, `events(updates)` → `{"kind": "text"|"button", "value": ...}`
- Sadece `TELEGRAM_CHAT_ID`'den gelenler işlenir

### `yt_oauth_exchange.py` — TEK SEFERLİK
- OAuth kodunu refresh token'a çevirir
- **Token'ın hangi kanala ait olduğunu ekrana yazar** (en kritik güvenlik kontrolü)

### Deneysel dosyalar (ana akışta kullanılmıyor)
- `songs.py` — telifsiz melodi şablonları, hece sayacı, kelime→nota eşleme, düzenleme
- `singer.py` — WORLD vokoder ile şarkı söyletme + `vocal_fx()`
- `rhythmic.py` — doğal sesle ritmik söyleme (en gelişmiş deneme)
  - Ayarlar: `LEAD=0.35`, `LEGATO=0.82`, `SPLIT_SYLLABLES=False`
  - `rb3()` — Rubber Band R3 motoru
  - `native_word()` — perdeyi doğrudan TTS motorunda üretir
  - `sustain()` — sadece ünlüyü uzatır, ünsüzler doğal kalır
- `sing_test.py` — şarkı testi üreteci

---

## Performans

| İş | Süre |
|---|---|
| Fikir üretimi | ~10 sn |
| Senaryo üretimi | 1–2 dk |
| Seslendirme (~60 cümle) | 2–4 dk |
| Render (10 dk video) | ~8–10 dk |
| YouTube yükleme | 1–2 dk |
| **Toplam** | **~13–15 dk** |

Workflow `timeout-minutes: 150` ile çalışıyor, bol pay var.
