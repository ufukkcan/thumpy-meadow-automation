# Kararlar

Mimari, içerik ve araç kararları; gerekçesi ve tarihiyle. Bir karar değişirse
eski satır silinmez, altına yeni karar ve sebebi yazılır.

---

## 2026-11-02

### K-01 · 3D değil, programatik 2D
**Karar:** Animasyonlar Pillow ile kodla çizilen düz renkli 2D olacak.
**Gerekçe:** Hedef kanal (SquareWheels TV) 3D kullanıyor ama 3D modelleme, rigging
ve saatlerce render gerektiriyor. GitHub'ın ücretsiz runner'larında grafik kartı yok
ve iş başına 6 saat sınırı var. Ücretsiz + otomatik kısıtıyla 3D **mümkün değil**.
**Sonuç:** Pinkfong tarzı düz renkli 2D hedeflendi, ulaşıldı.

### K-02 · Kanal adı "Thumpy Meadow"
**Karar:** İsim "Thumpy Meadow", kullanıcı adı `@ThumpyMeadow`.
**Gerekçe:** 12+ isim YouTube'da tarandı, neredeyse hepsi alınmıştı (bu alan çok
doymuş). Hem aramada hem kullanıcı adında boş olan tek uygun isimdi.
**Bilinen risk:** "Thumpy", Disney'in Thumper karakterini çağrıştırıyor. Marka
araması kullanıcıya bırakıldı (`todo.md`).

### K-03 · Yatay uzun video, dikey Shorts değil
**Karar:** 16:9, 1920×1080, 10–13 dakika.
**Gerekçe:** Çocuk kanallarında asıl izlenme, ebeveynlerin TV/tablette açtığı uzun
videolardan geliyor. Shorts ileride bu videolardan kesilerek üretilebilir.

### K-04 · Ses formatı: karışık (anlatım ağırlıklı + müzik molaları)
**Karar:** Ağırlık anlatımlı öğretici içerikte, aralarda müzik molaları.
**Gerekçe:** Ücretsiz TTS şarkı söyleyemiyor. Üç seçenek sunuldu (A: sadece anlatım,
B: sözsüz şarkı, C: karışık), kullanıcı C'yi seçti.

### K-05 · Anlatıcı ses: `en-US-AnaNeural`
**Karar:** Çocuk sesi Ana.
**Gerekçe:** Ana ve Jenny (kadın anlatıcı) GitHub Actions'ta test edildi, kullanıcı
Ana'yı seçti ("child voice daha güzel").

### K-06 · Onay modeli: senaryo onayı (video önizleme değil)
**Karar:** Kullanıcı videoyu değil, **senaryo metnini** onaylar.
**Gerekçe:** 10 dakikalık video Telegram'ın 50 MB gönderme sınırına sığmıyor;
ayrıca önizleme + final iki kez render demek (~30 dk fazladan). Senaryo onayı aynı
zamanda daha güçlü bir çocuk güvenliği kontrolü.
**Alternatif reddedildi:** 720p önizleme göndermek (yavaş + boyut riski).

