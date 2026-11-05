"""
Pilot bolum (todo 7b/7c): "Thumpy formulu" -- docs/arastirma-cocuk-izleme.md bolum 12.
Uretime bagli degil, YUKLEME YOK. Senaryo elle yazildi ve kullanici onayindan gecti.

Hikaye: Dino'nun dogum gunu; arkadaslari sakli (surpriz). Selam sarkisi (0. sn) -> yardim ister
(soru + bekleme) -> inek (cali), ordek (bulut), kopek (agac): ses ipucu -> "Who says ...?" + bekleme
-> gag (her biri bir oncekinden buyuk) -> cevap + kelime 3 kez + tekrar ettirme -> hareket molasi
-> tekrar (cocuk tamamlar) -> "Surprise!" + pasta + tac -> sonraki bolum silueti -> veda sarkisi.
Tekrar eden saka: Dino'nun kafasina bir seyler duser (yaprak -> ordek -> elma -> tac).
Hayvan sesleri gercek kayit (animal_sounds.py, CC0); hayvanlar konusmaz.
Cikti: out/pilot.mp4, out/pilot_report.txt, out/pilot_smoke.png, out/kare_*.png
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
import assets
import render2 as r

OUT = Path("out")
FPS = 24
SR = 44100
VOICE = os.environ.get("TTS_VOICE", "en-US-AnaNeural")
GY = r.GROUND_Y

# ---------------- senaryo ----------------
# Sarkilar: kamu mali melodi + bizim sozler. Satir basina hece = melodideki nota sayisi
# (jacques 8/6/12/6, london 7/6/7/4, twinkle 7/7). Tum kelimeler CMU sozlugunde (kontrol edildi).
HELLO = ("jacques", ["Hello Dino, hello Dino", "Come and play! Come and play!",
                     "Jump, jump, jump, jump, clap, clap, jump, jump, jump, jump, clap, clap",
                     "Hi! Hello! Hi! Hello!"])
DANCE = ("london", ["Let's all hop like bunnies now", "Hop, hop, hop! Hop, hop, hop!",
                    "Let's all stomp like elephants", "Stomp, stomp, stomp, stomp!"])
BYE = ("twinkle", ["Bye bye friends, it's time to go", "Wave goodbye, we love you so"])

ANIMALS = [
    dict(name="cow", says="moo", sound="Moo! Moo!", short="Moo!", color=r.rgb(150, 90, 200)),
    dict(name="duck", says="quack", sound="Quack! Quack!", short="Quack!", color=r.rgb(230, 150, 20)),
    dict(name="dog", says="woof", sound="Woof! Woof!", short="Woof!", color=r.rgb(215, 95, 40)),
]

# ---------------- sahne yerlesimi ----------------
DINO_HOME = 700
DINO_Y = GY - 175                       # govde merkezi (ayaklar zeminde)
# saklanma yerleri: inek cali, ordek bulut, kopek agac
HIDE = [
    dict(kind="bush", x=1120, y=GY + 10, eyes=(1120, GY - 130), hollow=r.rgb(35, 70, 40), ek=1.0,
         stage=(1120, GY - 150, 300), line="Look! The bush is wiggling!"),
    dict(kind="cloud", x=1180, y=200, eyes=(1180, 215), hollow=r.rgb(190, 210, 238), ek=1.0,
         stage=(1180, GY - 140, 260), line="Look! The cloud is wiggling!"),
    dict(kind="tree", x=1680, y=GY + 10, eyes=(1680, GY - 190), hollow=r.rgb(75, 45, 28), ek=0.72,
         stage=(1680, GY - 150, 280), line="Look! The tree is shaking!"),
]
TREE_TOP = (1600, 380)                  # elmanin dustugu yer
FRIEND = [(90, GY - 170, 140), (225, GY - 170, 140), (360, GY - 170, 140)]    # kurtarilan arkadaslar
ROW = [(980, GY - 150, 250), (1300, GY - 150, 250), (1620, GY - 150, 250)]     # tekrar sirasi
CAKE = (1140, GY - 95, 220)
SIL = (1300, 300, 300)                  # sonraki bolum: aslan silueti


def save_png(surface, path):
    Image.frombytes("RGBA", (r.W, r.H), r.frame_bytes(surface)).convert("RGB").save(path)


# ---------------- hareket yardimcilari ----------------
class Track:
    """Zamana bagli deger (sayi ya da demet). hold: degeri t'ye kadar tut; to: t'de v'ye var
    (yumusak gecis); jump: t'de aninda v'ye gec. Anahtarlar kronolojik eklenir."""

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
    """Tek ziplama (ph 0..1): comelme (hazirlik) -> havada (uzama) -> inis (basilma).
    Donus: (yukseklik 0..1, squash)."""
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


def tts(text, name, rate="-5%", pitch="+0Hz"):
    """edge-tts -> mono numpy. Bastaki/sondaki sessizlik kirpilir."""
    p = OUT / "tts" / f"{name}.mp3"
    p.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            asyncio.run(_tts_save(text, str(p), rate, pitch))
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    on = np.nonzero(np.abs(x) > 0.02 * (np.max(np.abs(x)) or 1.0))[0]
    if len(on):
        x = x[max(0, on[0] - int(0.03 * SR)): on[-1] + int(0.08 * SR)]
    return x


def mouth_track(speech, n_frames):
    """Kare basina agiz acikligi 0..1 (konusma zarfi, hizli acilip yavas kapanir)."""
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
    def __init__(self):
        self.t = 0.0
        self.segs = []
        self.audio = []          # (kanal, sinyal, baslangic): "dino" | "narr" | 0..2 | "song" | "sfx"
        self.n = 0

    def seg(self, kind, dur, **kw):
        s = dict(kind=kind, start=self.t, dur=dur, **kw)
        s["end"] = self.t + dur
        self.segs.append(s)
        self.t += dur
        return s

    def say(self, text, gap=0.35, who="dino", **kw):
        """Dino (agiz oynar) ya da anlatici ('narr', agiz oynamaz) konusur."""
        self.n += 1
        clip = tts(text, f"{self.n:03d}_{who}")
        s = self.seg("say", len(clip) / SR + gap, who=who, text=text, **kw)
        self.audio.append((who, clip, s["start"] + 0.05))
        return s

    def animal(self, i, n=1, gap=0.3, **kw):
        """Hayvanin gercek sesi (n cagri). Altyazi: 'Moo! Moo!' ya da 'Moo!'."""
        a = ANIMALS[i]
        clip = animal_sounds.clip(a["name"], n)
        text = a["sound"] if n > 1 else a["short"]
        s = self.seg("say", len(clip) / SR + gap, who=i, text=text, key=a["says"], color=a["color"], **kw)
        self.audio.append((i, clip, s["start"] + 0.05))
        return s

    def pause(self, dur, text, **kw):
        return self.seg("pause", dur, text=text, **kw)

    # ---- ses efektleri (CC0 ornekler, samples.py) ----
    def sfx(self, sig, t):
        self.audio.append(("sfx", sig, t))

    def rustle(self, t, dur):
        import samples
        for k in range(int(dur / 0.11)):
            self.sfx(samples.hit("shaker_down" if k % 2 == 0 else "shaker_up", 0.55), t + k * 0.11)

    def boing(self, t, v=0.7):
        import samples
        self.sfx(samples.hit("boing", v), t)

    def bell(self, t):
        import samples
        self.sfx(samples.hit("belltree", 0.5), t)

    def tada(self, t):
        import samples
        self.bell(t)
        for k, m in enumerate((72, 76, 79, 84)):
            self.sfx(samples.note("glock", m, 0.45, max_dur=0.6), t + 0.02 + k * 0.07)

    def claps(self, t):
        import samples
        for k in range(4):
            self.sfx(samples.hit("clap", 0.9), t + k * 0.22)

    def thud(self, t):
        import samples
        self.sfx(samples.hit("kick", 0.9), t)
        self.boing(t + 0.05, 0.5)

    def whistle(self, t):
        import samples
        self.sfx(samples.hit("whistle", 0.7), t)

    def twinkle(self, t):
        import samples
        for k, m in enumerate((91, 84, 96, 91)):
            self.sfx(samples.note("glock", m, 0.35, max_dur=0.5), t + k * 0.18)

    def ding(self, t, m=84):
        import samples
        self.sfx(samples.note("glock", m, 0.5, max_dur=0.8), t)

    def slide(self, t, up=True):
        import samples
        notes = (72, 74, 76, 79, 81, 84) if up else (84, 81, 79, 76, 74, 72)
        for k, m in enumerate(notes):
            self.sfx(samples.note("xylo", m, 0.5, max_dur=0.2), t + k * 0.07)

    def tiptoe(self, P, target, i):
        """Dino parmak ucunda saklanma yerine gider (klasik cizgi film pizzicato adimlari)."""
        import samples
        s = self.seg("tiptoe", 1.7, shot=("two", i))
        P.dino_x.hold(s["start"])
        P.dino_x.to(s["start"] + 1.6, target)
        for k in range(6):
            self.sfx(samples.note("bass", 45 if k % 2 == 0 else 52, 0.8, max_dur=0.25), s["start"] + k * 0.28)


def song_seg(tl, phase, spec, shots):
    import kidsong
    import vocal_break
    key, lines = spec
    audio, timings, dur = vocal_break.render(lines, key)
    beat, starts, _ = kidsong.timing(key, len(lines))
    words = [(st, li, lines[li].split()[wi].strip(".,!?").lower()) for li, wi, st in timings]
    s = tl.seg("song", dur, phase=phase, lines=lines, timings=timings, beat=beat, starts=starts,
               words=words, shots=shots)
    tl.audio.append(("song", audio, s["start"]))
    return s


def head_item(P, kind, t0, src, size):
    """Dino'nun kafasina dusen sey (tekrar eden saka). Oncekini kaldirir (puf)."""
    for h in P.head:
        if h["t1"] > t0:
            h["t1"] = t0
            P.fx.append(("poof", t0, None, None, 0))       # konum cizimde Dino'nun basi
    P.head.append(dict(kind=kind, t0=t0, t1=1e9, src=src, size=size))


