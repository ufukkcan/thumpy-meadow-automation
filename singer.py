"""
Konusmadan sarki (gelistirilmis): her kelime ayri seslendirilir, WORLD vokoder ile
  - perde notaya ayarlanir AMA konusmanin dogal tonlama dalgalanmasi kismen korunur
    (tamamen duz perde "autotune/robot" etkisi yaratir),
  - her notaya yarim ton asagidan kayarak girilir (insan sesindeki dogal "scoop"),
  - uzun notalarda gec baslayan hafif vibrato,
  - unluler uzatilirken spektrum kareleri arasinda yumusak gecis (tekrar eden kare vizultisi yok),
  - unsuz baslangic/bitis dogal hizinda birakilir.
vocal_fx(): cift vokal (chorus) + hafif yanki ile kalan yapaylik maskelenir.
"""
import numpy as np
import pyworld as pw

import music

SR = music.SR
FRAME_MS = 5.0


def _midi_to_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _interp_rows(mat, pos):
    """Kesirli kare indekslerinde satirlar arasi dogrusal gecis."""
    lo = np.floor(pos).astype(int)
    hi = np.minimum(lo + 1, len(mat) - 1)
    w = (pos - lo)[:, None]
    return mat[lo] * (1 - w) + mat[hi] * w


def sing_word(speech, notes, prev_hz=None):
    x = np.ascontiguousarray(speech, dtype=np.float64)
    if len(x) < SR * 0.06:
        x = np.pad(x, (0, int(SR * 0.06) - len(x)))
    f0, t = pw.harvest(x, SR, frame_period=FRAME_MS, f0_floor=90, f0_ceil=650)
    sp = pw.cheaptrick(x, f0, t, SR)
    ap = pw.d4c(x, f0, t, SR)
    n = len(f0)
    voiced = np.where(f0 > 0)[0]
    first, last = (int(voiced[0]), int(voiced[-1])) if len(voiced) else (n // 4, max(n // 4 + 1, 3 * n // 4))
    med = float(np.median(f0[voiced])) if len(voiced) else 250.0

    total_s = sum(d for _, d in notes)
    target = max(4, int(total_s * 1000 / FRAME_MS))
    pre = np.arange(max(0, first - int(120 / FRAME_MS)), first, dtype=float)
    post = np.arange(last + 1, min(n, last + 1 + int(80 / FRAME_MS)), dtype=float)
    body_len = max(2, target - len(pre) - len(post))
    pos = np.concatenate([pre, np.linspace(first, last, body_len), post])

    new_sp = _interp_rows(sp, pos)
    new_ap = _interp_rows(ap, pos)
    src_f0 = np.interp(pos, np.arange(n), f0)
    voiced_mask = np.interp(pos, np.arange(n), (f0 > 0).astype(float)) > 0.5
    if len(voiced) == 0:
        voiced_mask[len(pre): len(pre) + body_len] = True
    # konusmanin dogal dalgalanmasi (medyana gore oran), %35 oraninda korunur
    natural = np.where(src_f0 > 0, (np.maximum(src_f0, 1) / med) ** 0.35, 1.0)

    new_f0 = np.zeros(len(pos))
    durs = np.array([d for _, d in notes], dtype=float)
    bounds = np.concatenate([[0], np.cumsum(durs / durs.sum())]) * body_len
    s0 = len(pre)
    for k, (midi, dur) in enumerate(notes):
        a, b = s0 + int(bounds[k]), s0 + int(bounds[k + 1])
        if b <= a:
            continue
        hz = _midi_to_hz(midi)
        tt = np.arange(b - a) * FRAME_MS / 1000
        start_hz = hz * 2 ** (-0.6 / 12) if prev_hz is None else prev_hz
        scoop = np.clip(tt / 0.07, 0, 1)
        seg = start_hz * (hz / start_hz) ** scoop          # notaya kayarak giris
        if dur > 0.35:                                     # uzun notada hafif vibrato
            depth = np.clip((tt - 0.25) / 0.2, 0, 1) * 0.28
            seg = seg * 2 ** (depth * np.sin(2 * np.pi * 5.2 * tt) / 12)
        new_f0[a:b] = seg
        prev_hz = hz
    new_f0 = np.where(voiced_mask, new_f0 * natural, 0.0)
    new_f0[: len(pre)] = np.where(voiced_mask[: len(pre)], new_f0[: len(pre)], 0)

    y = pw.synthesize(np.ascontiguousarray(new_f0), np.ascontiguousarray(new_sp),
                      np.ascontiguousarray(new_ap), SR, FRAME_MS)
    want = int(total_s * SR)
    y = y[:want] if len(y) >= want else np.pad(y, (0, want - len(y)))
    fade = min(len(y) // 4, int(0.015 * SR))
    if fade > 0:
        y[:fade] *= np.linspace(0, 1, fade)
        y[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(y)) or 1.0
    return 0.9 * y / peak


def sing_line(word_notes, beat_s, tts):
    pieces, starts, t, prev = [], [], 0.0, None
    for word, notes in word_notes:
        secs = [(m, b * beat_s) for m, b in notes]
        dur = sum(d for _, d in secs)
        gap = min(0.035, dur * 0.08)
        secs[-1] = (secs[-1][0], secs[-1][1] - gap)
        pieces.append(np.concatenate([sing_word(tts(word), secs, prev_hz=prev), np.zeros(int(gap * SR))]))
        starts.append(t)
        t += dur
        prev = _midi_to_hz(notes[-1][0])
    return np.concatenate(pieces), starts


def _fft_convolve(a, b):
    n = len(a) + len(b) - 1
    size = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(a, size) * np.fft.rfft(b, size), size)[:n]


def vocal_fx(v: np.ndarray, reverb=0.18, chorus=0.35) -> np.ndarray:
    """Cift vokal (hafif perde ve zaman kaydirmali kopya) + kisa oda yankisi."""
    idx = np.arange(len(v)) * 1.004                      # ~7 cent yukari kopya
    copy = np.interp(idx, np.arange(len(v)), v, right=0)
    d = int(0.018 * SR)
    copy = np.concatenate([np.zeros(d), copy[:-d]])
    out = v + chorus * copy
    rng = np.random.default_rng(7)
    ir_t = np.arange(int(0.7 * SR)) / SR
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 6.5)
    ir = np.convolve(ir, np.ones(8) / 8, mode="same")    # yumusak (parlak degil) yanki
    ir /= np.sqrt(np.sum(ir ** 2))
    wet = _fft_convolve(out, ir)[: len(out)]
    return out + reverb * wet / (np.max(np.abs(wet)) or 1) * np.max(np.abs(out))
