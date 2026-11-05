"""
Gercek hayvan sesleri (7c): BigSoundBank kayitlari, CC0 / kamu mali (licenses/bigsoundbank-NOTICE.txt).

- Sabit dosya adresinden indirilir, sfx_cache/bigsoundbank/'e onbelleklenir.
- Kayittaki tek tek cagrilar (moo, quack, woof) enerji zarfina gore otomatik kesilir;
  en "yalniz" (arka plandan en belirgin) cagrilar once gelir.
- Hayvan konusmaz: senaryoda hayvanin sesi her zaman bu kayitlardir.
"""
import subprocess
import time
import urllib.request
from pathlib import Path

import numpy as np

SR = 44100
CACHE = Path(__file__).resolve().parent / "sfx_cache" / "bigsoundbank"

# ad -> (BigSoundBank no, dosya adresi, cagri uzunlugu araligi sn)
SOURCES = {
    "cow": ("2383", "https://bigsoundbank.com/UPLOAD/flac/2383.flac", (0.3, 2.6)),    # Cow moos #3
    "duck": ("0276", "https://bigsoundbank.com/UPLOAD/bwf-en/0276.wav", (0.1, 1.0)),  # Ducks
    "dog": ("2352", "https://bigsoundbank.com/UPLOAD/flac/2352.flac", (0.1, 1.0)),    # Old dog barking #1
}

_calls = {}


def _download(name):
    sid, url, _ = SOURCES[name]
    dst = CACHE / f"{sid}{Path(url).suffix}"
    if dst.exists() and dst.stat().st_size > 0:
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "thumpy-meadow-render"})
            with urllib.request.urlopen(req, timeout=60) as r:
                dst.write_bytes(r.read())
            return dst
        except Exception as exc:
            if attempt == 3:
                raise RuntimeError(f"Indirilemedi: {url}\n{exc}") from exc
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
    thr = max(0.2 * env.max(), 3 * np.median(env))
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
    lo, hi = SOURCES[name][2]
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
    if not out:
        raise RuntimeError(f"{name}: kayitta uygun cagri bulunamadi ({len(runs)} bolge)")
    _calls[name] = [seg for _, seg in out[:max_n]]
    return _calls[name]


def clip(name, n=1, gap=0.15):
    """n cagri art arda (cesitlilik icin farkli cagrilar sirayla)."""
    cs = calls(name)
    parts = []
    for k in range(n):
        parts += [cs[k % len(cs)], np.zeros(int(gap * SR))]
    return np.concatenate(parts[:-1])


def report():
    return [f"{k} (BigSoundBank #{v[0]}): {len(calls(k))} cagri, sureler "
            + ", ".join(f"{len(c) / SR:.2f}" for c in calls(k)) for k, v in SOURCES.items()]
