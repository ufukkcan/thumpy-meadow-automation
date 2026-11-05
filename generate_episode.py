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
import sing
import vocal_break

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
MUZIK MOLASI: her ders bolumunun sonunda 1 tane (toplam 4). Sarki bilinen bir kamu mali melodiyle
SOYLENIR; sozler OZGUN, o dersle ilgili, neseli, kafiyeli ve tekrarli olmali. Her molanin satir sayisi
ve satir basina HECE sayisi BIREBIR tutmali (hece = soylenen hece: ap-ple = 2, ba-na-na = 3, red = 1,
yel-low = 2, ap-ples = 2):
{patterns}
Sadece 2-6 yas cocuklarin bildigi yaygin Ingilizce kelimeler. Ozel isim, uydurma kelime, kisaltma,
rakam YOK (sayilari yaziyla yaz: "three"). Ses taklitleri sozlukte olanlar olsun (moo, quack, meow, oink).
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
- thumbnail_text: en fazla 14 karakter, BUYUK HARF. Cocugu ve ebeveyni merakla tiklatan kisa bir SORU
  ya da HEYECAN cumlesi olsun (or. "WHAT FRUIT?", "WHAT COLOR?", "COUNT WITH ME!", "WHO SAYS MOO?").
  Videonun icerigiyle BIREBIR uyumlu olmali; videoda olmayan bir seyi vaat etme.
- thumbnail_props: bolumde GERCEKTEN gecen, en renkli ve en kolay taninan 3-4 obje (kutuphaneden,
  birbirinden farkli). Kucuk resimde karakterin yaninda sticker olarak gosterilecek.

