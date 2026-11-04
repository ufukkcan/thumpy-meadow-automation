"""
CC0 lisansli kayitli enstruman sesleri (bkz. docs/kararlar.md K-17).

Kaynaklar commit SHA'sina sabitlenir; ilk kullanimda raw.githubusercontent.com'dan
indirilip sample_cache/ altinda saklanir (GitHub Actions'ta actions/cache ile tutulur).
Her ornek: mono 44.1 kHz'e cevrilir, tepe 1.0'a normalize edilir ve ATAK ANINA gore
kirpilir -> nota zamani = sesin duyuldugu an (ritim izgarasina tam oturur).
"""
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

SR = 44100
CACHE = Path(__file__).resolve().parent / "sample_cache"

# hepsinin LICENSE dosyasi CC0 1.0 (2026-11-04 dogrulandi)
SOURCES = {
    "vcsl": ("sgossner/VCSL", "c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e"),
    "uke": ("freepats/ukulele1", "86d345f6f7b79a106ace98eca0da19b087786dba"),
    "bass": ("sfzinstruments/dsmolken.double-bass", "c2985eb647109d2a8f30a70071e3e163339d7396"),
    "drums": ("sfzinstruments/karoryfer.big-rusty-drums", "f07ce00df34a46b6b08375be56fe116cf15782bc"),
}

_XYLO = "Idiophones/Struck Idiophones/Xylophone/Medium Mallets/Xylo_Medium_{}_ff_01_far.wav"
_GLOCK = "Idiophones/Struck Idiophones/Glockenspiel/glock_medium_{}_01.wav"

# perdeli enstrumanlar: (nominal_midi, kaynak, yol, ince_ayar_cent)
# ince ayar SFZ dosyalarindaki 'tune' degeri (ornegin kendi kucuk perde sapmasi)
PITCHED = {
    "xylo": [(m, "vcsl", _XYLO.format(n), 0) for m, n in
             ((55, "G3"), (60, "C4"), (67, "G4"), (72, "C5"), (79, "G5"), (84, "C6"), (91, "G6"), (96, "C7"))],
    "glock": [(m, "vcsl", _GLOCK.format(n), 0) for m, n in
              ((67, "G4"), (72, "C5"), (79, "G5"), (84, "C6"), (91, "G6"), (96, "C7"))],
    # Ukulele 20260811.sfz: pitch_keycenter + tune
    "uke": [(m, "uke", f"samples/{n}.flac", c) for m, n, c in
            ((60, "C4", -5), (62, "D4", -8), (64, "E4", -2), (66, "F#4", -11), (67, "G4", -1),
             (69, "A4", 0), (71, "B4", 0), (73, "C#5", 0), (75, "D#5", 3), (77, "F5", 4),
             (79, "G5", 6), (81, "A5", 8), (84, "C6", 4))],
    # d_smolken_rubner_bass_pizz.sfz: c1=24 ... a3=57 (orta guc, 'ma' katmani)
    "bass": [(m, "bass", f"pizz/pizz_{n}_ma.wav", 0) for m, n in
             ((31, "g1"), (34, "bb1"), (38, "d2"), (41, "f2"), (45, "a2"), (48, "c3"), (52, "e3"),
              (55, "g3"), (57, "a3"))],
}

# tek vurusluk sesler: ad -> [(kaynak, yol), ...] (birden fazlaysa sirayla calinir: round robin)
_PERC = "Idiophones/Struck Idiophones/"
HITS = {
    "kick": [("drums", f"Samples/kick_24/kick/kick/k_vl8_rr{i}.flac") for i in range(1, 5)],
    "snare": [("vcsl", "Membranophones/Struck Membranophones/Snare Drum, Modern 1/Snare2_HitSN_v5_rr1_Mid.wav")],
    "clap": [("vcsl", f"{_PERC}Claps/Clap_rr{i}.wav") for i in range(1, 7)],
    "shaker_down": [("vcsl", f"{_PERC}Shaker, Small/Mid_ShakerDouble_Down_rr1.wav")],
    "shaker_up": [("vcsl", f"{_PERC}Shaker, Small/Mid_ShakerDouble_Up_rr1.wav")],
    "tamb": [("vcsl", f"{_PERC}Tambourine 1/Tamb1_Hit_v2_rr1_Mid.wav")],
    "belltree": [("vcsl", f"{_PERC}Bell Tree/Stroke/BellTree_Stroke_1_Mid.wav")],
    "whistle": [("vcsl", "Aerophones/Edge-blown Aerophones/Ball Whistle/Main_BallWhistle_Short-001.wav")],
    "boing": [("vcsl", f"{_PERC}Flexatone/flexatone_slap1.wav")],
}


def _run(cmd: list[str], data: bytes | None = None) -> bytes:
    """Dis komut; hata olursa stderr'in son satirlarini gosterir (lessons A1)."""
    p = subprocess.run(cmd, input=data, capture_output=True)
    if p.returncode != 0:
        tail = "\n".join(p.stderr.decode(errors="ignore").splitlines()[-25:])
        raise RuntimeError(f"Komut basarisiz ({p.returncode}): {' '.join(cmd[:4])}...\n{tail}")
    return p.stdout


def _local(src: str, path: str) -> Path:
    return CACHE / src / path


def _all_files() -> list[tuple[str, str]]:
    files = [(s, p) for regs in PITCHED.values() for _, s, p, _ in regs]
    files += [f for lst in HITS.values() for f in lst]
    return files


