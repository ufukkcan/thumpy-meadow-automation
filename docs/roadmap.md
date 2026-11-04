# Ustalık Yol Haritası

Bu projede çalışılan konularda dünya çapında uzmanlığa giden yol. Maddeler
öğrenildikçe/uygulandıkça işaretlenir. `[x]` = projede fiilen uygulandı ve çalıştı.

---

## 1. Programatik 2D animasyon

### Temel
- [x] Pillow ile vektörel his veren çizim (yuvarlatılmış dikdörtgen, elips, polygon)
- [x] Katmanlı arka planla derinlik (uzak tepeler → ağaçlar → zemin)
- [x] Paralaks: farklı hızlarda kayan bulutlar
- [x] Statik arka planı bir kez çizip her karede kopyalama (performans)
- [x] Kareleri diske yazmadan doğrudan ffmpeg stdin'e akıtma
- [x] Güvenli alan hesabı (YouTube banner 1546×423 merkez)

### Orta
- [x] Karakter ruh halleri (`mood="happy"/"excited"`) tek fonksiyonda
- [x] Sticker efekti: alfa kanalını `MaxFilter` ile büyütüp beyaz kenar + gölge
- [x] Sunburst arka plan (merkezden yayılan ışınlar) — dikkat yönlendirme
- [ ] Easing fonksiyonları (ease-in-out, overshoot, anticipation)
- [ ] İskelet/parça tabanlı karakter (kol-bacak ayrı katman, poz interpolasyonu)
- [ ] Sahne geçiş efektleri (wipe, iris, zoom)

### İleri
- [ ] Disney'in 12 animasyon ilkesinin koda dökülmesi (squash & stretch,
      anticipation, follow-through, secondary action)
- [ ] Zaman çizelgesi/sahne tanımını veriden üretme (JSON → animasyon)
- [ ] Lip-sync: seslendirmeden fonem çıkarıp ağız şekli eşleme
- [ ] SVG tabanlı çizim + rasterleştirme (daha temiz kenarlar, ölçeklenebilirlik)

**Az bilinen teknik:** Alfa kanalına `MaxFilter` uygulayıp beyaz dolgu ile
birleştirmek, çizim kütüphanesi "stroke" desteklemese bile kalın kontur verir.
Aynı maskenin bulanıklaştırılmış hali gölge olur. Tek geçişte sticker görünümü.

---

## 2. Ses işleme ve şarkı sentezi

### Temel
- [x] Toplamalı sentez: sinüs + harmonik + üstel zarf (marimba, zil, bas)
- [x] Gürültüden davul: bant sınırlı gürültü + zarf (kick, clap, hi-hat)
- [x] Kaba beyaz gürültünün "cızırtı" duyulması, bant sınırlamanın çözmesi
- [x] Kesik noktalarda tıklama önleme (kare fade-in/out)
- [x] Ducking: vokal zarfına göre müziği kısma
- [x] Netlik EQ'su (2–5 kHz presence, 120 Hz altı temizlik)

### Orta
- [x] WORLD vokoder (`pyworld`): f0/spektrum/aperiyodiklik ayrıştırma ve sentez
- [x] Perdeyi notaya çekmenin "autotune/robot" etkisi; doğal dalgalanmayı kısmen
      koruyarak yumuşatma
- [x] Formant koruyarak perde kaydırma (Rubber Band `-F`)
- [x] Rubber Band R2 (ffmpeg filtresi) ile R3 (`rubberband -3`) kalite farkı
- [x] Sadece ünlüyü uzatma, ünsüzü doğal bırakma (legato + anlaşılırlık)
- [x] Ünlü başlangıcına göre hizalama (kulak vuruşu ünsüzde değil ünlüde algılar)
- [x] Kelime sınırlarını TTS'ten alma (edge-tts `WordBoundary`)
- [ ] Koartikülasyon: kelimeleri cümle akışından kesmenin doğallığa etkisi
      *(teşhis edildi, çözüm test edilmedi)*

### İleri
- [ ] HMM/sinir ağı tabanlı şarkı sentezi (NNSVS, DiffSinger) — yerel çalıştırma
- [ ] Vibrato, portamento, nefes seslerinin doğal modellenmesi
- [ ] Çok sesli (harmoni) vokal üretimi
- [ ] Gerçek zamanlı olmayan mastering zinciri (kompresör, limiter, stereo genişlik)

**Az bilinen teknik:** Perdeyi sonradan kaydırmak yerine **TTS motoruna doğru
perdede ürettirmek** (edge-tts `pitch="+80Hz"`) çok daha doğal sonuç verir; sonradan
yapılan her işlem kusur ekler. Kaynağı düzeltmek, çıktıyı onarmaktan iyidir.

