"""
Claude ile Thumpy Meadow bolumu uretir (7d: yeni format, show.py motoru):
  1) generate_ideas(): 3 bolum fikri (kullanici Telegram'dan birini secer)
  2) generate_script(idea): tam senaryo (show.py semasi) + SEO metaverisi + 3 kucuk resim yazisi
     + yerellestirilmis baslik/aciklama (es, pt, tr, id)
Cikti katalogla dogrulanir; cizilemeyen / sesi olmayan / uyumsuz secimler duzeltilir.
COCUK GUVENLIGI: senaryo ASLA otomatik onaylanmaz (check_and_produce.py insan onayi bekler).
"""
import json
import os
import re
from pathlib import Path

from anthropic import Anthropic

import animal_sounds
import assets
import sing
import show
import vocal_break

MODEL = "claude-sonnet-4-6"
STATE_DIR = Path(__file__).resolve().parent / "state"
USED_FILE = STATE_DIR / "topics_used.json"
LANGS = {"es": "Spanish", "pt": "Portuguese (Brazil)", "tr": "Turkish", "id": "Indonesian"}
FIND_ANIMALS = sorted(animal_sounds.SOURCES)                         # gercek sesi olanlar
GUESTS = ["bunny", "elephant", "monkey", "lion", "pig", "chick", "cat", "frog", "teddy", "butterfly"]
GAG_HELP = {
    "pop_fall": "KUCUK. Dino parmak ucunda gider; satir1 = bakarken soyledigi (or. 'Hmm? Nobody here.'); "
                "hayvan aniden cikar, Dino yumusakca popo ustu oturur; satir2 = gulerek (or. 'Ha ha! You got me!').",
    "bush_hop": "ORTA (sadece bush). satir1 = Dino seslenir (or. 'Come out, come out!'); cali ziplaya ziplaya "
                "Dino'ya gelir, hayvan cikar; satir2 = sasirip sevinir (or. 'Whoa! Hello, dog!').",
    "wrong_guess": "ORTA. satir1 = Dino merak eder (cloud ise 'Hmm? Up there?' -- Dino 3 kez ziplar, yetisemez); "
                   "satir2 = KOMIK YANLIS TAHMIN, tamamen alakasiz bir hayvan ve sesi (or. 'Is it a lion? Roar!'); "
                   "hayvan 'hayir' der gibi sallanip gercek sesini verir ve cikar (ucan hayvan Dino'nun kafasina "
                   "konar); satir3 = gulerek selam (or. 'Ha ha! Hello, duck!').",
    "peek_zoom": "BUYUK (sadece tree). satir1 = Dino arar (or. 'Hmm? Where are you?'); hayvan agacin iki yanindan "
                 "bakar, firlar, Dino'nun etrafinda kosar, agactan elma Dino'nun basina duser, Dino gulerek oturur; "
                 "satir2 = (or. 'Whoa! Ha ha! Hello, dog!').",
}

LIBRARY_TEXT = json.dumps({
    "bulunacak_hayvanlar (gercek sesleriyle, ses yazimi)": {k: v["says"] for k, v in animal_sounds.SOURCES.items()},
    "ucabilenler (cloud'da saklanabilir)": [k for k, v in animal_sounds.SOURCES.items() if v["fly"]],
    "saklanma_yerleri": list(show.HIDES),
    "sakalar": {k: {"satir_sayisi": v[0], "izinli_yerler": list(v[1])} for k, v in show.GAGS.items()},
    "hareketler (action)": list(show.ACTIONS),
    "hikaye_cerceveleri (frame)": {"birthday": "Dino'nun dogum gunu; finalde pasta, balonlar, tac",
                                   "picnic": "piknik; finalde meyveler yagar, Dino'ya cilek",
                                   "rainbow": "gokkusagi; finalde gokkusagi ve yildiz"},
    "dans_misafirleri (guests)": GUESTS,
}, ensure_ascii=False)

SAFETY_RULES = """COCUK GUVENLIGI KURALLARI (HER SEYDEN ONCELIKLI, ISTISNASIZ):
- Izleyiciler 2-6 yas. Icerik her zaman sakin, nazik, sevecen ve olumlu olmali.
- Korku, tehlike, siddet, kaza, yaralanma, kotu karakter, kotu sakalar, alay, utandirma YOK.
  Sakalar sadece yumusak cizgi film komikligi (yumusakca popo ustu oturmak, kafaya yaprak/elma konmasi,
  komik yanlis tahmin); kimse uzulmez, herkes guler.
- Cocuklarin taklit edebilecegi riskli davranis YOK: tirmanma, yuksekten atlama, ates, su kenari,
  yabanci, ilac, kucuk nesneleri agiza alma, hayvanlara dokunma/kovalama vb.
- Marka, unlu karakter, sarki, film, oyun veya baska bir telifli eserin adi ya da sozu YOK.
- Reklam, satin alma, uygulama, link, "yorum yap" gibi cocugu ticari/sosyal eyleme yonlendirme YOK.
- Saglik, beslenme tavsiyesi, din, siyaset, cinsiyet rolleri kalibi, tartismali konu YOK.
- Bilgiler DOGRU olmali (hayvan sesleri katalogdaki gibi).
- Tum sozler ve metinler OZGUN olmali; bilinen hicbir tekerleme/sarkiyi kopyalama ya da yakin taklit etme.
"""

IDEAS_PROMPT = """Thumpy Meadow: 2-6 yas cocuklar icin Ingilizce ogretici cizgi film kanali. Her bolum ayni oyun
kalibinda: Dino'nun arkadaslari saklanmis; cocuk Dino'yla birlikte gercek hayvan seslerini dinleyip
"Who says moo?" sorusunu cevaplar, 7 hayvani bulur. Bolumleri farkli kilan: hikaye cercevesi, hangi 7 hayvan,
saklanma yerleri, sakalar, hareketler ve sarki sozleri.

KATALOG (sadece bunlar cizilebilir/seslendirilebilir):
{library}

Daha once kullanilan basliklar (TEKRAR ETME): {used}
{must}
3 FARKLI bolum fikri uret. Her fikir: cerceve + 7 hayvan (katalogdaki bulunacak hayvanlardan, farkli) +
calisma basligi + 1 cumle Turkce ozet.

SADECE gecerli JSON dondur:
{{"ideas": [{{"working_title": "...", "summary": "...", "frame": "birthday", "animals": ["cow", "..."]}}]}}"""

