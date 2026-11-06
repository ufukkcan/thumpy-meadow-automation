# Yapılacaklar

İşaretleme: `[x]` doğrulanarak tamamlandı · `[~]` kısmen · `[ ]` yapılmadı

---

## 1. Kanal kurulumu — TAMAMLANDI

- [x] Kanal adı araştırması (12+ isim YouTube'da tarandı)
- [x] "Thumpy Meadow" seçildi, `@ThumpyMeadow` boş doğrulandı
- [x] YouTube kanalı oluşturuldu (`UC9_bFi-Pyp8hTlclZYkcz-Q`)
- [x] Kanal açıklaması yazıldı ve yayınlandı
- [x] 10 kanal anahtar kelimesi eklendi
- [x] **Audience: "made for kids"** ayarlandı (COPPA) — Studio'da doğrulandı
- [x] Banner üretildi (güvenli alan testi yapıldı) ve yüklendi
- [x] Profil resmi üretildi (daire kırpımı test edildi) ve yüklendi
- [x] Ülke ayarı yapıldı
- [x] Telefon doğrulaması (özel küçük resim izni) — Studio'da "Upload file" göründü
- [ ] Marka (ticari isim) araştırması: TÜRKPATENT / EUIPO / USPTO'da "Thumpy Meadow"

## 2. Üretim motoru — TAMAMLANDI

- [x] Dino karakteri (mutlu + heyecanlı ruh hali)
- [x] Katmanlı arka plan, kayan bulutlar
- [x] Obje kütüphanesi: balon(7), şekil(7×7), meyve(7), hayvan(6), sayma(1–10)
- [x] Obje doğrulama (beyaz liste) — bozuk prop testi yapıldı
- [x] 16:9 yatay düzen, 1920×1080, 24 fps
- [x] Kare kare çizim → ffmpeg borusu (diske PNG yazmıyor)
- [x] Altyazı kutusu, otomatik satır bölme
- [x] Karaoke görünümü (çalan kelime sarı, zıplıyor)
- [x] Fon müziği sentezi (marimba + pad, C-G-Am-F)
- [x] Seslendirme: `en-US-AnaNeural` seçildi (A/B testi yapıldı)
- [x] Gerçek ses süresine göre sahne zamanlaması
- [x] Meyve çizim hataları düzeltildi (elma, muz, çilek)

## 3. Otomasyon — TAMAMLANDI

- [x] Claude ile 3 fikir üretimi
- [x] Claude ile tam senaryo (bölümler, segmentler)
- [x] Çocuk güvenliği kuralları prompta gömüldü
- [x] SEO kuralları prompta gömüldü
- [x] Telegram botu `@thumpymeadow_bot`
- [x] Durum makinesi (idle/choosing/reviewing/done/error)
- [x] Senaryo onayı (.txt + Onayla/Yeniden yaz)
- [x] Hata durumu + "Tekrar dene" butonu
- [x] "video üret" her durumda sıfırlayıp yeni döngü başlatıyor
- [x] YouTube yükleme (gizli + zamanlanmış + made for kids + kategori 27)
- [x] GitHub Actions workflow'ları
- [x] State'in repoya yazılması
- [x] 6 GitHub Secret eklendi
- [x] YouTube OAuth — **doğru kanal doğrulanarak** alındı

## 4. SEO ve yayın — TAMAMLANDI

- [x] Başlık kuralları (anahtar kelime başta, ≤70 karakter, tık tuzağı yok)
- [x] Açıklama üretimi (ilk 150 karakter + öğrenilenler + chapters + kanal tanıtımı)
- [x] Bölüm başlıkları (YouTube chapter kurallarına uygun)
- [x] Etiket ve hashtag üretimi
- [x] Küçük resim: sunburst, sticker, heyecanlı karakter, renkli başlık, 3 varyasyon
- [x] Küçük resimde sadece senaryoda geçen objeler (yanıltıcı değil)
- [x] Öğrenen yayın saati planlayıcı (ABD Doğu, 4 aday saat)
- [x] 48 saatlik izlenme ölçümü + haftalık Telegram raporu
- [x] İlk videoya 3 varyasyonlu A/B testi kuruldu

## 5. İlk yayın — TAMAMLANDI

- [x] Uçtan uca ilk bölüm üretildi (10:41)
- [x] YouTube'a yüklendi ve zamanlandı (`WIEorW7zW10`)
- [x] Studio'da ayarlar doğrulandı
- [x] Küçük resimler elle yüklendi (A/B testi)
- [x] İlk gün analitiği alındı ve yorumlandı

## 6. Müzik molası vokal kalitesi — DEVAM EDİYOR

- [x] Telifsiz melodi şablonları (4 adet, 1929 öncesi kamu malı)
- [x] Hece sayacı (54/54 doğru) + kelime→nota eşleme
- [x] Davul, bas, akor düzenlemesi
- [x] Vokoder ile şarkı söyletme denemesi (A) — robotik, reddedildi
- [x] Ritmik anlatım denemesi (B) — ritim yok
- [x] Doğal satırdan kelime kesme (C) — cızırtılı
- [x] Hece bölme + ünlü hizalama (D) — **ritim onaylandı**
- [x] Perdeyi TTS motorunda üretme (E) — **ses beğenildi**, kayma var
- [x] Legato + küçük kelimeler (G) — sorun sürüyor
- [x] Cızırtı kaynakları giderildi (yumuşak geçişler, davul yumuşatma, R3 motoru)
- [x] Hece hizalaması ölçülerek doğrulandı (sapma ≤0,05 vuruş)
- [-] ~~`SPLIT_SYLLABLES=False` testi~~ — İPTAL (2026-11-04): bu değişiklik repoda yok,
      ayrıca kural 8 gereği edge-tts ile şarkı yolu kapatıldı (bkz. K-16)

### 6b. Yeni plan (2026-11-04) — kullanıcı: "kalite, ritim, melodi, vokal hepsi kötü"

Tespit (koddan): üretimdeki mola `music.music_break_track` kullanıyor — rastgele
pentatonik melodi (K-12 kararı üretime hiç bağlanmamış), kelimeler 6 vuruşa eşit
bölündüğü için notalar vuruş ızgarasına oturmuyor (`music.py:106`), davul yok,
enstrümanlar saf sinüs, mastering yok (sadece tepe normalizasyonu).

**Adım 1 — Araştırma (kod yok, sadece rapor)**
- [x] 1a. Açık kaynak şarkı modelleri: aday listesi; her biri için ticari kullanım
      lisansı, İngilizce kalite, söz+melodi kontrolü, GitHub Actions CPU'da süre/RAM
- [x] 1b. CC0 enstrüman ses paketleri: aday listesi; lisans sayfası tek tek doğrulanır
      (CC0 değilse elenir), boyut, enstrüman çeşitliliği
- [ ] 1c. Rapor + birlikte seçim

**Adım 2 — Enstrümantal mola (vokalden bağımsız)**
- [~] 2-test. `samples.py` + `kidsong.py` + `music_test.py` + `music_test.yml` yazıldı
      (2026-11-04). Yerelde çalıştırılmadı (kurumsal kısıt); GitHub Actions sonucu bekleniyor.
- [ ] 2a. Kamu malı melodiler (`songs.py`) üretime bağlanır; her nota vuruş ızgarasında
- [ ] 2b. Claude prompt'u: her satır için hece sayısı melodiye göre verilir
- [ ] 2c. Seçilen CC0 seslerle düzenleme (davul grubu, bas, akor, melodi enstrümanı)
- [ ] 2d. Mastering: kompresör + limiter + hedef ses yüksekliği (LUFS ölçülür)
- [ ] 2e. Karaoke zamanlaması nota ızgarasından alınır
- [ ] 2f. Kanıt: 1 dk örnek; nota başlangıçlarının ızgaradan sapması ölçülür, LUFS
      ölçülür, kullanıcı dinler (hangi dosyayı dinlediği yazılır)

**Adım 2 sonucu (2026-11-04):** Kullanıcı dinledi: "gayet güzel olmuş".
Ölçüm: ritim sapması ort. 2,0–2,3 ms, en kötü 6,7 ms (0,013 vuruş); -14,3 LUFS;
gerçek tepe -0,9 dBTP (hedef -1,0 → hedef -1,5'e çekilecek). Ksilofon örnekleri adından
1 oktav yüksek (tutarlı, akort sorunu yok).

**Adım 3 — Vokal: DiffSinger + Hanami Hoshino (İngilizce, Lotte V)**
- [!] 3a-bulgu (2026-11-04): `lottev1991/LotteV-Voicebank-Update-Repo` (commit b866687)
      okundu. ToU ve LICENSE-voicebank ticari kullanıma izin veriyor (kaynak gösterme
      şart, orijinal dosyaları yeniden yüklemek yasak). **LICENSE-vocoder = CC BY-NC-SA 4.0
      (ticari kullanım YASAK)** → bankanın kendi vocoder'ı monetize kanalda kullanılamaz.
      Kullanıcı kararı bekleniyor.
- [x] 3a-sonuç (2026-11-04): keşif raporu alındı (zip sha256 91d9302c…, 550 MB, MediaFire).
      acoustic.onnx ve pitch.onnx yalnızca ORT_DISABLE_ALL ile yükleniyor. Banka içindeki
      vocoder de CC BY-NC-SA → BigVGAN-v2 (MIT, rev 95a9d1d) kullanılacak.
- [x] 3b/3c deneme 1/3 (run 41831442626): ritim ✔ (ort. 16–28 ms), perde ✔ (ortanca 5–7 cent),
      **ses kalitesi ✘** (kullanıcı: "berbat"); vocoder uyumu 2.1–2.4. Kök neden: E13.
      Süre: akustik ~0.6x, BigVGAN ~5.5x gerçek zaman (CPU).
- [x] Deneme 2/3 (run 41834423965): vocoder uyumu 0.29–0.31 = kopya sentez tavanı (0.31);
      perde ortanca 4–5 cent; ritim ort. 20–27 ms. Kullanıcı (vocal_test.mp3): "ritim
      tutturması çok güzel, biraz robotik, ara sıra küçük cızırtılar".
- [~] Deneme 3/3: Hanami'nin perde modeli (pitch.onnx, OpenUtau beslemesiyle aynı), satır
      aralarında nefes (AP), fonem ≥2 kare, tık dedektörü. Olmazsa DUR → birlikte karar.
- [x] 3a. Keşif (ses üretmez): ses bankasının resmi indirme adresi ve ToU metni
      Claude tarafından okunur; vocoder lisansı okunur. Actions'ta keşif workflow'u:
      bankayı indirir, dosya yapısını, `dsconfig.yaml`'ı, sözlüğü ve ONNX modellerin
      giriş/çıkış adlarını yazdırır. (Varsayımla kod yazılmaz — kural 2)
- [ ] 3b. `sing.py`: söz → fonem (bankanın İngilizce sözlüğü) → süreler bizim nota
      ızgarasına (ünlü başı vuruşta, ünsüz vuruştan önce) → perde notalardan (yumuşak
      geçiş + hafif vibrato) → akustik model → vocoder. onnxruntime, sadece CPU.
- [ ] 3c. `music_test.py`'ye vokal: Twinkle + London Bridge (mevcut özgün sözlerle),
      vokal varken müzik hafif kısılır. Ölçüm: hece başlarının vuruştan sapması,
      perde doğruluğu (cent), süre, LUFS. Kullanıcı dinler.
- [x] Deneme 3/3 (run 41836574820) — **KULLANICI ONAYLADI: "süper olmuş"**. Perde ortanca
      10–11 cent (doğal perde), ritim ort. 20–27 ms, vocoder 0.30–0.33 (tavan 0.31), CPU ~7x
      gerçek zaman. Tık dedektörü: 6 olay, 4'ü nefes (AP) anında → takip maddesi.
- [ ] Takip: nefes (AP) anındaki kısa tıklar (dedektör 4 olay) — düşük öncelik

### 6c. Yeni müzik molasını üretime bağlama (2026-11-04, kullanıcı: "akşam için video")
> **2026-11-05: ÜRETİMDE.** episode_test run 41979380747 başarılı (mola -21.2 LUFS ≈ anlatım, karaoke senkron, 4 mola senaryosu); kullanıcı onayıyla main'e birleştirildi (fb231c2).
> **2026-11-04 akşam: ERTELENDİ, ertesi gün devam.** Kod değişikliği başlamadı.
> Bot `choosing` durumunda (11:00 fikirleri: Balloons / Shapes / Animal Sounds). Entegrasyon
> bitmeden fikir seçilirse video ESKİ müzik molasıyla üretilir.
> Kullanıcı onaysız yükleme istedi; senaryo onayı (⛔ kuralı) atlanmadı, plan: entegrasyon
> sonrası bot "yeni format hazır" mesajı atar, kullanıcı telefondan seçer + onaylar.
- [x] U1. `generate_episode.py`: her müzik molasına melodi atanır (twinkle/london/mary/jacques
      sırayla); Claude'a satır sayısı + satır başına HECE SAYISI verilir; sözler CMU sözlüğünde
      olmalı (yoksa Claude'a bir kez eksik kelimelerle yeniden yazdırılır)
- [x] U2. `kidsong.duration()` (ucuz süre hesabı, senaryo onayında süre tahmini için)
- [x] U3. `vocal_break.py`: mola sesi = kidsong + Hanami vokali (modeller bir kez yüklenir);
      karaoke kelime zamanları nota ızgarasından
- [x] U4. `episode.py`: build_timeline(with_audio) + mola ses seviyesi anlatımla eşitlenir
- [x] U5. Açıklamaya `sing.CREDIT` satırı (vokalli bölümlerde)
- [x] U6. (gerek kalmadi: agir bagimliliklar uretim aninda kuruluyor, vocal_break._ensure_deps) `check_and_produce.yml`: vokal bağımlılıkları + 3 önbellek
- [x] U7. Kanıt: `episode_test.yml` — örnek kısa bölüm (gerçek Ana sesi + 1 vokalli mola),
      YÜKLEME YOK; kareler gözle kontrol, ses ölçülür, kullanıcı izler
- [ ] U8. Kullanıcı Telegram'dan fikir seçer → senaryo onayı (İNSAN ONAYI ŞART) → yayın
- [ ] 3d. En fazla 3 deneme; olmazsa dur, birlikte karar (kural 8)
- [ ] 3e. Onaylanırsa üretime bağlama (ayrı plan) + açıklamaya "Voice: Hanami Hoshino
      by Lotte V" kaynak satırı

**Sonra**
- [ ] Müzik molası görselini zenginleştir (objeler dans etsin, sadece yazı+Dino olmasın)

## 7. İzlenme ve tıklanma — PLAN (2026-11-05, onay bekliyor)

**Veri (WIEorW7zW10, 3 gün):** 569 gösterim, CTR %2,3, 15 izlenme, ort. 1:44 (%16,3).
Tutma: ~%45 ilk ~12 sn'de çıkıyor (statik Dino + "Hello friends" yazısı), ~45. sn'de
%25'e iniyor, ~2:15'ten sonra %13 (2 kişi). Örnek küçük (15 izlenme), yön net.
**Hedef:** CTR > %4, izleme oranı > %35. A/B testi kullanıcı tarafından yanlışlıkla
silindi (11-05), yeni küçük resimle yeniden kurulacak.

**A. Açılış (en büyük kayıp burada)**
- [ ] A1. Soğuk açılış: 0. saniyede bölümün şarkısının nakaratı + hareketli objeler
      (şu an ilk obje 29. sn'de)
- [ ] A2. "Hello friends" selamlaması en fazla 3 sn, hemen ilk objeye geç
- [ ] A3. 3 sn'lik tanıdık jingle + Dino'nun tekrar eden sözü (marka)

**B. Format: şarkı ağırlıklı**
- [ ] B1. Anlatım/şarkı oranını tersine çevir: her ders kısa anlatım + şarkı
      (şu an ~%80 anlatım)
- [ ] B2. Ekranda sürekli hareket: objeler zıplasın/dönsün/parıltıyla belirsin,
      Dino yeni objede heyecanlansın, sahne 3–5 sn'de bir değişsin
      (önce mevcut tempoyu karelerden ölç)
- [ ] B3. Sahne çeşitliliği: çiftlik, deniz, gece, bahçe

**C. Paketleme**
- [ ] C1. Küçük resim yeniden: tek büyük ifadeli Dino yüzü + tek parlak obje +
      en fazla 1–3 kelime, yüksek kontrast; liste boyutunda okunurluk testi
- [ ] C2. A/B testini yeni tasarımla yeniden kur (kullanıcı, Studio)

**D. Dağıtım**
- [ ] D1. Shorts: her bölümün şarkı molalarından 30–60 sn dikey kesit
- [ ] D2. Derleme: mevcut bölümlerden 30–60 dk videolar
- [ ] D3. Oynatma listeleri (Colors, Numbers…)
- [ ] D4. Düzenli yükleme: en az gün aşırı

**E. Sonra**
- [ ] E1. İspanyolca ses kanalı (çok dilli ses)
- [ ] E2. 0–2 yaş duyusal seri (sade şekil + müzik)

**Politika notu:** YouTube düşük kaliteli çocuk içeriğini ve seri üretilmiş/tekrarlı
içeriği cezalandırıyor. Her bölüm gerçekten farklı olmalı; senaryo onayı korunur.

### 7a. Görsel prototip — 30 sn (K-19, 2026-11-05, onay bekliyor)

Amaç: yeni görünümü üretime bağlamadan önce kullanıcıya izletmek. Üretim koduna
dokunulmaz; ayrı dosyalar + ayrı workflow, ayrı dal (`visual-proto`).

- [x] P1. `assets.py`: Fluent Color SVG'leri commit `1ffb34c` ile sabit raw URL'den
      indir, `asset_cache/`'e önbellekle; prop adı → Fluent klasör eşlemesi; MIT metni
      `licenses/fluentui-emoji-LICENSE` olarak repoya
- [x] P2. `render2.py`: Skia motoru; SVG'yi bir kez rasterleştirip önbellekle; katman
      birleştirme. Skia'nın SVG desteği Fluent gradyanlarını doğru çiziyor mu, karede
      gözle kontrol (olmazsa resvg)
- [x] P3. Yeni Dino (Skia, gölgeli/gradyanlı, Fluent stiline uyumlu): göz kırpma,
      sese göre ağız hareketi, nefes salınımı, el sallama, zıplama
- [x] P4. Arka plan: çayır, 3 katman paralaks, yumuşak gradyan gökyüzü
- [x] P5. Hareket araçları: yumuşak geçişler (easing), esneyerek belirme, parıltı ve
      konfeti parçacıkları, kamera yakınlaşma/kayma, daire geçişi
- [x] P6. Prototip sahnesi (~30 sn): 0. sn şarkı nakaratı + zıplayan objeler →
      3 sn selam → "hediye kutusu sürprizi" oyunu (3 obje) → kısa şarkı kapanışı.
      Ses: mevcut `vocal_break` + edge-tts
- [x] P7. `visual_proto.yml`: mp4 + örnek kareler artifact; kare başına render süresi
      ölçülür → tam bölüm süresi tahmini (Actions 6 sa sınırı)
- [x] P8. Kareleri gözle kontrol, kullanıcı izledi (tur 1): "bir tık daha güzel ama
      daha çizgi filmsel olsun" → 7b
- [ ] P9. Onaylanırsa üretime bağlama planı (senaryo şeması: oyun kalıpları, sahneler,
      genişletilmiş beyaz liste) ayrıca yazılıp onaya sunulur

### 7b. Pilot bölüm — "Thumpy formülü" (2026-11-05, kullanıcı: "bu formatta yeni video")

Dayanak: `docs/arastirma-cocuk-izleme.md` §12, `docs/arastirma-2d-kanallar.md`.
Ayrı dosya `pilot.py` + `pilot.yml`, dal `visual-proto`. Üretime bağlı değil, YÜKLEME YOK.
Süre ~3–3,5 dk (tüm formül parçaları; tam 10–12 dk bölüm görünüm onayından sonra).
Senaryo elle yazıldı → **kullanıcı onayı** push'tan önce (çocuk güvenliği kuralı).

- [x] B1. Çizgi film stili (`render2.py`): kalın koyu kontur (Dino + Fluent nesneleri,
      alfa genişletme ile bir kez), bebek şemalı Dino (iri göz), doygun yanak/kuyruk,
      ifadeler (mutlu/şaşkın/dinliyor), kaş, düşme pozu, hazırlık + ezilme, kol gecikmesi
- [x] B2. Konturlu çalı (göz kırpan gözler arkasından bakar), soru balonu (bekleme sayacı)
- [x] B3. Kamera planları: geniş/yakın/çalı yakını, sert kesme (yavaş zoom yok)
- [x] B4. Senaryo (kullanıcı onayladı): selam şarkısı (0. sn, Frère Jacques) → saklambaç: inek, ördek, köpek
      (ses ipucu → soru + 2,5 sn bekleme → yanlış çalı gag'i → "Peekaboo!" → kelime 3 kez)
      → hareket molası (London Bridge: tavşan gibi zıpla, fil gibi tepin) → tekrar
      (çocuk tamamlar) → sonraki bölüm ipucu → veda şarkısı (Twinkle)
- [x] B5. Duman testi + render; run 42010325985 başarılı, 3:19, 71 ms/kare; 14 kare gözle
      kontrol. Ses yerelde ölçülmedi (kullanıcı dinleyecek)
- [ ] B6. Kullanıcı izler; en fazla 3 tur. Kendi bulduğum küçük hatalar (sonraki turda):
      arkadaş sırasındaki hayvanların gölgesi zeminde kalıyor; çalı gözleri kaybolurken
      göz kırpma çizgisi küçülmüyor; karaokede büyüyen kelime komşusuna biniyor
      Tur 1 geri bildirimi (11-05): bekleme süreleri ve ses dengesi iyi; hayvan sesleri gerçek
      olsun; çizgi film havası ve şakalar daha iyi ama geliştirilebilir → 7c

### 7d. Yeni formatı üretime bağlama + SEO + 3 küçük resim (2026-11-05, onay bekliyor)

Kullanıcı: "bu formatların hepsini commitleyelim, bugüne yeni video; arama için başlık/açıklama;
çok profesyonel 3 thumbnail, yüklemede otomatik (bundan sonraki tüm videolar için)".
Bulgu: API'de Test & compare yok; ayrıca made-for-kids videolarda Studio'da da kapalı
(support.google.com/youtube/answer/13861714) → sıralı otomatik test önerildi.

Kararlar (kullanıcı): bölüm 8–10 dk; küçük resim sıralı otomatik test (K-20, K-21).

- [x] D1. `show.py`: veriyle çalışan motor (6 oyun, kayan dünya, çerçeve finali, bölümler)
- [x] D2. Ses kütüphanesi 11 hayvan (BigSoundBank CC0, lisans sayfaları + HEAD doğrulandı;
      domuz/fil/maymun/aslan için gerçek kayıt yok)
- [x] D3. `generate_episode.py`: yeni şema + katalog doğrulaması + şarkı hece düzeltme turu
- [x] D4. SEO: başlık kalıbı, açıklama (hayvanlar, bölümler, kaynaklar), etiket, hashtag,
      `localizations` es/pt/tr/id
- [x] D5. `thumbs.py`: 3 konsept + telefon önizlemesi (kod yazıldı; görsel kanıt D7'de)
- [ ] D6. Yükleme: kanal doğrulaması `verify_channel()` + A otomatik + A/B/C `state/thumbs/`
      (yazıldı). Sıralı test koşucusu: yeni token (yt-analytics.readonly) gelince
- [x] D7. Uçtan uca test: run 42029359003 başarılı (8:08, tahmin 8:04, 14 bölüm, 73 ms/kare,
      üretim 24 dk, 3 thumbnail + telefon önizlemesi gözle kontrol). Son bulgu: tekrar/finalde
      eski ağaç ekranda (WALK 1100 yetersiz) → WALK 1900 (geometri: 1400-1900 = -500, ağaç ±310)
- [x] D7b. main'e birleştir (kullanıcı onayı 11-05)
- [ ] D8. Bugünkü video: Telegram "video üret" → fikir → senaryo onayı → yükleme

### 7e. Analitik (2026-11-06) + Shorts + başlık kuralı (onay bekliyor)

Veri: wfW6tyCYbz4 (yeni format, 5 Kasım 21:00 TR) 17 saatte 7 izlenme (sayfa sayacı); Studio verisi
48–72 sa gecikmeli → **8 Kasım'da** gösterim/CTR/tutma çekilecek. H9epa9bfhhI: 63 gösterim, %0 CTR,
0 izlenme (Studio, 3–4 Kasım). Aramada dizinde (ceza yok); kendi tam başlığıyla #36, "Count to 10" #1.
Yorum: gösterim var, tıklama yok + ilk videonun zayıf CTR/tutma sinyali sonrası küçük deneme bütçesi.

- [x] E1. Shorts: her bölümden 2 dikey (1080x1920) "Who says ...?" oyunu (~40 sn), bölümün KENDİ
      sesinden kesilir, sahne yakın planla yeniden çizilir; bölümden 1 ve 2 gün sonra zamanlanır
      → test run 42184070982: civciv 43,2 sn, inek 51,4 sn, kareler gözle kontrol edildi; main'e birleştirildi
      (11-06). Küçük kadraj kusurları (ağaç tacı başlığa biniyor, Dino kenarda kesik) açık.
- [ ] E2. Başlık kuralı: rekabeti düşük uzun ifade önce (aramada ölçülür), genel ifade ikincil
      (11-06 onaylandı). Claude 5 aday ifade + `title_rest` → `seo.py`: otomatik tamamlama talebi +
      search.list ilk 10 medyan izlenme/abone → talebi olan, rekabeti en düşük ifade başa. Onay metninde
      ölçüm tablosu. Hata bölümü durdurmaz. Test: show_test TITLE_ONLY (2 senaryo, render yok)
      → deneme 1 (run 42226025840): Claude'un 7 uydurma ifadesinin 7'si de aranmıyor (öneri 0).
      → deneme 2: adaylar otomatik tamamlamadan KEŞFEDİLİR, Claude yalnızca dürüst olanları seçer.
        Run 42226647735 başarılı: "Hide and Seek Animals | Rainbow Hide and Seek | Thumpy Meadow"
        (928K medyan vs "animal sounds for toddlers" 17,2M). main birleştirmesi onay bekliyor.
- [ ] E3. 8 Kasım: yeni videonun gösterim, CTR, trafik kaynağı, tutma grafiği → karar

### 7c. Pilot tur 2 (2026-11-05, onaylandı → push `69212e6`, run 42016648248 başarılı, 3:47)

Kanıt: 95 karenin 13'ü gözle kontrol. Ses kesimi: inek 1 çağrı (1,52 sn), ördek 6, köpek 1 (0,26 sn).
Bulunan hatalar (tur 3'te): aslan silueti tanınmıyor (Fluent aslan sadece yüz → koyu kalkan);
balon ipleri ikinci kez çizilmiş (Fluent balonun kendi ipi var); köpek ağaçtan bakarken Dino
çok yakın, sol bakış Dino'nun arkasında kalıyor; ördek buluttan bakarken ters yöne bakıyor ve
neredeyse görünmüyor.


- [ ] C1. Gerçek hayvan sesleri: BigSoundBank (lisans sayfası: CC0 / kamu malı, düzenleme,
      ticari ve videoda kullanım serbest, Content ID'ye kayıtlı değil). Sabit dosya adresi
      `bigsoundbank.com/UPLOAD/flac/<id>.flac`, önbellek + lisans notu `licenses/`.
      İnek s2383, ördek s0276 (en temiz tek "vak" kod ile kesilir), köpek s2352.
      Hayvan konuşmaz: "Peekaboo!" yerine gerçek sesiyle çıkar
- [ ] C2. Hikâye: neden saklanıyorlar → Dino'nun doğum günü sürprizi; sonda hepsi birden
      "Surprise!" + pasta (beyaz listeye "cake" eklenir, Fluent "Birthday cake")
- [ ] C3. Şakalar: üç kuralı (her biri bir öncekinden büyük), farklı saklanma yerleri
      (çalı / ağaç / bulut), hayvana özgü kutlama hareketi, tekrar eden küçük şaka (Dino'nun
      kuyruğu)
- [ ] C4. Çizgi film hareketi: inişte toz bulutu, sallanan çalıdan yaprak, hız çizgileri,
      hayvanlara ezilme-esneme ile yürüyüş, şaşkınlıkta ter damlası
- [ ] C5. Tur 1 hataları (gölge, göz kırpma çizgisi, karaoke binmesi, düşme açısı)

## 8. Büyüme — SONRA

- [ ] ABC / harf dersleri (harf çizimi kütüphaneye eklenecek)
- [ ] Her bölümden otomatik Shorts kesiti (dikey, 30–60 sn)
- [ ] Oynatma listeleri (YouTube yetkisi genişletilmeli)
- [ ] Yeni karakterler (tavşan, ayı, fil)
- [ ] Harici cron tetikleyici (cron-job.org) — GitHub cron gecikmesine karşı

## 9. Bakım ve güvenlik

- [ ] **Sohbette paylaşılan tüm anahtarları yenile** (Claude API, Telegram bot token,
      Google client secret, refresh token) ve GitHub Secrets'ı güncelle
- [ ] GitHub fine-grained token `thumpy-claude-push` yenile (2026-11-04'te 1 yıllık
      oluşturuldu; yalnızca bu repo, Contents+Workflows yazma; Windows Credential Manager'da)
- [ ] `astrologicalshorts` refresh token'ının doğru kanala ait olduğunu doğrula
      (`yt_oauth_exchange.py`'nin kanal yazdıran sürümüyle)
- [ ] Deneysel dosyaları temizle (karar verilince: `singer.py`, `sing_test.py`,
      `voice_test.py`, `sample_episode.py`, kullanılmayan `assets/`)
- [ ] `requirements.txt`'e `pyworld` ve `setuptools<81` eklensin (eğer şarkı sistemi
      ana akışa girerse)

---

## İnceleme

Tamamlanan işlerin sonucu ve kanıtı. (CLAUDE.md → Görev Yönetimi madde 4)

### Kanal kurulumu — 2026-11-02
**Sonuç:** Kanal tam yapılandırıldı.
**Kanıt:** YouTube Studio'da doğrulandı — Audience "made for kids" işaretli,
açıklama yayında ("Changes published"), 10 anahtar kelime kayıtlı ("Settings saved"),
`youtube.com/verify` "Phone number verified" döndü, Studio'da Thumbnail bölümünde
"Upload file" seçeneği göründü (telefon doğrulaması aktif).

### Üretim motoru — 2026-11-02
**Sonuç:** 16:9 video motoru, obje kütüphanesi ve müzik sentezi çalışıyor.
**Kanıt:** 36 obje tek sayfada çizilip gözle doğrulandı; hatalı çizimler (elma, muz,
çilek) düzeltilip yeniden kontrol edildi. Sayma/hayvan/meyve/şekil sahneleri gerçek
video karelerinden çıkarılıp incelendi. Küçük resimler telefon boyutunda (210×118)
okunabilirlik testinden geçti. Banner güvenli alan (1546×423) çizilerek doğrulandı.

### Otomasyon — 2026-11-02
**Sonuç:** Telegram → Claude → render → YouTube zinciri uçtan uca çalışıyor.
**Kanıt:** Taklit servislerle uçtan uca test yapıldı; bozuk obje (`{"kind":"dragon"}`)
`None`'a çevrildi, `"n": "3"` metni sayıya dönüştü, 9 kelimeden uzun şarkı satırı
kırpıldı, hashtag'lerden `#` ve boşluk temizlendi. Ardından gerçek çalıştırmada
fikirler → seçim → senaryo → onay → video → YouTube linki zinciri tamamlandı.

### Yayın saati planlayıcı — 2026-11-02
**Sonuç:** Öğrenen planlayıcı doğru çalışıyor.
**Kanıt:** 14 günlük benzetim yapıldı; sistem önce her adayı denedi, sonra daha iyi
performans gösteren saate yöneldi ve arada diğerini denemeye devam etti. Yaz/kış
saati geçişleri ayrı ayrı test edildi (Kasım: 13:00 ABD = 21:00 TR,
Temmuz: 13:00 ABD = 20:00 TR).

### İlk video — 2026-11-02
**Sonuç:** Yayınlandı.
**Kanıt:** `youtu.be/WIEorW7zW10`, 10:41, Studio'da made for kids + Scheduled +
7 chapter + 3 hashtag doğrulandı. Küçük resim A/B testi kuruldu.

### Müzik molası ritim hizalaması — 2026-11-03
**Sonuç:** Ritim hizalaması çözüldü (kullanıcı onayladı: "ritim tutması çok güzel").
**Kanıt:** Hece başlangıçları bağımsız yöntemle (perde + enerji analizi) ölçüldü;
dört farklı satırda hedef vuruşlardan sapma 0,01–0,05 vuruş çıktı. Hece bölme
("banana" → 3 parça) ve legato sonrası hizanın bozulmadığı ayrıca doğrulandı.
**Açık kalan:** Ses kalitesi ve anlaşılırlık (bkz. bölüm 6).

### Müzik molası araştırması (Adım 1a/1b) — 2026-11-04
**Sonuç (şarkı modeli):** Melodiyi (MIDI) + sözü birebir alan, ticari kullanıma açık tek
aday: **DiffSinger (Apache-2.0) + "Hanami Hoshino" İngilizce ses bankası** (Lotte V).
ToU: "allowed to use the voice ... in both commercial and noncommercial projects",
"Please credit me (Lotte V)" — github.com/lottev1991/LotteV-Voicebank-Update-Repo.
Yedek: SoulX-Singer (Apache-2.0, 2026-02) ama ticari hakkı temiz referans ses gerekiyor.
Elenenler: ACE-Step (MIT, ama verilen melodiyi takip edemiyor), YuE / MuLaCover
(CC BY-NC), DiffRhythm/HeartMuLa (melodi girdisi yok + GPU).
**Belirsiz (ölçülmedi):** GitHub Actions CPU süresi; OpenUtau olmadan İngilizce
komut satırı yolu kanıtlanmamış; vocoder lisansı (`LICENSE-vocoder`) okunamadı.
**Sonuç (CC0 sesler):** VCSL (github.com/sgossner/VCSL, LICENSE CC0 1.0): glokenspiel,
ksilofon, marimba, piyano, davul, el çırpma, shaker, tef, blok flüt. Bas:
sfzinstruments/dsmolken.double-bass (CC0). Ukulele: freepats/ukulele1 (CC0, ama repo
2026-08'de açılmış, tek katkıcı — orta risk; alternatif FreePats klasik gitar, CC0).
Elenen: Salamander (CC-BY), GeneralUser GS, FluidR3 (MIT), Philharmonia, 99Sounds,
Sonatina, Iowa MIS. Celesta/müzik kutusu için CC0 kaynak bulunamadı.
**Kanıt:** Lisanslar ajanlar tarafından birincil kaynaktan (GitHub LICENSE/README)
okundu; bağlantılar yukarıda. Ses kalitesi henüz dinlenmedi.