# ---------------- dersler ----------------
def gag_cow(tl, P, i):
    """Kucuk saka: inek calinin ustunden cikar, Dino hafifce dusar, kafasina yaprak konar."""
    h = HIDE[i]
    tl.tiptoe(P, h["x"] - 250, i)
    tl.say("Hmm? Nobody here.", expr="listen", look=1.0, lean=8, shot=("two", i))
    s = tl.animal(i, 1, shot=("two", i), surprise=True)
    tr = P.animal[i]
    tr.jump(s["start"], (h["x"], GY - 60, 300))
    tr.to(s["start"] + 0.45, (h["x"], GY - 300, 300))
    P.shown_from[i] = s["start"]
    P.fx.append(("poof", s["start"] + 0.3, h["x"], GY - 300, 0))
    tl.boing(s["start"])
    s = tl.seg("fall", 1.5, shot=("two", i))
    tl.whistle(s["start"])
    tl.thud(s["start"] + 0.58)
    tl.twinkle(s["start"] + 0.7)
    x = P.dino_x.at(s["start"])
    P.fx.append(("dust", s["start"] + 0.58, x, GY, 1))
    head_item(P, "leaf", s["start"] + 0.75, (h["x"] - 60, GY - 230), 1.6)
    tl.say("Ha ha! You got me!", expr="happy", sit=True, shot=("two", i))