SCRIPT_PROMPT = """Thumpy Meadow icin TAM bir bolum senaryosu yaz (yeni format, motor show.py).

SECILEN FIKIR: {idea}

KATALOG (alan degerleri SADECE buradan, birebir ayni yazimla):
{library}

{safety}
ANLATIM: Dino (sevimli dinozor) cocukla dogrudan konusur. Cok basit Ingilizce, her satir 3-10 kelime,
2-6 yas cocuklarin bildigi kelimeler. Ozel isim (Dino haric), rakam YOK.
Her satir Dino'nun AGZINDAN CIKAN konusmadir (birinci tekil sahis: "I", "me"). Sahne tarifi, hareket
anlatimi ya da kendinden ucuncu sahis olarak bahsetme YOK (YANLIS: "Dino jumps, jumps!"; DOGRU: "Up there?").
Hareketleri motor canlandirir.

BOLUM YAPISI (motor kurar, sen satirlari ve secimleri yazarsin):
- Selam ve veda sarkilari sabit (sen yazmazsin).
- hook: 2-3 satir. 1. satir cerceveyi kurar (or. "Today is my birthday!"), sonraki satir arkadaslarin
  saklandigini soyler (or. "But where are my friends?").
- ask: yardim istegi (or. "Can you help me find them?"); ardindan cocuga cevap icin bekleme olur.
- finds: TAM 7 oyun. Her biri: animal (bulunacak hayvanlardan, hepsi farkli), hide (saklanma yeri),
  gag (saka), notice (saklanma yerinin hareketini fark etme, or. "Look! The bush is wiggling!",
  "Look! The tree is shaking!", "Look! The cloud is wiggling!"), gag_lines (sakanin satir sayisi kadar),
  action (hayvanin hareketi) ve action_line (or. "The cow can dance! Can you dance too?").
  Kurallar: cloud'a sadece ucabilenler saklanir; saka izinli yerlerinde kullanilir; 1-3. oyunlarda sakalar
  KUCUK -> ORTA -> BUYUK diye buyusun, 4-7. oyunlarda yine; ayni saka art arda gelmesin; her bolumde en az
  bir bush, bir tree, (ucan hayvan varsa) bir cloud olsun.
  Sakalar: {gags}
  Motor her oyunda sabit sorulari kendisi ekler: "Who says moo?" (bekleme), "It's a cow! The cow says moo!",
  "Can you say cow?" (bekleme), "Cow! Great job!" -- bunlari tekrar yazma.
- breaks: TAM 2 hareket molasi sarkisi (2. ve 4. oyundan sonra). Sozler OZGUN, kafiyeli, tekrarli; cocuga
  hareket yaptirir. Satirlarda su hareket kelimeleri gecsin ki Dino yapsin: {moves}.
  Her sarkinin satir sayisi ve satir basina HECE sayisi BIREBIR tutmali (apple = 2, banana = 3, hop = 1;
  sozlerde tire ile heceleme YAZMA):
{patterns}
  guests: her sarkiya katalogdaki dans misafirlerinden 2 farkli hayvan (sarkida gecen hareketi yapacaklar).
- finale: 3 satir. 1) arkadaslara tesekkur (or. "Thank you for finding my friends!"), 2) odule tepki
  (birthday: "A cake! For me?"; picnic: "Yummy fruit for everyone!"; rainbow: "Wow! A big rainbow!"),
  3) sevgi/kapanis (or. "Thank you, friends! I love you!").
- shout: hayvanlar hep birlikte ortaya ciktiginda anlaticinin cumlesi (or. "Surprise! Happy birthday, Dino!").
- teaser_animal: bu bolumde OLMAYAN bir bulunacak hayvan (sonraki bolumde gelecek; silueti gosterilir);
  teaser_line: "Next time, a new friend comes to play!" gibi.

SEO (amac: arama ve onerilerde one cikmak, ama YANILTICI OLMADAN -- YouTube cocuk iceriginde yaniltici
metaveriyi cezalandirir):
- title: yedek baslik (olcum yapilamazsa kullanilir): arama ifadesi + bolume ozgu kisa ifade + " | Thumpy Meadow".
  En fazla 70 karakter. Abarti/tik tuzagi yok.
- title_phrases: TAM 5 farkli aday arama ifadesi, kucuk harf, 3-6 kelime, bir ebeveynin YouTube'a yazacagi
  gibi ve bolumun icerigiyle BIREBIR uyumlu. Yeni kanaliz: "animal sounds for kids" gibi devlerin oldugu genel
  ifadeler yerine daha ozgul, uzun ifadeler (or. "peekaboo animal sounds for toddlers", "hide and seek
  animals for kids", "guess the animal sound for preschool"). Sistem talebi ve rekabeti olcup birini secer.
- title_rest: bolume ozgu kisa ifade, Title Case, en fazla 30 karakter (or. "Dino's Birthday Surprise").
- description_intro: 2 cumle; ilk 150 karakter icinde ana anahtar kelimeler dogal sekilde gecsin.
- learning_points: cocugun ogrenecegi 3-5 madde (kisa).
- tags: 12-15 etiket; ebeveynlerin gercekten aradigi ifadeler ("animal sounds for kids", "peekaboo",
  "learn animals for toddlers" ...). Alakasiz populer kelime YOK.
- hashtags: TAM 3 tane, # OLMADAN, bosluksuz.
- thumbnail_texts: TAM 3 farkli kucuk resim yazisi, her biri en fazla 14 karakter, BUYUK HARF, 1-3 kelime:
  1) heyecan/oyun (or. "PEEKABOO!"), 2) konu (or. "ANIMAL SOUNDS"), 3) merak sorusu (or. "WHO SAYS MOO?" --
  sorudaki hayvan bolumdeki ILK hayvan olmali). Videoyla birebir uyumlu.
- localizations: {langs} icin baslik (en fazla 90 karakter, sonda " | Thumpy Meadow") ve 2 cumle aciklama.
  Video Ingilizce ogretir: basliklar o dili konusan ebeveynin arayacagi gibi olsun (or. es: "Sonidos de
  Animales en Ingles para Ninos | Thumpy Meadow").

SADECE gecerli JSON dondur, baska hicbir sey yazma:
{{
 "title": "...", "title_phrases": ["...", "...", "...", "...", "..."], "title_rest": "...",
 "description_intro": "...", "learning_points": ["..."], "tags": ["..."],
 "hashtags": ["...", "...", "..."], "thumbnail_texts": ["...", "...", "..."],
 "localizations": {{"es": {{"title": "...", "description": "..."}}}},
 "frame": "birthday", "hook": ["...", "..."], "ask": "...",
 "finds": [{{"animal": "cow", "hide": "bush", "gag": "pop_fall", "notice": "...", "gag_lines": ["...", "..."],
            "action": "dance", "action_line": "..."}}],
 "breaks": [{{"lines": ["...", "..."], "guests": ["bunny", "elephant"]}}],
 "finale": ["...", "...", "..."], "shout": "...", "teaser_animal": "...", "teaser_line": "..."
}}"""


# ---------------- yardimcilar ----------------
def _client() -> Anthropic:
    return Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _ask(prompt: str, max_tokens: int) -> dict:
    resp = _client().messages.create(model=MODEL, max_tokens=max_tokens,
                                     messages=[{"role": "user", "content": prompt}])
    text = "".join(b.text for b in resp.content if b.type == "text")
    start = text.find("{")
    if start == -1:
        raise ValueError("Claude JSON dondurmedi:\n" + text[:500])
    # ilk TAM JSON nesnesi; arkasina eklenen aciklama/ikinci nesne yok sayilir (lessons E17)
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    return obj


def _load_state() -> dict:
    return json.loads(USED_FILE.read_text(encoding="utf-8")) if USED_FILE.exists() else {}


def load_used() -> list[str]:
    return _load_state().get("topics", [])


