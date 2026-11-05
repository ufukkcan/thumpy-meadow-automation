"""
Gercek hayvan sesleri (7c/7d): BigSoundBank kayitlari, CC0 / kamu mali (licenses/bigsoundbank-NOTICE.txt).

- Sabit dosya adresinden indirilir, sfx_cache/bigsoundbank/'e onbelleklenir.
- Kayittaki tek tek cagrilar (moo, quack, woof ...) enerji zarfina gore otomatik kesilir;
  en "yalniz" (arka plandan en belirgin) cagrilar once gelir.
- Hayvan konusmaz: senaryoda hayvanin sesi her zaman bu kayitlardir.
- SOURCES = bolumlerde "bulunabilecek" hayvanlarin listesi (gercek kaydi olmayan hayvan bulunamaz:
  domuz, fil, maymun, aslan icin CC0 gercek kayit yok -- 2026-11-05 tum hayvan kategorisi tarandi).
"""
import subprocess
import time
import urllib.request
from pathlib import Path

import numpy as np

SR = 44100
CACHE = Path(__file__).resolve().parent / "sfx_cache" / "bigsoundbank"

_B = "https://bigsoundbank.com/UPLOAD/"
# ad -> no, dosya, cagri suresi araligi (sn), ses yazimi (altyazi + "Who says ...?"), ucabilir mi
SOURCES = {
    "cow": dict(id="2383", url=_B + "flac/2383.flac", rng=(0.3, 2.6), says="moo", fly=False),
    "duck": dict(id="0276", url=_B + "bwf-en/0276.wav", rng=(0.1, 1.0), says="quack", fly=True),
    "dog": dict(id="2352", url=_B + "flac/2352.flac", rng=(0.1, 1.0), says="woof", fly=False),
    "cat": dict(id="1890", url=_B + "flac/1890.flac", rng=(0.2, 2.0), says="meow", fly=False),
    "sheep": dict(id="2343", url=_B + "flac/2343.flac", rng=(0.2, 1.6), says="baa", fly=False),
    "rooster": dict(id="0283", url=_B + "bwf-en/0283.wav", rng=(0.5, 3.0), says="cock-a-doodle-doo", fly=True),
    "horse": dict(id="0863", url=_B + "flac/0863.flac", rng=(0.4, 3.5), says="neigh", fly=False),
    "frog": dict(id="0819", url=_B + "bwf-en/0819.wav", rng=(0.08, 1.5), says="ribbit", fly=False),
    "chick": dict(id="0430", url=_B + "bwf-en/0430.wav", rng=(0.05, 0.8), says="peep", fly=False),
    "owl": dict(id="1763", url=_B + "flac/1763.flac", rng=(0.3, 3.5), says="hoot", fly=True),
    "bird": dict(id="1667", url=_B + "flac/1667.flac", rng=(0.3, 3.0), says="tweet", fly=True),
}

_calls = {}


def _download(name):
    src = SOURCES[name]
    dst = CACHE / f"{src['id']}{Path(src['url']).suffix}"
    if dst.exists() and dst.stat().st_size > 0:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            req = urllib.request.Request(src["url"], headers={"User-Agent": "thumpy-meadow-render"})
            with urllib.request.urlopen(req, timeout=60) as r:
                dst.write_bytes(r.read())
            return dst
        except Exception as exc:
            if attempt == 3:
                raise RuntimeError(f"Indirilemedi: {src['url']}\n{exc}") from exc
            time.sleep(2 * (attempt + 1))


def load(name):
    """Mono, 44,1 kHz, -1..1; 80 Hz alti (ruzgar ugultusu) kirpilir."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(_download(name)), "-af", "highpass=f=80",
                          "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0


def calls(name, max_n=6):
    """Kayittan kesilmis tek cagrilar (en belirgin once). Donus: [np.ndarray]."""
    if name in _calls:
        return _calls[name]
    x = load(name)
    hop = int(0.01 * SR)
    n = len(x) // hop
    env = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1))
    # esik: sessizlige gore belirgin ama asla zirvenin yarisini gecmez (ses tum dosyayi kaplayan kisa
    # kayitlarda ortanca yuksek -> eski esik zirveyi asiyor, hic cagri bulunmuyordu; lessons C6)
    thr = min(max(0.2 * env.max(), 3 * np.median(env)), 0.5 * env.max())
    on = env > thr
    runs, i = [], 0
    while i < n:                                   # esik ustu bolgeler; 60 ms'den kisa bosluklar birlesir
        if on[i]:
            j = i
            while j < n and (on[j] or np.any(on[j:j + 6])):
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    lo, hi = SOURCES[name]["rng"]
    out = []
    for s, e in runs:
        if not (lo * 100 <= e - s <= hi * 100):
            continue
        around = np.concatenate([env[max(0, s - 30):s], env[e:e + 30]])
        score = env[s:e].max() / (np.median(around) + 1e-6 if len(around) else 1e-6)
        a, b = max(0, s - 4) * hop, min(n, e + 12) * hop
        seg = x[a:b].copy()
        fi, fo = int(0.005 * SR), int(0.04 * SR)
        seg[:fi] *= np.linspace(0, 1, fi)
        seg[-fo:] *= np.linspace(1, 0, fo)
        out.append((score, seg))
    out.sort(key=lambda z: -z[0])
    if not out:                                    # yedek: kaydin sesli kismi tek cagri (kayit zaten tek cagriysa)
        loud = np.nonzero(env > 0.1 * env.max())[0]
        if not len(loud):
            raise RuntimeError(f"{name}: kayit sessiz")
        a, b = max(0, loud[0] - 4) * hop, min(n, loud[-1] + 12) * hop
        seg = x[a:b][: int(hi * SR)].copy()
        fo = int(0.04 * SR)
        seg[-fo:] *= np.linspace(1, 0, fo)
        out = [(0.0, seg)]
    _calls[name] = [seg for _, seg in out[:max_n]]
    return _calls[name]


def clip(name, n=1, gap=0.15):
    """n cagri art arda (cesitlilik icin farkli cagrilar sirayla)."""
    cs = calls(name)
    parts = []
    for k in range(n):
        parts += [cs[k % len(cs)], np.zeros(int(gap * SR))]
    return np.concatenate(parts[:-1])


def report(names=None):
    return [f"{k} (BigSoundBank #{SOURCES[k]['id']}): {len(calls(k))} cagri, sureler "
            + ", ".join(f"{len(c) / SR:.2f}" for c in calls(k)) for k in (names or SOURCES)]
