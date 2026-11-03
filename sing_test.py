"""
SARKI TESTI (iki versiyon, Ana sesiyle):
  A) gelistirilmis sarki soyleme (out/sing_test_A_singing.mp3)
  B) ritmik anlatim: Ana dogal sesiyle sozleri ritme oturtur, melodiyi enstruman calar
     (out/sing_test_B_rhythmic.mp3)
Hicbir yere yukleme yapmaz.
"""
import asyncio
import subprocess
from pathlib import Path

import edge_tts
import numpy as np

import music
import singer
import songs

VOICE = "en-US-AnaNeural"
OUT = Path("out")
OUT.mkdir(exist_ok=True)
_cache = {}


def _tts_raw(text: str, rate: str = "+0%") -> np.ndarray:
    mp3 = OUT / "tmp.mp3"
    asyncio.run(edge_tts.Communicate(text, VOICE, rate=rate).save(str(mp3)))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp3), "-f", "s16le", "-ac", "1",
                          "-ar", str(singer.SR), "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768
    nz = np.where(np.abs(a) > 0.02)[0]
    return a[max(0, nz[0] - 200): nz[-1] + 200] if len(nz) else a


def tts_word(word: str) -> np.ndarray:
    key = word.lower().strip(",.!?")
    if key not in _cache:
        _cache[key] = _tts_raw(key)
    return _cache[key]


def tts_line_fitted(text: str, target_s: float) -> np.ndarray:
    """Satiri dogal sesle, verilen sureye oturacak hizda okur (perdeye dokunmadan)."""
    natural = _tts_raw(text)
    ratio = (len(natural) / singer.SR) / target_s
    pct = int(round(max(-25, min(35, (ratio - 1) * 100))))
    return _tts_raw(text, rate=f"{pct:+d}%") if abs(pct) >= 3 else natural


def version_a(key, lyrics):
    backing, starts, beat, total, lines = songs.arrangement(key, len(lyrics), lead_vel=0.10)
    vocal = np.zeros_like(backing)
    for li, (text, notes) in enumerate(zip(lyrics, lines)):
        audio, _ = singer.sing_line(songs.map_words_to_notes(text, notes), beat, tts_word)
        music._add(vocal, audio, starts[li])
    return backing * 0.75 + singer.vocal_fx(vocal) * 0.55


def version_b(key, lyrics):
    backing, starts, beat, total, lines = songs.arrangement(key, len(lyrics), lead_vel=0.24)
    voice = np.zeros_like(backing)
    for li, text in enumerate(lyrics):
        music._add(voice, tts_line_fitted(text, 6 * beat), starts[li])
    return backing * 0.7 + voice * 0.9


SONGS = [
    ("twinkle", ["Apple, banana, so sweet", "Red and yellow, what a treat",
                 "Grapes are purple, pears are green", "Yummy fruits, the best I've seen",
                 "Apple, banana, so sweet", "Red and yellow, what a treat"]),
    ("london", ["Let us count the apples now", "one, two, three, one, two, three",
                "Let us count the apples now", "one, two, three, four"]),
]

if __name__ == "__main__":
    for name, fn in (("A_singing", version_a), ("B_rhythmic", version_b)):
        parts = []
        for key, lyrics in SONGS:
            parts += [fn(key, lyrics), np.zeros(music.SR)]
        wav = OUT / f"sing_test_{name}.wav"
        music.write_wav(str(wav), np.concatenate(parts))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-b:a", "160k",
                        str(OUT / f"sing_test_{name}.mp3")], check=True)
        print(f"out/sing_test_{name}.mp3 hazir")
