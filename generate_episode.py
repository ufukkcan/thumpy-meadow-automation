"""
Claude ile Thumpy Meadow bolumu uretir:
  1) generate_ideas(): 3 bolum fikri (kullanici Telegram'dan birini secer)
  2) generate_script(idea): tam senaryo + SEO metaverisi (baslik, aciklama, etiket, hashtag, thumbnail)
Cikti props.ALLOWED'a gore dogrulanir; cizilemeyen objeler atilir.
"""
import json
import os
import re
from pathlib import Path

from anthropic import Anthropic

import props

MODEL = "claude-sonnet-4-6"
STATE_DIR = Path(__file__).resolve().parent / "state"
USED_FILE = STATE_DIR / "topics_used.json"

LIBRARY_TEXT = json.dumps(props.ALLOWED, ensure_ascii=False)

SAFETY_RULES = """COCUK GUVENLIGI KURALLARI (HER SEYDEN ONCELIKLI, ISTISNASIZ):
- Izleyiciler 2-6 yas. Icerik her zaman sakin, nazik, sevecen ve olumlu olmali.
- Korku, tehlike, siddet, kaza, yaralanma, kotu karakter, kotu sakalar, alay, utandirma YOK.
- Cocuklarin taklit edebilecegi riskli davranis YOK: tirmanma, atlama, yuksek yer, ates, su kenari,
  yabanci, ilac, kucuk nesneleri agiza alma, hayvanlara dokunma/kovalama vb.
- Marka, unlu karakter, sarki, film, oyun veya baska bir telifli eserin adi ya da sozu YOK.
- Reklam, satin alma, uygulama, link, "yorum yap" gibi cocugu ticari/sosyal eyleme yonlendirme YOK.
  (Sadece kapanista nazikce "ask a grown-up to subscribe" denebilir.)
- Saglik, beslenme tavsiyesi, din, siyaset, cinsiyet rolleri kalibi, tartismali konu YOK.
- Bilgiler DOGRU olmali: renkler, sayilar, sekiller, meyve renkleri, hayvan sesleri gercekle uyumlu.
  (Ornek: ordek "quack", kedi "meow", domuz "oink", kurbaga "ribbit"; tavsan ve balik belirgin bir ses
  CIKARMAZ -- onlar icin ses uydurma, ne yaptiklarini anlat: tavsan zipar, balik yuzer.)
- Tum sozler ve metinler OZGUN olmali; bilinen hicbir tekerleme/sarkiyi kopyalama ya da yakin taklit etme.
"""

STYLE_RULES = """ANLATIM STILI:
- Anlatici: Dino (sevimli dinozor), cocugun arkadasi gibi konusur. Cok basit Ingilizce, kisa cumleler.
- Tekrar ve etkilesim cok onemli: "Can you say red? Red!", "Let's count together!", "Point to the circle!"
  Cocuga cevap icin kisa bir es birak (cumleyi soruyla bitir, sonraki cumlede cevabi ver).
- Her anlatim segmenti 6-22 kelime. Her segmentte EN FAZLA bir obje (prop) olur.
- Bir obje tanitilirken o segmentin prop'u o obje olmali; sayma yapiliyorsa prop "count" ve n, sayilan
  sayiyla BIREBIR ayni olmali.
"""

IDEAS_PROMPT = """Thumpy Meadow, 2-6 yas cocuklar icin Ingilizce ogretici kanal. Asagidaki CIZIM KUTUPHANESI
disinda gorsel KULLANILAMAZ:
{library}

Daha once kullanilan konular (TEKRAR ETME, farkli acidan ele almak serbest): {used}

YouTube'da ebeveynlerin en cok aradigi okul oncesi konulari dusun (renkler, sayilar, sekiller,
meyveler, hayvan sesleri ve bunlarin karisimlari, or. "meyvelerin renkleri"). Arama hacmi yuksek,
kutuphaneyle cizilebilir 3 FARKLI bolum fikri uret.

SADECE gecerli JSON dondur:
{{"ideas": [{{"working_title": "...", "summary": "1 cumle Turkce ozet", "lessons": ["...", "..."]}}]}}"""

