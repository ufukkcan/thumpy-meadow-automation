"""
Baslik secimi (7e E2): Claude'un 5 aday arama ifadesinden TALEBI OLAN ve REKABETI EN ZAYIF olani basa koyar.
- Talep: YouTube arama otomatik tamamlamasi (resmi olmayan, herkese acik uc nokta). Ifade ya da ifade + ek
  kelime oneriliyorsa insanlar bunu ariyor demektir.
- Rekabet: YouTube Data API search.list (ABD, Ingilizce) ilk 10 video -> medyan izlenme ve medyan kanal abonesi.
  Arama basina 100 kota birimi (5 aday = gunluk kotanin ~%5'i). Yalnizca okuma.
- Kanal dogrulamasi yapilmadan token kullanilmaz (CLAUDE.md).
- Herhangi bir hata bolumu durdurmaz: Claude'un kendi basligi kalir, rapor nedenini yazar.
"""
import json
import statistics
import urllib.parse
import urllib.request

import upload_youtube as yt

SUGGEST_URL = "https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&hl=en&gl=US&q="
SMALL = {"a", "an", "and", "for", "in", "of", "on", "the", "to", "with"}


def suggestions(q: str) -> list[str]:
    req = urllib.request.Request(SUGGEST_URL + urllib.parse.quote(q), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode("utf-8", errors="replace"))
    return [str(s).lower() for s in data[1]] if len(data) > 1 else []


def demand(q: str) -> int:
    """Ifadenin kendisi ya da devami olan oneri sayisi (0 = kimse aramiyor)."""
    return sum(1 for s in suggestions(q) if s == q or s.startswith(q + " "))


def competition(api, q: str) -> dict:
    ids = [it["id"]["videoId"] for it in api.search().list(
        part="id", q=q, type="video", maxResults=10, regionCode="US", relevanceLanguage="en",
        safeSearch="strict").execute().get("items", [])]
    if not ids:
        return {"views": 0, "subs": 0, "n": 0}
    vids = api.videos().list(part="statistics,snippet", id=",".join(ids)).execute().get("items", [])
    views = [int(v["statistics"].get("viewCount", 0)) for v in vids]
    chans = list({v["snippet"]["channelId"] for v in vids})
    subs = [int(c["statistics"].get("subscriberCount", 0)) for c in api.channels().list(
        part="statistics", id=",".join(chans)).execute().get("items", [])]
    return {"views": int(statistics.median(views)) if views else 0,
            "subs": int(statistics.median(subs)) if subs else 0, "n": len(ids)}


def title_case(q: str) -> str:
    return " ".join(w if (k and w in SMALL) else w[:1].upper() + w[1:] for k, w in enumerate(q.split()))


def build_title(phrase: str, rest: str) -> str:
    t = f"{title_case(phrase)} | {rest} | Thumpy Meadow" if rest else f"{title_case(phrase)} | Thumpy Meadow"
    return t if len(t) <= 90 else f"{title_case(phrase)} | Thumpy Meadow"


def _num(n: int) -> str:
    return f"{n / 1e6:.1f}M" if n >= 1e6 else f"{n / 1e3:.0f}K" if n >= 1e3 else str(n)


def apply_title(ep: dict) -> dict:
    """ep['title'] ve ep['title_report'] gunceller. Hata olursa baslik degismez."""
    phrases = ep.get("title_phrases") or []
    report = []
    try:
        if not phrases:
            raise ValueError("aday ifade yok")
        yt.verify_channel()
        api = yt._youtube()
        rows = []
        for p in phrases:
            d = demand(p)
            c = competition(api, p) if d else None
            rows.append((p, d, c))
            report.append(f"- \"{p}\": oneri {d}" + (f", ilk 10 medyan izlenme {_num(c['views'])}, "
                                                    f"medyan abone {_num(c['subs'])}" if c else " (talep yok, olculmedi)"))
        ok = [r for r in rows if r[1] and r[2]["n"]]
        if not ok:
            report.append("Talebi olan ifade bulunamadi; Claude'un basligi kaldi.")
        else:
            best = min(ok, key=lambda r: (r[2]["views"], r[2]["subs"]))
            ep["title"] = build_title(best[0], ep.get("title_rest", ""))[:100]
            report.append(f"SECILEN: \"{best[0]}\" (talep var, rekabet en dusuk)")
    except Exception as exc:
        report.append(f"Olcum yapilamadi ({str(exc)[:150]}); Claude'un basligi kaldi.")
    ep["title_report"] = report
    return ep