### K-07 · Repo public
**Karar:** `thumpy-meadow-automation` public olacak.
**Gerekçe:** Private repoda ücretsiz Actions dakikası tükendi ve sistem tamamen
durdu. Public repolarda Actions sınırsız ve ücretsiz. Kod gizli bilgi içermiyor
(her şey Secrets'ta).

### K-08 · "Made for kids" işaretlenecek
**Karar:** Kanal ve tüm videolar `madeForKids=true`.
**Gerekçe:** COPPA yasal zorunluluğu. İçerik açıkça 2–6 yaşa yönelik.
**Kabul edilen sonuç:** Yorumlar, bildirimler ve kişiselleştirilmiş reklam kapalı.
Bu değiştirilmeyecek; yanlış etiketleme kanalı ve sahibini cezai riske sokar.

### K-09 · Yayın saati: ABD Doğu, öğrenen planlayıcı
**Karar:** Hafta içi 13:00/15:30, hafta sonu 07:00/09:00 (America/New_York).
Sistem 48 saatlik izlenmeyi ölçüp en iyi saati öğreniyor.
**Gerekçe:** Hedef kitle ABD ağırlıklı. Video, izlenme yoğunluğundan 1–2 saat önce
yayına girmeli ki YouTube işleyip önermeye başlayabilsin. Başlangıç saatleri genel
izleme örüntülerinden tahmin; kanala özel ölçüm sistemin kendisi tarafından yapılacak.

### K-10 · Küçük resimde sadece senaryoda geçen objeler
**Karar:** `thumbnail_props` koddan doğrulanıyor; senaryoda olmayan obje küçük resme
giremiyor.
**Gerekçe:** YouTube çocuk içeriğinde yanıltıcı küçük resmi cezalandırıyor.
Merak uyandırma, yanıltmadan, soru cümlesiyle yapılıyor ("WHAT FRUIT?").

### K-11 · TikTok terk edildi
**Karar:** İçerik sadece YouTube'a gidecek.
**Gerekçe:** TikTok'un onaylanmamış uygulamaları **yalnızca gizli hesaplara**
paylaşabiliyor (`unaudited_client_can_only_post_to_private_accounts`). Gizli hesap
keşfete düşmediği için büyüme hedefiyle doğrudan çelişiyor. Tam inceleme süreci
günler/haftalar sürüyor.
**Kalıntı:** `tiktok-legal-pages` GitHub Pages reposu OAuth callback için
kullanılmaya devam ediyor (adı yanıltıcı ama işlevsel).

---

## 2026-11-03

### K-12 · Melodiler 1929 öncesi kamu malından
**Karar:** Müzik molası melodileri Twinkle Twinkle (1761), Mary Had a Little Lamb
(1830), London Bridge (17. yy), Frère Jacques (18. yy) şablonlarından; düzenleme ve
sözler bize ait.
**Gerekçe:** Rastgele üretilen melodiler akılda kalmıyordu. Tanıdık melodiler
çocuklarda bağ kuruyor. Bu eserler kamu malı; düzenleme ve sözler özgün.
**Dikkat:** "Geleneksel" sanılan her şarkı kamu malı değil — *The Wheels on the Bus*
1939'da yazıldı, kullanılmıyor.

### K-13 · Şarkı yöntemi: perdeyi TTS motorunda üretmek
**Karar:** Vokoderle perdeyi sonradan zorlamak yerine, edge-tts'e doğru perdede
ürettirmek (`pitch="+NHz"`).
**Gerekçe:** Vokoderle zorlanan perde "autotune/robot" etkisi yaratıyordu (A
versiyonu reddedildi). Kaynağı düzeltmek çıktıyı onarmaktan iyi.
**Durum:** E versiyonu bu yöntemle üretildi ve kullanıcı tarafından beğenildi;
kelime kayması ve anlaşılırlık sorunu sürüyor.

### K-14 · Rubber Band R3 motoru
**Karar:** Zaman/perde işlemleri `rubberband -3 -F` komut satırı aracıyla.
**Gerekçe:** ffmpeg'in `rubberband` filtresi eski R2 motorunu kullanıyor ve insan
sesinde metalik tını bırakıyor. R3 ("finer") belirgin şekilde temiz.

### K-15 · Döngü engeli kuralı eklendi
**Karar:** Bir sorun en fazla 3 denemede çözülmezse durup birlikte karar verilecek.
**Gerekçe:** Müzik molası vokalinde 7 versiyon denendi, hâlâ çözülmedi. Erken durup
alternatifleri (sözsüz dans molası, elle kaydedilmiş şarkılar, ücretli servis)
değerlendirmek daha verimli olurdu.

### K-16 · 2026-11-04 · Vokal: edge-tts ile şarkı yolu kapatıldı, açık kaynak model araştırılacak
**Karar:** edge-tts konuşmasını şarkıya çevirme denemeleri (A–G) sonlandırıldı.
Açık kaynak şarkı söyleyen modeller araştırılacak (önce sadece rapor).
**Gerekçe:** 7 deneme sonrası kullanıcı hem yayındaki molayı hem şarkı testini
beğenmedi (ritim, melodi, ses kalitesi, vokal). Kural 8 (K-15).
**Seçilmeyenler:** tezahürat+dans, insan sesiyle kayıt, vokalsiz.

### K-17 · 2026-11-04 · Enstrüman sesi: CC0 örnek ses paketi
**Karar:** Saf sinüs sentezi yerine kamu malı (CC0) kayıtlı enstrüman sesleri.
**Gerekçe:** Kullanıcı ses kalitesini beğenmedi; sinüs dalgası ince/elektronik
duyuluyor. "Her şey kodla sıfırdan" ilkesinden bilinçli sapma (kullanıcı onayı).
**Şart:** Her paketin lisans sayfası doğrulanır; CC0 olmayan (CC-BY dahil) kullanılmaz,
lisans kanıtı `docs/kararlar.md`'ye eklenir.
**Lisans kanıtı (2026-11-04, her reponun `LICENSE` dosyası okundu: "CC0 1.0 Universal"):**

| Kaynak | Commit (sabit) | Kullanılan |
|---|---|---|
| `github.com/sgossner/VCSL` | `c1ea7bcc3c73…` | ksilofon, glokenspiel, el çırpma, trampet, shaker, tef, zil ağacı, düdük, flexatone |
| `github.com/freepats/ukulele1` | `86d345f6f7b7…` | ukulele (13 nota) |
| `github.com/sfzinstruments/dsmolken.double-bass` | `c2985eb647109…` | kontrbas pizzicato |
| `github.com/sfzinstruments/karoryfer.big-rusty-drums` | `f07ce00df34a…` | kick |

Tam SHA'lar `samples.py` içinde. Ticari marka: kaynak adları kanal tanıtımında
"onaylıyor" izlenimi verecek şekilde kullanılmaz.
**Seçim gerekçesi (ukulele):** Ukulele (gitar yerine) — parlak, okul öncesi şarkılarının tipik
tınısı; kullanıcı "çocukların dikkatini en çok çekecek şekilde" dedi.

### K-18 · 2026-11-04 · Vokal: Hanami akustik modeli + BigVGAN-v2 vocoder
**Karar:** Şarkı vokali DiffSinger "Hoshino Hanami ~AI❤dol~ v1.0" (Lotte V) akustik
modeliyle üretilir; ses dalgası NVIDIA BigVGAN-v2 44 kHz (MIT, HF rev `95a9d1d`) ile.
**Gerekçe:** Melodiyi + sözü birebir alan, ticari kullanıma açık tek seçenek. Bankanın
kendi vocoder'ı (AI❤dolGAN) **CC BY-NC-SA 4.0** → monetize kanalda kullanılamaz.
**Lisans kanıtı (zip içindeki `__License/` ve repo `LotteV-Voicebank-Update-Repo` b866687):**
voicebank "Use this voicebank for any creative purpose, even commercially", şart:
kaynak gösterme, orijinal dosyaları yeniden dağıtmama; sözlükler MIT; logolar CC BY-NC
(kullanılmıyor); karakter görseli ticari kullanılmaz (kullanılmıyor).
**Şartlar:** (1) Ses bankası repoya/artifact'a asla konmaz, yalnızca actions/cache.
(2) Vokalli her videonun açıklamasına `sing.CREDIT` satırı. (3) Zip sha256 ile sabit.
**Risk:** Yazar 2026-07'de süresiz ara verdi; MediaFire linki kaybolabilir (cache 7 gün
kullanılmazsa silinir). Vokal üretime girerse kalıcı saklama çözümü konuşulacak.

