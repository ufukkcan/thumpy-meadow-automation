"""
Dogal sesle ritmik soyleme (v2).

1) Ana her satiri DOGAL AKISIYLA tek seferde soyler; edge-tts kelime sinirlarini verir.
2) Cok heceli kelimeler enerji zarfindan HECELERINE bolunur; her hece kendi notasina yerlesir.
3) Hizalama hecenin basina degil UNLU BASLANGICINA yapilir (kulak vurusu orada algilar).
4) Uzun notalarda hece en fazla %35 uzatilir (sarkiya yaklasir), sigmiyorsa hafif hizlandirilir.
   Islem Rubber Band ile, perde ve ses karakteri korunarak; kenar bozulmasi olmasin diye bosluk eklenir.
5) Her parcanin basinda/sonunda yumusak gecis var (kesik noktalarda 'cit' sesi olmasin).
6) melody>0: dogal tonlama korunur, ortalama perde notaya dogru 'melody' oraninda kaydirilir.
"""
import asyncio
import subprocess

import edge_tts
import numpy as np
import pyworld as pw

import music
import songs

SR = music.SR
FADE_MS = 10
LEAD = 0.35    # satir basinda on bosluk: ilk hecenin unsuzu vurustan once baslayabilsin
LEGATO = 0.80  # her hece notasinin ~%80'ini doldurur (kesik kesik degil, bagli soyleme)


def _decode(mp3_bytes: bytes) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         input=mp3_bytes, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768


async def _stream(text: str, voice: str, rate: str, pitch: str = "+0Hz"):
    try:
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    except TypeError:
        comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    audio, bounds = bytearray(), []
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            bounds.append((chunk["offset"] / 1e7, chunk["duration"] / 1e7, chunk["text"]))
    return bytes(audio), bounds


def _fade(x: np.ndarray, ms: float = FADE_MS) -> np.ndarray:
    x = x.copy()
    f = min(len(x) // 3, int(ms / 1000 * SR))
    if f > 1:
        x[:f] *= np.linspace(0, 1, f) ** 2
        x[-f:] *= np.linspace(1, 0, f) ** 2
    return x


def _trim(a: np.ndarray, thr: float = 0.015) -> np.ndarray:
    nz = np.where(np.abs(a) > thr)[0]
    return a[max(0, nz[0] - 150): nz[-1] + 300] if len(nz) else a


def line_word_clips(text: str, voice: str, rate: str = "+0%") -> list[np.ndarray]:
    words = text.split()
    audio, bounds = asyncio.run(_stream(text, voice, rate))
    x = _decode(audio)
    if len(bounds) == len(words):
        clips = []
        for i, (off, dur, _) in enumerate(bounds):
            a = int(max(0.0, off - 0.02) * SR)
            end_t = bounds[i + 1][0] if i + 1 < len(bounds) else off + dur + 0.12
            b = int(min(len(x) / SR, end_t) * SR)
            clips.append(_fade(_trim(x[a:b])))
        print(f"   [kelime sinirlari OK] {text}")
        return clips
    print(f"   [yedek yol: {len(bounds)} sinir / {len(words)} kelime] {text}")
    return [_fade(_trim(_decode(asyncio.run(_stream(w.strip(",.!?"), voice, rate))[0]))) for w in words]


def _envelope(x: np.ndarray, frame: int = 441) -> np.ndarray:
    n = len(x) // frame
    if n == 0:
        return np.zeros(1)
    e = np.sqrt(np.mean(x[: n * frame].reshape(n, frame) ** 2, axis=1))
    return np.convolve(e, np.ones(5) / 5, mode="same")


def split_syllables(x: np.ndarray, k: int) -> list[np.ndarray] | None:
    """Kelimeyi enerji tepelerinden k heceye boler. Basaramazsa None."""
    if k <= 1:
        return [x]
    env = _envelope(x)
    peaks = [i for i in range(1, len(env) - 1) if env[i] >= env[i - 1] and env[i] > env[i + 1]
             and env[i] > 0.25 * env.max()]
    chosen = []
    for p in sorted(peaks, key=lambda i: -env[i]):
        if all(abs(p - c) >= 8 for c in chosen):  # tepeler arasi en az 80 ms
            chosen.append(p)
        if len(chosen) == k:
            break
    if len(chosen) < k:
        return None
    chosen.sort()
    cuts = [int(np.argmin(env[a:b]) + a) * 441 for a, b in zip(chosen[:-1], chosen[1:])]
    edges = [0] + cuts + [len(x)]
    return [_fade(x[a:b], 8) for a, b in zip(edges[:-1], edges[1:])]


def _vowel_onset(x: np.ndarray) -> float:
    """Unlunun basladigi an (sn). Perdeli (titresimli) ve yeterince guclu ilk kare:
    's', 't', 'k' gibi perdesiz unsuzler atlanir -> kulak vurusu unlunun basinda duyar."""
    xc = np.ascontiguousarray(x, dtype=np.float64)
    if len(xc) > SR * 0.04:
        f0, t = pw.dio(xc, SR, frame_period=5, f0_floor=90, f0_ceil=650)
        hop = int(SR * 0.005)
        n = min(len(f0), len(xc) // hop)
        if n > 0:
            e = np.sqrt(np.mean(xc[: n * hop].reshape(n, hop) ** 2, axis=1))
            ok = np.where((f0[:n] > 0) & (e >= 0.2 * e.max()))[0]
            if len(ok):
                return float(ok[0] * 0.005)
    env = _envelope(x)  # yedek: enerji
    idx = np.where(env >= 0.35 * env.max())[0]
    return float(idx[0] * 441 / SR) if len(idx) else 0.0


def _rubberband(x: np.ndarray, tempo: float = 1.0, pitch: float = 1.0) -> np.ndarray:
    if abs(tempo - 1) < 0.01 and abs(pitch - 1) < 0.005:
        return x
    pad = int(0.12 * SR)  # kenar bozulmasina karsi bosluk
    xp = np.concatenate([np.zeros(pad), x, np.zeros(pad)])
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "pipe:0",
         "-af", f"rubberband=tempo={tempo:.4f}:pitch={pitch:.4f}:formant=preserved:transients=mixed:window=standard",
         "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"],
        input=xp.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    y = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    p_out = int(pad / tempo)
    want = int(len(x) / tempo)
    return _fade(y[p_out: p_out + want])


def _write_wav16(path: str, x: np.ndarray) -> None:
    import wave
    data = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())


