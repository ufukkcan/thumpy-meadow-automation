"""
Muzik molasi icin enstrumantal cocuk sarkisi duzenlemesi (CC0 kayitli seslerle).

Melodi: songs.MELODIES (1929 oncesi kamu mali, K-12). Her nota vurus izgarasina oturur.
Cocugun dikkatini tutmak icin:
  - parlak tinilar: ksilofon (melodi) + glokenspiel (bir oktav ustte parilti) + ukulele (ritim)
  - 2. ve 4. vuruslarda el cirpma (cocuklarin katildigi vurus), surekli shaker
  - 'ta-da' girisi: zil agaci + yukari kosan ksilofon
  - 3. satirdan itibaren tef: enerji yukselir
  - son satirdan once 2 vurusluk DURUS (stop-time) + duduk: dikkati geri ceker
  - parlak kapanis + 'boing'
Donus: stereo ses + nota/satir zamanlari (karaoke ve olcum icin).
"""
import numpy as np

import samples
import songs

SR = samples.SR

# cocuk sarkilari icin canli tempo (orijinal sablon temposundan biraz hizli)
TEMPO = {"twinkle": 112, "mary": 118, "london": 120, "jacques": 112}

# ukulele akor tutuslari (tel sirasi G-C-E-A, re-entrant akort)
UKE_VOICING = {
    songs.C: (67, 60, 64, 72),
    songs.F: (69, 65, 69, 72),
    songs.G: (67, 62, 67, 71),
    songs.Am: (69, 60, 64, 69),
}
# olcu ici tarama kalibi "D DU UDU": (vurus, yon, siddet)
STRUM = [(0.0, "D", 1.0), (1.0, "D", 0.7), (1.5, "U", 0.5), (2.5, "U", 0.5), (3.0, "D", 0.75), (3.5, "U", 0.45)]

# bus: (kazanc, pan -1 sol..+1 sag)
LEVELS = {
    "xylo": (0.55, 0.0), "glock": (0.16, 0.3), "uke": (0.30, -0.35), "bass": (0.60, 0.0),
    "kick": (0.55, 0.0), "snare": (0.12, 0.0), "clap": (0.32, 0.1), "shaker": (0.10, 0.45),
    "tamb": (0.16, -0.4), "fx": (0.28, 0.0),
}
TONAL = ("xylo", "glock", "uke")          # yankisi biraz daha fazla
PERC = ("snare", "clap", "shaker", "tamb", "fx")


class _Mix:
    def __init__(self, total: float):
        self.n = int(total * SR) + 3 * SR
        self.bus = {name: np.zeros(self.n) for name in LEVELS}

    def add(self, bus: str, sig: np.ndarray, t: float) -> None:
        i = int(round(t * SR))
        if i >= self.n or i < 0:
            return
        end = min(self.n, i + len(sig))
        self.bus[bus][i:end] += sig[: end - i]


def _uke_chord(ch: tuple) -> tuple:
    return UKE_VOICING.get(tuple(ch), tuple(ch))


def _strum(mix: _Mix, chord: tuple, t: float, direction: str, vel: float, ring: float) -> None:
    """Gercek tarama: teller 12 ms arayla (asagi: G->A, yukari: A->G); yukari tarama daha hafif."""
    voicing = _uke_chord(chord)
    order = voicing if direction == "D" else voicing[::-1]
    for k, m in enumerate(order):
        mix.add("uke", samples.note("uke", m, vel * (0.85 + 0.15 * (k == 0)), max_dur=ring), t + k * 0.012)


