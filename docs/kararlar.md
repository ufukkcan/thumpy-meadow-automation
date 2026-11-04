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