def remember_topic(title: str, next_friend: str | None = None) -> None:
    """Kullanilan baslik + bir sonraki bolumde mutlaka gelecek hayvan (siluet sozu)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    st = _load_state()
    st["topics"] = (st.get("topics", []) + [title])[-200:]
    if next_friend:
        st["next_friend"] = next_friend
    USED_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def _line(x, default: str, max_words: int = 14) -> str:
    """Tek satir, duz ASCII, cok uzunsa kirp; bossa varsayilan."""
    s = " ".join(str(x or "").replace("’", "'").split())
    s = re.sub(r"[^A-Za-z0-9 ,.!?'\-]", "", s).strip()
    words = s.split()
    if not words:
        return default
    s = " ".join(words[:max_words])
    return s if s[-1] in ".!?" else s + "!"


def _clean_tag(tag: str) -> str:
    return re.sub(r"[^\w ]", "", str(tag)).strip()


GAG_DEFAULTS = {
    "pop_fall": ["Hmm? Nobody here.", "Ha ha! You got me!"],
    "bush_hop": ["Come out, come out!", "Whoa! Hello, friend!"],
    "wrong_guess": ["Hmm? Who is in there?", "Is it a lion? Roar!", "Ha ha! Hello, friend!"],
    "peek_zoom": ["Hmm? Where are you?", "Whoa! Ha ha! Hello, friend!"],
}
NOTICE_DEFAULTS = {"bush": "Look! The bush is wiggling!", "tree": "Look! The tree is shaking!",
                   "cloud": "Look! The cloud is wiggling!"}
GAG_FOR_HIDE = {"bush": ["pop_fall", "bush_hop", "wrong_guess"], "tree": ["peek_zoom", "pop_fall", "wrong_guess"],
                "cloud": ["wrong_guess"]}


def _fix_find(f: dict, used_animals: set) -> dict:
    animal = str(f.get("animal", "")).lower().strip()
    if animal not in animal_sounds.SOURCES or animal in used_animals:
        animal = next(a for a in FIND_ANIMALS if a not in used_animals)
    meta = animal_sounds.SOURCES[animal]
    hide = str(f.get("hide", "bush")).lower()
    if hide not in show.HIDES or (hide == "cloud" and not meta["fly"]):
        hide = "bush"
    gag = str(f.get("gag", "")).lower()
    if gag not in show.GAGS or hide not in show.GAGS[gag][1]:
        gag = GAG_FOR_HIDE[hide][0]
    n = show.GAGS[gag][0]
    lines = [_line(x, GAG_DEFAULTS[gag][k]) for k, x in enumerate((list(f.get("gag_lines") or []) + [""] * n)[:n])]
    action = str(f.get("action", "hop")).lower()
    if action not in show.ACTIONS:
        action = "hop"
    return {"animal": animal, "hide": hide, "gag": gag,
            "notice": _line(f.get("notice"), NOTICE_DEFAULTS[hide]), "gag_lines": lines, "action": action,
            "action_line": _line(f.get("action_line"), f"The {animal} can {action}! Can you {action} too?")}


def normalize_episode(ep: dict) -> dict:
    """Claude ciktisini katalogla dogrular ve guvenli hale getirir."""
    finds, used = [], set()
    for f in (ep.get("finds") or [])[:show.N_FINDS]:
        ff = _fix_find(f, used)
        used.add(ff["animal"])
        finds.append(ff)
    while len(finds) < show.N_FINDS:
        ff = _fix_find({}, used)
        used.add(ff["animal"])
        finds.append(ff)
    # her yarida sakalar kucukten buyuge (uc kurali); esitlerde Claude'un sirasi korunur
    half = show.N_FINDS // 2
    finds = (sorted(finds[:half], key=lambda f: show.GAGS[f["gag"]][2])
             + sorted(finds[half:], key=lambda f: show.GAGS[f["gag"]][2]))

    breaks, brs = [], ep.get("breaks") or []
    for k, melody in enumerate(show.BREAK_MELODIES):
        br = brs[k] if k < len(brs) and isinstance(brs[k], dict) else {}
        want = len(vocal_break.pattern(melody))
        lines = [" ".join(str(x).split()) for x in br.get("lines", []) if str(x).strip()] or ["Hop, hop, hop!"]
        lines = (lines * want)[:want]
        guests = [g for g in br.get("guests", []) if g in GUESTS and g in assets.NAMES][:2]
        guests = (guests + [g for g in ("bunny", "elephant", "monkey", "frog") if g not in guests])[:2]
        breaks.append({"melody": melody, "lines": lines, "guests": guests})

    frame = ep.get("frame") if ep.get("frame") in show.FRAMES else "birthday"
    hook = [_line(x, "") for x in (ep.get("hook") or [])][:3]
    hook = [h for h in hook if h] or ["Today is a happy day!", "But where are my friends?"]
    finale_def = ["Thank you for finding my friends!", "Wow! For me?", "Thank you, friends! I love you!"]
    finale = [_line(x, finale_def[k]) for k, x in enumerate((list(ep.get("finale") or []) + [""] * 3)[:3])]
    teaser = str(ep.get("teaser_animal", "")).lower()
    if teaser not in animal_sounds.SOURCES or teaser in used:
        teaser = next(a for a in FIND_ANIMALS if a not in used)

    title = str(ep.get("title", "Animal Sounds for Kids")).strip()
    if "thumpy meadow" not in title.lower():
        title = f"{title} | Thumpy Meadow"
    phrases = []
    for p in ep.get("title_phrases") or []:
        p = " ".join(re.sub(r"[^a-z0-9' ]", " ", str(p).lower()).split())
        if 2 <= len(p.split()) <= 7 and p not in phrases:
            phrases.append(p)
    title_rest = " ".join(re.sub(r"[^A-Za-z0-9 ,!?'&-]", "", str(ep.get("title_rest", ""))).split())[:40]
    tags, total = [], 0
    for tg_ in ep.get("tags", []):
        tg_ = _clean_tag(tg_)
        if tg_ and total + len(tg_) + 2 <= 480:
            tags.append(tg_)
            total += len(tg_) + 2
    tags = (tags + ["Thumpy Meadow"])[:16]
    hashtags = [h for h in (re.sub(r"[^\w]", "", str(h)) for h in ep.get("hashtags", [])) if h][:3]
    # kanal adi hashtag'i her zaman dogru yazimla (Claude bir kez "ThumypMeadow" yazdi)
    hashtags = ["ThumpyMeadow" if h.lower().startswith("thum") else h for h in hashtags]
    first = finds[0]
    thumbs_def = ["PEEKABOO!", "ANIMAL SOUNDS", f"WHO SAYS {animal_sounds.SOURCES[first['animal']]['says'].upper()}?"]
    texts = [str(x).upper().strip()[:16] for x in (ep.get("thumbnail_texts") or [])][:3]
    texts = [t or thumbs_def[k] for k, t in enumerate((texts + ["", "", ""])[:3])]
    locs = {}
    for lang in LANGS:
        loc = (ep.get("localizations") or {}).get(lang) or {}
        lt = " ".join(str(loc.get("title", "")).split())
        if lt:
            if "thumpy meadow" not in lt.lower():
                lt = f"{lt} | Thumpy Meadow"
            locs[lang] = {"title": lt[:100], "description": " ".join(str(loc.get("description", "")).split())[:1500]}

    return {
        "title": title[:100], "title_phrases": phrases[:5], "title_rest": title_rest,
        "description_intro": str(ep.get("description_intro", "")).strip(),
        "learning_points": [str(p).strip() for p in ep.get("learning_points", []) if str(p).strip()][:6],
        "tags": tags, "hashtags": hashtags, "thumbnail_texts": texts, "localizations": locs,
        "frame": frame, "hook": hook, "ask": _line(ep.get("ask"), "Can you help me find them?"),
        "finds": finds, "breaks": breaks, "finale": finale,
        "shout": _line(ep.get("shout"), "Surprise!"), "teaser_animal": teaser,
        "teaser_line": _line(ep.get("teaser_line"), "Next time, a new friend comes to play!"),
    }


# ---------------- sarki kontrolu ----------------
FIX_PROMPT = """Bir cocuk sarkisinin sozlerinde hata var. Her satirin HECE sayisi hedefi TAM tutmali ve
tum kelimeler yaygin Ingilizce sozlukte bulunmali. Anlami, kafiyeyi, hareket kelimelerini ve cocuk guvenligi
kurallarini koru, sadece gerekeni duzelt. Kelimeleri tireyle heceleme ("a-round" YANLIS, "around" DOGRU).
Hatalarda her kelimenin sayilan hecesi parantez icinde verildi; hece eklemek/cikarmak icin kisa kelime
ekle/cikar (or. "now", "so", "and", "up") ya da 1 heceli kelimeyi 2 heceliyle degistir.

{items}