SCRIPT_PROMPT = """Thumpy Meadow icin TAM bir bolum senaryosu yaz.

SECILEN FIKIR: {idea}

CIZIM KUTUPHANESI (prop'lar SADECE bunlardan secilir, alan adlari birebir ayni olmali):
{library}
Prop formati ornekleri: {{"kind":"balloon","color":"red"}}, {{"kind":"count","item":"apple","n":3}},
{{"kind":"shape","shape":"star","color":"yellow"}}, {{"kind":"fruit","fruit":"banana"}},
{{"kind":"animal","animal":"duck"}}. Obje yoksa "prop": null.

{safety}
{style}

YAPI (toplam 10-13 dakika hedef):
- "Hello Friends!" giris bolumu (4-6 anlatim segmenti)
- 4 ders bolumu: her biri 12-16 anlatim segmenti + bolum sonunda 1 muzik molasi
- "Let's Remember!" tekrar bolumu (6-8 segment, ogrenilenleri hizlica tekrar)
- "Bye-Bye!" kapanis bolumu (3-4 segment)
Muzik molasi: 4-6 satir, her satir 4-8 kelime, basit, ritmik, kafiyeli, OZGUN, o dersle ilgili.
Bolum (section) basliklari kisa ve aranabilir olsun (YouTube chapters olarak gorunecek), or. "Red and Blue Balloons".

SEO (amac: arama ve onerilerde one cikmak, ama YANILTICI OLMADAN -- YouTube cocuk iceriginde
yaniltici metaveriyi cezalandirir):
- title: en guclu arama ifadesi EN BASTA (or. "Learn Colors with Balloons"), sonra ikincil ifade,
  sonda " | Thumpy Meadow". En fazla 70 karakter. Abartili/tik tuzagi iddia yok.
- description_intro: 2 cumle; ilk 150 karakter icinde ana anahtar kelimeler dogal sekilde gecsin.
- learning_points: cocugun ogrenecegi 3-5 madde (kisa).
- tags: 12-15 etiket; ebeveynlerin gercekten aradigi ifadeler (or. "colors for toddlers",
  "learn colors", "preschool learning"). Alakasiz populer kelime YOK.
- hashtags: TAM 3 tane, en alakalisi ilk sirada, # isareti OLMADAN, bosluksuz.
- thumbnail_text: en fazla 3 kelime, en fazla 14 karakter, BUYUK HARF (or. "COLORS!").
- thumbnail_prop: kutuphaneden bolumu en iyi temsil eden TEK obje.

SADECE gecerli JSON dondur, baska hicbir sey yazma:
{{
 "title": "...", "description_intro": "...", "learning_points": ["..."],
 "tags": ["..."], "hashtags": ["...","...","..."],
 "thumbnail_text": "...", "thumbnail_prop": {{...}},
 "sections": [
   {{"title": "Hello Friends!", "segments": [
      {{"type": "narration", "text": "...", "prop": null}},
      {{"type": "music_break", "lines": ["...", "..."]}}
   ]}}
 ]
}}"""


