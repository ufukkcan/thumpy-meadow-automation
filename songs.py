"""
Muzik molalari icin telifsiz (1929 oncesi, kamu malı) melodiler + kendi duzenlememiz.

Melodiler serbest; duzenleme (davul, bas, akor, zil) sifirdan kodla uretiliyor.
Sozler her bolum icin Claude tarafindan yaziliyor ve satir basina HECE SAYISI melodiyle eslesiyor.

Not formati: (midi_nota, vurus_suresi)
"""
import re

import numpy as np

import music

SR = music.SR

# ---------------- melodi sablonlari ----------------
# Her satir 8 vurus (2 olcu, 4/4). chords: satir basina 4 akor (her biri 2 vurus).
C, F, G, Am = (60, 64, 67), (65, 69, 72), (67, 71, 74), (57, 60, 64)

MELODIES = {
    # Twinkle Twinkle Little Star -- melodi 1761 (Fransiz halk sarkisi), soz 1806
    "twinkle": {
        "name": "Twinkle Twinkle Little Star melody",
        "lines": [
            [(60, 1), (60, 1), (67, 1), (67, 1), (69, 1), (69, 1), (67, 2)],
            [(65, 1), (65, 1), (64, 1), (64, 1), (62, 1), (62, 1), (60, 2)],
            [(67, 1), (67, 1), (65, 1), (65, 1), (64, 1), (64, 1), (62, 2)],
            [(67, 1), (67, 1), (65, 1), (65, 1), (64, 1), (64, 1), (62, 2)],
            [(60, 1), (60, 1), (67, 1), (67, 1), (69, 1), (69, 1), (67, 2)],
            [(65, 1), (65, 1), (64, 1), (64, 1), (62, 1), (62, 1), (60, 2)],
        ],
        "chords": [[C, C, F, C], [F, C, G, C], [C, F, C, G], [C, F, C, G], [C, C, F, C], [F, C, G, C]],
        "bpm": 104,
    },
    # Mary Had a Little Lamb -- 1830
    "mary": {
        "name": "Mary Had a Little Lamb melody",
        "lines": [
            [(64, 1.5), (62, 0.5), (60, 1), (62, 1), (64, 1), (64, 1), (64, 2)],
            [(62, 1), (62, 1), (62, 2), (64, 1), (67, 1), (67, 2)],
            [(64, 1.5), (62, 0.5), (60, 1), (62, 1), (64, 1), (64, 1), (64, 1), (64, 1)],
            [(62, 1), (62, 1), (64, 1), (62, 1), (60, 4)],
        ],
        "chords": [[C, C, C, C], [G, G, C, C], [C, C, C, C], [G, G, C, C]],
        "bpm": 108,
    },
    # London Bridge Is Falling Down -- geleneksel, 17. yy
    "london": {
        "name": "London Bridge melody",
        "lines": [
            [(67, 1.5), (69, 0.5), (67, 1), (65, 1), (64, 1), (65, 1), (67, 2)],
            [(62, 1), (64, 1), (65, 2), (64, 1), (65, 1), (67, 2)],
            [(67, 1.5), (69, 0.5), (67, 1), (65, 1), (64, 1), (65, 1), (67, 2)],
            [(62, 2), (67, 2), (64, 1), (60, 3)],
        ],
        "chords": [[C, C, C, C], [G, G, C, C], [C, C, C, C], [G, G, C, C]],
        "bpm": 112,
    },
    # Frere Jacques -- 18. yy (F majorde, cocuk sesine uygun aralik)
    "jacques": {
        "name": "Frere Jacques melody",
        "lines": [
            [(65, 1), (67, 1), (69, 1), (65, 1), (65, 1), (67, 1), (69, 1), (65, 1)],
            [(69, 1), (70, 1), (72, 2), (69, 1), (70, 1), (72, 2)],
            [(72, 0.5), (74, 0.5), (72, 0.5), (70, 0.5), (69, 1), (65, 1),
             (72, 0.5), (74, 0.5), (72, 0.5), (70, 0.5), (69, 1), (65, 1)],
            [(65, 1), (60, 1), (65, 2), (65, 1), (60, 1), (65, 2)],
        ],
        "chords": [[(65, 69, 72)] * 4] * 4,
        "bpm": 100,
    },
}


def syllable_pattern(key: str) -> list[int]:
    """Her satirin hece (nota) sayisi -- Claude'a soz yazdirirken verilir."""
    return [len(line) for line in MELODIES[key]["lines"]]


# ---------------- hece sayma ve kelime->nota esleme ----------------
# kurallarla dogru sayilamayan sik kelimeler
SYLLABLE_EXCEPTIONS = {"triangle": 3, "triangles": 3, "lion": 2, "lions": 2, "piano": 3, "idea": 3,
                       "video": 3, "rainbow": 2, "every": 2, "diamond": 2, "hello": 2, "dinosaur": 3}


def count_syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    if w in SYLLABLE_EXCEPTIONS:
        return SYLLABLE_EXCEPTIONS[w]
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if n > 1:
        if w.endswith("e") and not w.endswith(("le", "ee", "ye")):
            n -= 1                                   # make, five, blue degil
        elif w.endswith("es") and not w.endswith("ies") and not re.search(r"(s|x|z|ch|sh|c|g|l)es$", w):
            n -= 1                                   # grapes, shapes (ama boxes, apples, oranges 2+)
        elif w.endswith("ed") and not re.search(r"[td]ed$", w):
            n -= 1                                   # jumped, played (ama counted 2)
    return max(1, n)