def gag_duck(tl, P, i):
    """Orta saka: Dino buluta yetismek icin 3 kez ziplar, yanlis tahmin eder, ordek kafasina konar."""
    h = HIDE[i]
    tl.tiptoe(P, h["x"] - 200, i)
    tl.say("Hmm? Up there?", look=1.0, look_y=-1.0, shot=("two", i))
    s = tl.seg("jumps", 2.7, shot=("two", i))
    x = P.dino_x.at(s["start"])
    for k in range(3):
        a = s["start"] + k * 0.9
        tl.boing(a + 0.15, 0.5 + 0.15 * k)
        P.fx.append(("dust", a + 0.75, x, GY, 10 + k))
    tl.say("It's too high!", expr="surprised", sweat=1.0, shot=("two", i))
    tl.say("Is it a lion? Roar!", arms=(140, 140), expr="happy", look=1.0, look_y=-1.0, shot=("two", i))
    s = tl.animal(i, 1, shake_no=i, shot=("two", i))           # ordek buluttan basini cikarir: "hayir!"
    tr = P.animal[i]
    tr.jump(s["start"], (h["x"] + 70, 215, 200))
    tr.to(s["start"] + 0.35, (h["x"] + 170, 215, 200))
    P.shown_from[i] = s["start"]
    s = tl.seg("fly", 1.4, shot=("two", i), surprise=True)
    dx = P.dino_x.at(s["start"])
    tr.hold(s["start"])
    tr.to(s["start"] + 0.6, (dx + 260, 300, 210))
    tr.to(s["start"] + 1.25, (dx + 10, DINO_Y - 235, 210))
    P.front_from[i] = s["start"]
    tl.slide(s["start"], up=False)
    tl.boing(s["start"] + 1.25)
    tl.animal(i, 1, look_y=-1.0, expr="surprised", shot=("two", i), bonk=True)
    head_item(P, "none", s["start"] + 1.25, (0, 0), 0)          # yaprak puf olur, ordek onun yerinde
    tl.say("Ha ha! Hello, duck!", expr="happy", look_y=-1.0, shot=("two", i))
    P.on_head = (s["start"] + 1.25, tl.t, i)


def gag_dog(tl, P, i):
    """Buyuk saka: kopek agacin iki yanindan bakar, firlar, Dino'nun etrafinda doner,
    agactan elma kafasina duser, Dino basi donerek yere oturur."""
    h = HIDE[i]
    tl.tiptoe(P, h["x"] - 280, i)
    tl.say("Hmm? Where are you?", expr="listen", look=1.0, sweat=0.8, shot=("two", i))
    s = tl.seg("peek", 2.6, shot=("two", i), peek=i)
    tl.ding(s["start"] + 0.2, 84)
    tl.ding(s["start"] + 1.5, 79)
    s = tl.animal(i, 2, shot=("wide",))
    dx = P.dino_x.at(s["start"])
    P.animal[i].jump(s["start"], (dx + 280, GY - 125, 260))
    P.shown_from[i] = P.front_from[i] = s["start"]
    P.fx += [("poof", s["start"], dx + 280, GY - 125, 0), ("dust", s["start"] + 0.1, dx + 280, GY, 20)]
    tl.whistle(s["start"])
    s = tl.seg("zoom", 2.6, shot=("wide",), cx=dx, sweat=1.0)
    for k in (0.4, 1.5):
        tl.audio.append((i, animal_sounds.clip("dog", 1), s["start"] + k))
    s = tl.seg("fall", 1.6, shot=("two", i), bonk=True)
    head_item(P, "apple", s["start"] + 0.45, TREE_TOP, 110)
    tl.boing(s["start"] + 0.45, 0.9)
    tl.thud(s["start"] + 0.75)
    tl.twinkle(s["start"] + 0.85)
    P.fx.append(("dust", s["start"] + 0.75, dx, GY, 21))
    tl.say("Whoa! Ha ha! Hello, dog!", expr="happy", sit=True, shot=("two", i))


GAGS = [gag_cow, gag_duck, gag_dog]


def lesson(tl, P, i):
    a, h = ANIMALS[i], HIDE[i]
    name, says, col = a["name"], a["says"], a["color"]
    s = tl.say(h["line"], expr="surprised", look=1.0, wiggle=i, shot=("two", i))
    tl.rustle(s["start"], s["dur"])
    if h["kind"] == "bush":
        P.fx.append(("leaves", s["start"] + 0.2, h["x"], h["eyes"][1] - 40, 50 + i))
    elif h["kind"] == "tree":
        P.fx.append(("leaves", s["start"] + 0.2, TREE_TOP[0], TREE_TOP[1], 50 + i))
    tl.say("Shh... listen!", expr="listen", arms=(20, 165), look=1.0, shot=("two", i))
    tl.animal(i, 2, wiggle=i, eyes=i, shot=("hide", i))
    tl.say(f"Who says {says}?", key=says, color=col, shot=("dino",))
    tl.pause(2.6, f"Who says {says}?", key=says, color=col, shot=("dino",))
    GAGS[i](tl, P, i)

    # cevap: hayvan sahnenin onune gelir, kendine ozgu kutlama, kelime 3 kez + tekrar ettirme
    s = tl.say(f"It's a {name}! The {name} says {says}!", key=name, color=col,
               expr="happy", excited=True, shot=("animal", i))
    tr = P.animal[i]
    tr.hold(s["start"])
    tr.to(s["start"] + 0.6, h["stage"])
    P.front_from[i] = min(P.front_from[i], s["start"])
    st = h["stage"]
    P.fx += [("confetti", s["start"] + 0.5, st[0], st[1], 11 + i), ("sparkle", s["start"] + 0.55, st[0], st[1], i)]
    tl.tada(s["start"] + 0.5)
    tl.animal(i, 1, celebrate=i, shot=("animal", i))
    tl.say(f"Can you say {name}?", key=name, color=col, shot=("dino",))
    tl.pause(2.0, f"Can you say {name}?", key=name, color=col, shot=("dino",))
    s = tl.say(f"{name.capitalize()}! Great job!", key=name, color=col, expr="happy", excited=True,
               shot=("wide",))
    tl.claps(s["start"])
    P.fx.append(("sparkle", s["start"], P.dino_x.at(s["start"]), DINO_Y - 60, 30 + i))

    # arkadas sirasina katilir, Dino evine doner
    s = tl.seg("join", 1.3, shot=("wide",))
    tr.hold(s["start"])
    tr.to(s["end"], FRIEND[i])
    P.dino_x.hold(s["start"])
    P.dino_x.to(s["end"], DINO_HOME)


