"""
SARKI TESTI v5 (Ana sesiyle, D'nin ritim hizalamasi + daha kaliteli ses):
  E) Perde dogrudan seslendirme motorunda uretilir (her kelime notasina yakin perdede),
     kucuk duzeltmeler Rubber Band R3 ile      -> out/sing_test_E_native_pitch.mp3
  F) D'nin aynisi, ama perde kaydirma eski motor yerine kaliteli R3 motoruyla
                                                -> out/sing_test_F_r3_engine.mp3
Ikisinde de: legato (heceler bagli), kucuk kelimeler dogal soylenisle, netlik ayari, azaltilmis yanki,
Ana soylerken muzik hafifce kisilir. Hicbir yere yukleme yapmaz.
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


def voice_eq(x: np.ndarray, cutoff: float = 9500.0) -> np.ndarray:
    """Netlik: konusmanin anlasilirligini tasiyan 2-5 kHz bolgesi +3 dB, 120 Hz alti temizlenir,
    sikistirilmis kaynaktaki tiz 'cizirti' yumusakca alcaltilir."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / music.SR)
    lowcut = 1 / np.sqrt(1 + (120 / np.maximum(f, 1)) ** 4)
    highcut = 1 / np.sqrt(1 + (f / cutoff) ** 6)
    presence = 1 + 0.41 * np.exp(-((np.log2(np.maximum(f, 1) / 3200)) ** 2) / (2 * 0.6 ** 2))  # ~+3 dB
    return np.fft.irfft(spec * lowcut * highcut * presence, len(x))


def duck(backing: np.ndarray, voice: np.ndarray, depth: float = 0.4) -> np.ndarray:
    """Ana soylerken muzigi ~4 dB kisar (sozler net duyulsun)."""
    env = np.convolve(np.abs(voice), np.ones(2205) / 2205, mode="same")  # 50 ms
    env = env / (env.max() or 1)
    gain = 1 - depth * np.clip(env / 0.15, 0, 1)
    return backing * np.convolve(gain, np.ones(4410) / 4410, mode="same")  # yumusak gecis


def render_song(key, lyrics, mode, melody):
    backing, starts, beat, total, lines = songs.arrangement(key, len(lyrics), lead_vel=0.12)
    voice = np.zeros_like(backing)
    for li, (text, notes) in enumerate(zip(lyrics, lines)):
        line = rhythmic.render_line(text, notes, beat, VOICE, melody=melody, mode=mode, engine="r3")
        music._add(voice, line, max(0.0, starts[li] - rhythmic.LEAD))
    voice = singer.vocal_fx(voice_eq(voice), reverb=0.06, chorus=0.0)
    return duck(backing, voice) * 0.7 + voice * 1.0


if __name__ == "__main__":
    for name, mode, melody in (("G_legato", "native", 0.7),):
        print(f"--- {name} ---")
        parts = []
        for key, lyrics in SONGS:
            parts += [render_song(key, lyrics, mode, melody), np.zeros(music.SR)]
        wav = OUT / f"sing_test_{name}.wav"
        music.write_wav(str(wav), np.concatenate(parts))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-b:a", "192k",
                        str(OUT / f"sing_test_{name}.mp3")], check=True)
        print(f"out/sing_test_{name}.mp3 hazir")