def _read_wav16(path: str) -> np.ndarray:
    import wave
    with wave.open(path, "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768


def rb3(x: np.ndarray, tempo: float = 1.0, semitones: float = 0.0) -> np.ndarray:
    """Rubber Band R3 (finer) motoru + formant koruma: insan sesinde en temiz zaman/perde degisimi."""
    if abs(tempo - 1) < 0.01 and abs(semitones) < 0.1:
        return x
    import os
    import tempfile
    pad = int(0.12 * SR)
    xp = np.concatenate([np.zeros(pad), x, np.zeros(pad)])
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "in.wav"), os.path.join(d, "out.wav")
        _write_wav16(a, xp)
        subprocess.run(["rubberband", "-q", "-3", "-F", "-T", f"{tempo:.4f}", "-p", f"{semitones:.3f}", a, b],
                       check=True, capture_output=True)
        y = _read_wav16(b)
    p_out = int(pad / tempo)
    return _fade(y[p_out: p_out + int(len(x) / tempo)])


def native_word(word: str, voice: str, target_hz: float, strength: float, _cache={}) -> tuple[np.ndarray, float]:
    """Kelimeyi, perdesi notaya yakin olacak sekilde DOGRUDAN seslendirme motoruna urettirir.
    Donus: (ses, uygulanan perde orani). Perdeyi sonradan bozmaktan cok daha dogal."""
    w = word.lower().strip(",.!?")
    if (w, voice) not in _cache:
        _cache[(w, voice)] = _fade(_trim(_decode(asyncio.run(_stream(w, voice, "+0%"))[0])))
    base = _cache[(w, voice)]
    med = _median_hz(base) or 280.0
    offset = (target_hz - med) * strength
    offset = float(np.clip(offset, -0.4 * med, 0.6 * med))
    if abs(offset) < 3:
        return base, 1.0
    key = (w, voice, int(round(offset)))
    if key not in _cache:
        audio, _ = asyncio.run(_stream(w, voice, "+0%", pitch=f"{int(round(offset)):+d}Hz"))
        _cache[key] = _fade(_trim(_decode(audio)))
    return _cache[key], (med + offset) / med


FUNCTION_WORDS = {"a", "an", "the", "of", "to", "and", "for", "as", "at", "in", "on", "or", "is"}


