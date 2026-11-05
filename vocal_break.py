"""
Muzik molasi (uretim): kidsong enstrumantal duzenleme + Hanami vokali (sing.py).

- Her molaya sirayla bir kamu mali melodi atanir (ORDER). Satir sayisi = melodinin satir sayisi,
  satir basina hece sayisi = melodideki nota sayisi (Claude'a bu kalip verilir).
- Ses: stereo uretilir, bolum ses hatti mono oldugu icin tek kanala indirilir.
- Karaoke: kelime baslangiclari nota izgarasindan (ses uretmeden de hesaplanir).
- Agir bagimliliklar (torch, onnxruntime, librosa ...) yalnizca ses uretilecegi zaman kurulur;
  boylece 5 dakikalik kontrol calistirmalari yavaslamaz.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

import kidsong
import sing
import songs

ORDER = ["twinkle", "london", "mary", "jacques"]
SPEAKER = "Root"
LEAD = 0.45            # vokal varken melodi enstrumanlarinin kazanci
NAMES = {"twinkle": "Twinkle Twinkle", "london": "London Bridge", "mary": "Mary Had a Little Lamb",
         "jacques": "Frere Jacques"}

_singer = None
_vocoder = None


def melody_for(k: int) -> str:
    return ORDER[k % len(ORDER)]


def pattern(key: str) -> list[int]:
    """Satir basina hece (nota) sayisi."""
    return songs.syllable_pattern(key)


def counter(word: str) -> int:
    return sing.syllable_count(word) or songs.count_syllables(word)


def word_timings(lines: list[str], key: str) -> list[tuple[int, int, float]]:
    """[(satir, kelime_index, baslangic_sn)] -- kelime_index, lines[satir].split() sirasina gore."""
    beat, starts, _ = kidsong.timing(key, len(lines))
    melody = (songs.MELODIES[key]["lines"] * 2)[:len(lines)]
    out = []
    for li, (text, notes, ls) in enumerate(zip(lines, melody, starts)):
        t, note_t = ls, []
        for _, b in notes:
            note_t.append(t)
            t += b * beat
        wi, ni = 0, 0
        for word, wnotes in songs.map_words_to_notes(text, notes, counter=counter):
            for _ in word.split():          # birlestirilmis kelimeler ayni anda vurgulanir
                out.append((li, wi, note_t[min(ni, len(note_t) - 1)]))
                wi += 1
            ni += len(wnotes)
    return out


def duration(lines: list[str], key: str) -> float:
    return kidsong.timing(key, len(lines))[2]


def _ensure_deps() -> None:
    try:
        import huggingface_hub, librosa, matplotlib, onnxruntime, scipy, torch, tqdm, yaml  # noqa: F401
        return
    except ImportError:
        pass
    req = Path(__file__).resolve().parent / "requirements-vocal.txt"
    for cmd in ([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)],
                [sys.executable, "-m", "pip", "install", "-q", "torch==2.5.1",
                 "--index-url", "https://download.pytorch.org/whl/cpu"]):
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError("Vokal bagimliliklari kurulamadi:\n" + "\n".join(p.stderr.splitlines()[-20:]))


def _models():
    global _singer, _vocoder
    if _singer is None:
        _ensure_deps()
        import samples
        samples.ensure()
        _singer = sing.Singer(speaker=SPEAKER)
        _vocoder = sing.Vocoder()
    return _singer, _vocoder


def mix(music: np.ndarray, vocal: np.ndarray) -> np.ndarray:
    """Vokal: hafif yanki, muzigin ~4 dB ustunde; vokal varken muzik ~3 dB kisilir. Donus: stereo."""
    vocal = vocal + 0.15 * kidsong._reverb(vocal, 0.9, seed=7)
    env = np.convolve(np.abs(vocal), np.ones(2205) / 2205, mode="same")
    active = env > 0.1 * env.max()
    m_rms = np.sqrt(np.mean(music[active] ** 2)) or 1e-6
    v_rms = np.sqrt(np.mean(vocal[active] ** 2)) or 1e-6
    vocal = vocal * (m_rms / v_rms) * 10 ** (4 / 20)
    duck = 1 - (1 - 10 ** (-3 / 20)) * np.clip(env / (0.1 * env.max()), 0, 1)
    duck = np.convolve(duck, np.ones(4410) / 4410, mode="same")
    return music * duck[:, None] + vocal[:, None] * np.array([0.71, 0.71])


def render(lines: list[str], key: str) -> tuple[np.ndarray, list, float]:
    """Donus: (mono ses, karaoke zamanlari, sure_sn)."""
    singer, voc = _models()
    song = kidsong.arrange(key, len(lines), lead=LEAD)
    melody = (songs.MELODIES[key]["lines"] * 2)[:len(lines)]
    mel, f0, ph, slots = singer.render_mel(lines, melody, song["line_starts"], song["beat"])
    y = voc(voc.ds_to_bigvgan(mel, singer.fmin, singer.fmax))
    n = len(song["audio"])
    y = np.pad(y, (0, max(0, n - len(y))))[:n]
    mono = mix(song["audio"], y).mean(axis=1)
    print(f"Muzik molasi ({NAMES[key]}): {n / sing.SR:.1f} sn, akustik {singer.timing['acoustic_s']:.0f} sn, "
          f"vocoder {voc.timing['vocoder_s']:.0f} sn")
    return mono, word_timings(lines, key), n / sing.SR