SADECE gecerli JSON dondur (TUM sarkilar, sirasiyla, her biri hedef satir sayisinda):
{{"music_breaks": [[<1. sarkinin satirlari, metin olarak>], [<2. sarkinin satirlari>]]}}"""


def _patterns_text() -> str:
    return "\n".join(f"  - {k + 1}. sarki ({vocal_break.NAMES[m]}): {len(vocal_break.pattern(m))} satir; "
                     f"satir basina hece: " + ", ".join(map(str, vocal_break.pattern(m)))
                     for k, m in enumerate(show.BREAK_MELODIES))


def song_issues(ep: dict) -> list[str]:
    out = []
    for k, br in enumerate(ep["breaks"]):
        pat = vocal_break.pattern(br["melody"])
        for li, line in enumerate(br["lines"]):
            missing = [w for w in line.split() if re.search(r"[A-Za-z]", w) and sing.syllable_count(w) is None]
            got = sum(vocal_break.counter(w) for w in line.split() if re.search(r"[A-Za-z]", w))
            if missing or got != pat[li]:
                # kelime kelime sayim: Claude hece saymakta zorlaniyor; neyin kac sayildigini gorsun
                per = " + ".join(f"{w.strip('.,!?')}({vocal_break.counter(w)})" for w in line.split()
                                 if re.search(r"[A-Za-z]", w))
                note = f"hece {got} = {per}; hedef {pat[li]}" + (f"; sozlukte yok: {', '.join(missing)}" if missing else "")
                out.append(f"{k + 1}. sarki, {li + 1}. satir: \"{line}\" ({note})")
    return out


def _fix_songs(ep: dict, issues: list[str]) -> None:
    items = []
    for k, br in enumerate(ep["breaks"]):
        items.append(f"{k + 1}. sarki, melodi {vocal_break.NAMES[br['melody']]}, satir basina hece: "
                     + ", ".join(map(str, vocal_break.pattern(br["melody"]))))
        items += [f"   {li + 1}) {line}" for li, line in enumerate(br["lines"])]
    items.append("\nHATALAR:\n" + "\n".join(f"- {x}" for x in issues))
    fixed = _ask(FIX_PROMPT.format(items="\n".join(items)), max_tokens=3000).get("music_breaks", [])
    for k, (br, new) in enumerate(zip(ep["breaks"], fixed)):
        lines = [" ".join(str(x).split()) for x in new if str(x).strip()]
        want = len(vocal_break.pattern(br["melody"]))
        if len(lines) != want or _missing_words(lines):
            continue                 # eksik satir ya da sozlukte olmayan kelime (or. ornekteki "satir"): reddet
        old = len(song_issues({"breaks": [br]}))
        cand = {**br, "lines": lines}
        if len(song_issues({"breaks": [cand]})) <= old:
            br["lines"] = lines      # yalnizca iyilestiriyorsa kabul (lessons E19)


def _missing_words(lines: list[str]) -> list[str]:
    return [w for line in lines for w in line.split()
            if re.search(r"[A-Za-z]", w) and sing.syllable_count(w) is None]


def _drop_unknown_words(ep: dict) -> None:
    """Sozlukte olmayan kelime render'i durdurur (KeyError): onaydan ONCE cikarilir, uyari metinde kalir."""
    for br in ep["breaks"]:
        new = []
        for line in br["lines"]:
            kept = " ".join(w for w in line.split()
                            if not (re.search(r"[A-Za-z]", w) and sing.syllable_count(w) is None))
            new.append(kept if re.search(r"[A-Za-z]", kept) else "Hop, hop, hop!")
        br["lines"] = new


# ---------------- disariya acik fonksiyonlar ----------------
def generate_ideas() -> list[dict]:
    if os.environ.get("EPISODE_FORMAT", "story") == "story":     # H7: varsayilan hikaye-sarki
        return generate_story_ideas()
    used = ", ".join(load_used()[-40:]) or "(yok)"
    nf = _load_state().get("next_friend")
    must = (f"ONCEKI BOLUMUN SONUNDA SOZ VERILDI: her fikirde '{nf}' mutlaka 7 hayvandan biri olsun.\n"
            if nf in animal_sounds.SOURCES else "")
    data = _ask(IDEAS_PROMPT.format(library=LIBRARY_TEXT, used=used, must=must), max_tokens=2000)
    ideas = data.get("ideas", [])[:3]
    if not ideas:
        raise ValueError("Fikir uretilemedi.")
    return ideas


def generate_script(idea: dict) -> dict:
    if idea.get("format") == "story" or idea.get("stories"):
        return generate_story_script(idea)
    gags = " | ".join(f"{k}: {v}" for k, v in GAG_HELP.items())
    raw = _ask(SCRIPT_PROMPT.format(idea=json.dumps(idea, ensure_ascii=False), library=LIBRARY_TEXT,
                                    safety=SAFETY_RULES, gags=gags, moves=", ".join(show.SONG_MOVES),
                                    patterns=_patterns_text(), langs=", ".join(LANGS.values())),
               max_tokens=12000)
    ep = normalize_episode(raw)
    issues = song_issues(ep)
    for _ in range(2):                 # en fazla 2 tur Claude'a duzelttir; kalanlar senaryoda kullaniciya gosterilir
        if not issues:
            break
        try:
            _fix_songs(ep, issues)
        except Exception as exc:       # duzeltme turu bolumu durdurmaz; kalan sorunlar onay metninde gorunur
            print(f"Sarki duzeltme turu basarisiz: {exc}", flush=True)
            break
        issues = song_issues(ep)
    _drop_unknown_words(ep)
    ep["song_issues"] = song_issues(ep)
    return ep


def _chapters_text(chapter_list) -> str:
    return "\n".join(f"{int(t // 60):02d}:{int(t % 60):02d} {title}" for t, title in chapter_list)


def build_description(ep: dict, chapter_list: list[tuple[float, str]]) -> str:
    """SEO: ust satirlarda anahtar kelimeler, ogrenilenler, zaman damgali bolumler, kanal tanitimi,
    kaynaklar (sarki sesi lisansi kaynak ister), hashtag."""
    if ep.get("stories"):
        return story_description(ep, chapter_list)
    animals = ", ".join(f["animal"] for f in ep["finds"])
    parts = [ep["description_intro"]]
    if ep["learning_points"]:
        parts.append("In this video, little ones will:\n" + "\n".join(f"- {p}" for p in ep["learning_points"]))
    parts.append(f"Animals in this episode: {animals}.")
    if chapter_list:
        parts.append("Chapters:\n" + _chapters_text(chapter_list))
    parts.append(
        "Thumpy Meadow makes gentle, original cartoon learning videos for toddlers and preschoolers (ages 2-6). "
        "Play peekaboo with Dino, listen to real animal sounds, sing, dance and learn English words. "
        "New episodes regularly - ask a grown-up to subscribe!")
    parts.append("Songs: original lyrics on public-domain melodies. " + sing.CREDIT +
                 ". Real animal sounds: BigSoundBank (CC0).")
    if ep["hashtags"]:
        parts.append(" ".join(f"#{h}" for h in ep["hashtags"]))
    return "\n\n".join(parts)[:4900]


def build_localizations(ep: dict, chapter_list) -> dict:
    """YouTube 'localizations': o dildeki izleyiciye baslik + aciklama (bolumler ve hashtag'ler korunur)."""
    out = {}
    for lang, loc in ep.get("localizations", {}).items():
        desc = loc["description"]
        if chapter_list:
            desc += "\n\n" + _chapters_text(chapter_list)
        if ep["hashtags"]:
            desc += "\n\n" + " ".join(f"#{h}" for h in ep["hashtags"])
        out[lang] = {"title": loc["title"], "description": desc[:4900]}
    return out


def short_meta(ep: dict, find_index: int, full_video_id: str | None) -> dict:
    """Short icin baslik / aciklama / etiket: oyunun sorusu one cikar, tam bolume yonlendirir."""
    if ep.get("stories"):
        return story_short_meta(ep, find_index, full_video_id)
    f = ep["finds"][find_index]
    animal, says = f["animal"], animal_sounds.SOURCES[f["animal"]]["says"]
    title = f"Who Says {says.capitalize()}? Peekaboo {animal.capitalize()} Sound for Kids | Thumpy Meadow"
    desc = [f"Who says {says}? Listen, guess and play peekaboo with Dino! A real {animal} sound for "
            f"toddlers and preschoolers."]
    if full_video_id:
        desc.append(f"Find all the animal friends in the full episode: https://youtu.be/{full_video_id}")
    desc.append(" ".join(f"#{h}" for h in (["shorts"] + ep["hashtags"])[:4]))
    tags = ([f"{animal} sound for kids", f"who says {says}", "peekaboo animals", "animal sounds for kids"]
            + ep["tags"])[:15]
    return {"title": title[:100], "description": "\n\n".join(desc), "tags": tags}