def sustain(seg: np.ndarray, target_s: float, max_factor: float = 3.2) -> np.ndarray:
    """Heceyi hedef sureye uzatir: SADECE unlu (perdeli) kisim uzatilir, bastaki ve sondaki
    unsuzler (s, t, k, p...) dogal hizinda kalir -> hem sarki gibi bagli, hem anlasilir."""
    xc = np.ascontiguousarray(seg, dtype=np.float64)
    need = target_s * SR
    if len(xc) >= need or len(xc) < SR * 0.05:
        return seg
    f0, t = pw.dio(xc, SR, frame_period=5, f0_floor=90, f0_ceil=650)
    hop = int(SR * 0.005)
    n = min(len(f0), len(xc) // hop)
    e = np.sqrt(np.mean(xc[: n * hop].reshape(n, hop) ** 2, axis=1)) if n else np.zeros(1)
    voiced = np.where((f0[:n] > 0) & (e >= 0.15 * e.max()))[0] if n else []
    if len(voiced) < 4:
        return seg
    a, b = int(voiced[0] * hop), int((voiced[-1] + 1) * hop)
    onset, vowel, coda = xc[:a], xc[a:b], xc[b:]
    factor = float(np.clip((need - len(onset) - len(coda)) / max(len(vowel), 1), 1.0, max_factor))
    if factor < 1.05:
        return seg
    long_vowel = rb3(vowel, tempo=1.0 / factor)
    x = 64  # birlesme noktalarinda cok kisa capraz gecis
    parts = [onset, long_vowel, coda]
    out = parts[0]
    for p in parts[1:]:
        if len(out) > x and len(p) > x:
            out = np.concatenate([out[:-x], out[-x:] * np.linspace(1, 0, x) + p[:x] * np.linspace(0, 1, x), p[x:]])
        else:
            out = np.concatenate([out, p])
    return _fade(out)


def _median_hz(x: np.ndarray) -> float | None:
    if len(x) < SR * 0.05:
        return None
    xc = np.ascontiguousarray(x)
    f0, t = pw.dio(xc, SR, frame_period=5, f0_floor=90, f0_ceil=650)
    f0 = pw.stonemask(xc, f0, t, SR)
    v = f0[f0 > 0]
    return float(np.median(v)) if len(v) > 3 else None


def render_line(text: str, notes: list[tuple], beat: float, voice: str, melody: float = 0.0,
                mode: str = "line", engine: str = "r3") -> np.ndarray:
    """Donus: satirin sesi; basinda LEAD sn on bosluk var -> satir_baslangici - LEAD konumuna eklenmeli.
    mode="line":   satir dogal akisiyla soylenir, kelimelere bolunur (perde sonradan 'melody' oraninda kaydirilir)
    mode="native": her kelime perdesi notaya yakin olacak sekilde dogrudan seslendirme motorunda uretilir
    engine="r3":   zaman/perde islemleri Rubber Band R3 (en kaliteli) ile; "r2": eski ffmpeg filtresi"""
    word_notes = songs.map_words_to_notes(text, notes)
    native_ratio = []
    if mode == "native":
        line_clips = line_word_clips(text, voice)   # kucuk kelimelerin dogal soylenisi icin
        clips, ti = [], 0
        for w, wn in word_notes:
            target = 440.0 * 2 ** ((wn[0][0] - 69) / 12)
            toks = w.split()
            parts, all_func = [], True
            for tok in toks:
                if tok.lower().strip(",.!?'") in FUNCTION_WORDS and ti < len(line_clips):
                    parts.append(line_clips[ti])          # "a" -> "uh", "the" -> "thuh" (dogal)
                else:
                    parts.append(native_word(tok, voice, target, max(melody, 0.7))[0])
                    all_func = False
                ti += 1
            clips.append(np.concatenate(parts))
            native_ratio.append(not all_func)  # tamamen kucuk kelimeyse perde sonradan ayarlanir
    else:
        raw_clips = line_word_clips(text, voice)
        clips, i = [], 0
        for w, _ in word_notes:  # birlestirilmis kelimeler (or. "a b") icin parcalari birlestir
            n_tok = len(w.split())
            clips.append(np.concatenate(raw_clips[i:i + n_tok]) if raw_clips[i:i + n_tok] else np.zeros(441))
            i += n_tok
            native_ratio.append(False)

    out = np.zeros(int((9 * beat + LEAD) * SR) + SR)
    t_note, prev_end = LEAD, 0.0   # zamanlar LEAD kadar kaydirilmis; cagiran satiri LEAD erken yerlestirir
    for (word, wnotes), clip, is_native in zip(word_notes, clips, native_ratio):
        segs = split_syllables(clip, len(wnotes)) or [clip] + [None] * (len(wnotes) - 1)
        first_midi = wnotes[0][0]
        for seg, (midi, beats) in zip(segs, wnotes):
            slot = beats * beat
            if seg is None or len(seg) < 200:
                t_note += slot
                continue
            seg_len = len(seg) / SR
            if seg_len > slot * 0.95:                        # sigmiyor: hafif hizlandir
                tempo = min(1.6, seg_len / (slot * 0.95))
            else:
                tempo = 1.0                                  # uzatma asagida 'sustain' ile (sadece unlu)
            semis = 0.0
            if is_native:      # ilk hece motorda zaten notaya yakin; sonraki heceler icin kucuk fark
                semis = float(np.clip((midi - first_midi) * 0.7, -3, 3))
            elif melody > 0:
                med = _median_hz(seg)
                if med:
                    target = 440.0 * 2 ** ((midi - 69) / 12)
                    semis = float(np.clip(12 * np.log2(target / med) * melody, -4, 4))
            if engine == "r3":
                y = rb3(seg, tempo, semis)
            else:
                y = _rubberband(seg, tempo, 2 ** (semis / 12))
            y = sustain(y, slot * LEGATO)                    # legato: notanin ~%80'ini doldur
            start = max(0.0, t_note - _vowel_onset(y))       # unlu basini vurusa hizala
            if start < prev_end:                             # oncekinin kuyrugu tasiyorsa: ERTELEME,
                a = max(0, int(start * SR) - int(0.012 * SR))  # onceki hecenin kuyrugunu yumusakca kes
                b = int(prev_end * SR) + 1
                k = int(start * SR) - a
                if k > 1:
                    out[a:a + k] *= np.linspace(1, 0, k) ** 2
                out[a + max(k, 0): b] = 0.0
            music._add(out, y, start)
            prev_end = start + len(y) / SR
            t_note += slot
    return out[: int((8 * beat + LEAD) * SR)]