def ensure() -> None:
    """Eksik ornekleri indirir (sabit commit'ten)."""
    for src, path in _all_files():
        dst = _local(src, path)
        if dst.exists() and dst.stat().st_size > 0:
            continue
        repo, sha = SOURCES[src]
        url = f"https://raw.githubusercontent.com/{repo}/{sha}/{urllib.parse.quote(path)}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    dst.write_bytes(r.read())
                break
            except Exception as exc:
                if attempt == 3:
                    raise RuntimeError(f"Indirilemedi: {url}\n{exc}") from exc
                time.sleep(2 * (attempt + 1))


_loaded: dict[tuple[str, str], np.ndarray] = {}


def _trim_to_attack(x: np.ndarray) -> np.ndarray:
    """Bastaki sessizligi atar: sesin tepe degerin %10'unu gectigi andan 3 ms once baslar."""
    peak = np.max(np.abs(x)) or 1.0
    idx = np.where(np.abs(x) >= 0.1 * peak)[0]
    start = max(0, int(idx[0]) - int(0.003 * SR)) if len(idx) else 0
    return x[start:]


def load(src: str, path: str) -> np.ndarray:
    key = (src, path)
    if key not in _loaded:
        raw = _run(["ffmpeg", "-v", "error", "-i", str(_local(src, path)),
                    "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"])
        x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
        x = _trim_to_attack(x)
        _loaded[key] = x / (np.max(np.abs(x)) or 1.0)
    return _loaded[key]


def _release(x: np.ndarray, max_dur: float | None, rel: float = 0.06) -> np.ndarray:
    """Notayi max_dur'da yumusakca susturur (tel/cubuk susturma gibi); uca 5 ms gecis."""
    if max_dur is not None and len(x) > int((max_dur + rel) * SR):
        n, r = int(max_dur * SR), int(rel * SR)
        x = x[: n + r].copy()
        x[n:] *= np.linspace(1, 0, r) ** 2
    else:
        x = x.copy()
    f = min(len(x), int(0.005 * SR))
    x[-f:] *= np.linspace(1, 0, f)
    return x


def note(inst: str, midi: float, vel: float = 1.0, max_dur: float | None = None) -> np.ndarray:
    """Perdeli nota: en yakin ornek secilir, yeniden ornekleme ile perdesi ayarlanir."""
    nom, src, path, cents = min(PITCHED[inst], key=lambda r: abs(r[0] - midi))
    x = load(src, path)
    ratio = 2 ** ((midi - nom) / 12 + cents / 1200)
    if abs(ratio - 1) > 1e-4:
        n_out = int(len(x) / ratio)
        x = np.interp(np.arange(n_out) * ratio, np.arange(len(x)), x)
    return vel * _release(x, max_dur)


_rr: dict[str, int] = {}


def hit(name: str, vel: float = 1.0, max_dur: float | None = None) -> np.ndarray:
    """Tek vurusluk ses; birden fazla kayit varsa sirayla (dogal, makine gibi degil)."""
    lst = HITS[name]
    i = _rr.get(name, 0)
    _rr[name] = i + 1
    src, path = lst[i % len(lst)]
    return vel * _release(load(src, path), max_dur)


# ---------------- dogrulama: orneklerin gercek perdesi ----------------
def detect_f0(x: np.ndarray, fmin: float = 28.0, fmax: float = 4200.0) -> float | None:
    """YIN yontemi (de Cheveigne & Kawahara 2002) -- atak sonrasi kararli bolgede."""
    x = x[int(0.03 * SR):]
    w, maxlag, minlag = 4096, int(SR / fmin), int(SR / fmax)
    seg = x[: w + maxlag]
    if len(seg) < w + maxlag:
        return None
    cs = np.concatenate([[0.0], np.cumsum(seg ** 2)])
    taus = np.arange(maxlag + 1)
    n = 1 << int(np.ceil(np.log2(len(seg) + w)))
    r = np.fft.irfft(np.conj(np.fft.rfft(seg[:w], n)) * np.fft.rfft(seg, n), n)[: maxlag + 1]
    d = cs[w] + (cs[taus + w] - cs[taus]) - 2 * r
    cmnd = np.ones_like(d)
    cmnd[1:] = d[1:] * taus[1:] / np.maximum(np.cumsum(d[1:]), 1e-12)
    below = np.where(cmnd[minlag:] < 0.15)[0]
    tau = minlag + (below[0] if len(below) else int(np.argmin(cmnd[minlag:])))
    while tau + 1 <= maxlag and cmnd[tau + 1] < cmnd[tau]:
        tau += 1
    if 0 < tau < maxlag:  # parabolik ara deger
        a, b, c = cmnd[tau - 1], cmnd[tau], cmnd[tau + 1]
        den = a - 2 * b + c
        tau = tau + (0.5 * (a - c) / den if den else 0)
    return SR / tau


def pitch_report() -> list[str]:
    """Her perdeli ornegin olculen perdesi ile beklenen perdesi arasindaki fark (cent)."""
    lines = []
    for inst, regs in PITCHED.items():
        for nom, src, path, cents in regs:
            f0 = detect_f0(load(src, path))
            expect = 440.0 * 2 ** ((nom - 69) / 12) * 2 ** (-cents / 1200)
            if f0 is None:
                lines.append(f"{inst:5s} {nom:3d} {Path(path).name}: olculemedi")
                continue
            diff = 1200 * np.log2(f0 / expect)
            flag = "  <-- OKTAV?" if abs(abs(diff) - 1200) < 150 else ("  <-- SAPMA" if abs(diff) > 50 else "")
            lines.append(f"{inst:5s} {nom:3d} {Path(path).name}: {f0:8.1f} Hz, fark {diff:+7.0f} cent{flag}")
    return lines
