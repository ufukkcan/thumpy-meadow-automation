"""
Yeni format bolum motoru (7d): Claude'un yazdigi (kullanicinin onayladigi) senaryo JSON'u -> video.
Pilot (pilot.py) motorunun veriyle calisan hali. Bicim: "Thumpy formulu" (docs/arastirma-cocuk-izleme.md).

Akis: selam sarkisi (0. sn, ritual) -> hikaye cercevesi + yardim istegi (soru + bekleme)
-> 6 "bulma oyunu" (saklanma yeri sallanir -> gercek hayvan sesi -> "Who says ...?" + bekleme -> saka
-> cevap + kelime 3 kez + tekrar ettirme -> hayvana ozgu hareket, cocuk da yapar -> arkadas sirasina katilir
-> yuruyerek yeni yere) ; 2. ve 4. oyundan sonra hareket molasi (sarki) -> tekrar (cocuk tamamlar)
-> final (cerceveye gore odul) -> sonraki bolum silueti -> veda sarkisi (ritual).
Tekrar eden saka: Dino'nun kafasina bir seyler duser; sonunda odul (tac / cilek / yildiz) konar.
Hayvan sesleri gercek kayit (animal_sounds.py, CC0); hayvanlar konusmaz.
"""
import asyncio
import math
import os
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image

import animal_sounds
import render2 as r

FPS = 24
SR = 44100
VOICE = os.environ.get("TTS_VOICE", "en-US-AnaNeural")
GY = r.GROUND_Y

# ---------------- sabit ritueller (her bolumde ayni: tekrar = guven) ----------------
HELLO = ("jacques", ["Hello Dino, hello Dino", "Come and play! Come and play!",
                     "Jump, jump, jump, jump, clap, clap, jump, jump, jump, jump, clap, clap",
                     "Hi! Hello! Hi! Hello!"])
BYE = ("twinkle", ["Bye bye friends, it's time to go", "Wave goodbye, we love you so"])
BREAK_MELODIES = ["london", "mary"]           # hareket molalari (sozleri Claude yazar)
BREAK_AFTER = {1: 0, 3: 1}                    # 2. ve 4. oyundan sonra
N_FINDS = 7                                   # 7 oyun ~ 8,2 dk (6 oyun 7,4 dk olcuildu; hedef 8-10 dk)

# ---------------- katalog (Claude yalnizca bunlardan secer) ----------------
COLORS = {"cow": (150, 90, 200), "duck": (230, 150, 20), "dog": (215, 95, 40), "cat": (240, 120, 40),
          "sheep": (120, 140, 220), "rooster": (220, 60, 60), "horse": (170, 100, 50), "frog": (60, 170, 70),
          "chick": (230, 170, 0), "pig": (235, 100, 150), "owl": (140, 100, 60), "elephant": (110, 120, 150),
          "monkey": (170, 110, 60), "lion": (230, 140, 20), "bird": (60, 140, 230)}
HIDES = {
    "bush": dict(y=GY + 10, eyes_dy=-140, hollow=(35, 70, 40), ek=1.0),
    "cloud": dict(y=200, eyes_dy=15, hollow=(190, 210, 238), ek=1.0),
    "tree": dict(y=GY + 10, eyes_dy=-200, hollow=(75, 45, 28), ek=0.72),
}
GAGS = {   # ad -> (Claude'un yazacagi satir sayisi, izinli saklanma yerleri, buyukluk)
    "pop_fall": (2, ("bush", "tree"), 1),
    "bush_hop": (2, ("bush",), 2),
    "wrong_guess": (3, ("bush", "tree", "cloud"), 2),
    "peek_zoom": (2, ("tree",), 3),
}
ACTIONS = ("hop", "dance", "spin", "flap", "stomp", "wiggle")
FRAMES = {   # hikaye cercevesi -> final
    "birthday": dict(shout_caption="Surprise!", head="crown"),
    "picnic": dict(shout_caption="Picnic time!", head="strawberry"),
    "rainbow": dict(shout_caption="Look up!", head="star"),
}
SONG_MOVES = ("hop", "jump", "stomp", "clap", "wave", "spin", "flap", "wiggle", "dance", "march", "stretch")

# ---------------- sahne yerlesimi (ekran koordinatlari; arka plan kaydirilir) ----------------
DINO_HOME = 760
DINO_Y = GY - 175
HIDE_X = 1400
WALK = 1900   # yuruyuste dunya kaymasi: HIDE_X - WALK = -500 -> en genis nesne (agac, +-310) bile ekran disi
FRIEND = [(60 + k * 85, GY - 190, 100) for k in range(N_FINDS)]
ROW = [(970 + k * 140, GY - 140, 160) for k in range(N_FINDS)]
SIL = (1300, 300, 300)
CAKE = (1150, GY - 95, 220)
FRUITS = ["apple", "banana", "strawberry", "watermelon", "grapes", "orange"]


def rgbt(t):
    return r.rgb(*t)


def article(name):
    return "an" if name[0] in "aeiou" else "a"


