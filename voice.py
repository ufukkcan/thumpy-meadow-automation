"""
Anlatim cumlelerini edge-tts ile seslendirir ve numpy dizisine cevirir
(muzikle karistirabilmek icin).
"""
import asyncio
import subprocess

import edge_tts
import numpy as np

SR = 44100


async def _save(text: str, voice: str, path: str, rate: str) -> None:
    await edge_tts.Communicate(text, voice, rate=rate).save(path)


def synthesize(text: str, voice: str, mp3_path: str, rate: str = "-10%") -> np.ndarray:
    """Metni seslendirir; -1..1 araliginda mono ses ornekleri dondurur.
    rate -10%: kucuk cocuklar icin biraz yavas ve net konusma."""
    asyncio.run(_save(text, voice, mp3_path, rate))
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", mp3_path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