def dance(tl, P):
    s = tl.say("Dance break! Stand up and dance with me!", excited=True, expr="happy", shot=("wide",))
    P.dino_x.hold(s["start"])
    P.dino_x.to(s["start"] + 0.8, 760)
    s = song_seg(tl, "dance", DANCE, [("wide",), ("wide",), ("pt", 1150, 600, 1.5), ("wide",),
                                      ("pt", 1520, 600, 1.5)])
    P.extras = [("bunny", 1150, s["start"], s["end"]), ("elephant", 1520, s["start"], s["end"])]
    for _, x, a, b in P.extras:
        P.fx += [("poof", a + 0.1, x, GY - 130, 0), ("poof", b, x, GY - 130, 0)]
    tl.bell(s["start"])
    s = tl.seg("join", 1.0, shot=("wide",))
    P.dino_x.hold(s["start"])
    P.dino_x.to(s["end"], DINO_HOME)


def recap(tl, P):
    s = tl.say("Let's say it together!", excited=True, expr="happy", shot=("wide",))
    for i in range(3):
        P.animal[i].hold(s["start"])
        P.animal[i].to(s["start"] + 0.9, ROW[i])
    for i, a in enumerate(ANIMALS):
        shot = ("pt", ROW[i][0], 560, 1.45)
        s = tl.say(f"The {a['name']} says...", key=a["name"], color=a["color"], shot=shot, recap=i)
        P.fx.append(("sparkle", s["start"], ROW[i][0], ROW[i][1], 40 + i))
        tl.pause(1.8, f"The {a['name']} says...", key=a["name"], color=a["color"], shot=shot, recap=i)
        s = tl.animal(i, 1, shot=shot, recap=i, celebrate=i)
        tl.ding(s["start"])


def finale(tl, P):
    """Dogum gunu odulu: hayvanlar hep birlikte ses verir, pasta, balonlar, Dino'ya tac."""
    tl.say("Thank you for finding my friends!", expr="happy", shot=("wide",))
    s = tl.seg("surprise", 1.6, shot=("wide",), all_hop=True, text="Surprise!")
    for i, a in enumerate(ANIMALS):
        tl.audio.append((i, animal_sounds.clip(a["name"], 1), s["start"] + 0.05 + 0.12 * i))
    tl.bell(s["start"])
    tl.whistle(s["start"] + 0.1)
    P.cake = s["start"] + 0.4
    P.balloons = s["start"] + 0.2
    P.fx += [("confetti", s["start"] + 0.2, 980, 400, 61), ("confetti", s["start"] + 0.3, 1620, 400, 62)]
    tl.say("Surprise! Happy birthday, Dino!", who="narr", expr="surprised", arms=(150, 150),
           shot=("pt", CAKE[0] - 150, 560, 1.35))
    s = tl.say("A cake! For me?", expr="happy", excited=True, shot=("pt", CAKE[0] - 150, 560, 1.35))
    head_item(P, "crown", s["start"] + s["dur"] - 0.2, (DINO_HOME, -150), 150)
    tl.tada(s["start"] + s["dur"] + 0.4)
    s = tl.say("Thank you, friends! I love you!", expr="happy", wave=1.0, shot=("dino",))
    P.fx.append(("sparkle", s["start"], DINO_HOME, DINO_Y - 200, 70))


def teaser(tl, P):
    s = tl.say("Next time, a new friend comes to play!", expr="happy", shot=("wide",))
    P.sil = s["start"]
    tl.slide(s["start"])
    tl.say("Who is it?", look=1.0, look_y=-1.0, shot=("pt", SIL[0], 420, 1.4))
    tl.pause(1.6, "Who is it?", shot=("pt", SIL[0], 420, 1.4))