# ---------------- hareket yardimcilari ----------------
class Track:
    """Zamana bagli deger (sayi ya da demet). hold / to / jump; anahtarlar kronolojik."""

    def __init__(self, v0):
        self.k = [(0.0, v0)]

    def hold(self, t):
        self.k.append((t, self.k[-1][1]))

    def to(self, t, v):
        self.k.append((t, v))

    def jump(self, t, v):
        self.hold(t)
        self.k.append((t, v))

    def at(self, t):
        k = self.k
        if t <= k[0][0]:
            return k[0][1]
        for (t0, v0), (t1, v1) in zip(k, k[1:]):
            if t < t1:
                e = r.ease_in_out((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
                if isinstance(v0, tuple):
                    return tuple(a + (b - a) * e for a, b in zip(v0, v1))
                return v0 + (v1 - v0) * e
        return k[-1][1]


def jump(ph):
    """Tek ziplama (ph 0..1): comelme -> havada -> inis basilmasi. Donus: (yukseklik 0..1, squash)."""
    ph = r.clamp01(ph)
    if ph < 0.18:
        return 0.0, 0.14 * math.sin(ph / 0.18 * math.pi / 2)
    if ph < 0.82:
        x = (ph - 0.18) / 0.64
        return math.sin(math.pi * x), -0.08 * (1 - x)
    x = (ph - 0.82) / 0.18
    return 0.0, 0.16 * math.sin(math.pi * x)


# ---------------- ses ----------------
def _active_rms(x):
    a = x[np.abs(x) > 0.05 * (np.max(np.abs(x)) or 1.0)]
    return float(np.sqrt(np.mean(a ** 2))) if len(a) else 1e-6


def _add(buf, sig, start_s):
    i = int(start_s * SR)
    end = min(len(buf), i + len(sig))
    if 0 <= i < end:
        buf[i:end] += sig[: end - i]


async def _tts_save(text, path, rate, pitch):
    import edge_tts
    await edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch).save(path)


def tts(text, path, rate="-5%", pitch="+0Hz"):
    """edge-tts -> mono numpy. Bastaki/sondaki sessizlik kirpilir."""
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            asyncio.run(_tts_save(text, str(path), rate, pitch))
            break
        except Exception:
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    on = np.nonzero(np.abs(x) > 0.02 * (np.max(np.abs(x)) or 1.0))[0]
    if len(on):
        x = x[max(0, on[0] - int(0.03 * SR)): on[-1] + int(0.08 * SR)]
    return x


def mouth_track(speech, n_frames):
    hop = SR // FPS
    env = np.array([np.sqrt(np.mean(speech[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(speech) else 0.0
                    for i in range(n_frames)])
    ref = np.percentile(env[env > 1e-4], 90) if np.any(env > 1e-4) else 1.0
    raw = np.clip(env / ref, 0, 1)
    out, v = np.zeros(n_frames), 0.0
    for i, x in enumerate(raw):
        v = x if x > v else v * 0.55
        out[i] = v
    return out


# ---------------- zaman cizelgesi ----------------
class TL:
    def __init__(self, work, estimate=False):
        self.t = 0.0
        self.segs = []
        self.audio = []          # (kanal, sinyal, baslangic): "dino" | "narr" | 0..5 | "song" | "sfx"
        self.work = Path(work)
        self.estimate = estimate  # True: ses uretmeden sure tahmini (Telegram onay mesaji icin)
        self.n = 0
        self.chapters = []

    def chapter(self, title):
        self.chapters.append((self.t, title))

    def seg(self, kind, dur, **kw):
        s = dict(kind=kind, start=self.t, dur=dur, **kw)
        s["end"] = self.t + dur
        self.segs.append(s)
        self.t += dur
        return s

    def say(self, text, gap=0.35, who="dino", **kw):
        self.n += 1
        if self.estimate:
            clip = np.zeros(int((len(text.split()) / 2.4 + 0.4) * SR))
        else:
            clip = tts(text, self.work / "tts" / f"{self.n:03d}_{who}.mp3")
        s = self.seg("say", len(clip) / SR + gap, who=who, text=text, **kw)
        self.audio.append((who, clip, s["start"] + 0.05))
        return s

    def animal(self, P, i, n=1, gap=0.3, **kw):
        a = P.finds[i]
        clip = np.zeros(int(0.8 * n * SR)) if self.estimate else animal_sounds.clip(a["animal"], n)
        says = a["says"].capitalize() + "!"
        s = self.seg("say", len(clip) / SR + gap, who=i, text=" ".join([says] * n), key=a["says"],
                     color=a["rgb"], **kw)
        self.audio.append((i, clip, s["start"] + 0.05))
        return s

    def pause(self, dur, text, **kw):
        return self.seg("pause", dur, text=text, **kw)

    # ---- ses efektleri (CC0, samples.py) ----
    def sfx(self, sig_fn, t):
        if not self.estimate:
            self.audio.append(("sfx", sig_fn(), t))

    def rustle(self, t, dur):
        import samples
        for k in range(int(dur / 0.11)):
            self.sfx(lambda k=k: samples.hit("shaker_down" if k % 2 == 0 else "shaker_up", 0.55), t + k * 0.11)

    def boing(self, t, v=0.7):
        import samples
        self.sfx(lambda: samples.hit("boing", v), t)

    def bell(self, t):
        import samples
        self.sfx(lambda: samples.hit("belltree", 0.5), t)

    def tada(self, t):
        import samples
        self.bell(t)
        for k, m in enumerate((72, 76, 79, 84)):
            self.sfx(lambda m=m: samples.note("glock", m, 0.45, max_dur=0.6), t + 0.02 + k * 0.07)

    def claps(self, t, n=4):
        import samples
        for k in range(n):
            self.sfx(lambda: samples.hit("clap", 0.9), t + k * 0.22)

    def thud(self, t):
        import samples
        self.sfx(lambda: samples.hit("kick", 0.9), t)
        self.boing(t + 0.05, 0.5)

    def whistle(self, t):
        import samples
        self.sfx(lambda: samples.hit("whistle", 0.7), t)

    def twinkle(self, t):
        import samples
        for k, m in enumerate((91, 84, 96, 91)):
            self.sfx(lambda m=m: samples.note("glock", m, 0.35, max_dur=0.5), t + k * 0.18)

    def ding(self, t, m=84):
        import samples
        self.sfx(lambda: samples.note("glock", m, 0.5, max_dur=0.8), t)

    def slide(self, t, up=True):
        import samples
        notes = (72, 74, 76, 79, 81, 84) if up else (84, 81, 79, 76, 74, 72)
        for k, m in enumerate(notes):
            self.sfx(lambda m=m: samples.note("xylo", m, 0.5, max_dur=0.2), t + k * 0.07)

    def steps(self, t, n, dt=0.28, notes=(45, 52)):
        import samples
        for k in range(n):
            self.sfx(lambda k=k: samples.note("bass", notes[k % 2], 0.8, max_dur=0.25), t + k * dt)

    def jingle(self, t, dur):
        """Hareket aninda neseli ritim: ksilofon + el cirpma."""
        import samples
        beat = 0.36
        for k in range(int(dur / beat)):
            m = (72, 76, 79, 76)[k % 4]
            self.sfx(lambda m=m: samples.note("xylo", m, 0.55, max_dur=0.3), t + k * beat)
            if k % 2:
                self.sfx(lambda: samples.hit("clap", 0.7), t + k * beat)


def song_seg(tl, phase, key, lines, shots, **kw):
    import kidsong
    import vocal_break
    if tl.estimate:
        audio, timings, dur = np.zeros(1), vocal_break.word_timings(lines, key), vocal_break.duration(lines, key)
    else:
        audio, timings, dur = vocal_break.render(lines, key)
    beat, starts, _ = kidsong.timing(key, len(lines))
    words = [(st, li, lines[li].split()[wi].strip(".,!?").lower()) for li, wi, st in timings]
    s = tl.seg("song", dur, phase=phase, lines=lines, timings=timings, beat=beat, starts=starts,
               words=words, shots=shots, **kw)
    tl.audio.append(("song", audio, s["start"]))
    return s


def head_item(P, kind, t0, src, size):
    """Dino'nun kafasina dusen sey (tekrar eden saka). Oncekini kaldirir (puf)."""
    for h in P.head:
        if h["t1"] > t0:
            h["t1"] = t0
            P.fx.append(("poof", t0, None, None, 0))
    P.head.append(dict(kind=kind, t0=t0, t1=1e9, src=src, size=size))


# ---------------- oyun parcalari ----------------
def _hx(P, i, t):
    return P.hide[i]["x"].at(t)


def tiptoe(tl, P, target, i):
    s = tl.seg("tiptoe", 1.7, shot=("two", i))
    P.dino_x.hold(s["start"])
    P.dino_x.to(s["start"] + 1.6, target)
    tl.steps(s["start"], 6)


def pop(tl, P, i, t0):
    """Hayvan saklandigi yerden ortaya cikar (saklanma yerine gore)."""
    kind, hx = P.hide[i]["kind"], _hx(P, i, t0)
    tr = P.animal[i]
    if kind == "bush":
        tr.jump(t0, (hx, GY - 60, 280))
        tr.to(t0 + 0.45, (hx, GY - 300, 280))
        P.fx.append(("poof", t0 + 0.3, hx, GY - 300, 0))
    elif kind == "tree":
        tr.jump(t0, (hx, GY - 125, 250))
        tr.to(t0 + 0.45, (hx + 190, GY - 125, 250))
        P.fx.append(("dust", t0 + 0.4, hx + 190, GY, 3))
    else:
        tr.jump(t0, (hx + 90, 215, 200))
        tr.to(t0 + 0.4, (hx + 270, 215, 200))
    P.shown_from[i] = min(P.shown_from[i], t0)
    tl.boing(t0)


def gag_pop_fall(tl, P, i, lines):
    """Kucuk: Dino parmak ucunda gider, hayvan cikar, Dino dusup oturur, kafasina yaprak/elma."""
    kind = P.hide[i]["kind"]
    hx = _hx(P, i, tl.t)
    tiptoe(tl, P, hx - 260, i)
    tl.say(lines[0], expr="listen", look=1.0, lean=8, shot=("two", i))
    s = tl.animal(P, i, 1, shot=("two", i), surprise=True)
    pop(tl, P, i, s["start"])
    s = tl.seg("fall", 1.5, shot=("two", i))
    tl.whistle(s["start"])
    tl.thud(s["start"] + 0.58)
    tl.twinkle(s["start"] + 0.7)
    P.fx.append(("dust", s["start"] + 0.58, P.dino_x.at(s["start"]), GY, 1))
    if kind == "tree":
        head_item(P, "apple", s["start"] + 0.75, (hx - 80, 380), 110)
    else:
        head_item(P, "leaf", s["start"] + 0.75, (hx - 60, GY - 230), 1.6)
    tl.say(lines[1], expr="happy", sit=True, shot=("two", i))


def gag_bush_hop(tl, P, i, lines):
    """Orta: cali ziplaya ziplaya Dino'ya gelir, hayvan cikar."""
    tl.say(lines[0], wave=1.0, look=1.0, shot=("wide",))
    s = tl.seg("bushhop", 2.1, shot=("wide",), eyes=i)
    tr = P.hide[i]["x"]
    x0, x1 = tr.at(s["start"]), P.dino_x.at(s["start"]) + 330
    for k in range(3):
        a = s["start"] + k * 0.7
        tr.hold(a)
        tr.to(a + 0.55, x0 + (x1 - x0) * (k + 1) / 3)
        P.bush_hops.append((i, a, 0.55))
        tl.boing(a + 0.5)
    s = tl.animal(P, i, 2, shot=("two", i), surprise=True)
    pop(tl, P, i, s["start"])
    tl.bell(s["start"])
    tl.say(lines[1], expr="happy", excited=True, shot=("two", i))


def gag_wrong_guess(tl, P, i, lines):
    """Orta: Dino yanlis tahmin eder; hayvan 'hayir' der gibi sallanir, sonra cikar.
    Bulutta Dino once 3 kez ziplar (yetisemez). Kus ise ucup Dino'nun kafasina konar."""
    f, kind = P.finds[i], P.hide[i]["kind"]
    hx = _hx(P, i, tl.t)
    tiptoe(tl, P, hx - (200 if kind == "cloud" else 280), i)
    tl.say(lines[0], look=1.0, look_y=-1.0 if kind == "cloud" else 0.0, shot=("two", i))
    if kind == "cloud":
        s = tl.seg("jumps", 2.7, shot=("two", i))
        x = P.dino_x.at(s["start"])
        for k in range(3):
            a = s["start"] + k * 0.9
            tl.boing(a + 0.15, 0.5 + 0.15 * k)
            P.fx.append(("dust", a + 0.75, x, GY, 10 + k))
        tl.say("It's too high!", expr="surprised", sweat=1.0, shot=("two", i))
    tl.say(lines[1], arms=(140, 140), expr="happy", look=1.0, shot=("two", i))
    s = tl.animal(P, i, 1, shake_no=i, shot=("two", i))
    pop(tl, P, i, s["start"])
    dx = P.dino_x.at(s["start"])
    tr = P.animal[i]
    if f["fly"]:
        s = tl.seg("fly", 1.4, shot=("two", i), surprise=True)
        tr.hold(s["start"])
        tr.to(s["start"] + 0.6, (dx + 260, 300, 200))
        tr.to(s["start"] + 1.25, (dx + 10, DINO_Y - 235, 200))
        P.front_from[i] = s["start"]
        tl.slide(s["start"], up=False)
        tl.boing(s["start"] + 1.25)
        land = s["start"] + 1.25
        tl.animal(P, i, 1, look_y=-1.0, expr="surprised", shot=("two", i), bonk=True)
        head_item(P, "none", land, (0, 0), 0)
        tl.say(lines[2], expr="happy", look_y=-1.0, shot=("two", i))
        P.on_head.append((land, tl.t, i))
    else:
        s = tl.seg("hopout", 1.1, shot=("two", i), surprise=True)
        tr.hold(s["start"])
        tr.to(s["start"] + 0.8, (dx + 250, GY - 130, 250))
        P.front_from[i] = s["start"]
        tl.slide(s["start"])
        P.fx.append(("dust", s["start"] + 0.8, dx + 250, GY, 30 + i))
        tl.say(lines[2], expr="happy", excited=True, shot=("two", i))


def gag_peek_zoom(tl, P, i, lines):
    """Buyuk: hayvan agacin iki yanindan bakar, firlar, Dino'nun etrafinda doner, elma duser."""
    hx = _hx(P, i, tl.t)
    tiptoe(tl, P, hx - 380, i)
    tl.say(lines[0], expr="listen", look=1.0, sweat=0.8, shot=("two", i))
    s = tl.seg("peek", 2.6, shot=("two", i), peek=i)
    tl.ding(s["start"] + 0.2, 84)
    tl.ding(s["start"] + 1.5, 79)
    s = tl.animal(P, i, 2, shot=("wide",))
    dx = P.dino_x.at(s["start"])
    P.animal[i].jump(s["start"], (dx + 280, GY - 125, 240))
    P.shown_from[i] = P.front_from[i] = s["start"]
    P.fx += [("poof", s["start"], dx + 280, GY - 125, 0), ("dust", s["start"] + 0.1, dx + 280, GY, 20)]
    tl.whistle(s["start"])
    s = tl.seg("zoom", 2.6, shot=("wide",), cx=dx, sweat=1.0, actor=i)
    if not tl.estimate:
        for k in (0.4, 1.5):
            tl.audio.append((i, animal_sounds.clip(P.finds[i]["animal"], 1), s["start"] + k))
    s = tl.seg("fall", 1.6, shot=("two", i), bonk=True)
    head_item(P, "apple", s["start"] + 0.45, (hx - 80, 380), 110)
    tl.boing(s["start"] + 0.45, 0.9)
    tl.thud(s["start"] + 0.75)
    tl.twinkle(s["start"] + 0.85)
    P.fx.append(("dust", s["start"] + 0.75, dx, GY, 21))
    tl.say(lines[1], expr="happy", sit=True, shot=("two", i))


GAG_FN = {"pop_fall": gag_pop_fall, "bush_hop": gag_bush_hop, "wrong_guess": gag_wrong_guess,
          "peek_zoom": gag_peek_zoom}


def walk(tl, P, i=None):
    """Yuruyus: arka plan kayar, onceki TUM saklanma yerleri dunyayla birlikte sola kayar (birikmez),
    i verilirse yeni saklanma yeri sagdan gelir; i=None: temiz cayira yuruyus (tekrar/final oncesi)."""
    s = tl.seg("walk", 2.8, shot=("wide",))
    P.cam.hold(s["start"])
    P.cam.to(s["end"], P.cam.at(s["start"]) + WALK)
    for j in range(len(P.hide) if i is None else i):
        old = P.hide[j]["x"]
        x0 = old.at(s["start"])
        if x0 > -600:
            old.hold(s["start"])
            old.to(s["end"], x0 - WALK)
    if i is not None:
        new = P.hide[i]["x"]
        new.jump(s["start"], HIDE_X + WALK)
        new.to(s["end"], HIDE_X)
    tl.steps(s["start"], 9, dt=0.3, notes=(72 - 24, 76 - 24))


def find(tl, P, i):
    f = P.finds[i]
    name, says, col = f["animal"], f["says"], f["rgb"]
    kind = P.hide[i]["kind"]
    tl.chapter(f"The {name.capitalize()} Says {says.capitalize()}")
    t_start = tl.t                                   # Shorts icin oyunun basi
    s = tl.say(f["notice"], expr="surprised", look=1.0, wiggle=i, shot=("two", i))
    tl.rustle(s["start"], s["dur"])
    hx = _hx(P, i, s["start"])
    if kind == "bush":
        P.fx.append(("leaves", s["start"] + 0.2, hx, GY - 180, 50 + i))
    elif kind == "tree":
        P.fx.append(("leaves", s["start"] + 0.2, hx - 80, 380, 50 + i))
    tl.say("Shh... listen!", expr="listen", arms=(20, 165), look=1.0, shot=("two", i))
    tl.animal(P, i, 2, wiggle=i, eyes=i, shot=("hide", i))
    tl.say(f"Who says {says}?", key=says, color=col, shot=("dino",))
    tl.pause(2.6, f"Who says {says}?", key=says, color=col, shot=("dino",))
    GAG_FN[f["gag"]](tl, P, i, f["gag_lines"])

    # cevap: kelime 3 kez + tekrar ettirme
    hx = _hx(P, i, tl.t)
    stage = (hx, GY - 150, 280)
    s = tl.say(f"It's {article(name)} {name}! The {name} says {says}!", key=name, color=col,
               expr="happy", excited=True, shot=("animal", i))
    tr = P.animal[i]
    tr.hold(s["start"])
    tr.to(s["start"] + 0.6, stage)
    P.front_from[i] = min(P.front_from[i], s["start"])
    P.fx += [("confetti", s["start"] + 0.5, stage[0], stage[1], 11 + i), ("sparkle", s["start"] + 0.55,
                                                                           stage[0], stage[1], i)]
    tl.tada(s["start"] + 0.5)
    tl.animal(P, i, 1, celebrate=i, shot=("animal", i))
    tl.say(f"Can you say {name}?", key=name, color=col, shot=("dino",))
    tl.pause(2.0, f"Can you say {name}?", key=name, color=col, shot=("dino",))
    s = tl.say(f"{name.capitalize()}! Great job!", key=name, color=col, expr="happy", excited=True,
               shot=("wide",))
    tl.claps(s["start"])
    P.fx.append(("sparkle", s["start"], P.dino_x.at(s["start"]), DINO_Y - 60, 30 + i))

    # hayvana ozgu hareket: cocuk da yapar (TPR)
    tl.say(f["action_line"], expr="happy", shot=("two", i))
    s = tl.seg("action", 3.2, verb=f["action"], actor=i, shot=("two", i))
    tl.jingle(s["start"], s["dur"])
    P.spans.append((t_start, s["end"]))              # Shorts: bildirimden harekete kadar tek oyun

    # arkadas sirasina katilir, Dino evine doner
    s = tl.seg("join", 1.3, shot=("wide",))
    tr.hold(s["start"])
    tr.to(s["end"], FRIEND[i])
    P.dino_x.hold(s["start"])
    P.dino_x.to(s["end"], DINO_HOME)


def dance(tl, P, k, ep):
    br = ep["breaks"][k]
    tl.chapter("Dance Break!" if k == 0 else "Move and Groove!")
    intro = ("Dance break! Stand up and dance with me!", "Wiggle time! Stand up and move with me!")[k]
    s = tl.say(intro, excited=True, expr="happy", shot=("wide",))
    P.dino_x.hold(s["start"])
    P.dino_x.to(s["start"] + 0.8, 820)
    shots = [("wide",), ("wide",), ("pt", 1180, 600, 1.5), ("wide",), ("pt", 1560, 600, 1.5)]
    shots = (shots + [("wide",)] * 6)[:len(br["lines"]) + 1]
    s = song_seg(tl, "dance", br["melody"], br["lines"], shots)
    for name, x in zip(br["guests"], (1180, 1560)):
        P.extras.append((name, x, s["start"], s["end"]))
        P.fx += [("poof", s["start"] + 0.1, x, GY - 130, 0), ("poof", s["end"], x, GY - 130, 0)]
    tl.bell(s["start"])
    s = tl.seg("join", 1.0, shot=("wide",))
    P.dino_x.hold(s["start"])
    P.dino_x.to(s["end"], DINO_HOME)


def recap(tl, P):
    tl.chapter("Let's Remember!")
    s = tl.say("Let's say it together!", excited=True, expr="happy", shot=("wide",))
    for i in range(len(P.finds)):
        P.animal[i].hold(s["start"])
        P.animal[i].to(s["start"] + 0.9, ROW[i])
    for i, f in enumerate(P.finds):
        shot = ("pt", ROW[i][0], 560, 1.45)
        s = tl.say(f"The {f['animal']} says...", key=f["animal"], color=f["rgb"], shot=shot, recap=i)
        P.fx.append(("sparkle", s["start"], ROW[i][0], ROW[i][1], 40 + i))
        tl.pause(1.7, f"The {f['animal']} says...", key=f["animal"], color=f["rgb"], shot=shot, recap=i)
        s = tl.animal(P, i, 1, shot=shot, recap=i, celebrate=i)
        tl.ding(s["start"])


def finale(tl, P, ep):
    fr = FRAMES[ep["frame"]]
    lines = ep["finale"]
    tl.chapter(fr["shout_caption"])
    tl.say(lines[0], expr="happy", shot=("wide",))
    s = tl.seg("surprise", 1.6, shot=("wide",), all_hop=True, text=fr["shout_caption"])
    if not tl.estimate:
        for i, f in enumerate(P.finds):
            tl.audio.append((i, animal_sounds.clip(f["animal"], 1), s["start"] + 0.05 + 0.1 * i))
    tl.bell(s["start"])
    tl.whistle(s["start"] + 0.1)
    P.finale_t = s["start"] + 0.3
    P.fx += [("confetti", s["start"] + 0.2, 1000, 400, 61), ("confetti", s["start"] + 0.3, 1650, 400, 62)]
    shot = ("pt", 1150, 560, 1.3)
    tl.say(ep["shout"], who="narr", expr="surprised", arms=(150, 150), shot=shot)
    s = tl.say(lines[1], expr="happy", excited=True, shot=shot)
    head_item(P, fr["head"], s["start"] + s["dur"] - 0.2, (DINO_HOME, -150), 140)
    tl.tada(s["start"] + s["dur"] + 0.4)
    s = tl.say(lines[2], expr="happy", wave=1.0, shot=("dino",))
    P.fx.append(("sparkle", s["start"], DINO_HOME, DINO_Y - 200, 70))


def teaser(tl, P, ep):
    s = tl.say(ep["teaser_line"], expr="happy", shot=("wide",))
    P.sil = s["start"]
    tl.slide(s["start"])
    tl.say("Who is it?", look=1.0, look_y=-1.0, shot=("pt", SIL[0], 420, 1.4))
    tl.pause(1.6, "Who is it?", shot=("pt", SIL[0], 420, 1.4))


def build(ep, work, estimate=False):
    """Senaryo -> zaman cizelgesi + ses. estimate=True: ses uretmeden sure (Telegram onayi icin)."""
    import music
    if not estimate:
        import samples
        samples.ensure()
    finds = []
    for f in ep["finds"]:
        meta = animal_sounds.SOURCES[f["animal"]]
        finds.append({**f, "says": meta["says"], "fly": meta["fly"], "rgb": rgbt(COLORS.get(f["animal"], (230, 70, 70)))})
    P = SimpleNamespace(finds=finds, dino_x=Track(DINO_HOME), cam=Track(0.0),
                        hide=[dict(kind=f["hide"], x=Track(HIDE_X if i == 0 else HIDE_X + WALK)) for i, f in enumerate(finds)],
                        animal=[Track((HIDE_X, GY - 60, 260)) for _ in finds],
                        shown_from=[1e9] * len(finds), front_from=[1e9] * len(finds), on_head=[],
                        fx=[], extras=[], head=[], bush_hops=[], finale_t=1e9, sil=1e9, spans=[],
                        frame=ep["frame"], teaser=ep["teaser_animal"])
    tl = TL(work, estimate)

    tl.chapter("Hello Song")
    song_seg(tl, "hello", HELLO[0], HELLO[1],
             [("wide",), ("dino",), ("wide",), ("wide",), ("hide", 0)])
    tl.chapter("Can You Help Dino?")
    hook = ep["hook"]
    tl.say(f"Hi friends! I'm Dino!", wave=1.0, expr="happy", shot=("dino",))
    s = tl.say(hook[0], excited=True, expr="happy", shot=("wide",))
    tl.tada(s["start"] + 0.3)
    P.fx.append(("sparkle", s["start"] + 0.3, DINO_HOME, DINO_Y - 100, 5))
    for line in hook[1:]:
        tl.say(line, expr="surprised", look=1.0, eyes_all=True, shot=("wide",))
    tl.say(ep["ask"], shot=("dino",))
    tl.pause(2.2, ep["ask"], shot=("dino",))
    tl.say("Yay! Let's go!", excited=True, expr="happy", shot=("wide",))
    for i in range(len(finds)):
        if i > 0:
            walk(tl, P, i)
        find(tl, P, i)
        if i in BREAK_AFTER:
            dance(tl, P, BREAK_AFTER[i], ep)
    walk(tl, P)                                     # tekrar ve final temiz cayirda
    recap(tl, P)
    finale(tl, P, ep)
    teaser(tl, P, ep)
    tl.chapter("Goodbye Song")
    song_seg(tl, "bye", BYE[0], BYE[1], [("wide",), ("wide",), ("dino",)])
    total = tl.t
    P.segs, P.total, P.chapters = tl.segs, total, tl.chapters
    if estimate:
        return P

    # ---- miks ----
    n = int(total * SR) + SR
    dino_sp, narr = np.zeros(n), np.zeros(n)
    an_sp = [np.zeros(n) for _ in finds]
    songs_b, sfx = np.zeros(n), np.zeros(n)
    for who, sig, t0 in tl.audio:
        if who == "dino":
            _add(dino_sp, sig, t0)
        elif who == "narr":
            _add(narr, sig, t0)
        elif who == "song":
            _add(songs_b, sig / _active_rms(sig), t0)
        elif who == "sfx":
            _add(sfx, sig, t0)
        else:
            _add(an_sp[who], sig, t0)
    nar = _active_rms(dino_sp)
    an_sp = [x * (nar / _active_rms(x)) * 0.9 for x in an_sp]      # gercek kayitlar konusma seviyesine
    bg = music.background_track(total)
    gain = np.full(len(bg), 0.20)
    for s in tl.segs:
        if s["kind"] == "song":
            gain[int(s["start"] * SR):int(s["end"] * SR)] = 0.0
    gain = np.convolve(gain, np.ones(SR // 4) / (SR // 4), mode="same")
    buf = np.zeros(n)
    buf[:len(bg)] += bg * gain * (nar / _active_rms(bg))
    buf += dino_sp + narr + sum(an_sp) + songs_b * 0.9 * nar + sfx * (nar / _active_rms(sfx)) * 0.5
    n_frames = int(total * FPS)
    P.audio = buf[: int(total * SR)]
    P.dmouth = mouth_track(dino_sp, n_frames)
    P.amouth = [mouth_track(x, n_frames) for x in an_sp]
    return P


# ---------------- cizim ----------------
def _seg_at(segs, t):
    lo, hi = 0, len(segs) - 1
    while lo < hi:                                   # ikili arama (uzun bolumde hiz)
        mid = (lo + hi + 1) // 2
        if segs[mid]["start"] <= t:
            lo = mid
        else:
            hi = mid - 1
    return segs[lo]


def _cur_word(s, tl):
    words = s["words"]
    for k in range(len(words) - 1, -1, -1):
        if words[k][0] <= tl:
            nxt = words[k + 1][0] if k + 1 < len(words) else words[k][0] + s["beat"]
            return words[k][0], words[k][1], words[k][2], nxt
    return None


def _short_spec(spec, s, P, i):
    """Shorts (dar dikey kadraj): Dino ile saklanma yeri ayni kadraja sigmaz; genis/ikili plan yerine
    o an konusana ya da olayin oldugu yere yakin plan."""
    if spec[0] not in ("wide", "two", "pt"):
        return spec
    if isinstance(s.get("who"), int) or s["kind"] in ("peek", "bushhop") or s.get("wiggle") == i:
        return ("hide", i)
    if s["kind"] in ("action",) or s.get("celebrate") == i:
        return ("animal", i)
    return ("dino",)


def _camera(spec, t, P, fw=r.W, fh=r.H, zmin=1.0):
    kind = spec[0]
    if kind == "wide":
        cx, cy, z = r.W / 2, r.H / 2, 1.0
    elif kind == "dino":
        cx, cy, z = P.dino_x.at(t), DINO_Y - 30, 1.55
    elif kind == "hide":
        i = spec[1]
        h = HIDES[P.hide[i]["kind"]]
        cx, cy, z = _hx(P, i, t), h["y"] + h["eyes_dy"] + (-30 if P.hide[i]["kind"] == "cloud" else 10), 1.7
    elif kind == "two":
        i = spec[1]
        if P.hide[i]["kind"] == "cloud":
            cx, cy, z = (P.dino_x.at(t) + _hx(P, i, t)) / 2, 420, 1.15
        else:
            cx, cy, z = (P.dino_x.at(t) + _hx(P, i, t)) / 2, 610, 1.3
    elif kind == "animal":
        x, y, _ = P.animal[spec[1]].at(t)
        cx, cy, z = x, y - 40, 1.6
    else:
        cx, cy, z = spec[1], spec[2], spec[3]
    z = max(z, zmin)
    hw, hh = fw / 2 / z, fh / 2 / z               # gorunen dunya yari-genislik/yukseklik (dunya 1920x1080)
    return min(max(cx, hw), r.W - hw), min(max(cy, hh), r.H - hh), z


def _zoom_pos(s, tl):
    a = 2 * math.pi * 2 * r.clamp01(tl / s["dur"])
    return s["cx"] + 280 * math.cos(a), GY - 125 + 40 * math.sin(a), math.sin(a) > 0, -280 * math.sin(a)


def _move(verb, ph, t, tl):
    """Sarki/hareket fiili -> Dino pozu parcasi: (yukseklik, squash, kw)."""
    kw = {}
    hop, sq = 0.0, 0.0
    if verb in ("hop", "jump"):
        h, sq = jump(ph)
        hop, kw["arms"] = h * 100, (60, 60)
    elif verb == "stomp":
        sq = 0.2 * math.exp(-ph * 4)
        kw["arms"] = (120, 120)
    elif verb == "clap":
        a = -25 - 35 * math.sin(math.pi * r.clamp01(ph))
        kw["arms"] = (a, a)
    elif verb == "wave":
        kw["wave"] = 1.0
    elif verb == "spin":
        kw.update(look=math.sin(t * 12), arms=(150, 150))
        hop = 20 * abs(math.sin(t * 6))
    elif verb == "flap":
        a = 40 + 110 * abs(math.sin(t * 9))
        kw["arms"] = (a, a)
    elif verb in ("wiggle", "dance"):
        kw.update(lean=12 * math.sin(t * 9), arms=(90 + 40 * math.sin(t * 9), 90 - 40 * math.sin(t * 9)))
        hop = 15 * abs(math.sin(t * 9))
    elif verb == "march":
        hop = 25 * abs(math.sin(t * 7))
        kw["arms"] = (40 + 30 * math.sin(t * 7), 40 - 30 * math.sin(t * 7))
    elif verb == "stretch":
        sq, kw["arms"] = -0.1, (165, 165)
    return hop, sq, kw


def _dino_pose(P, s, t, tl, f):
    x = P.dino_x.at(t)
    kw = dict(t=t, mouth=float(P.dmouth[min(f, len(P.dmouth) - 1)]), expr=s.get("expr", "neutral"),
              look=s.get("look", 0.0), look_y=s.get("look_y", 0.0), arms=s.get("arms"),
              wave=s.get("wave", 0.0), excited=s.get("excited", False), lean=s.get("lean", 0.0),
              sweat=s.get("sweat", 0.0))
    hop, sq, dy = abs(math.sin(t * 2.2)) * 10, 0.0, 0.0
    k = s["kind"]
    if k == "song":
        beat = s["beat"]
        h, sq = jump((tl / beat) % 1.0)
        hop = h * 30
        kw["expr"] = "happy" if (tl % (4 * beat)) < 2 * beat else "neutral"
        cw = _cur_word(s, tl)
        if cw:
            st, li, w, nxt = cw
            kw["mouth"] = math.exp(-(tl - st) / 0.18) if tl - st < 1.0 else 0.0
            ph = (tl - st) / max(0.05, nxt - st)
            if s["phase"] == "hello" and li in (0, 3):
                kw["wave"] = 1.0
            elif s["phase"] == "hello" and li == 1:
                kw["arms"] = (110 + 12 * math.sin(t * 6),) * 2
            elif s["phase"] == "bye":
                kw["wave"] = 1.0
            elif w in SONG_MOVES:
                h2, sq2, kw2 = _move(w, ph, t, tl)
                hop, sq = (h2, sq2) if (h2 or sq2) else (hop, sq)
                kw.update(kw2)
    elif k == "tiptoe":
        hop = abs(math.sin(tl * math.pi / 0.28)) * 16
        kw.update(look=1.0, lean=6.0, arms=(-20, -20))
    elif k == "walk":
        hop = abs(math.sin(tl * math.pi / 0.3)) * 22
        kw.update(look=1.0, expr="happy", arms=(40 + 25 * math.sin(tl * 10), 40 - 25 * math.sin(tl * 10)))
    elif k == "jumps":
        j = min(2, int(tl / 0.9))
        h, sq = jump((tl - j * 0.9) / 0.9)
        hop = h * (60, 110, 170)[j]
        kw.update(look=1.0, look_y=-1.0, arms=(150, 150), expr="neutral", sweat=0.6 * (j == 2))
    elif k == "peek":
        side = 1 if tl < 1.3 else -1
        kw.update(look=-side * 1.0 if tl % 1.3 > 0.7 else side * 1.0, expr="listen", lean=4 * side, sweat=0.8)
    elif k == "zoom":
        a = 2 * math.pi * 2 * r.clamp01(tl / s["dur"])
        kw.update(expr="surprised", look=math.cos(a), sweat=1.0, arms=(130 + 20 * math.sin(t * 20),) * 2)
        hop = abs(math.sin(tl * 9)) * 18
    elif k == "fall":
        kw.update(expr="surprised", look=1.0)
        t0 = 0.45 if s.get("bonk") else 0.0
        if tl < t0:
            hop, kw["look_y"] = 0.0, -1.0
        elif tl < t0 + 0.35:
            hop, kw["arms"] = 100 * math.sin((tl - t0) / 0.35 * math.pi / 2), (150, 150)
        elif tl < t0 + 0.6:
            x2 = (tl - t0 - 0.35) / 0.25
            hop, kw["lean"], kw["arms"] = 100 * (1 - x2), -14 * x2, (150, 150)
        else:
            hop, sq, dy, kw["lean"] = 0.0, 0.14, 26.0, -14.0
            kw["dizzy"] = 1 - r.clamp01((tl - 1.2) / 0.4)
            kw["arms"] = (60, 60)
    elif k in ("fly", "hopout"):
        kw.update(expr="surprised", look=1.0, look_y=-1.0 if (k == "fly" and tl > 0.4) else 0.0)
    elif k == "join":
        hop = abs(math.sin(tl * 10)) * 18
        kw["expr"] = "happy"
    elif k == "pause":
        kw.update(expr="listen", arms=(20, 165), look=0.0)
    elif k == "surprise":
        kw.update(expr="surprised", arms=(150, 150))
        hop = 60 * math.sin(r.clamp01(tl / 0.5) * math.pi)
    elif k == "action":
        ph = (tl % 0.8) / 0.8
        h2, sq, kw2 = _move(s["verb"], ph, t, tl)
        hop = h2
        kw.update(kw2)
        kw["expr"] = "happy"
    if s.get("sit"):
        hop, sq, dy, kw["lean"] = 0.0, 0.14, 26.0, -14.0 * (1 - r.clamp01((tl - (s["dur"] - 0.4)) / 0.4))
        kw["dizzy"] = 0.0
    if s.get("bonk") and k == "say" and tl < 0.3:
        sq = 0.12 * math.sin(tl / 0.3 * math.pi)
    if s.get("surprise") and k == "say":
        kw.update(expr="surprised", look=1.0)
        if tl < 0.5:
            hop = 60 * math.sin(tl / 0.5 * math.pi)
    if kw["excited"] and k == "say":
        hop = abs(math.sin(tl * 7)) * 40
    return x, hop, sq, dy, kw


def _eyes_k(P, s, t, i):
    if t >= P.shown_from[i] or s.get("peek") == i:
        return 0.0
    if s.get("eyes") == i or (s.get("eyes_all") and i == 0):
        return 1.0
    if s["kind"] == "song" and s["phase"] in ("hello", "dance"):
        return r.clamp01((math.sin(t * 1.3 + i * 2.1) - 0.2) * 3)
    return 0.0


def draw(c, t, P, meadow, spr, f, fw=r.W, fh=r.H, short=None):
    """fw x fh tuvale bir kare. short=i: dikey Shorts kadraji (i. oyun), yakin plan + ust baslik."""
    s = _seg_at(P.segs, t)
    tl = t - s["start"]
    if s["kind"] == "song":
        idx = sum(1 for x in s["starts"] if x <= tl)
        spec = s["shots"][min(idx, len(s["shots"]) - 1)]
    else:
        spec = s.get("shot", ("wide",))
    zmin = 1.0
    if short is not None:
        spec = _short_spec(spec, s, P, short)
        zmin = fh / r.H                                # dunyanin tam yuksekligi kadraja oturur
    cx, cy, z = _camera(spec, t, P, fw, fh, zmin)

    shake = 0.0
    cw = _cur_word(s, tl) if s["kind"] == "song" else None
    if cw and s["phase"] == "dance" and cw[2] == "stomp":
        shake = 12 * math.exp(-(tl - cw[0]) / 0.15) * math.sin((tl - cw[0]) * 60)
    if s["kind"] == "action" and s["verb"] == "stomp":
        ph = (tl % 0.8)
        shake = 10 * math.exp(-ph / 0.15) * math.sin(ph * 60)

    c.save()
    c.translate(fw / 2, fh / 2 + shake)
    c.scale(z, z)
    c.translate(-cx, -cy)
    meadow.draw(c, t, P.cam.at(t) + 20 * math.sin(t * 0.3))

    beat_hop = 0.0
    if s["kind"] == "song":
        h, _ = jump((tl / s["beat"]) % 1.0)
        beat_hop = h * 26
    nA = len(P.finds)

    def animal_state(i):
        x, y, size = P.animal[i].at(t)
        x0, y0, _ = P.animal[i].at(t - 1.0 / FPS)
        m = float(P.amouth[i][min(f, len(P.amouth[i]) - 1)])
        rot, sx, sq, hop = 2 * math.sin(t * 1.7 + i), 1.0, 0.0, 0.0
        if t > P.front_from[i]:
            hop += beat_hop
            v = math.hypot(x - x0, y - y0) * FPS
            if 40 < v and y > GY - 400:
                hop += abs(math.sin(t * 14)) * 22
                sq = 0.06 * math.sin(t * 28)
            if s["kind"] == "walk":
                hop += abs(math.sin(tl * math.pi / 0.3 + i)) * 14
        if s.get("celebrate") == i:
            mode = i % 3
            if mode == 0:
                rot, hop = 12 * math.sin(tl * 9), hop + abs(math.sin(tl * 9)) * 30
            elif mode == 1:
                x, rot = x + 25 * math.sin(tl * 8), 10 * math.sin(tl * 16)
            else:
                rot = 720 * r.ease_in_out(tl / 1.0)
        if s["kind"] == "action" and s.get("actor") == i:
            verb, ph = s["verb"], (tl % 0.8) / 0.8
            if verb in ("hop", "flap"):
                hh, sq = jump(ph)
                hop += hh * (90 if verb == "hop" else 50)
                if verb == "flap":
                    rot = 10 * math.sin(t * 18)
            elif verb == "spin":
                rot = 360 * r.ease_in_out((tl % 1.0) / 0.8)
            elif verb == "stomp":
                sq = 0.18 * math.exp(-(tl % 0.8) / 0.12)
            else:
                x, rot = x + 22 * math.sin(t * 9), 12 * math.sin(t * 9)
                hop += 12 * abs(math.sin(t * 9))
        if s.get("shake_no") == i:
            rot = 15 * math.sin(tl * 20)
        if s.get("all_hop") and t > P.front_from[i]:
            hh, sq2 = jump((tl + 0.1 * i) / 0.8)
            hop, sq = hop + hh * 90, sq2
        if s.get("recap") == i:
            size *= 1.12 + 0.04 * math.sin(t * 8)
        if t < P.front_from[i] and P.hide[i]["kind"] in ("cloud", "tree"):
            sx = -1.0                                  # saga dogru bakarken bas once ciksin (Fluent sola bakar)
        if s["kind"] == "zoom" and s.get("actor") == i:
            x, y, _, vx = _zoom_pos(s, tl)
            sx = 1.0 if vx < 0 else -1.0
        return x, y - hop - 6 * math.sin(t * 2.5 + i) - m * 10, size, rot, sx, sq, m

    def draw_animal(i):
        x, y, size, rot, sx, sq, m = animal_state(i)
        feet = y + size * 0.42
        shadow = min(GY + 8, feet + 6) if (t > P.front_from[i] and feet > GY - 220) else None
        spr.draw(c, P.finds[i]["animal"], x, y, size, rot=rot + 6 * m * math.sin(t * 9),
                 sx=sx * (1 + 0.5 * sq - 0.04 * m), sy=1 - sq + 0.08 * m, shadow_y=shadow)

    on_head = next((h for h in P.on_head if h[0] <= t < h[1]), None)
    zoom_actor = s.get("actor") if s["kind"] == "zoom" else None
    zoom_front = zoom_actor is not None and _zoom_pos(s, tl)[2]

    for i in range(nA):                                   # saklanma yerinin arkasindakiler
        if P.shown_from[i] <= t < P.front_from[i]:
            draw_animal(i)
    if s.get("peek") is not None:                         # agacin iki yanindan bakis (govde kirpar)
        i = s["peek"]
        hx = _hx(P, i, t)
        side = 1 if tl < 1.3 else -1
        out = math.sin(math.pi * r.clamp01((tl % 1.3) / 1.1))
        c.save()
        c.clipRect(r.skia.Rect.MakeXYWH(hx if side > 0 else hx - 6000, -2000, 6000, 6000))
        spr.draw(c, P.finds[i]["animal"], hx + side * (60 - 125 + 125 * out), GY - 130, 250,
                 sx=-1.0 if side > 0 else 1.0, rot=-side * 8 * out)
        c.restore()

    for i in range(nA):                                   # saklanma yerleri (ekranda olanlar)
        hx = _hx(P, i, t)
        if not (-500 < hx < r.W + 500):
            continue
        kind = P.hide[i]["kind"]
        h = HIDES[kind]
        wig = 1.0 if s.get("wiggle") == i else 0.0
        if s["kind"] == "song" and t < P.shown_from[i]:
            wig = max(wig, 0.6 * math.exp(-((tl + i * s["beat"] / 3) % s["beat"]) / 0.15))
        lift = 0.0
        for bi, a, d in P.bush_hops:
            if bi == i and a <= t < a + d:
                lift, wig = 120 * math.sin(math.pi * (t - a) / d), 0.5
        if kind == "bush":
            r.bush(c, hx, h["y"] - lift, 1.0, wiggle=wig, t=t)
        elif kind == "tree":
            r.big_tree(c, hx, h["y"], 1.0, shake=wig, t=t)
        else:
            r.cloud(c, hx, h["y"], 1.6, wiggle=wig, t=t)
        r.peek_eyes(c, hx, h["y"] + h["eyes_dy"] - lift, t, k=_eyes_k(P, s, t, i) * h["ek"], look=-1.0,
                    hollow=rgbt(h["hollow"]))

    for i in range(nA):                                   # ondeki hayvanlar
        if t >= P.front_from[i] and not (on_head and on_head[2] == i) and not (zoom_front and zoom_actor == i):
            draw_animal(i)
    for name, x, a, b in P.extras:                        # dans molasi misafirleri
        if a <= t < b:
            k = r.ease_out_back((t - a) / 0.45)
            hop, sq = 0.0, 0.0
            if cw and cw[2] in SONG_MOVES:
                ph = (tl - cw[0]) / max(0.05, cw[3] - cw[0])
                if cw[2] in ("hop", "jump"):
                    hh, sq = jump(ph)
                    hop = hh * 140
                elif cw[2] == "stomp":
                    sq = 0.18 * math.exp(-(tl - cw[0]) / 0.12)
                else:
                    hop = 20 * abs(math.sin(t * 8))
            spr.draw(c, name, x, GY - 130 - hop, 250 * k, rot=6 * math.sin(t * 4), sx=1 + 0.5 * sq, sy=1 - sq,
                     shadow_y=GY + 8)

    x, hop, sq, dy, kw = _dino_pose(P, s, t, tl, f)
    r.dino_shadow(c, x, GY, lift=hop)
    r.dino(c, x, DINO_Y - hop + dy, squash=sq, **kw)
    head_y = DINO_Y - hop + dy - 170 * (1 - sq)
    if on_head:
        i = on_head[2]
        m = float(P.amouth[i][min(f, len(P.amouth[i]) - 1)])
        spr.draw(c, P.finds[i]["animal"], x + 10, head_y - 65 - 8 * abs(math.sin(t * 4)), 200,
                 rot=5 * math.sin(t * 3), sy=1 + 0.08 * m)
    if zoom_front:
        draw_animal(zoom_actor)
    if zoom_actor is not None:
        zx, zy, _, vx = _zoom_pos(s, tl)
        r.speed_lines(c, zx, zy, 1.0, direction=1 if vx > 0 else -1, seed=int(tl * 6))
        r.dust(c, zx - (60 if vx > 0 else -60), GY, tl % 0.3, seed=int(tl / 0.3), life=0.3, spread=0.5)

    for hd in P.head:                                     # kafaya dusenler
        if hd["kind"] == "none" or not (hd["t0"] - 0.7 <= t < hd["t1"]):
            continue
        k = r.clamp01((t - (hd["t0"] - 0.7)) / 0.7)
        tx, ty = x + 15, head_y - hd["size"] * (0.3 if hd["kind"] != "leaf" else 0.05) - 8
        if k < 1:
            px = hd["src"][0] + (tx - hd["src"][0]) * k + (25 * math.sin(k * 9) if hd["kind"] == "leaf" else 0)
            py = hd["src"][1] + (ty - hd["src"][1]) * k * k
        else:
            px, py = tx, ty + 3 * math.sin(t * 4)
        if hd["kind"] == "leaf":
            r.leaf(c, px, py, rot=-20 + 30 * math.sin(t * 2) * (k < 1), s=hd["size"])
        else:
            spr.draw(c, hd["kind"], px, py, hd["size"], rot=4 * math.sin(t * 3))

    if t >= P.finale_t:                                   # final odulu (cerceveye gore)
        a = t - P.finale_t
        if P.frame == "birthday":
            for k, bx in enumerate((1060, 1350, 1640)):
                by = GY - 60 - 140 * a - 30 * k + 10 * math.sin(t * 2 + k)
                if by > -300:
                    spr.draw(c, "balloon", bx, by, 150, rot=6 * math.sin(t * 2 + k))
            y = -200 + (CAKE[1] + 200) * r.ease_out_elastic((a - 0.1) / 1.0)
            spr.draw(c, "cake", CAKE[0], y, CAKE[2], shadow_y=GY + 8)
            r.sparkles(c, CAKE[0], CAKE[1] - 60, (a % 2.2) - 0.3, seed=88, radius=170, n=7)
        elif P.frame == "picnic":
            for k, name in enumerate(FRUITS):
                fx_ = 960 + k * 150
                fy = -200 + (GY - 60 + 200) * r.ease_out_elastic((a - 0.15 * k) / 1.0)
                if a - 0.15 * k > 0:
                    spr.draw(c, name, fx_, fy, 120, rot=8 * math.sin(t * 3 + k), shadow_y=GY + 8)
        else:
            k = r.ease_out_back(a / 0.9)
            spr.draw(c, "rainbow", 1250, 330, 700 * k)
            r.sparkles(c, 1250, 330, (a % 2.0) - 0.2, seed=91, radius=320, n=10)
    if t >= P.sil:
        a = t - P.sil
        spr.draw(c, P.teaser, SIL[0], SIL[1] + 8 * math.sin(t * 2), SIL[2] * r.ease_out_back(a / 0.6), sil=True)
        r.sparkles(c, SIL[0], SIL[1], (a % 2.0) - 0.2, seed=99, radius=200, n=8)

    for kind, t0, ex, ey, seed in P.fx:
        age = t - t0
        if age < 0 or age > 2.0:
            continue
        if ex is None:
            ex, ey = x, head_y - 40
        if kind == "poof":
            r.poof(c, ex, ey, age)
        elif kind == "confetti":
            r.confetti(c, ex, ey, age, seed=seed)
        elif kind == "sparkle":
            r.sparkles(c, ex, ey, age, seed=seed, radius=210)
        elif kind == "dust":
            r.dust(c, ex, ey, age, seed=seed)
        elif kind == "leaves":
            r.leaves(c, ex, ey, age, seed=seed)
    c.restore()

    if short is not None:                             # Shorts arayuzu: ust baslik, orta-alt altyazi
        import thumbs                                 # (alt ~%25 Shorts dugmeleri/aciklamasiyla kapali)
        fnd = P.finds[short]
        thumbs._text(c, f"WHO SAYS {fnd['says'].upper()}?", fw / 2, 230, fw - 120, size=120, rot=-3)
        if "text" in s and s["kind"] != "song":
            r.caption(c, s["text"], key=s.get("key"), key_color=s.get("color", r.rgb(235, 70, 70)),
                      y=int(fh * 0.70), cw=fw)
        if s["kind"] == "pause":
            r.ask_bubble(c, fw * 0.74, fh * 0.30, tl / 0.35, tl / s["dur"], t)
        return
    if s["kind"] == "song":
        r.karaoke(c, s["lines"], s["timings"], tl)
        if s["phase"] == "bye":
            r.iris(c, r.W / 2 + (x - cx) * z, r.H / 2 + (DINO_Y - 60 - cy) * z, (tl - (s["dur"] - 1.3)) / 1.2)
    elif "text" in s:
        r.caption(c, s["text"], key=s.get("key"), key_color=s.get("color", r.rgb(235, 70, 70)))
    if s["kind"] == "pause":
        r.ask_bubble(c, 1480, 300, tl / 0.35, tl / s["dur"], t)


# ---------------- render ----------------
def render(ep, work, out_mp4, frames_dir=None):
    """Tam uretim. Donus: {"total", "chapters", "P"}. frames_dir verilirse kontrol kareleri kaydedilir."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    P = build(ep, work)
    print(f"Ses hazirligi: {time.time() - t0:.0f} sn; sure {P.total / 60:.2f} dk; segment {len(P.segs)}", flush=True)
    import music
    wav = work / "audio.wav"
    music.write_wav(str(wav), P.audio)

    spr = r.Sprites(outline=14)
    meadow = r.Meadow()
    surf = r.new_surface()
    c = surf.getCanvas()
    n_frames = int(P.total * FPS)
    keys = {}
    if frames_dir:
        Path(frames_dir).mkdir(parents=True, exist_ok=True)
        for k, s in enumerate(P.segs):
            keys[int((s["start"] + s["dur"] * 0.5) * FPS)] = f"{k:03d}_{s['kind']}"
        keys[n_frames - int(0.6 * FPS)] = "999_kapanis"
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{r.W}x{r.H}",
         "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
         "-ar", str(SR), "-shortest", "-movflags", "+faststart", str(out_mp4)],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    t1 = time.time()
    try:
        for fr in range(n_frames):
            t = fr / FPS
            c.clear(r.rgb(0, 0, 0))
            draw(c, t, P, meadow, spr, fr)
            data = r.frame_bytes(surf)
            ff.stdin.write(data)
            if fr in keys:
                Image.frombytes("RGBA", (r.W, r.H), data).convert("RGB").save(Path(frames_dir) / f"kare_{keys[fr]}.png")
    finally:
        ff.stdin.close()
    err = ff.stderr.read().decode(errors="ignore")
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg hatasi:\n" + err[-1500:])
    print(f"Render: {n_frames} kare, {(time.time() - t1) / n_frames * 1000:.0f} ms/kare", flush=True)
    return {"total": P.total, "chapters": P.chapters, "P": P}


def estimate_seconds(ep):
    return build(ep, "/tmp", estimate=True).total


# ---------------- Shorts (7e) ----------------
SW, SH = 1080, 1920


def pick_shorts(P, n=2):
    """En komik n oyun: saka buyuklugu en yuksek olanlar (esitlikte erken olan). Donus: oyun indeksleri."""
    order = sorted(range(len(P.finds)), key=lambda i: (-GAGS[P.finds[i]["gag"]][2], i))
    return sorted(order[:n])


def render_shorts(P, work, n=2, frames_dir=None):
    """Bolumden n dikey Short: ayni zaman cizelgesi ve AYNI ses (yeniden seslendirme yok), sahne dikey
    kadraja yakin planla yeniden cizilir. Donus: [{"path", "find", "dur"}]."""
    import music
    work = Path(work)
    spr = r.Sprites(outline=14)
    meadow = r.Meadow()
    surf = skia_surface(SW, SH)
    c = surf.getCanvas()
    out = []
    for i in pick_shorts(P, n):
        t0, t1 = P.spans[i]
        t0, t1 = max(0.0, t0 - 0.1), t1 + 0.4
        a = P.audio[int(t0 * SR): int(t1 * SR)].copy()
        fade = int(0.08 * SR)
        a[:fade] *= np.linspace(0, 1, fade)
        a[-fade:] *= np.linspace(1, 0, fade)
        wav = work / f"short_{i}.wav"
        music.write_wav(str(wav), a)
        mp4 = work / f"short_{i}.mp4"
        ff = subprocess.Popen(
            ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{SW}x{SH}",
             "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
             "-ar", str(SR), "-shortest", "-movflags", "+faststart", str(mp4)],
            stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        f0, f1 = int(t0 * FPS), int(t1 * FPS)
        keys = {f0 + 2: "a", (f0 + f1) // 2: "b", f1 - 12: "c"}
        try:
            for fr in range(f0, f1):
                c.clear(r.rgb(0, 0, 0))
                draw(c, fr / FPS, P, meadow, spr, fr, fw=SW, fh=SH, short=i)
                img = surf.makeImageSnapshot()
                arr = img.toarray(colorType=r.skia.kRGBA_8888_ColorType, alphaType=r.skia.kUnpremul_AlphaType)
                data = np.ascontiguousarray(arr).tobytes()
                ff.stdin.write(data)
                if frames_dir and fr in keys:
                    Image.frombytes("RGBA", (SW, SH), data).convert("RGB").save(
                        Path(frames_dir) / f"short_{i}_{keys[fr]}.png")
        finally:
            ff.stdin.close()
        err = ff.stderr.read().decode(errors="ignore")
        if ff.wait() != 0:
            raise RuntimeError("ffmpeg (short) hatasi:\n" + err[-1500:])
        out.append({"path": str(mp4), "find": i, "dur": t1 - t0})
        print(f"Short {i} ({P.finds[i]['animal']}): {t1 - t0:.1f} sn", flush=True)
    return out


def skia_surface(w, h):
    return r.skia.Surface(w, h)