# ---------------- yardimcilar ----------------
def _client() -> Anthropic:
    return Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _ask(prompt: str, max_tokens: int) -> dict:
    resp = _client().messages.create(
        model=MODEL, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Claude JSON dondurmedi:\n" + text[:500])
    return json.loads(text[start: end + 1])


def load_used() -> list[str]:
    if USED_FILE.exists():
        return json.loads(USED_FILE.read_text(encoding="utf-8")).get("topics", [])
    return []


def remember_topic(title: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    topics = (load_used() + [title])[-200:]
    USED_FILE.write_text(json.dumps({"topics": topics}, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------- dogrulama ----------------
def _clean_tag(tag: str) -> str:
    return re.sub(r"[^\w ]", "", str(tag)).strip()


def normalize_episode(ep: dict) -> dict:
    """Claude ciktisini dogrular ve guvenli hale getirir."""
    sections = []
    for sec in ep.get("sections", []):
        segs = []
        for seg in sec.get("segments", []):
            if seg.get("type") == "narration" and str(seg.get("text", "")).strip():
                segs.append({"type": "narration", "text": seg["text"].strip(),
                             "prop": props.validate_prop(seg.get("prop"))})
            elif seg.get("type") == "music_break":
                lines = [str(x).strip() for x in seg.get("lines", []) if str(x).strip()]
                lines = [" ".join(l.split()[:9]) for l in lines][:6]
                if len(lines) >= 2:
                    segs.append({"type": "music_break", "lines": lines})
        if segs:
            sections.append({"title": str(sec.get("title", "Learning Time"))[:60], "segments": segs})
    if len(sections) < 3:
        raise ValueError("Senaryo cok kisa ya da bozuk (3'ten az bolum).")

    title = str(ep.get("title", "Learning Time")).strip()
    if "thumpy meadow" not in title.lower():
        title = f"{title} | Thumpy Meadow"
    title = title[:100]

    tags, total = [], 0
    for tg in ep.get("tags", []):
        tg = _clean_tag(tg)
        if tg and total + len(tg) + 2 <= 480:
            tags.append(tg)
            total += len(tg) + 2
    tags = (tags + ["Thumpy Meadow"])[:16]

    hashtags = [re.sub(r"[^\w]", "", str(h)) for h in ep.get("hashtags", [])]
    hashtags = [h for h in hashtags if h][:3]

    thumb_text = str(ep.get("thumbnail_text", "LET'S LEARN!")).upper()[:14]
    thumb_prop = props.validate_prop(ep.get("thumbnail_prop"))
    if thumb_prop is None:
        thumb_prop = next((sg["prop"] for sc in sections for sg in sc["segments"]
                           if sg["type"] == "narration" and sg["prop"]), None)

    return {
        "title": title,
        "description_intro": str(ep.get("description_intro", "")).strip(),
        "learning_points": [str(p).strip() for p in ep.get("learning_points", []) if str(p).strip()][:6],
        "tags": tags,
        "hashtags": hashtags,
        "thumbnail_text": thumb_text,
        "thumbnail_prop": thumb_prop,
        "sections": sections,
    }


# ---------------- disariya acik fonksiyonlar ----------------
def generate_ideas() -> list[dict]:
    used = ", ".join(load_used()[-40:]) or "(yok)"
    data = _ask(IDEAS_PROMPT.format(library=LIBRARY_TEXT, used=used), max_tokens=1500)
    ideas = data.get("ideas", [])[:3]
    if not ideas:
        raise ValueError("Fikir uretilemedi.")
    return ideas


def generate_script(idea: dict) -> dict:
    raw = _ask(SCRIPT_PROMPT.format(idea=json.dumps(idea, ensure_ascii=False), library=LIBRARY_TEXT,
                                    safety=SAFETY_RULES, style=STYLE_RULES), max_tokens=12000)
    return normalize_episode(raw)


def build_description(ep: dict, chapter_list: list[tuple[float, str]]) -> str:
    """SEO'ya uygun aciklama: ust satirlarda anahtar kelimeler, sonra ogrenilenler, zaman damgali
    bolumler (chapters), kanal tanitimi ve en fazla 3 hashtag."""
    parts = [ep["description_intro"]]
    if ep["learning_points"]:
        parts.append("In this video, little ones will:\n" + "\n".join(f"- {p}" for p in ep["learning_points"]))
    if chapter_list:
        lines = [f"{int(t // 60):02d}:{int(t % 60):02d} {title}" for t, title in chapter_list]
        parts.append("Chapters:\n" + "\n".join(lines))
    parts.append(
        "Thumpy Meadow makes gentle, original learning videos for toddlers and preschoolers (ages 2-6): "
        "colors, numbers, shapes, fruits and animals with our friendly little dino. "
        "New episodes regularly - ask a grown-up to subscribe!"
    )
    if ep["hashtags"]:
        parts.append(" ".join(f"#{h}" for h in ep["hashtags"]))
    return "\n\n".join(parts)[:4900]


def script_as_text(ep: dict, est_minutes: float) -> str:
    """Telegram'da okunacak duz metin senaryo."""
    out = [f"BASLIK: {ep['title']}", f"Tahmini sure: ~{est_minutes:.1f} dakika", ""]
    for sec in ep["sections"]:
        out.append(f"=== {sec['title']} ===")
        for seg in sec["segments"]:
            if seg["type"] == "narration":
                tag = f"  [{props.prop_label(seg['prop'])[0]}]" if seg["prop"] else ""
                out.append(f"- {seg['text']}{tag}")
            else:
                out.append("  (muzik molasi)")
                out.extend(f"  ~ {line}" for line in seg["lines"])
        out.append("")
    out.append("ETIKETLER: " + ", ".join(ep["tags"]))
    out.append("HASHTAG: " + " ".join("#" + h for h in ep["hashtags"]))
    out.append("THUMBNAIL YAZISI: " + ep["thumbnail_text"])
    return "\n".join(out)