def build():
    import music
    import samples
    samples.ensure()
    P = SimpleNamespace(dino_x=Track(DINO_HOME),
                        animal=[Track((h["x"], GY - 60, 260)) for h in HIDE],
                        shown_from=[1e9] * 3, front_from=[1e9] * 3, on_head=None,
                        fx=[], extras=[], head=[], cake=1e9, balloons=1e9, sil=1e9)
    tl = TL()

    # 1. kanca + ritueller: 0. saniyede sarki, saklanma yerlerinden bakan gozler (merak)
    song_seg(tl, "hello", HELLO, [("wide",), ("dino",), ("wide",), ("wide",), ("pt", 1350, 560, 1.3)])
    # 2. hikaye: dogum gunu, arkadaslar sakli; Dino dogrudan izleyiciye konusur
    tl.say("Hi friends! I'm Dino!", wave=1.0, expr="happy", shot=("dino",))
    s = tl.say("Today is my birthday!", excited=True, expr="happy", shot=("wide",))
    tl.tada(s["start"] + 0.3)
    P.fx.append(("sparkle", s["start"] + 0.3, DINO_HOME, DINO_Y - 100, 5))
    tl.say("But where are my friends?", expr="surprised", look=1.0, eyes_all=True, shot=("wide",))
    tl.say("Can you help me find them?", shot=("dino",))
    tl.pause(2.2, "Can you help me find them?", shot=("dino",))
    tl.say("Yay! Let's go!", excited=True, expr="happy", shot=("wide",))
    # 3. saklambac (dersler) + hareket molasi
    for i in range(3):
        lesson(tl, P, i)
        if i == 1:
            dance(tl, P)
    # 4. tekrar, odul, ipucu, veda
    recap(tl, P)
    finale(tl, P)
    teaser(tl, P)
    song_seg(tl, "bye", BYE, [("wide",), ("wide",), ("dino",)])
    total = tl.t

    # ---- miks ----
    n = int(total * SR) + SR
    dino_sp, narr = np.zeros(n), np.zeros(n)
    an_sp = [np.zeros(n) for _ in ANIMALS]
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
    an_sp = [x * (nar / _active_rms(x)) * 0.9 for x in an_sp]     # gercek kayitlar konusma seviyesine
    speech = dino_sp + narr + sum(an_sp)
    bg = music.background_track(total)
    gain = np.full(len(bg), 0.20)
    for s in tl.segs:                       # sarki sirasinda fon muzigi sussun (yumusak gecis)
        if s["kind"] == "song":
            gain[int(s["start"] * SR):int(s["end"] * SR)] = 0.0
    gain = np.convolve(gain, np.ones(SR // 4) / (SR // 4), mode="same")
    buf = np.zeros(n)
    buf[:len(bg)] += bg * gain * (nar / _active_rms(bg))
    buf += speech + songs_b * 0.9 * nar + sfx * (nar / _active_rms(sfx)) * 0.5

    n_frames = int(total * FPS)
    P.segs, P.total, P.audio = tl.segs, total, buf[: int(total * SR)]
    P.dmouth = mouth_track(dino_sp, n_frames)
    P.amouth = [mouth_track(x, n_frames) for x in an_sp]
    return P


# ---------------- cizim ----------------
def _seg_at(segs, t):
    for s in segs:
        if s["start"] <= t < s["end"]:
            return s
    return segs[-1]


def _cur_word(s, tl):
    """Sarkida su an soylenen kelime: (baslangic, satir, kelime, sonraki_baslangic) ya da None."""
    words = s["words"]
    for k in range(len(words) - 1, -1, -1):
        if words[k][0] <= tl:
            nxt = words[k + 1][0] if k + 1 < len(words) else words[k][0] + s["beat"]
            return words[k][0], words[k][1], words[k][2], nxt
    return None


def _camera(spec, t, P):
    kind = spec[0]
    if kind == "wide":
        cx, cy, z = r.W / 2, r.H / 2, 1.0
    elif kind == "dino":
        cx, cy, z = P.dino_x.at(t), DINO_Y - 30, 1.55
    elif kind == "hide":
        h = HIDE[spec[1]]
        cx, cy, z = h["eyes"][0], h["eyes"][1] - (30 if h["kind"] == "cloud" else -10), 1.7
    elif kind == "two":
        h = HIDE[spec[1]]
        if h["kind"] == "cloud":
            cx, cy, z = (P.dino_x.at(t) + h["x"]) / 2, 420, 1.15
        else:
            cx, cy, z = (P.dino_x.at(t) + h["x"]) / 2, 610, 1.3
    elif kind == "animal":
        x, y, _ = P.animal[spec[1]].at(t)
        cx, cy, z = x, y - 40, 1.6
    else:                                   # ("pt", x, y, zoom)
        cx, cy, z = spec[1], spec[2], spec[3]
    hw, hh = r.W / 2 / z, r.H / 2 / z
    return min(max(cx, hw), r.W - hw), min(max(cy, hh), r.H - hh), z


def _zoom_pos(s, tl):
    """Kopek Dino'nun etrafinda 2 tur atar. Donus: (x, y, onde_mi, yatay_hiz)."""
    a = 2 * math.pi * 2 * r.clamp01(tl / s["dur"])
    x = s["cx"] + 280 * math.cos(a)
    y = GY - 125 + 40 * math.sin(a)
    return x, y, math.sin(a) > 0, -280 * math.sin(a)


def _dino_pose(P, s, t, tl, f):
    """Donus: (x, yukseklik, squash, asagi_kayma, dino() argumanlari)."""
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
            if s["phase"] == "hello":
                if li in (0, 3):
                    kw["wave"] = 1.0
                elif li == 1:
                    kw["arms"] = (110 + 12 * math.sin(t * 6), 110 + 12 * math.sin(t * 6))
                elif w == "jump":
                    h, sq = jump(ph)
                    hop, kw["arms"] = h * 110, (150, 150)
                elif w == "clap":
                    a = -25 - 35 * math.sin(math.pi * r.clamp01(ph))
                    kw["arms"] = (a, a)
            elif s["phase"] == "dance":
                if w == "hop":
                    h, sq = jump(ph)
                    hop, kw["arms"] = h * 100, (60, 60)
                elif w == "stomp":
                    hop, sq = 0.0, 0.2 * math.exp(-(tl - st) / 0.12)
                    kw["arms"] = (120, 120)
            else:
                kw["wave"] = 1.0
    elif k == "tiptoe":
        hop = abs(math.sin(tl * math.pi / 0.28)) * 16
        kw.update(look=1.0, lean=6.0, arms=(-20, -20))
    elif k == "jumps":                       # 3 ziplama, her biri daha yuksek; sonunda ter
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
        t0 = 0.45 if s.get("bonk") else 0.0           # bonk: once elma basa duser
        if tl < t0:
            hop = 0.0
            kw["look_y"] = -1.0
        elif tl < t0 + 0.35:
            hop, kw["arms"] = 100 * math.sin((tl - t0) / 0.35 * math.pi / 2), (150, 150)
        elif tl < t0 + 0.6:
            x2 = (tl - t0 - 0.35) / 0.25
            hop, kw["lean"], kw["arms"] = 100 * (1 - x2), -14 * x2, (150, 150)
        else:
            hop, sq, dy, kw["lean"] = 0.0, 0.14, 26.0, -14.0
            kw["dizzy"] = 1 - r.clamp01((tl - 1.2) / 0.4)
            kw["arms"] = (60, 60)
    elif k == "fly":
        kw.update(expr="surprised", look=1.0, look_y=-1.0 if tl > 0.4 else 0.0)
    elif k == "join":
        hop = abs(math.sin(tl * 10)) * 18
        kw["expr"] = "happy"
    elif k == "pause":
        kw.update(expr="listen", arms=(20, 165), look=0.0)
    elif k == "surprise":
        kw.update(expr="surprised", arms=(150, 150))
        hop = 60 * math.sin(r.clamp01(tl / 0.5) * math.pi)
    if s.get("sit"):
        hop, sq, dy, kw["lean"] = 0.0, 0.14, 26.0, -14.0 * (1 - r.clamp01((tl - (s["dur"] - 0.4)) / 0.4))
        kw["dizzy"] = 0.0
    if s.get("bonk") and k == "say" and tl < 0.3:           # ordek kafasina kondu: basilma
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
    if s.get("eyes") == i or s.get("eyes_all"):
        return 1.0
    if s["kind"] == "song" and s["phase"] in ("hello", "dance"):
        return r.clamp01((math.sin(t * 1.3 + i * 2.1) - 0.2) * 3)
    return 0.0


def draw(c, t, P, meadow, spr, f):
    s = _seg_at(P.segs, t)
    tl = t - s["start"]
    if s["kind"] == "song":
        idx = sum(1 for x in s["starts"] if x <= tl)
        spec = s["shots"][min(idx, len(s["shots"]) - 1)]
    else:
        spec = s.get("shot", ("wide",))
    cx, cy, z = _camera(spec, t, P)

    # dans molasinda "stomp": ekran sarsintisi
    shake = 0.0
    cw = _cur_word(s, tl) if s["kind"] == "song" else None
    if cw and s["phase"] == "dance" and cw[2] == "stomp":
        shake = 12 * math.exp(-(tl - cw[0]) / 0.15) * math.sin((tl - cw[0]) * 60)

    c.save()
    c.translate(r.W / 2, r.H / 2 + shake)
    c.scale(z, z)
    c.translate(-cx, -cy)
    meadow.draw(c, t, 20 * math.sin(t * 0.3))

    beat_hop = 0.0
    if s["kind"] == "song":
        h, _ = jump((tl / s["beat"]) % 1.0)
        beat_hop = h * 26

    def animal_state(i):
        x, y, size = P.animal[i].at(t)
        x0, y0, _ = P.animal[i].at(t - 1.0 / FPS)
        m = float(P.amouth[i][min(f, len(P.amouth[i]) - 1)])
        rot, sx, sq, hop = 2 * math.sin(t * 1.7 + i), 1.0, 0.0, 0.0
        if t > P.front_from[i]:
            hop += beat_hop
            v = math.hypot(x - x0, y - y0) * FPS
            if 40 < v and y > GY - 400:                       # yururken ziplayarak/esneyerek
                hop += abs(math.sin(t * 14)) * 22
                sq = 0.06 * math.sin(t * 28)
        if s.get("celebrate") == i:                           # hayvana ozgu kutlama
            if i == 0:
                rot, hop = 12 * math.sin(tl * 9), hop + abs(math.sin(tl * 9)) * 30
            elif i == 1:
                x, rot = x + 25 * math.sin(tl * 8), 10 * math.sin(tl * 16)
            else:
                rot = 720 * r.ease_in_out(tl / 1.0)
        if s.get("shake_no") == i:
            rot = 15 * math.sin(tl * 20)
        if s.get("all_hop") and t > P.front_from[i]:
            hh, sq2 = jump((tl + 0.1 * i) / 0.8)
            hop, sq = hop + hh * 90, sq2
        if s.get("recap") == i:
            size *= 1.12 + 0.04 * math.sin(t * 8)
        if s["kind"] == "zoom" and i == 2:
            x, y, _, vx = _zoom_pos(s, tl)
            sx = 1.0 if vx < 0 else -1.0                       # Fluent kopek sola bakar
        return x, y - hop - 6 * math.sin(t * 2.5 + i) - m * 10, size, rot, sx, sq, m

    def draw_animal(i):
        x, y, size, rot, sx, sq, m = animal_state(i)
        feet = y + size * 0.42
        shadow = min(GY + 8, feet + 6) if (t > P.front_from[i] and feet > GY - 200) else None
        spr.draw(c, ANIMALS[i]["name"], x, y, size, rot=rot + 6 * m * math.sin(t * 9),
                 sx=sx * (1 + 0.5 * sq - 0.04 * m), sy=1 - sq + 0.08 * m, shadow_y=shadow)

    on_head = P.on_head is not None and P.on_head[0] <= t < P.on_head[1]
    zoom_front = s["kind"] == "zoom" and _zoom_pos(s, tl)[2]

    # hayvanlar (saklanma yerinin arkasindakiler)
    for i in range(3):
        if P.shown_from[i] <= t < P.front_from[i]:
            draw_animal(i)
    if s.get("peek") is not None:                    # kopek agacin iki yanindan bakar (govde kirpar)
        h = HIDE[2]
        side = 1 if tl < 1.3 else -1
        out = math.sin(math.pi * r.clamp01((tl % 1.3) / 1.1))
        c.save()
        if side > 0:
            c.clipRect(skia_rect(h["x"], -2000, 6000, 6000))
        else:
            c.clipRect(skia_rect(h["x"] - 6000, -2000, 6000, 6000))
        spr.draw(c, "dog", h["x"] + side * (60 - 130 + 130 * out), GY - 130, 260,
                 sx=-1.0 if side > 0 else 1.0, rot=-side * 8 * out)
        c.restore()

    # saklanma yerleri
    for i, h in enumerate(HIDE):
        wig = 1.0 if s.get("wiggle") == i else 0.0
        if s["kind"] == "song" and t < P.shown_from[i]:
            wig = max(wig, 0.6 * math.exp(-((tl + i * s["beat"] / 3) % s["beat"]) / 0.15))
        if h["kind"] == "bush":
            r.bush(c, h["x"], h["y"], 1.0, wiggle=wig, t=t)
        elif h["kind"] == "tree":
            r.big_tree(c, h["x"], h["y"], 1.0, shake=wig, t=t)
        else:
            r.cloud(c, h["x"], h["y"], 1.6, wiggle=wig, t=t)
        ex, ey = h["eyes"]
        r.peek_eyes(c, ex, ey, t, k=_eyes_k(P, s, t, i) * h["ek"], look=-1.0, hollow=h["hollow"])

    # hayvanlar (onde); kosan kopek Dino'nun onundeyse Dino'dan sonra cizilir
    for i in range(3):
        if t >= P.front_from[i] and not (on_head and P.on_head[2] == i) and not (zoom_front and i == 2):
            draw_animal(i)
    for name, x, a, b in P.extras:                   # dans molasi misafirleri
        if a <= t < b:
            k = r.ease_out_back((t - a) / 0.45)
            hop, sq = 0.0, 0.0
            if cw:
                ph = (tl - cw[0]) / max(0.05, cw[3] - cw[0])
                if name == "bunny" and cw[2] == "hop":
                    h, sq = jump(ph)
                    hop = h * 150
                elif name == "elephant" and cw[2] == "stomp":
                    sq = 0.18 * math.exp(-(tl - cw[0]) / 0.12)
            spr.draw(c, name, x, GY - 130 - hop, 260 * k, sx=1 + 0.5 * sq, sy=1 - sq, shadow_y=GY + 8)

    # Dino
    x, hop, sq, dy, kw = _dino_pose(P, s, t, tl, f)
    r.dino_shadow(c, x, GY, lift=hop)
    r.dino(c, x, DINO_Y - hop + dy, squash=sq, **kw)
    head_y = DINO_Y - hop + dy - 170 * (1 - sq)
    if on_head:
        i = P.on_head[2]
        m = float(P.amouth[i][min(f, len(P.amouth[i]) - 1)])
        spr.draw(c, ANIMALS[i]["name"], x + 10, head_y - 65 - 8 * abs(math.sin(t * 4)), 210,
                 rot=5 * math.sin(t * 3), sy=1 + 0.08 * m)
    if zoom_front:
        draw_animal(2)
    if s["kind"] == "zoom":
        zx, zy, _, vx = _zoom_pos(s, tl)
        r.speed_lines(c, zx, zy, 1.0, direction=1 if vx > 0 else -1, seed=int(tl * 6))
        r.dust(c, zx - (60 if vx > 0 else -60), GY, tl % 0.3, seed=int(tl / 0.3), life=0.3, spread=0.5)

    # Dino'nun kafasina dusenler (tekrar eden saka)
    for hd in P.head:
        if hd["kind"] == "none" or not (hd["t0"] - 0.7 <= t < hd["t1"]):
            continue
        k = r.clamp01((t - (hd["t0"] - 0.7)) / 0.7)
        tx, ty = x + 15, head_y - hd["size"] * (0.3 if hd["kind"] != "leaf" else 0.05) - 8
        if k < 1:                                     # dusus (yercekimi: hizlanarak)
            px = hd["src"][0] + (tx - hd["src"][0]) * k + (25 * math.sin(k * 9) if hd["kind"] == "leaf" else 0)
            py = hd["src"][1] + (ty - hd["src"][1]) * k * k
        else:
            px, py = tx, ty + 3 * math.sin(t * 4)
        if hd["kind"] == "leaf":
            r.leaf(c, px, py, rot=-20 + 30 * math.sin(t * 2) * (k < 1), s=hd["size"])
        else:
            spr.draw(c, hd["kind"], px, py, hd["size"], rot=4 * math.sin(t * 3))

    # final: pasta, balonlar, siluet
    if t >= P.balloons:
        a = t - P.balloons
        for k, bx in enumerate((1060, 1300, 1540)):
            by = GY - 60 - 140 * a - 30 * k + 10 * math.sin(t * 2 + k)
            if by > -300:
                c.drawLine(bx, by + 90, bx + 8 * math.sin(t * 3 + k), by + 210, r.paint(r.INK, stroke=4))
                spr.draw(c, "balloon", bx, by, 150, rot=6 * math.sin(t * 2 + k))
    if t >= P.cake:
        a = t - P.cake
        y = -200 + (CAKE[1] + 200) * r.ease_out_elastic(a / 1.0)
        spr.draw(c, "cake", CAKE[0], y, CAKE[2], shadow_y=GY + 8)
        r.sparkles(c, CAKE[0], CAKE[1] - 60, (a % 2.2) - 0.3, seed=88, radius=170, n=7)
    if t >= P.sil:
        a = t - P.sil
        k = r.ease_out_back(a / 0.6)
        spr.draw(c, "lion", SIL[0], SIL[1] + 8 * math.sin(t * 2), SIL[2] * k, sil=True)
        r.sparkles(c, SIL[0], SIL[1], (a % 2.0) - 0.2, seed=99, radius=200, n=8)

    # efektler
    for kind, t0, ex, ey, seed in P.fx:
        age = t - t0
        if age < 0 or age > 2.0:
            continue
        if ex is None:                                # Dino'nun basinda puf
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

    # ---- arayuz (kamera disi) ----
    if s["kind"] == "song":
        r.karaoke(c, s["lines"], s["timings"], tl)
        if s["phase"] == "bye":
            fx_, fy_ = r.W / 2 + (x - cx) * z, r.H / 2 + (DINO_Y - 60 - cy) * z
            r.iris(c, fx_, fy_, (tl - (s["dur"] - 1.3)) / 1.2)
    elif "text" in s:
        r.caption(c, s["text"], key=s.get("key"), key_color=s.get("color", r.rgb(235, 70, 70)))
    if s["kind"] == "pause":
        r.ask_bubble(c, 1480, 300, tl / 0.35, tl / s["dur"], t)


def skia_rect(x, y, w, h):
    import skia
    return skia.Rect.MakeXYWH(x, y, w, h)


# ---------------- duman testi ----------------
def smoke(spr):
    """Agir ses kurulumundan ONCE: yeni cizim ogeleri tek sayfada (hata erken ciksin, gozle kontrol)."""
    t0 = time.time()
    meadow = r.Meadow()
    surf = r.new_surface()
    c = surf.getCanvas()
    meadow.draw(c, 1.0)
    for h in HIDE:
        if h["kind"] == "bush":
            r.bush(c, h["x"], h["y"], 1.0)
        elif h["kind"] == "tree":
            r.big_tree(c, h["x"], h["y"], 1.0)
        else:
            r.cloud(c, h["x"], h["y"], 1.6)
        r.peek_eyes(c, h["eyes"][0], h["eyes"][1], 1.0, k=h["ek"], hollow=h["hollow"])
    poses = [dict(expr="neutral", wave=1.0, sweat=1.0), dict(expr="happy", excited=True),
             dict(expr="surprised", arms=(150, 150)), dict(expr="happy", lean=-14, dizzy=1.0, arms=(60, 60))]
    for k, p in enumerate(poses):
        x = 150 + k * 260
        r.dino_shadow(c, x, GY, s=0.7)
        r.dino(c, x, GY - 175 * 0.7, s=0.7, t=1.0, mouth=0.5, **p)
    for k, n in enumerate(["cow", "duck", "dog", "cake", "crown", "balloon"]):
        spr.draw(c, n, 130 + k * 170, 150, 140)
    spr.draw(c, "lion", 1180, 420, 200, sil=True)
    r.leaf(c, 150, 330, s=1.6)
    r.dust(c, 400, GY + 60, 0.2)
    r.leaves(c, 1120, 500, 0.5, seed=1)
    r.speed_lines(c, 900, 900, 1.0)
    r.ask_bubble(c, 1500, 330, 1.0, 0.7)
    r.caption(c, "Who says moo?", key="moo", key_color=ANIMALS[0]["color"])
    save_png(surf, OUT / "pilot_smoke.png")
    return time.time() - t0


# ---------------- render ----------------
def main():
    OUT.mkdir(exist_ok=True)
    spr = r.Sprites(outline=14)
    report = [f"Fluent commit: {assets.SHA}"]
    report.append(f"Duman testi: {smoke(spr):.1f} sn (out/pilot_smoke.png)")
    print(report[-1], flush=True)
    report += animal_sounds.report()
    print("\n".join(report[-3:]), flush=True)

    t0 = time.time()
    P = build()
    report.append(f"Ses hazirligi: {time.time() - t0:.0f} sn; toplam sure {P.total:.1f} sn "
                  f"({P.total / 60:.2f} dk); segment {len(P.segs)}")
    for s in P.segs:
        report.append(f"  {s['start']:7.2f}  {s['kind']:8s} {s['dur']:5.2f}  "
                      f"{s.get('text', s.get('phase', ''))}")
    print("\n".join(report), flush=True)

    import music
    wav = OUT / "pilot.wav"
    music.write_wav(str(wav), P.audio)

    meadow = r.Meadow()
    surf = r.new_surface()
    c = surf.getCanvas()
    n_frames = int(P.total * FPS)
    keys = {}
    for k, s in enumerate(P.segs):
        keys[int((s["start"] + s["dur"] * 0.5) * FPS)] = f"{k:03d}_{s['kind']}"
        if s["kind"] in ("fall", "fly", "jumps", "zoom", "peek", "surprise"):
            keys[int((s["start"] + s["dur"] * 0.85) * FPS)] = f"{k:03d}_{s['kind']}_son"
    keys[int(0.4 * FPS)] = "000_baslangic"
    keys[n_frames - int(0.6 * FPS)] = "999_kapanis"

    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{r.W}x{r.H}",
         "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
         "-ar", str(SR), "-shortest", str(OUT / "pilot.mp4")],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    t1 = time.time()
    try:
        for f in range(n_frames):
            t = f / FPS
            c.clear(r.rgb(0, 0, 0))
            draw(c, t, P, meadow, spr, f)
            data = r.frame_bytes(surf)
            ff.stdin.write(data)
            if f in keys:
                Image.frombytes("RGBA", (r.W, r.H), data).convert("RGB").save(OUT / f"kare_{keys[f]}.png")
    finally:
        ff.stdin.close()
    err = ff.stderr.read().decode(errors="ignore")
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg hatasi:\n" + err[-1500:])
    spf = (time.time() - t1) / n_frames
    report.append(f"Render: {n_frames} kare, {spf * 1000:.0f} ms/kare -> 12 dk bolum ~"
                  f"{spf * 12 * 60 * FPS / 60:.0f} dk")
    (OUT / "pilot_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(report[-1])


if __name__ == "__main__":
    main()