**Ölçüm tekniği:** Müzik kodla üretildiği için birebir yeniden üretilip karışımdan
çıkarılabilir; geriye sadece vokal kalır ve objektif ölçülebilir.

---

## 3. YouTube çocuk içeriği: algoritma ve SEO

### Temel
- [x] COPPA / "made for kids" ve sonuçları (yorum, bildirim, reklam)
- [x] Chapter kuralları (00:00 başlangıç, ≥3 adet, ≥10 sn)
- [x] Başlıkta anahtar kelime önceliği, ≤70 karakter
- [x] Açıklamanın ilk 150 karakterinin önemi
- [x] Küçük resim A/B testi (Test & Compare)
- [x] Yanıltıcı küçük resmin cezalandırılması → sadece videoda geçen objeler
- [x] Yayın tarihinin ilk yüklemede sabitlenmesi

### Orta
- [ ] Audience retention grafiğini okuma ve düşüş noktalarını tespit
- [ ] İlk 30 saniyenin elde tutmaya etkisi (ölçülerek)
- [ ] Oynatma listelerinin oturum süresine etkisi
- [ ] Shorts → uzun video yönlendirme hunisi
- [ ] Rakip kanal analizi (hangi konular, hangi uzunluk, hangi sıklık)

### İleri
- [ ] YouTube Analytics API ile otomatik performans raporu
- [ ] İçerik-performans korelasyonu (hangi ders tipi daha çok izleniyor)
- [ ] Çok dilli yayın (aynı animasyon, farklı seslendirme)

**Az bilinen gerçek:** "Made for kids" kanallarda trafiğin neredeyse tamamı
**önerilen videolar**dan gelir (ilk videoda %100). Arama ve abonelik ikincildir.
Bu yüzden asıl optimizasyon hedefi ortalama izlenme süresidir, tıklanma ikincil.

---

## 4. Python medya üretim hattı

- [x] ffmpeg'i stdin borusuyla besleme (ara dosya yok)
- [x] `filter_complex` zinciri (altyazı, overlay, drawtext)
- [x] libass `MarginV` ölçeklemesi ve gerçek kareyle doğrulama
- [x] Süreye göre bitrate hesaplayarak hedef dosya boyutu tutturma
- [x] Dış komut hatalarını stderr ile birlikte yüzeye çıkarma
- [ ] Paralel kare üretimi (multiprocessing) — render süresini düşürmek için
- [ ] Donanım hızlandırmalı kodlama (NVENC/QSV) — runner'da yok, yerelde olabilir
- [ ] Ara ürünleri önbellekleme (aynı sahne tekrar render edilmesin)

---

## 5. LLM ile içerik üretimi

- [x] Yapılandırılmış JSON çıktısı isteme ve ayrıştırma
- [x] Beyaz liste doğrulaması (`validate_prop`) — modelin uydurduğunu engelleme
- [x] Güvenlik kurallarını prompta gömme (`SAFETY_RULES`)
- [x] Talimat dili ile çıktı dilini ayırma (Türkçe talimat → İngilizce içerik)
- [x] Tekrarı önlemek için geçmiş konu listesi besleme
- [ ] Senaryo kalitesini otomatik puanlama (ikinci bir model ile kontrol)
- [ ] Few-shot örneklerle stil tutarlılığı
- [ ] A/B: farklı prompt sürümlerinin izlenme performansına etkisi

**Az bilinen teknik:** Modelin ürettiği her "nesne"yi koddaki bir beyaz listeye karşı
doğrulamak, halüsinasyonu tamamen ortadan kaldırır. Model listede olmayan bir şey
isterse o alan sessizce boş bırakılır, sistem çökmez.

---

## 6. Otomasyon altyapısı

- [x] GitHub Actions: cron + `workflow_dispatch` + `concurrency`
- [x] State'i repoya commit ederek kalıcılık (veritabanı olmadan)
- [x] OAuth 2.0 refresh token akışı ve kanal doğrulaması
- [x] Secret yönetimi (değerler kodda değil)
- [x] Public repo ile sınırsız ücretsiz Actions
- [x] Telegram Bot API ile buton tabanlı onay akışı
- [ ] Harici cron tetikleyici (GitHub cron gecikmesine karşı)
- [ ] Hata durumunda otomatik yeniden deneme (exponential backoff)
- [ ] Çok kanallı tek kod tabanı (konfigürasyonla ayrışan kanallar)

**Az bilinen teknik:** Küçük otomasyonlarda veritabanı kurmak yerine state'i JSON
olarak repoya commit etmek yeterli; hem ücretsiz, hem versiyonlu, hem denetlenebilir.