SADECE gecerli JSON dondur, baska hicbir sey yazma:
{{
 "title": "...", "description_intro": "...", "learning_points": ["..."],
 "tags": ["..."], "hashtags": ["...","...","..."],
 "thumbnail_text": "...", "thumbnail_props": [{{...}}, {{...}}, {{...}}],
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
    n_breaks = 0
    for sec in ep.get("sections", []):
        segs = []
        for seg in sec.get("segments", []):
            if seg.get("type") == "narration" and str(seg.get("text", "")).strip():
                segs.append({"type": "narration", "text": seg["text"].strip(),
                             "prop": props.validate_prop(seg.get("prop"))})
            elif seg.get("type") == "music_break":
                lines = [" ".join(str(x).split()) for x in seg.get("lines", []) if str(x).strip()]
                if len(lines) >= 2:
                    key = vocal_break.melody_for(n_breaks)
                    n_breaks += 1
                    want = len(vocal_break.pattern(key))
                    lines = (lines * want)[:want]          # eksikse tekrar (nakarat), fazlaysa kirp
                    segs.append({"type": "music_break", "melody": key, "lines": lines})
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
    # kucuk resimde SADECE senaryoda gercekten gecen objeler (yaniltici kucuk resim olmasin)
    script_props = []
    for sc in sections:
        for sg in sc["segments"]:
            if sg["type"] == "narration" and sg["prop"] and sg["prop"] not in script_props:
                script_props.append(sg["prop"])
    wanted = ep.get("thumbnail_props") or ([ep["thumbnail_prop"]] if ep.get("thumbnail_prop") else [])
    thumb_props = []
    for p in wanted:
        vp = props.validate_prop(p)
        if vp and vp in script_props and vp not in thumb_props:
            thumb_props.append(vp)
    if not thumb_props:
        thumb_props = script_props[:3]
    thumb_props = thumb_props[:4]

    return {
        "title": title,
        "description_intro": str(ep.get("description_intro", "")).strip(),
        "learning_points": [str(p).strip() for p in ep.get("learning_points", []) if str(p).strip()][:6],
        "tags": tags,
        "hashtags": hashtags,
        "thumbnail_text": thumb_text,
        "thumbnail_props": thumb_props,
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


FIX_PROMPT = """Bir cocuk sarkisinin sozlerinde hata var. Her satirin HECE sayisi hedefi TAM tutmali ve
tum kelimeler yaygin Ingilizce sozlukte bulunmali. Anlami, kafiyeyi ve cocuk guvenligi kurallarini koru,
sadece gerekeni duzelt.

{items}

SADECE gecerli JSON dondur (TUM molalar, sirasiyla, her biri hedef satir sayisinda):
{{"music_breaks": [["satir", "..."], ["..."]]}}"""


def _patterns_text() -> str:
    return "\n".join(f"- {k + 1}. mola ({vocal_break.NAMES[vocal_break.melody_for(k)]}): "
                     f"{len(vocal_break.pattern(vocal_break.melody_for(k)))} satir; satir basina hece: "
                     + ", ".join(map(str, vocal_break.pattern(vocal_break.melody_for(k)))) for k in range(4))


def _breaks(ep: dict) -> list[dict]:
    return [sg for sc in ep["sections"] for sg in sc["segments"] if sg["type"] == "music_break"]


def song_issues(ep: dict) -> list[str]:
    """Sozlukte olmayan kelimeler ve hece sayisi tutmayan satirlar."""
    out = []
    for k, br in enumerate(_breaks(ep)):
        pat = vocal_break.pattern(br["melody"])
        for li, line in enumerate(br["lines"]):
            missing = [w for w in line.split() if re.search(r"[A-Za-z]", w) and sing.syllable_count(w) is None]
            got = sum(vocal_break.counter(w) for w in line.split() if re.search(r"[A-Za-z]", w))
            if missing or got != pat[li]:
                note = f"hece {got}, hedef {pat[li]}" + (f"; sozlukte yok: {', '.join(missing)}" if missing else "")
                out.append(f"{k + 1}. mola, {li + 1}. satir: \"{line}\" ({note})")
    return out


def _fix_songs(ep: dict, issues: list[str]) -> None:
    items = []
    for k, br in enumerate(_breaks(ep)):
        items.append(f"{k + 1}. mola, melodi {vocal_break.NAMES[br['melody']]}, satir basina hece: "
                     + ", ".join(map(str, vocal_break.pattern(br["melody"]))))
        items += [f"   {li + 1}) {line}" for li, line in enumerate(br["lines"])]
    items.append("\nHATALAR:\n" + "\n".join(f"- {x}" for x in issues))
    fixed = _ask(FIX_PROMPT.format(items="\n".join(items)), max_tokens=3000).get("music_breaks", [])
    for br, new in zip(_breaks(ep), fixed):
        lines = [" ".join(str(x).split()) for x in new if str(x).strip()]
        if len(lines) >= 2:
            want = len(vocal_break.pattern(br["melody"]))
            br["lines"] = (lines * want)[:want]


def generate_script(idea: dict) -> dict:
    raw = _ask(SCRIPT_PROMPT.format(idea=json.dumps(idea, ensure_ascii=False), library=LIBRARY_TEXT,
                                    safety=SAFETY_RULES, style=STYLE_RULES, patterns=_patterns_text()),
               max_tokens=12000)
    ep = normalize_episode(raw)
    issues = song_issues(ep)
    if issues:                         # bir kez Claude'a duzelttir; kalanlar senaryoda kullaniciya gosterilir
        _fix_songs(ep, issues)
        issues = song_issues(ep)
    ep["song_issues"] = issues
    return ep


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
    if _breaks(ep):   # vokal lisansi kaynak gostermeyi sart kosuyor (docs/kararlar.md K-18)
        parts.append("Songs: original lyrics on public-domain melodies. " + sing.CREDIT)
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
                key = seg.get("melody", "")
                out.append(f"  (muzik molasi -- melodi: {vocal_break.NAMES.get(key, key)}, Hanami soyler)")
                pat = vocal_break.pattern(key) if key else []
                for li, line in enumerate(seg["lines"]):
                    got = sum(vocal_break.counter(w) for w in line.split() if re.search(r"[A-Za-z]", w))
                    mark = f"  [{got}/{pat[li]} hece]" if li < len(pat) and got != pat[li] else ""
                    out.append(f"  ~ {line}{mark}")
        out.append("")
    out.append("ETIKETLER: " + ", ".join(ep["tags"]))
    out.append("HASHTAG: " + " ".join("#" + h for h in ep["hashtags"]))
    out.append("THUMBNAIL YAZISI: " + ep["thumbnail_text"])
    out.append("THUMBNAIL OBJELERI: " + ", ".join(props.prop_label(p)[0] for p in ep["thumbnail_props"]))
    if ep.get("song_issues"):
        out.append("\nSARKI UYARILARI (duzeltilemedi; sarki yine soylenir ama bu satirlarda hece kayabilir):")
        out.extend(f"- {x}" for x in ep["song_issues"])
    return "\n".join(out)