def story_as_text(ep: dict, est_minutes: float) -> str:
    """Hikaye-sarki bolumu (H3) icin Telegram onay metni: her hikaye, konusmalar, kitalar (hece kontrolu)."""
    out = [f"BASLIK: {ep['title']}"]
    if ep.get("title_report"):
        out += ["BASLIK OLCUMU:"] + ep["title_report"]
    out += [f"Tahmini sure: ~{est_minutes:.1f} dakika", f"Hikaye sayisi: {len(ep['stories'])}", ""]
    for k, st in enumerate(ep["stories"]):
        mel = vocal_break.NAMES.get(st["melody"], st["melody"])
        out.append(f"=== Hikaye {k + 1}: {st['name']} -- yer: {st['place']}"
                   + (f", hava: {st['weather']}" if st.get("weather") else "")
                   + f", melodi: {mel}, kadro: Dino + {', '.join(st['cast'])} ===")
        if st.get("props"):
            out.append(f"  [sahnede: {', '.join(st['props'])}]")
        for b in st.get("hook", []):
            out.append(f"- {b['who']}: {b['say']}" if b.get("say") else f"- {b['who']}: [gercek ses]")
        pat = vocal_break.pattern(st["melody"])
        for vi, v in enumerate(st["verses"]):
            for b in v.get("talk", []):
                out.append(f"- {b['who']}: {b['say']}" if b.get("say") else f"- {b['who']}: [gercek ses]")
            extra = (f", gorunur: {v['show']}" if v.get("show") else "")
            out.append(f"  ~ Kita {vi + 1} (odak: {v.get('focus', '-')}, hareket: {v.get('do', 'dance')}{extra})")
            for li, line in enumerate(v["lines"]):
                got = sum(vocal_break.counter(w) for w in line.split() if re.search(r"[A-Za-z]", w))
                mark = f"  [{got}/{pat[li]} hece]" if li < len(pat) and got != pat[li] else ""
                out.append(f"    {line}{mark}")
        end = st.get("ending") or {}
        if end:
            out.append(f"- {end.get('who', 'dino')}: {end.get('say', '')}  [hep birlikte: {end.get('do', 'hug')}]")
        if st.get("next"):
            out.append(f"- dino: {st['next']}  (siradaki hikayenin ipucu)")
        out.append("")
    out.append(f"- dino: {ep.get('goodbye', 'Bye bye, friends! See you next time!')}")
    out += ["", "ETIKETLER: " + ", ".join(ep.get("tags", [])),
            "HASHTAG: " + " ".join("#" + h for h in ep.get("hashtags", []))]
    if ep.get("localizations"):
        out.append("DIL BASLIKLARI: " + " | ".join(f"{k}: {v['title']}" for k, v in ep["localizations"].items()))
    if ep.get("song_issues"):
        out.append("\nSARKI UYARILARI (duzeltilemedi; sarki yine soylenir ama bu satirlarda hece kayabilir):")
        out.extend(f"- {x}" for x in ep["song_issues"])
    return "\n".join(out)


def script_as_text(ep: dict, est_minutes: float) -> str:
    """Telegram'da okunacak duz metin senaryo."""
    if ep.get("stories"):
        return story_as_text(ep, est_minutes)
    out = [f"BASLIK: {ep['title']}"]
    if ep.get("title_report"):
        out += ["BASLIK OLCUMU (otomatik tamamlama talebi + ilk 10 sonucun gucu):"] + ep["title_report"]
    out += [f"Tahmini sure: ~{est_minutes:.1f} dakika",
            f"Cerceve: {ep['frame']}", "",
           "=== Selam sarkisi (sabit: Hello Dino, hello Dino...) ===", "",
           "=== Giris ===", "- Hi friends! I'm Dino!"] + [f"- {h}" for h in ep["hook"]] + \
          [f"- {ep['ask']}  (bekleme)", "- Yay! Let's go!", ""]
    for i, f in enumerate(ep["finds"]):
        says = animal_sounds.SOURCES[f["animal"]]["says"]
        out.append(f"=== Oyun {i + 1}: {f['animal']} ({says}) -- yer: {f['hide']}, saka: {f['gag']} ===")
        out += [f"- {f['notice']}", "- Shh... listen!", f"  [gercek ses: {says} x2]",
                f"- Who says {says}?  (bekleme)"]
        out += [f"- {x}" for x in f["gag_lines"]]
        out += [f"- It's {show.article(f['animal'])} {f['animal']}! The {f['animal']} says {says}!",
                f"- Can you say {f['animal']}?  (bekleme)", f"- {f['animal'].capitalize()}! Great job!",
                f"- {f['action_line']}  [hareket: {f['action']}]", ""]
        if i in show.BREAK_AFTER:
            br = ep["breaks"][show.BREAK_AFTER[i]]
            out.append(f"=== Hareket molasi -- melodi: {vocal_break.NAMES[br['melody']]}, "
                       f"misafirler: {', '.join(br['guests'])} ===")
            pat = vocal_break.pattern(br["melody"])
            for li, line in enumerate(br["lines"]):
                got = sum(vocal_break.counter(w) for w in line.split() if re.search(r"[A-Za-z]", w))
                mark = f"  [{got}/{pat[li]} hece]" if got != pat[li] else ""
                out.append(f"  ~ {line}{mark}")
            out.append("")
    out += ["=== Tekrar === (her hayvan: 'The cow says...' bekleme, gercek ses)", "",
            "=== Final ===", f"- {ep['finale'][0]}", f"  [anlatici] {ep['shout']}",
            f"- {ep['finale'][1]}", f"- {ep['finale'][2]}", "",
            f"=== Sonraki bolum ipucu: {ep['teaser_animal']} silueti ===", f"- {ep['teaser_line']}",
            "- Who is it?  (bekleme)", "", "=== Veda sarkisi (sabit) ===", "",
            "ETIKETLER: " + ", ".join(ep["tags"]),
            "HASHTAG: " + " ".join("#" + h for h in ep["hashtags"]),
            "KUCUK RESIM YAZILARI: " + " / ".join(ep["thumbnail_texts"]),
            "DIL BASLIKLARI: " + " | ".join(f"{k}: {v['title']}" for k, v in ep["localizations"].items())]
    if ep.get("song_issues"):
        out.append("\nSARKI UYARILARI (duzeltilemedi; sarki yine soylenir ama bu satirlarda hece kayabilir):")
        out.extend(f"- {x}" for x in ep["song_issues"])
    return "\n".join(out)


# =====================================================================================================
# H7 (2026-11-20, todo 7h; K-24/K-25): HIKAYE-SARKI BOLUMU. Arastirma: sarkiyla anlatilan hikayeler
# konusmali hikayelerden kat kat cok izleniyor (67k vs 6k/gun medyan); kucuk kanal hitleri ayni kadroyla
# arka arkaya 2-3 dk'lik hikaye-sarkilar; sorun ilk 10 sn'de; sonu kurtarma + sarilma; baslikta "Song" ve "!".
# =====================================================================================================
import math
from datetime import date

import critters
import kidsong
import songs
import story as story_engine

N_STORIES = 4
PERSONALITY = {"cow": "sicak, anne gibi, sakin; gercek sesi moo", "bunny": "utangac, nazik, kolay usur",
               "puppy": "enerjik, cesur, kosmayi sever; gercek sesi woof", "kitten": "kendine guvenen, oyuncu, "
               "bazen paylasmak istemez; gercek sesi meow", "piglet": "komik, camuru ve yemegi sever",
               "lamb": "yardimsever, kayip seyleri bulur; gercek sesi baa", "duck": "sakaci, yagmuru ve suyu sever; "
               "gercek sesi quack", "chick": "en kucuk, merakli, bazen korkar; gercek sesi peep"}


def _xmas_season(d: date | None = None) -> bool:
    d = d or date.today()
    return (d.month == 11 and d.day >= 15) or d.month == 12 or (d.month == 1 and d.day <= 6)


def _story_melodies() -> list[str]:
    return [m for m in songs.STORY_MELODIES if m != "jingle" or _xmas_season()]


