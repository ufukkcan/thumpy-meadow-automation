"""
SARKI TESTI v5 (Ana sesiyle, D'nin ritim hizalamasi + daha kaliteli ses):
  E) Perde dogrudan seslendirme motorunda uretilir (her kelime notasina yakin perdede),
     kucuk duzeltmeler Rubber Band R3 ile      -> out/sing_test_E_native_pitch.mp3
  F) D'nin aynisi, ama perde kaydirma eski motor yerine kaliteli R3 motoruyla
                                                -> out/sing_test_F_r3_engine.mp3
Ikisinde de vokale hafif yanki ve tiz parazit yumusatma uygulanir. Hicbir yere yukleme yapmaz.
"""
import subprocess
from pathlib import Path

import numpy as np

import music
import rhythmic
import singer
import songs

VOICE = "en-US-AnaNeural"
OUT = Path("out")
OUT.mkdir(exist_ok=True)

SONGS = [
    ("twinkle", ["Apple, banana, so sweet", "Red and yellow, what a treat",
                 "Grapes are purple, pears are green", "Yummy fruits, the best I've seen",
                 "Apple, banana, so sweet", "Red and yellow, what a treat"]),
    ("london", ["Let us count the apples now", "one, two, three, one, two, three",
                "Let us count the apples now", "one, two, three, four"]),
]


def soften_highs(x: np.ndarray, cutoff: float = 9500.0) -> np.ndarray:
    """Sikistirilmis ses kaynagindaki tiz 'cizirti'yi yumusakca alcaltir."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / music.SR)
    gain = 1 / np.sqrt(1 + (f / cutoff) ** 6)
    return np.fft.irfft(spec * gain, len(x))


def render_song(key, lyrics, mode, melody):
    backing, starts, beat, total, lines = songs.arrangement(key, len(lyrics), lead_vel=0.20)
    voice = np.zeros_like(backing)
    for li, (text, notes) in enumerate(zip(lyrics, lines)):
        line = rhythmic.render_line(text, notes, beat, VOICE, melody=melody, mode=mode, engine="r3")
        music._add(voice, line, max(0.0, starts[li] - rhythmic.LEAD))
    voice = singer.vocal_fx(soften_highs(voice), reverb=0.10, chorus=0.12)
    return backing * 0.7 + voice * 0.95


if __name__ == "__main__":
    for name, mode, melody in (("E_native_pitch", "native", 0.7), ("F_r3_engine", "line", 0.5)):
        print(f"--- {name} ---")
        parts = []
        for key, lyrics in SONGS:
            parts += [render_song(key, lyrics, mode, melody), np.zeros(music.SR)]
        wav = OUT / f"sing_test_{name}.wav"
        music.write_wav(str(wav), np.concatenate(parts))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-b:a", "192k",
                        str(OUT / f"sing_test_{name}.mp3")], check=True)
        print(f"out/sing_test_{name}.mp3 hazir")
