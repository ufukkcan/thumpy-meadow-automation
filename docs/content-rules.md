# İçerik Kuralları

Claude'un senaryo yazarken uyduğu kurallar. Bu kurallar `generate_episode.py`
içindeki `SAFETY_RULES` ve `STYLE_RULES` bloklarında yaşar; burası insan tarafı
referansıdır.

---

## A. Çocuk güvenliği (en öncelikli, istisnasız)

- İzleyici 2–6 yaş. İçerik her zaman **sakin, nazik, sevecen, olumlu**.
- ⛔ Korku, şiddet, tehlike, kaza, yaralanma, kötü karakter, alay, utandırma
- ⛔ Taklit edilebilecek riskli davranış: tırmanma, atlama, yüksek yer, ateş,
  su kenarı, yabancı, ilaç, küçük nesneleri ağza alma, hayvan kovalama
- ⛔ Marka, ünlü karakter, film, oyun, telifli şarkı adı ya da sözü
- ⛔ Reklam, satın alma, uygulama, link, çocuğu ticari/sosyal eyleme yöneltme
  (kapanışta sadece "ask a grown-up to subscribe" denebilir)
- ⛔ Sağlık/beslenme tavsiyesi, din, siyaset, cinsiyet kalıpları, tartışmalı konu
- ✅ Bilgiler **doğru** olmalı: renkler, sayılar, şekiller, meyve renkleri,
  hayvan sesleri gerçekle uyumlu
  - Ördek "quack", kedi "meow", domuz "oink", kurbağa "ribbit"
  - Tavşan ve balık belirgin ses çıkarmaz → ses uydurma, ne yaptıklarını anlat
    (tavşan zıplar, balık yüzer)
- ✅ Tüm sözler ve metinler **özgün**; bilinen hiçbir tekerleme kopyalanmaz ya da
  yakından taklit edilmez

**Kod tarafındaki güvenlik ağı:** `props.validate_prop()` Claude'un istediği her
objeyi beyaz listeye göre doğrular. Listede olmayan hiçbir şey çizilmez.

**İnsan tarafındaki güvenlik ağı:** Senaryo onayı. Hiçbir bölüm insan okumadan
üretilmez.

---

## B. Anlatım stili

- Anlatıcı: Dino, çocuğun arkadaşı gibi konuşur. Çok basit İngilizce, kısa cümleler.
- **Tekrar ve etkileşim** çok önemli:
  "Can you say red? Red!", "Let's count together!", "Point to the circle!"
  Soruyla bitir, sonraki cümlede cevabı ver (çocuğa cevap için boşluk kalsın).
- Her anlatım segmenti **6–22 kelime**
- Her segmentte **en fazla 1 obje**
- Sayma yapılıyorsa `prop` = `count` ve `n` sayılan sayıyla **birebir aynı**

---

## C. Bölüm yapısı

```
Hello Friends!     4–6 anlatım segmenti
Ders 1             12–16 segment + 1 müzik molası
Ders 2             12–16 segment + 1 müzik molası
Ders 3             12–16 segment + 1 müzik molası
Ders 4             12–16 segment + 1 müzik molası
Let's Remember!    6–8 segment (hızlı tekrar)
Bye-Bye!           3–4 segment
```

Hedef süre: 10–13 dakika.
Bölüm (section) başlıkları kısa ve aranabilir olmalı — YouTube chapter'ı olacaklar.

**Müzik molası:** 4–6 satır, her satır 4–8 kelime, basit, ritmik, kafiyeli, özgün,
o dersle ilgili.

---

## D. Müzik telif durumu

| Öğe | Durum |
|---|---|
| Melodi şablonları | 1929 öncesi kamu malı (Twinkle 1761, Mary 1830, London Bridge 17. yy, Frère Jacques 18. yy) |
| Düzenleme (davul, bas, akor) | Bize ait, kodla üretiliyor |
| Sözler | Claude tarafından özgün yazılıyor |
| Fon müziği | Tamamen sentetik, C-G-Am-F gibi temel akor dizileri (telife konu değil) |

⚠️ **Dikkat:** "Geleneksel" sanılan bazı şarkılar aslında telifli. Örnek:
*The Wheels on the Bus* 1939'da yazıldı → kullanılmaz.
