"""
Dogal sesle ritmik soyleme.

1) Ana her satiri DOGAL AKISIYLA tek seferde soyler (tonlama dogal kalir).
2) edge-tts her kelimenin baslangic/bitis zamanini verir (WordBoundary); satir kelimelerine bolunur.
3) Her kelime kendi notasinin vurusuna yerlestirilir. Nota suresine sigmiyorsa Rubber Band ile
   (perdeyi ve ses karakterini koruyarak) hafifce hizlandirilir; yavaslatma yapilmaz.
4) melody>0 ise: kelimenin dogal tonlamasi aynen korunur, sadece ortalama perdesi notaya dogru
   'melody' oraninda kaydirilir (formant korunur -> cocuk sesi karakteri bozulmaz).
Kelime sinirlari alinamazsa kelimeler tek tek seslendirilir (yedek yol).
"""
import asyncio
import subprocess

import edge_tts
import numpy as np
import pyworld as pw

import music
import songs

SR = music.SR


def _decode(mp3_bytes: bytes) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         input=mp3_bytes, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768


async def _stream(text: str, voice: str, rate: str):
    try:
        comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    except TypeError:  # eski surumlerde bu parametre yok, kelime sinirlari zaten gelir
        comm = edge_tts.Communicate(text, voice, rate=rate)
    audio, bounds = bytearray(), []
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            bounds.append((chunk["offset"] / 1e7, chunk["duration"] / 1e7, chunk["text"]))
    return bytes(audio), bounds


def _trim(a: np.ndarray, thr: float = 0.015) -> np.ndarray:
    nz = np.where(np.abs(a) > thr)[0]
    return a[max(0, nz[0] - 150): nz[-1] + 300] if len(nz) else a


def line_word_clips(text: str, voice: str, rate: str = "+0%") -> list[np.ndarray]:
    """Satirdaki her kelime icin dogal ses parcasi (satirin akisindan kesilmis)."""
    words = text.split()
    audio, bounds = asyncio.run(_stream(text, voice, rate))
    x = _decode(audio)
    if len(bounds) == len(words):
        clips = []
        for i, (off, dur, _) in enumerate(bounds):
            a = int(max(0.0, off - 0.02) * SR)
            end_t = bounds[i + 1][0] if i + 1 < len(bounds) else off + dur + 0.12
            b = int(min(len(x) / SR, end_t) * SR)
            clips.append(_trim(x[a:b]))
        print(f"   [kelime sinirlari OK] {text}")
        return clips
    print(f"   [yedek yol: {len(bounds)} sinir / {len(words)} kelime] {text}")
    out = []
    for w in words:  # yedek: kelimeleri tek tek seslendir
        aud, _ = asyncio.run(_stream(w.strip(",.!?"), voice, rate))
        out.append(_trim(_decode(aud)))
    return out


def _rubberband(x: np.ndarray, tempo: float = 1.0, pitch: float = 1.0) -> np.ndarray:
    if abs(tempo - 1) < 0.01 and abs(pitch - 1) < 0.005:
        return x
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "pipe:0",
         "-af", f"rubberband=tempo={tempo:.4f}:pitch={pitch:.4f}:formant=preserved:transients=crisp",
         "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"],
        input=x.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def _median_hz(x: np.ndarray) -> float | None:
    if len(x) < SR * 0.05:
        return None
    f0, t = pw.dio(np.ascontiguousarray(x), SR, frame_period=5, f0_floor=90, f0_ceil=650)
    f0 = pw.stonemask(np.ascontiguousarray(x), f0, t, SR)
    v = f0[f0 > 0]
    return float(np.median(v)) if len(v) > 3 else None


def render_line(text: str, notes: list[tuple], beat: float, voice: str, melody: float = 0.0) -> np.ndarray:
    """Satiri ritme oturtur. Donus: satir uzunlugunda (8 vurus) ses."""
    word_notes = songs.map_words_to_notes(text, notes)
    clips = line_word_clips(text, voice)
    if len(clips) != len(word_notes):  # birlestirilmis kelime olduysa yedek
        clips = clips[: len(word_notes)] + [np.zeros(1)] * max(0, len(word_notes) - len(clips))
    out = np.zeros(int(8 * beat * SR) + SR)
    t = 0.0
    for (word, wnotes), clip in zip(word_notes, clips):
        slot = sum(b for _, b in wnotes) * beat
        avail = max(0.12, slot - 0.03)
        clip_len = len(clip) / SR
        tempo = min(1.7, clip_len / avail) if clip_len > avail else 1.0
        pitch = 1.0
        if melody > 0:
            med = _median_hz(clip)
            if med:
                target = 440.0 * 2 ** ((wnotes[0][0] - 69) / 12)
                shift = float(np.clip(12 * np.log2(target / med) * melody, -4, 4))
                pitch = 2 ** (shift / 12)
        y = _rubberband(clip, tempo, pitch)
        if len(y) / SR > slot:  # hala sigmiyorsa yumusakca kes
            y = y[: int(slot * SR)]
            f = min(len(y) // 4, int(0.02 * SR))
            if f > 0:
                y[-f:] *= np.linspace(1, 0, f)
        music._add(out, y, t)
        t += slot
    return out[: int(8 * beat * SR)]