def _verse_sec(m: str) -> float:
    return kidsong.timing(m, len(vocal_break.pattern(m)))[2]


def _verse_range(m: str) -> tuple[int, int]:
    """Bir hikayenin sarkisi ~100-150 sn olsun (arastirma: hikaye basi 2-3 dk)."""
    lo = max(3, math.ceil(90 / _verse_sec(m)))
    return lo, max(lo + 1, min(7, math.floor(170 / _verse_sec(m))))


def _story_library() -> str:
    mel = {}
    for m in _story_melodies():
        lo, hi = _verse_range(m)
        pat = vocal_break.pattern(m)
        note = ""
        if m == "oldmac":
            note = ("2., 4. ve 8. satirlar AYNEN 'E I E I O' (harfler ayri). 5. ve 6. satir ses/eylem tekrari "
                    "(or. 'With a moo moo here and a moo moo there,' / 'Here a moo, there a moo, everywhere a moo moo,')")
        if m == "jingle":
            note = "Noel donemi. 1. ve 5. satir 'Jingle bells, jingle bells,' olabilir (1857, kamu mali)."
        mel[m] = {"ad": vocal_break.NAMES[m], "satir": len(pat), "satir_basina_hece": pat,
                  "kita_suresi_sn": round(_verse_sec(m)), "kita_sayisi": f"{lo}-{hi}", "not": note}
    return json.dumps({
        "karakterler (Dino her hikayede var; digerleri)": PERSONALITY,
        "mekanlar (place)": {"meadow": "cicekli cayir", "farm": "ahir, silo, cit", "pond": "gol, nilufer",
                             "snow": "karli tepe, cam agaclari, kulube", "forest": "orman, mantarlar",
                             "home": "ev ici oturma odasi (pencere, hali)", "night": "gece cayiri, ay, yildizlar"},
        "hava (weather)": ["rain", "snow", None],
        "eylemler (do)": [a for a in story_engine.ACTIONS if a != "none"],
        "duygular (feel)": list(story_engine.FEELS),
        "objeler (props / show)": assets.STORY_PROPS,
        "melodiler (melody)": mel,
    }, ensure_ascii=False)


STORY_SAFETY = SAFETY_RULES + """- Hikayelerde YUMUSAK sorun SERBEST ve gerekli: yagmur geliyor, usudu, ulasamiyor, paylasmak istemiyor,
  atkisi ucmus, karanlikta biraz korkuyor. Tehlike, yaralanma, kotu karakter, gercek korku YOK; sorun hep
  arkadaslik ve yardimlasmayla cozulur, sonunda herkes mutlu.
- Melodiler verilenlerdir (kamu mali). Sozler OZGUN; yalniz 'E I E I O' ve 'Jingle bells' nakarat kelimeleri
  geleneksel/kamu malidir, kullanilabilir. Baska bilinen sarkinin sozlerini kopyalama.
"""

STORY_IDEAS_PROMPT = """Thumpy Meadow: 2-6 yas cocuklar icin Ingilizce cizgi film kanali (maskot: yesil dinozor Dino).
BICIM: her video = AYNI KADROYLA arka arkaya {n} HIKAYE-SARKI (her biri ~2-2,5 dk). Hikayenin kendisi sarkidir:
1-2 konusma satiriyla sorun ILK 10 SANIYEDE gorunur, sarki kitalari olayi anlatir, sonunda kurtarma/cozum +
sarilma/kutlama. Her hikayede yeni mekan ve yeni sorun.

OLCUM (YouTube, son 12 ay): guclu temalar: hava (yagmur, firtina, kar), paylasma, kurtarma/yardim, dinozor,
rutinler (dis fircalama, banyo, toparlanma, giyinme). ZAYIF (kullanma): masal/ahlak dersi, uyku vakti, kayip
esya / anneni bul.
{season}
KATALOG: {library}

Daha once kullanilan bolum basliklari (TEKRAR ETME): {used}
Daha once kullanilan hikaye adlari (TEKRAR ETME): {used_stories}

3 FARKLI bolum fikri uret (her biri farkli tema karisimi). Her fikir: working_title (Ingilizce, '<Olay>! <Konu> Song'
kalibi, or. 'Rainy Day Rescue! Farm Animals Song'), summary (1 cumle Turkce), stories ({n} kisa hikaye adi +
parantez icinde mekan ve sorun, Turkce), cast (Dino disinda katalogdan 3-4 hayvan).

SADECE gecerli JSON dondur:
{{"ideas": [{{"working_title": "...", "summary": "...", "stories": ["...", "..."], "cast": ["cow", "..."]}}]}}"""

STORY_SCRIPT_PROMPT = """Thumpy Meadow icin TAM bir HIKAYE-SARKI bolumu yaz (motor story.py).

SECILEN FIKIR: {idea}

KATALOG (alan degerleri SADECE buradan, birebir ayni yazimla):
{library}

{safety}
YAPI: TAM {n} hikaye, ayni kadro (Dino + fikirdeki hayvanlar). Her hikaye:
- name: hikaye adi, Ingilizce Title Case, '!' ile, en fazla 28 karakter (or. "Rainy Day Rescue!").
- song_title: o hikayenin sarki adi, en fazla 26 karakter, "Song" ile biter (or. "Farm Animals Song").
- place, weather (rain/snow/null), clears (hava sonunda duruyorsa true; yagmur durunca gokkusagi cikar),
  melody: katalogdan; HER HIKAYE FARKLI MELODI. cast: Dino HARIC 2-3 hayvan (bolum kadrosundan).
  props: 0-2 sahne objesi (katalog objeleri).
- hook: 1-2 konusma: ILK satir sorunu gosterir (or. cow: "Oh no! The rain is coming!"), 3-9 kelime, cok basit.
  Her konusma: {{"who": "<karakter ya da dino>", "say": "...", "feel": "<duygu>", "do": "<eylem>"}}.
  Bir hayvan gercek sesini cikarabilir: {{"who": "cow", "sound": true}} (sadece gercek sesi olanlar).
- verses: melodinin kita_sayisi araliginda kita. Her kita: lines (melodinin satir sayisi KADAR satir, her satir
  hece sayisi BIREBIR), focus (o kitada one cikan karakter), do (eylem), feel, istege bagli show (o kitada ortaya
  cikan obje), istege bagli talk (kitadan once EN FAZLA 1 kisa konusma), istege bagli clear (hava bu kitada
  duruyorsa true).
  Sozler hikayeyi ANLATIR: 1. kita sorun, ortadaki kitalarda her kitada bir arkadas yardim eder ya da bir deneme
  olur (tekrarli yapi IYI: cocuklar tekrari sever), son kita kurtarma/kutlama. Sozlerin icinde diyalog olabilir
  ("Would you share?" / "Yes, I will!"). Cok basit kelimeler, kafiye, tekrar. Rakam, ozel isim (Dino haric) YOK.
  Hece sayilari: apple = 2, banana = 3, everywhere = 3, our = 2, hop = 1. Tireyle heceleme YAZMA.
- ending: {{"who": "...", "say": "kutlama cumlesi", "do": "hug" | "dance" | "jump" | "clap"}}.
- next: (son hikaye HARIC) Dino'nun siradaki hikaye icin merak cumlesi, en fazla 8 kelime
  (or. "Hmm? What's that jingle sound?").
- goodbye: bolum sonu veda cumlesi (or. "Bye bye, friends! See you next time!").

SEO (YANILTICI OLMADAN):
- title_rest: bolum adi = ilk hikayenin olayi, '!' ile, en fazla 30 karakter (or. "Rainy Day Rescue!").
  "Story", "Moral", "Bedtime", "for Kids" kelimeleri YOK.
- title: yedek baslik: "<title_rest> <Konu> Song | Thumpy Meadow", en fazla 70 karakter.
- title_phrases: TAM 5 aday arama ifadesi, kucuk harf, 3-6 kelime, ebeveynin yazacagi gibi, mumkunse "song" icersin
  (or. "farm animals song for toddlers", "rain rain song for kids").
- description_intro (2 cumle), learning_points (3-5), tags (12-15), hashtags (TAM 3, # olmadan),
  localizations: {langs} icin baslik (en fazla 90 karakter, sonda " | Thumpy Meadow") ve 2 cumle aciklama.

SADECE gecerli JSON dondur, baska hicbir sey yazma:
{{"title": "...", "title_rest": "...", "title_phrases": ["..."], "description_intro": "...",
 "learning_points": ["..."], "tags": ["..."], "hashtags": ["...", "...", "..."],
 "localizations": {{"es": {{"title": "...", "description": "..."}}}},
 "stories": [{{"name": "...", "song_title": "...", "place": "farm", "weather": "rain", "clears": true,
   "melody": "oldmac", "cast": ["cow", "duck"], "props": [],
   "hook": [{{"who": "cow", "say": "...", "feel": "scared", "do": "shiver"}}],
   "verses": [{{"focus": "cow", "do": "run", "feel": "scared", "lines": ["..."]}}],
   "ending": {{"who": "dino", "say": "...", "do": "hug"}}, "next": "..."}}],
 "goodbye": "..."}}"""