def _reverb(x: np.ndarray, seconds: float = 1.1, seed: int = 0) -> np.ndarray:
    """Basit oda yankisi: ustel sonumlu, tizi yumusatilmis gurultu ile FFT konvolusyonu."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * SR)) / SR
    ir = rng.standard_normal(len(t)) * np.exp(-t / (seconds / 4.5))
    ir = np.convolve(ir, np.ones(6) / 6, mode="same")
    ir[: int(0.012 * SR)] = 0.0  # 12 ms on gecikme (kuru ses net kalsin)
    ir /= np.sqrt(np.sum(ir ** 2)) or 1.0
    n = 1 << int(np.ceil(np.log2(len(x) + len(ir))))
    y = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[: len(x)]
    return y


def _pan(x: np.ndarray, pan: float) -> np.ndarray:
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def _glue(st: np.ndarray, thr_db: float = -20.0, ratio: float = 2.5) -> np.ndarray:
    """Yumusak bus kompresoru (10 ms bloklar, 5 ms atak / 150 ms birakma): parcalari birbirine yapistirir."""
    blk = int(0.010 * SR)
    nb = len(st) // blk
    mono = np.mean(st[: nb * blk], axis=1).reshape(nb, blk)
    lvl = 20 * np.log10(np.sqrt(np.mean(mono ** 2, axis=1)) + 1e-9)
    over = np.maximum(0.0, lvl - thr_db)
    target = -over * (1 - 1 / ratio)
    g = np.zeros(nb)
    a_att, a_rel = np.exp(-10 / 5), np.exp(-10 / 150)
    cur = 0.0
    for i in range(nb):
        a = a_att if target[i] < cur else a_rel
        cur = a * cur + (1 - a) * target[i]
        g[i] = cur
    gain = 10 ** (np.interp(np.arange(len(st)), np.arange(nb) * blk + blk / 2, g) / 20)
    return st * gain[:, None]


def arrange(key: str, n_lines: int, seed: int = 1, lead: float = 1.0) -> dict:
    """lead: melodi enstrumanlarinin (ksilofon+glokenspiel) kazanci; vokal varken ~0.45.
    Donus: {"audio": (n,2) stereo, "melody_stem": mono ksilofon (olcum icin),
    "note_times": [(satir, nota_index, t)], "line_starts": [...], "beat": sn, "total": sn}"""
    m = songs.MELODIES[key]
    beat = 60.0 / TEMPO.get(key, m["bpm"])
    lines = (m["lines"] * 2)[:n_lines]
    chords = (m["chords"] * 2)[:n_lines]
    intro, line_len = 4 * beat, 8 * beat
    end_t = intro + line_len * len(lines)
    total = end_t + 4 * beat
    rng = np.random.default_rng(seed)
    hum = lambda: 1.0 + rng.uniform(-0.07, 0.07)   # canli calis hissi: SADECE siddet degisir, zaman degil
    mix = _Mix(total)

    # ---- giris: 'ta-da' ----
    mix.add("fx", samples.hit("belltree", 0.8), 0.0)
    _strum(mix, chords[0][0], 0.0, "D", 1.0, ring=beat * 0.9)
    for k, mm in enumerate((72, 74, 76, 79, 81, 84, 88, 91)):   # yukari kosan ksilofon (16'liklar)
        mix.add("xylo", samples.note("xylo", mm, 0.55 + 0.05 * k, max_dur=0.25), (1.0 + 0.25 * k) * beat)
    mix.add("clap", samples.hit("clap"), 3 * beat)
    mix.add("kick", samples.hit("kick"), 3 * beat)

    note_times, line_starts = [], []
    for li, (notes, chs) in enumerate(zip(lines, chords)):
        start = intro + li * line_len
        line_starts.append(start)
        stop_from = 6 if li == len(lines) - 2 else 99   # sondan bir onceki satirin son 2 vurusu: durus

        # melodi: ksilofon + glokenspiel (bir oktav ustte, hafif)
        t = start
        for ni, (midi, beats) in enumerate(notes):
            dur = beats * beat
            mix.add("xylo", samples.note("xylo", midi + 12, 0.85 * hum(), max_dur=dur + 0.25), t)
            mix.add("glock", samples.note("glock", midi + 24, 0.9 * hum(), max_dur=dur + 0.4), t)
            note_times.append((li, ni, t))
            t += dur

        # ukulele taramasi (her olcu ayni kalip; bir sonraki taramada onceki susturulur)
        strums = []
        for bar in (0, 1):
            for pos, d, v in STRUM:
                b = bar * 4 + pos
                if b >= stop_from:
                    continue
                strums.append((start + b * beat, chs[int(b // 2)], d, v))
        for k, (ts, ch, d, v) in enumerate(strums):
            nxt = strums[k + 1][0] if k + 1 < len(strums) else start + min(stop_from, 8) * beat
            _strum(mix, ch, ts, d, v * hum(), ring=max(0.05, nxt - ts - 0.01))

        # kontrbas: kok (1. vurus) + besli (2. vurus), her akor 2 vurus
        for ci, ch in enumerate(chs):
            if ci * 2 >= stop_from:
                continue
            root = 36 + ch[0] % 12
            fifth = root + 7 if root + 7 <= 50 else root - 5
            mix.add("bass", samples.note("bass", root, 0.95 * hum(), max_dur=beat * 0.9), start + ci * 2 * beat)
            mix.add("bass", samples.note("bass", fifth, 0.8 * hum(), max_dur=beat * 0.9), start + (ci * 2 + 1) * beat)

        # davul: kick 1-3, el cirpma (+ hafif trampet) 2-4, shaker sekizlik, 3. satirdan sonra tef
        for b in range(8):
            if b >= stop_from:
                continue
            bt = start + b * beat
            if b % 2 == 0:
                mix.add("kick", samples.hit("kick", hum()), bt)
            else:
                mix.add("clap", samples.hit("clap", hum()), bt)
                mix.add("snare", samples.hit("snare", hum()), bt)
            mix.add("shaker", samples.hit("shaker_down", 0.7 * hum()), bt)
            mix.add("shaker", samples.hit("shaker_up", 1.0 * hum()), bt + beat / 2)
            if li >= 2 and b in (3, 7):
                mix.add("tamb", samples.hit("tamb", hum()), bt)
        if stop_from < 99:
            mix.add("fx", samples.hit("whistle", 0.9), start + 7 * beat)   # durusta duduk

    # ---- kapanis: son akor + parilti + 'boing' ----
    mix.add("kick", samples.hit("kick"), end_t)
    mix.add("clap", samples.hit("clap"), end_t)
    _strum(mix, songs.C, end_t, "D", 1.0, ring=3 * beat)
    mix.add("glock", samples.note("glock", 96, 1.0, max_dur=3 * beat), end_t)
    mix.add("xylo", samples.note("xylo", 84, 0.8, max_dur=2 * beat), end_t)
    mix.add("fx", samples.hit("belltree", 0.7), end_t)
    mix.add("bass", samples.note("bass", 36, 1.0, max_dur=2 * beat), end_t)
    mix.add("fx", samples.hit("boing", 0.8), end_t + 2 * beat)

    # ---- miks: pan + yanki + yapistirma ----
    st = np.zeros((mix.n, 2))
    for name, (gain, pan) in LEVELS.items():
        x = mix.bus[name] * gain * (lead if name in ("xylo", "glock") else 1.0)
        seed = sum(map(ord, name))   # sabit tohum: her calistirmada ayni yanki
        if name in TONAL:
            x = x + 0.18 * _reverb(x, seed=seed)
        elif name in PERC:
            x = x + 0.08 * _reverb(x, 0.7, seed=seed)
        st += _pan(x, pan)
    st = _glue(st)
    n_total = int((total + 1.5) * SR)   # kapanis sesleri sonumlensin
    st = st[:n_total]
    fade = int(0.5 * SR)
    st[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return {"audio": st, "melody_stem": mix.bus["xylo"][:n_total], "note_times": note_times,
            "line_starts": line_starts, "beat": beat, "total": total}