def map_words_to_notes(line_text: str, notes: list[tuple], counter=None) -> list[tuple[str, list[tuple]]]:
    """Her kelimeye hece sayisi kadar nota atar. Hece < nota ise son kelime uzar,
    hece > nota ise fazla heceler son notalara sikistirilir.
    counter: kelime -> hece sayisi (varsayilan: kural tabanli count_syllables; vokalde CMU sozlugu)."""
    counter = counter or count_syllables
    words = [w for w in line_text.split() if re.search(r"[A-Za-z]", w)]
    counts = [counter(w) for w in words]
    total = sum(counts)
    if total > len(notes):  # fazlaliklari sondan kirp
        overflow = total - len(notes)
        for i in range(len(counts) - 1, -1, -1):
            cut = min(overflow, counts[i] - 1)
            counts[i] -= cut
            overflow -= cut
            if overflow == 0:
                break
        while sum(counts) > len(notes):  # hala fazla: kelimeleri birlestir
            words[-2] = words[-2] + " " + words[-1]
            counts[-2] += counts[-1] - 1
            words, counts = words[:-1], counts[:-1]
    if sum(counts) < len(notes):
        counts[-1] += len(notes) - sum(counts)
    out, i = [], 0
    for w, c in zip(words, counts):
        out.append((w, notes[i:i + c]))
        i += c
    return out


# ---------------- davul / bas / akor sentezi ----------------
_rng = np.random.default_rng(3)


def _kick(dur=0.32):
    t = np.arange(int(SR * dur)) / SR
    freq = 55 + 90 * np.exp(-t * 28)
    return 0.9 * np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 9)


def _soft_noise(n, hp=10, lp=3):
    """Kaba beyaz gurultu yerine bant sinirli (yumusak) gurultu -- 'cizirti' etkisi olmasin."""
    noise = _rng.standard_normal(n)
    noise = noise - np.convolve(noise, np.ones(hp) / hp, mode="same")   # basi al
    return np.convolve(noise, np.ones(lp) / lp, mode="same")            # tizi yumusat


def _clap(dur=0.18):
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 26)
    for k in (0.0, 0.010, 0.020):  # el cirpmanin "cift vurus" hissi
        env += 0.5 * np.exp(-np.clip(t - k, 0, None) * 170) * (t >= k)
    return 0.16 * _soft_noise(n, hp=12, lp=4) * env


def _hat(dur=0.05):
    n = int(SR * dur)
    return 0.035 * _soft_noise(n, hp=6, lp=3) * np.exp(-np.arange(n) / SR * 80)


def _bass(midi, dur):
    t = np.arange(int(SR * dur)) / SR
    f = music.midi_to_freq(midi)
    sig = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    return 0.28 * sig * np.minimum(1, t / 0.01) * np.exp(-t * 2.2)


def _bell(midi, dur, vel=0.18):
    t = np.arange(int(SR * dur)) / SR
    f = music.midi_to_freq(midi)
    sig = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 8)
    return vel * sig * np.exp(-t * 3.5) * np.minimum(1, t / 0.005)


def arrangement(key: str, n_lines: int, lead_vel: float = 0.10):
    """Muzik altyapisi: 1 olcu giris + satirlar + kapanis vurusu.
    Donus: (ses, satir_baslangiclari_sn, beat_sn, toplam_sn)"""
    m = MELODIES[key]
    beat = 60.0 / m["bpm"]
    lines = (m["lines"] * 2)[:n_lines]
    chords = (m["chords"] * 2)[:n_lines]
    intro = 4 * beat
    total = intro + 8 * beat * len(lines) + 2 * beat
    buf = np.zeros(int(SR * total) + SR)
    n_beats = int(total / beat)
    for b in range(n_beats):  # davul: kick 1&3, clap 2&4, hihat sekizlik
        t0 = b * beat
        if b % 2 == 0:
            music._add(buf, _kick(), t0)
        else:
            music._add(buf, _clap(), t0)
        music._add(buf, _hat(), t0)
        music._add(buf, _hat() * 0.6, t0 + beat / 2)
    line_starts = []
    for li, (notes, chs) in enumerate(zip(lines, chords)):
        start = intro + li * 8 * beat
        line_starts.append(start)
        for ci, ch in enumerate(chs):  # akor + bas (2 vurusta bir)
            t0 = start + ci * 2 * beat
            music._add(buf, music._pad(ch, 2 * beat, 0.07), t0)
            music._add(buf, _bass(ch[0] - 24, 2 * beat), t0)
            music._add(buf, _bass(ch[0] - 24, beat) * 0.7, t0 + beat)
        t = start  # melodiyi zil sesiyle hafifce destekle (vokali tutturur)
        for midi, beats in notes:
            music._add(buf, _bell(midi + 12, min(beats * beat, 0.9), vel=lead_vel), t)
            t += beats * beat
    for ch_t in range(4):  # giris olcusunde akor
        music._add(buf, music._pad(C, beat, 0.06), ch_t * beat)
    music._add(buf, _kick(), total - 2 * beat)
    music._add(buf, music._pad(C, 2 * beat, 0.10), total - 2 * beat)
    return buf[: int(SR * total)], line_starts, beat, total, lines