def _beat(b, cast: list[str]) -> dict | None:
    if not isinstance(b, dict):
        return None
    who = str(b.get("who", "dino")).lower()
    if who not in cast and who != "dino":
        who = "dino"
    if b.get("sound") and who in story_engine.SOUND:
        return {"who": who, "sound": True}
    say = _line(b.get("say"), "", max_words=12)
    if not say:
        return None
    feel = b.get("feel") if b.get("feel") in story_engine.FEELS else "neutral"
    do = b.get("do") if b.get("do") in story_engine.ACTIONS else "none"
    return {"who": who, "say": say, "feel": feel, "do": do}


def _lyric(x) -> str:
    s = " ".join(str(x or "").replace("’", "'").split())
    return re.sub(r"[^A-Za-z ,.!?']", " ", s.replace("-", " ")).strip() and " ".join(
        re.sub(r"[^A-Za-z ,.!?']", " ", s.replace("-", " ")).split())


def normalize_story_episode(raw: dict, cast_hint: list[str] | None = None) -> dict:
    """Claude'un hikaye bolumunu katalogla dogrular; cizilemeyen/uyumsuz secimler duzeltilir."""
    mels = _story_melodies()
    stories, used_m = [], []
    for k, st in enumerate((raw.get("stories") or [])[:N_STORIES]):
        if not isinstance(st, dict):
            continue
        cast = [c for c in dict.fromkeys(str(x).lower() for x in st.get("cast", [])) if c in critters.SPEC][:3]
        if len(cast) < 2:
            cast = (cast + [c for c in (cast_hint or []) + ["cow", "bunny", "puppy"] if c in critters.SPEC
                            and c not in cast])[:2]
        mel = st.get("melody") if st.get("melody") in mels and st.get("melody") not in used_m else \
            next(m for m in mels if m not in used_m)
        used_m.append(mel)
        pat = vocal_break.pattern(mel)
        lo, hi = _verse_range(mel)
        verses = []
        vs = [v for v in (st.get("verses") or []) if isinstance(v, dict)]
        if len(vs) > hi:                               # fazlaysa son kita (kurtarma/kutlama) korunur
            vs = vs[:hi - 1] + vs[-1:]
        for v in vs:
            if not isinstance(v, dict):
                continue
            lines = [_lyric(x) for x in v.get("lines", []) if _lyric(x)]
            if not lines:
                continue
            lines = (lines + lines)[:len(pat)] if len(lines) < len(pat) else lines[:len(pat)]
            vv = {"lines": lines,
                  "focus": v.get("focus") if v.get("focus") in cast + ["dino"] else None,
                  "do": v.get("do") if v.get("do") in story_engine.ACTIONS else "dance",
                  "feel": v.get("feel") if v.get("feel") in story_engine.FEELS else "happy"}
            if v.get("show") in assets.STORY_PROPS:
                vv["show"] = v["show"]
            talk = [b for b in (_beat(x, cast) for x in (v.get("talk") or [])[:1]) if b]
            if talk:
                vv["talk"] = talk
            if v.get("clear"):
                vv["clear"] = True
            verses.append(vv)
        if not verses:
            continue
        while len(verses) < lo:                        # kisa kalan sarki: son (kutlama) kitasi tekrar
            verses.append({**verses[-1], "focus": "dino", "do": "dance", "feel": "happy"})
            verses[-1].pop("show", None)
            verses[-1].pop("talk", None)
            verses[-1].pop("clear", None)
        hook = [b for b in (_beat(x, cast) for x in (st.get("hook") or [])[:2]) if b] or \
            [{"who": cast[0], "say": "Oh no! What can we do?", "feel": "surprised", "do": "look"}]
        end = _beat(st.get("ending") or {}, cast) or {"who": "dino", "say": "Hooray! We did it!", "do": "hug"}
        if end.get("do") not in ("hug", "dance", "jump", "clap"):
            end["do"] = "hug"
        place = st.get("place") if st.get("place") in story_engine.PLACES else ("farm", "meadow", "pond", "forest")[k % 4]
        weather = st.get("weather") if st.get("weather") in story_engine.WEATHER else None
        name = " ".join(re.sub(r"[^A-Za-z0-9 ,!?'&-]", "", str(st.get("name", ""))).split())[:32] or f"Story {k + 1}!"
        song_title = " ".join(re.sub(r"[^A-Za-z0-9 ,!?'&-]", "", str(st.get("song_title", ""))).split())[:30]
        if not song_title.lower().endswith("song"):
            song_title = (song_title + " Song").strip() if song_title else f"{vocal_break.NAMES[mel]} Song"
        out = {"name": name, "song_title": song_title, "place": place, "weather": weather,
               "clears": bool(st.get("clears")) and weather is not None, "melody": mel, "cast": cast,
               "props": [p for p in st.get("props", []) if p in assets.STORY_PROPS][:2],
               "hook": hook, "verses": verses, "ending": end}
        nx = _line(st.get("next"), "", max_words=9)
        if nx:
            out["next"] = nx
        stories.append(out)
    if len(stories) < 3:
        raise ValueError(f"Gecerli hikaye sayisi yetersiz ({len(stories)}).")
    stories[-1].pop("next", None)

    title = str(raw.get("title", "")).strip() or f"{stories[0]['name']} {stories[0]['song_title']}"
    if "thumpy meadow" not in title.lower():
        title = f"{title} | Thumpy Meadow"
    phrases = []
    for p in raw.get("title_phrases") or []:
        p = " ".join(re.sub(r"[^a-z0-9' ]", " ", str(p).lower()).split())
        if 2 <= len(p.split()) <= 7 and p not in phrases:
            phrases.append(p)
    title_rest = " ".join(re.sub(r"[^A-Za-z0-9 ,!?'&-]", "", str(raw.get("title_rest", ""))).split())[:40] \
        or stories[0]["name"]
    tags, total = [], 0
    for tg_ in raw.get("tags", []):
        tg_ = _clean_tag(tg_)
        if tg_ and total + len(tg_) + 2 <= 480:
            tags.append(tg_)
            total += len(tg_) + 2
    tags = (tags + ["Thumpy Meadow"])[:16]
    hashtags = [h for h in (re.sub(r"[^\w]", "", str(h)) for h in raw.get("hashtags", [])) if h][:3]
    hashtags = ["ThumpyMeadow" if h.lower().startswith("thum") else h for h in hashtags]
    locs = {}
    for lang in LANGS:
        loc = (raw.get("localizations") or {}).get(lang) or {}
        lt = " ".join(str(loc.get("title", "")).split())
        if lt:
            if "thumpy meadow" not in lt.lower():
                lt = f"{lt} | Thumpy Meadow"
            locs[lang] = {"title": lt[:100], "description": " ".join(str(loc.get("description", "")).split())[:1500]}
    return {"title": title[:100], "title_phrases": phrases[:5], "title_rest": title_rest,
            "description_intro": str(raw.get("description_intro", "")).strip(),
            "learning_points": [str(p).strip() for p in raw.get("learning_points", []) if str(p).strip()][:6],
            "tags": tags, "hashtags": hashtags, "thumbnail_texts": ["", "", ""], "localizations": locs,
            "stories": stories, "goodbye": _line(raw.get("goodbye"), "Bye bye, friends! See you next time!")}