---

## 2026-11-05

### K-19 · Görseller: Fluent Emoji Color (MIT) + kendi Dino/arka planımız, Skia motoru
**Karar:** Nesne çizimleri Microsoft Fluent UI Emoji "Color" SVG setinden alınır
(github.com/microsoft/fluentui-emoji, commit `1ffb34c752ecf5d402f04cfb4b392c77f57c54bc`).
Dino, arka planlar ve efektler kodla çizilir, Fluent stiline uyumlu. Çizim motoru
Pillow'dan Skia'ya geçirilecek (kenar yumuşatma, gölge, gradyan). K-01'in "her şey
kodla" ilkesi nesneler için değişti; K-01'in 2D kararı geçerli.
**Gerekçe:** Analitik (WIEorW7zW10): CTR %2,3, izleme %16; kullanıcı "tekdüze, çizimler
basit" dedi. El çizimi kütüphane ~30 obje ve tavanı düşük; Fluent 1285 obje, tek stil,
vektör (1080p'de net). Telif riski K-17 mantığıyla çözülü: açık, ticari kullanıma
izin veren lisans.
**Lisans kanıtı:** repo kök LICENSE = MIT (Copyright Microsoft), görseller için ayrı
lisans/istisna yok (2026-11-05 kontrol). Şart: MIT metni repoda saklanır; ekranda
kaynak gösterme gerekmez.
**Elenenler:** Noto 3D (görsel lisansı belirsiz), Twemoji (CC-BY, her açıklamada kaynak),
OpenMoji (CC BY-SA, share-alike), Kenney (sabit indirme adresi yok), 3D Fluent PNG
(256 px, büyütmede bulanık).
**Kurallar:** Maskot asla emoji olmaz (marka korunamaz). Bayraklar ve marka benzeri
semboller kullanılmaz. "Microsoft/emoji" adı ve logosu kullanılmaz. Kullanılabilir
objeler yine beyaz listeden (`props.validate_prop`).

### K-20 · Yeni bölüm formatı: "Thumpy formülü" saklambaç, 8–10 dk (kullanıcı onayı)
**Karar:** Üretim `show.py` motoruna geçer. Sabit ritüeller (selam/veda şarkısı), hikâye
çerçevesi (birthday/picnic/rainbow), 6 bulma oyunu (gerçek hayvan sesi → soru + bekleme →
büyüyen şaka → kelime 3 kez + tekrar ettirme → hareket), 2 hareket molası, tekrar, ödül,
sonraki bölüm silueti. Beyaz liste artık katalog: `animal_sounds.SOURCES` (gerçek CC0 sesi
olan 11 hayvan), `show.HIDES/GAGS/ACTIONS/FRAMES`, `assets.NAMES`. Claude yalnızca
katalogdan seçer, `generate_episode.normalize_episode` doğrular. Senaryo onayı aynen korunur.
**Gerekçe:** `docs/arastirma-cocuk-izleme.md` (anlama, tekrar, katılım, karakter, müzik);
kullanıcı pilotu (2 tur) onayladı; süre seçimi kullanıcıdan (8–10 dk).
**Risk:** Tek oyun kalıbı → zamanla "inauthentic/repetitive" riski. Önlem: çerçeve, hayvan,
şaka, şarkı sözleri her bölümde değişir; sonraki adım yeni oyun kalıpları (renk, sayı).

### K-21 · Küçük resim: 3 konsept, A otomatik; B/C sıralı test (izin bekliyor)
**Karar:** `thumbs.py` aynı motorla 3 konsept üretir (sürpriz / arkadaşlar / merak). A
`thumbnails.set` ile yüklenir; A/B/C `state/thumbs/`'a saklanır.
**Gerekçe:** Data API'de Test & compare yok; ayrıca YouTube made-for-kids videolarda
Test & compare'i kapatıyor (support.google.com/youtube/answer/13861714: "You cannot use
this feature on videos that are made for kids"). Kullanıcı sıralı otomatik testi seçti.
CTR yalnızca Reporting API toplu raporlarında (`channel_reach_basic_a1`,
`video_thumbnail_impressions(_ctr)`, 2026-01-15) → `yt-analytics.readonly` izinli yeni token
gerekir (anahtar yenilemesiyle birlikte). O gelene kadar test başlamaz (durum: waiting_scope).