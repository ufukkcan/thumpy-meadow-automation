"""
SARKI TESTI v3 (Ana sesiyle, dogal ses + ritim):
  C) Dogal ritmik: satir dogal akisiyla soylenir, her kelime kendi vurusuna yerlesir,
     perdeye dokunulmaz (out/sing_test_C_natural_rhythm.mp3)
  D) C + hafif melodi: kelimelerin perdesi notaya dogru yari yariya kaydirilir,
     dogal tonlama ve ses karakteri korunur (out/sing_test_D_rhythm_melody.mp3)
Hicbir yere yukleme yapmaz.
"""
import subprocess
from pathlib import Path

import numpy as np

import music
import rhythmic
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


def render_song(key, lyrics, melody):
    backing, starts, beat, total, lines = songs.arrangement(key, len(lyrics), lead_vel=0.22)
    voice = np.zeros_like(backing)
    for li, (text, notes) in enumerate(zip(lyrics, lines)):
        music._add(voice, rhythmic.render_line(text, notes, beat, VOICE, melody=melody), starts[li])
    return backing * 0.7 + voice * 0.95


if __name__ == "__main__":
    for name, melody in (("C_natural_rhythm", 0.0), ("D_rhythm_melody", 0.5)):
        print(f"--- {name} ---")
        parts = []
        for key, lyrics in SONGS:
            parts += [render_song(key, lyrics, melody), np.zeros(music.SR)]
        wav = OUT / f"sing_test_{name}.wav"
        music.write_wav(str(wav), np.concatenate(parts))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-b:a", "160k",
                        str(OUT / f"sing_test_{name}.mp3")], check=True)
        print(f"out/sing_test_{name}.mp3 hazir")
