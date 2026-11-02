"""
Tamamen kodla uretilen, telifsiz muzik.
- Fon muzigi: yumusak marimba arpejleri + hafif pad akorlar (anlatimin altinda kisik calar)
- Muzik molasi: pentatonik dizide algoritmik olarak uretilen OZGUN melodi
  (her kelime bir notaya denk gelir, karaoke vurgusu icin zamanlama dondurulur)

Akor dizisi (C-G-Am-F) gibi temel yapilar telife konu degildir; melodiler
rastgele ama tekrarlanabilir (seed) sekilde uretildigi icin ozgundur.
"""
import random
import wave

import numpy as np

SR = 44100

# C - G - Am - F (orta oktav ucluler)
PROGRESSION = [
    (60, 64, 67),  # C
    (59, 62, 67),  # G
    (57, 60, 64),  # Am
    (57, 60, 65),  # F
]
PENTATONIC = [60, 62, 64, 67, 69, 72, 74, 76]  # Do majör pentatonik


def midi_to_freq(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def _marimba(freq: float, dur: float, vel: float) -> np.ndarray:
    n = int(SR * dur)
    t = np.arange(n) / SR
    sig = (
        np.sin(2 * np.pi * freq * t)
        + 0.15 * np.sin(2 * np.pi * freq * 2 * t)
        + 0.30 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t * 20)
    )
    env = np.exp(-t * 4.5) * np.minimum(1.0, t / 0.004)
    return vel * sig * env


def _pad(midis, dur: float, vel: float) -> np.ndarray:
    n = int(SR * dur)
    t = np.arange(n) / SR
    sig = sum(
        np.sin(2 * np.pi * midi_to_freq(m) * t) + 0.25 * np.sin(2 * np.pi * midi_to_freq(m) * 2 * t)
        for m in midis
    ) / len(midis)
    attack = np.minimum(1.0, t / 0.35)
    release = np.clip((dur - t) / 0.35, 0.0, 1.0)
    return vel * sig * attack * release


def _add(buf: np.ndarray, sig: np.ndarray, start_s: float) -> None:
    i = int(start_s * SR)
    if i >= len(buf):
        return
    end = min(len(buf), i + len(sig))
    buf[i:end] += sig[: end - i]


def background_track(duration: float, bpm: float = 88, vel: float = 1.0) -> np.ndarray:
    """Anlatimin altinda calan sakin fon muzigi."""
    buf = np.zeros(int(SR * duration) + SR)
    beat = 60.0 / bpm
    bar = 4 * beat
    t, bar_i = 0.0, 0
    while t < duration:
        chord = PROGRESSION[bar_i % len(PROGRESSION)]
        _add(buf, _pad(chord, bar, 0.07 * vel), t)
        _add(buf, _marimba(midi_to_freq(chord[0] - 12), 1.2, 0.10 * vel), t)  # bas
        arp = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[1] + 12]
        for k in range(8):  # sekizlik arpej
            _add(buf, _marimba(midi_to_freq(arp[k % 4]), 0.6, 0.05 * vel), t + k * beat / 2)
        t += bar
        bar_i += 1
    return buf[: int(SR * duration)]


def music_break_track(lines: list[str], bpm: float = 100, seed: int = 0):
    """Ozgun melodi uretir. Donus: (ses, kelime_zamanlari, sure)
    kelime_zamanlari: [(satir_index, kelime_index, baslangic_s), ...]"""
    rng = random.Random(seed)
    beat = 60.0 / bpm
    line_len = 8 * beat  # her satir 2 olcu
    intro = 4 * beat     # 1 olcu giris
    total = intro + line_len * len(lines) + 4 * beat
    buf = np.zeros(int(SR * total) + SR)
    timings = []

    # akorlar (her olcu bir akor)
    n_bars = int(total / (4 * beat)) + 1
    for b in range(n_bars):
        chord = PROGRESSION[b % len(PROGRESSION)]
        _add(buf, _pad(chord, 4 * beat, 0.10), b * 4 * beat)
        _add(buf, _marimba(midi_to_freq(chord[0] - 12), 1.0, 0.16), b * 4 * beat)
        for k in (0, 2):  # hafif tempo vurgusu
            _add(buf, _marimba(midi_to_freq(chord[2] + 12), 0.3, 0.05), b * 4 * beat + k * beat)

    idx = 4  # baslangic notasi: 67 (Sol)
    for li, line in enumerate(lines):
        words = line.split()
        start = intro + li * line_len
        usable = 6 * beat  # son 2 vurus nefes payi
        step = usable / max(len(words), 1)
        for wi, _w in enumerate(words):
            idx = max(0, min(len(PENTATONIC) - 1, idx + rng.choice([-2, -1, -1, 0, 1, 1, 2])))
            note = PENTATONIC[idx]
            is_last_word = wi == len(words) - 1
            if is_last_word:
                note = 60 if li == len(lines) - 1 else rng.choice([64, 67])
            t0 = start + wi * step
            _add(buf, _marimba(midi_to_freq(note), 0.9 if is_last_word else 0.5, 0.32), t0)
            timings.append((li, wi, t0))
    return buf[: int(SR * total)], timings, total


def write_wav(path: str, samples: np.ndarray) -> None:
    peak = np.max(np.abs(samples)) or 1.0
    data = (samples / peak * 0.85 * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(data.tobytes())