def story_song_issues(ep: dict) -> list[str]:
    out = []
    for k, st in enumerate(ep["stories"]):
        pat = vocal_break.pattern(st["melody"])
        for vi, v in enumerate(st["verses"]):
            for li, line in enumerate(v["lines"]):
                words = [w for w in line.split() if re.search(r"[A-Za-z]", w)]
                missing = [w for w in words if sing.syllable_count(w) is None]
                got = sum(vocal_break.counter(w) for w in words)
                if missing or got != pat[li]:
                    per = " + ".join(f"{w.strip('.,!?')}({vocal_break.counter(w)})" for w in words)
                    note = f"hece {got} = {per}; hedef {pat[li]}" + (f"; sozlukte yok: {', '.join(missing)}" if missing else "")
                    out.append(f"{k + 1}. hikaye, {vi + 1}. kita, {li + 1}. satir: \"{line}\" ({note})")
    return out


STORY_FIX_PROMPT = """Cocuk sarkilarinin sozlerinde hata var. Her satirin HECE sayisi hedefi TAM tutmali ve tum
kelimeler yaygin Ingilizce sozlukte bulunmali. Anlami, hikayeyi, kafiyeyi ve cocuk guvenligi kurallarini koru,
sadece hatali satirlari duzelt. Tireyle heceleme YAZMA. Hece eklemek/cikarmak icin kisa kelime ekle/cikar
(or. "now", "so", "and", "up") ya da kelimeyi degistir. Hatalarda kelimelerin sayilan hecesi parantez icinde.

{items}

SADECE gecerli JSON dondur (TUM hikayeler ve TUM kitalar, sirasiyla, her kita hedef satir sayisinda):
{{"stories": [[[<1. hikaye 1. kita satirlari>], [<1. hikaye 2. kita>]], [[<2. hikaye 1. kita>]]]}}"""


def _fix_story_songs(ep: dict, issues: list[str]) -> None:
    items = []
    for k, st in enumerate(ep["stories"]):
        pat = vocal_break.pattern(st["melody"])
        items.append(f"{k + 1}. hikaye, melodi {vocal_break.NAMES[st['melody']]}, satir basina hece: "
                     + ", ".join(map(str, pat)))
        for vi, v in enumerate(st["verses"]):
            items.append(f"  {vi + 1}. kita:")
            items += [f"     {li + 1}) {line}" for li, line in enumerate(v["lines"])]
    items.append("\nHATALAR:\n" + "\n".join(f"- {x}" for x in issues))
    fixed = _ask(STORY_FIX_PROMPT.format(items="\n".join(items)), max_tokens=8000).get("stories", [])
    for st, new_st in zip(ep["stories"], fixed):
        pat = vocal_break.pattern(st["melody"])
        for v, new in zip(st["verses"], new_st or []):
            lines = [_lyric(x) for x in (new or []) if _lyric(x)]
            if len(lines) != len(pat) or _missing_words(lines):
                continue
            one = {"stories": [{"melody": st["melody"], "verses": [v]}]}
            cand = {"stories": [{"melody": st["melody"], "verses": [{**v, "lines": lines}]}]}
            if len(story_song_issues(cand)) <= len(story_song_issues(one)):
                v["lines"] = lines                     # yalnizca iyilestiriyorsa (lessons E19)


def _drop_unknown_story_words(ep: dict) -> None:
    for st in ep["stories"]:
        for v in st["verses"]:
            new = []
            for line in v["lines"]:
                kept = " ".join(w for w in line.split()
                                if not (re.search(r"[A-Za-z]", w) and sing.syllable_count(w) is None))
                new.append(kept if re.search(r"[A-Za-z]", kept) else "La la la la!")
            v["lines"] = new


def generate_story_ideas() -> list[dict]:
    st = _load_state()
    used = ", ".join(load_used()[-40:]) or "(yok)"
    used_stories = ", ".join(st.get("stories_used", [])[-60:]) or "(yok)"
    season = ("MEVSIM: Noel donemi (25 Kasim - 6 Ocak arasi Noel/kis videolari en cok izlenir): 3 fikrin EN AZ "
              "2'sinde en az bir Noel ya da kar hikayesi olsun; Jingle Bells melodisi kullanilabilir.\n"
              if _xmas_season() else "")
    data = _ask(STORY_IDEAS_PROMPT.format(n=N_STORIES, season=season, library=_story_library(), used=used,
                                          used_stories=used_stories), max_tokens=2500)
    ideas = data.get("ideas", [])[:3]
    if not ideas:
        raise ValueError("Fikir uretilemedi.")
    for idea in ideas:
        idea["format"] = "story"
    return ideas


def generate_story_script(idea: dict) -> dict:
    raw = _ask(STORY_SCRIPT_PROMPT.format(idea=json.dumps(idea, ensure_ascii=False), library=_story_library(),
                                          safety=STORY_SAFETY, n=N_STORIES, langs=", ".join(LANGS.values())),
               max_tokens=16000)
    ep = normalize_story_episode(raw, cast_hint=[c for c in idea.get("cast", []) if c in critters.SPEC])
    issues = story_song_issues(ep)
    for _ in range(2):
        if not issues:
            break
        try:
            _fix_story_songs(ep, issues)
        except Exception as exc:
            print(f"Sarki duzeltme turu basarisiz: {exc}", flush=True)
            break
        issues = story_song_issues(ep)
    _drop_unknown_story_words(ep)
    ep["song_issues"] = story_song_issues(ep)
    return ep


def remember_story_episode(ep: dict) -> None:
    """Tekrar onleme hafizasi: hikaye adlari (son 120)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    st = _load_state()
    st["stories_used"] = (st.get("stories_used", []) + [s["name"] for s in ep["stories"]])[-120:]
    USED_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def _song_title(s: dict) -> str:
    return s.get("song_title") or f"{vocal_break.NAMES.get(s.get('melody'), 'Kids')} Song"


def story_short_meta(ep: dict, k: int, full_video_id: str | None) -> dict:
    s = ep["stories"][k]
    title = f"{s['name']} {_song_title(s)} | Thumpy Meadow"
    desc = [f"{s['name']} A sing-along cartoon song with Dino and friends for toddlers and preschoolers."]
    if full_video_id:
        desc.append(f"Watch all the songs in the full episode: https://youtu.be/{full_video_id}")
    desc.append(" ".join(f"#{h}" for h in (["shorts"] + ep["hashtags"])[:4]))
    tags = list(dict.fromkeys([_song_title(s).lower()] + ep["tags"]))[:15]
    return {"title": title[:100], "description": "\n\n".join(desc), "tags": tags}


def story_description(ep: dict, chapter_list) -> str:
    parts = [ep["description_intro"]]
    if ep["learning_points"]:
        parts.append("In this video, little ones will:\n" + "\n".join(f"- {p}" for p in ep["learning_points"]))
    parts.append("Songs in this video:\n" + "\n".join(f"- {s['name']} ({_song_title(s)})" for s in ep["stories"]))
    if chapter_list:
        parts.append("Chapters:\n" + _chapters_text(chapter_list))
    parts.append("Thumpy Meadow makes gentle, original cartoon sing-along stories for toddlers and preschoolers "
                 "(ages 2-6). Sing, dance and learn English with Dino and friends. New episodes regularly - ask a "
                 "grown-up to subscribe!")
    parts.append("Songs: original lyrics on public-domain melodies. " + sing.CREDIT +
                 ". Some real animal sounds: BigSoundBank (CC0).")
    if ep["hashtags"]:
        parts.append(" ".join(f"#{h}" for h in ep["hashtags"]))
    return "\n\n".join(parts)[:4900]
