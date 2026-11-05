"""
Pilot bolum (todo 7b): "Thumpy formulu" -- docs/arastirma-cocuk-izleme.md bolum 12.
Uretime bagli degil, YUKLEME YOK. Senaryo elle yazildi ve kullanici onayindan gecti.

Akis: selam sarkisi (0. sn, logo yok) -> Dino yardim ister (soru + bekleme) -> saklambac:
inek, ordek, kopek (calı sallanir -> ses ipucu -> "Who says ...?" + bekleme -> gag ->
"Peekaboo!" -> kelime 3 kez + tekrar ettirme) -> hareket molasi (London Bridge: tavsan gibi
zipla, fil gibi tepin) -> tekrar (cocuk tamamlar) -> sonraki bolum ipucu -> veda sarkisi.
Gorsel: cizgi film stili (konturlu), sert kamera kesmeleri (yavas zoom yok), 3-6 sn'de bir olay.
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
    dict(name="cow", says="moo", sound="Moo! Moo!", short="Moo!", pitch="-30Hz", rate="-15%",
         color=r.rgb(150, 90, 200)),
    dict(name="duck", says="quack", sound="Quack! Quack!", short="Quack!", pitch="+35Hz", rate="+10%",
         color=r.rgb(230, 150, 20)),
    dict(name="dog", says="woof", sound="Woof! Woof!", short="Woof!", pitch="-10Hz", rate="+0%",
         color=r.rgb(215, 95, 40)),
]

# ---------------- sahne yerlesimi ----------------
DINO_HOME = 700
DINO_Y = GY - 175                       # govde merkezi (ayaklar zeminde)
BUSH_X = [1080, 1420, 1760]
FRIEND = [(90, GY - 170, 140), (225, GY - 170, 140), (360, GY - 170, 140)]    # kurtarilan arkadaslar
ROW = [(980, GY - 150, 250), (1300, GY - 150, 250), (1620, GY - 150, 250)]     # tekrar sirasi
GIFT = (1300, 330, 200)


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
    """edge-tts -> mono numpy. Bastaki/sondaki sessizlik kirpilir (selamin 7,5 sn surmesi bundandi)."""
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
        self.audio = []          # (kanal, sinyal, baslangic): kanal "dino" | 0..2 | "song" | "sfx"
        self.n = 0

    def seg(self, kind, dur, **kw):
        s = dict(kind=kind, start=self.t, dur=dur, **kw)
        s["end"] = self.t + dur
        self.segs.append(s)
        self.t += dur
        return s

    def say(self, who, text, gap=0.35, **kw):
        self.n += 1
        if who == "dino":
            clip = tts(text, f"{self.n:03d}_dino")
        else:
            a = ANIMALS[who]
            clip = tts(text, f"{self.n:03d}_{a['name']}", rate=a["rate"], pitch=a["pitch"])
        s = self.seg("say", len(clip) / SR + gap, who=who, text=text, **kw)
        self.audio.append((who, clip, s["start"] + 0.05))
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

    def ding(self, t):
        import samples
        self.sfx(samples.note("glock", 84, 0.5, max_dur=0.8), t)

    def flyup(self, t):
        import samples
        for k, m in enumerate((72, 74, 76, 79, 81, 84, 79, 76, 72)):
            self.sfx(samples.note("xylo", m, 0.5, max_dur=0.2), t + k * 0.13)

    def tiptoe(self, P, target, i):
        """Dino parmak ucunda calıya gider (klasik cizgi film pizzicato adimlari)."""
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


def pop(P, i, t0, bx):
    """Hayvan calinin arkasindan yukselir ("Peekaboo!")."""
    tr = P.animal[i]
    tr.jump(t0, (bx, GY - 60, 300))
    tr.to(t0 + 0.45, (bx, GY - 300, 300))
    P.shown_from[i] = t0
    P.fx.append(("poof", t0 + 0.3, bx, GY - 300, 0))


def gag_cow(tl, P, i):
    bx = P.bush_x[i].at(tl.t)
    tl.tiptoe(P, bx - 250, i)
    tl.say("dino", "Hmm? Nobody here.", expr="listen", look=1.0, lean=8, shot=("two", i))
    s = tl.say(i, "Peekaboo!", shot=("two", i), surprise=True)
    pop(P, i, s["start"], bx)
    tl.boing(s["start"])
    tl.bell(s["start"])
    s = tl.seg("fall", 1.6, shot=("two", i))
    tl.whistle(s["start"])
    tl.thud(s["start"] + 0.58)
    tl.twinkle(s["start"] + 0.7)
    tl.say("dino", "Ha ha! You got me!", expr="happy", sit=True, shot=("two", i))


def gag_duck(tl, P, i):
    bx = P.bush_x[i].at(tl.t)
    tl.tiptoe(P, bx - 260, i)
    tl.say("dino", "Is it a lion? Roar!", arms=(140, 140), expr="happy", look=1.0, lean=6, shot=("two", i))
    tl.say(i, "No! Quack!", eyes=i, wiggle=i, shot=("two", i), surprise=True)
    s = tl.seg("fly", 1.4, shot=("two", i), surprise=True)
    dx = P.dino_x.at(s["start"])
    tr = P.animal[i]
    tr.jump(s["start"], (bx, GY - 120, 230))
    tr.to(s["start"] + 0.6, ((bx + dx) / 2, 250, 230))
    tr.to(s["start"] + 1.3, (dx + 10, DINO_Y - 235, 210))
    P.shown_from[i] = s["start"]
    P.front_from[i] = s["start"] + 0.25
    tl.flyup(s["start"])
    tl.boing(s["start"] + 1.3)
    tl.say("dino", "Ha ha! Hello, duck!", expr="happy", look_y=-1.0, shot=("two", i))
    P.on_head = (s["start"] + 1.3, tl.t, i)


def gag_dog(tl, P, i):
    tl.say("dino", "Come out, come out!", wave=1.0, look=1.0, shot=("wide",))
    s = tl.seg("bushhop", 2.1, shot=("wide",), eyes=i)
    tr = P.bush_x[i]
    x0, x1 = tr.at(s["start"]), P.dino_x.at(s["start"]) + 330
    for k in range(3):
        a = s["start"] + k * 0.7
        tr.hold(a)
        tr.to(a + 0.55, x0 + (x1 - x0) * (k + 1) / 3)
        P.bush_hops.append((i, a, 0.55))
        tl.boing(a + 0.5)
    s = tl.say(i, "Peekaboo! Woof!", shot=("two", i), surprise=True)
    pop(P, i, s["start"], x1)
    tl.bell(s["start"])
    tl.say("dino", "Whoa! Hello, dog!", expr="happy", excited=True, shot=("two", i))


GAGS = [gag_cow, gag_duck, gag_dog]


def lesson(tl, P, i):
    a = ANIMALS[i]
    name, says, col = a["name"], a["says"], a["color"]
    s = tl.say("dino", "Look! The bush is wiggling!", expr="surprised", look=1.0, wiggle=i, shot=("two", i))
    tl.rustle(s["start"], s["dur"])
    tl.say("dino", "Shh... listen!", expr="listen", arms=(20, 165), look=1.0, shot=("two", i))
    s = tl.say(i, a["sound"], key=says, color=col, wiggle=i, eyes=i, shot=("bush", i))
    tl.rustle(s["start"], 0.6)
    tl.say("dino", f"Who says {says}?", key=says, color=col, shot=("dino",))
    tl.pause(2.6, f"Who says {says}?", key=says, color=col, shot=("dino",))
    GAGS[i](tl, P, i)

    # cevap: hayvan sahnenin onune gelir, kelime 3 kez + tekrar ettirme
    stage = (P.bush_x[i].at(tl.t), GY - 150, 300)
    s = tl.say("dino", f"It's a {name}! The {name} says {says}!", key=name, color=col,
               expr="happy", excited=True, shot=("animal", i))
    tr = P.animal[i]
    tr.hold(s["start"])
    tr.to(s["start"] + 0.6, stage)
    P.front_from[i] = min(P.front_from[i], s["start"])
    P.fx += [("confetti", s["start"] + 0.5, stage[0], stage[1], 11 + i),
             ("sparkle", s["start"] + 0.55, stage[0], stage[1], i)]
    tl.tada(s["start"] + 0.5)
    tl.say(i, a["short"], key=says, color=col, shot=("animal", i))
    tl.say("dino", f"Can you say {name}?", key=name, color=col, shot=("dino",))
    tl.pause(2.0, f"Can you say {name}?", key=name, color=col, shot=("dino",))
    s = tl.say("dino", f"{name.capitalize()}! Great job!", key=name, color=col, expr="happy", excited=True,
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
    s = tl.say("dino", "Dance break! Stand up and dance with me!", excited=True, expr="happy", shot=("wide",))
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
    s = tl.say("dino", "Let's say it together!", excited=True, expr="happy", shot=("wide",))
    for i in range(3):
        P.animal[i].hold(s["start"])
        P.animal[i].to(s["start"] + 0.9, ROW[i])
    for i, a in enumerate(ANIMALS):
        shot = ("pt", ROW[i][0], 560, 1.45)
        s = tl.say("dino", f"The {a['name']} says...", key=a["name"], color=a["color"], shot=shot, recap=i)
        P.fx.append(("sparkle", s["start"], ROW[i][0], ROW[i][1], 40 + i))
        tl.pause(1.8, f"The {a['name']} says...", key=a["name"], color=a["color"], shot=shot, recap=i)
        s = tl.say(i, a["short"], key=a["says"], color=a["color"], shot=shot, recap=i)
        tl.ding(s["start"])


def teaser(tl, P):
    s = tl.say("dino", "Next time, a big surprise!", expr="happy", shot=("wide",))
    P.gift = s["start"]
    tl.whistle(s["start"])
    tl.boing(s["start"] + 0.8)
    tl.say("dino", "What is in the box?", look=1.0, look_y=-1.0, shot=("pt", GIFT[0], 420, 1.5))


def build():
    import music
    import samples
    samples.ensure()
    P = SimpleNamespace(dino_x=Track(DINO_HOME), bush_x=[Track(x) for x in BUSH_X],
                        animal=[Track((x, GY - 60, 300)) for x in BUSH_X],
                        shown_from=[1e9] * 3, front_from=[1e9] * 3, on_head=None,
                        bush_hops=[], fx=[], extras=[], gift=1e9)
    tl = TL()

    # 1. kanca + ritueller: 0. saniyede sarki, calilardan bakan gozler (merak)
    song_seg(tl, "hello", HELLO, [("wide",), ("dino",), ("wide",), ("wide",), ("pt", 1420, 640, 1.35)])
    # 2. Dino dogrudan izleyiciye konusur, yardim ister
    tl.say("dino", "Hi friends! I'm Dino!", wave=1.0, expr="happy", shot=("dino",))
    tl.say("dino", "Oh no! My animal friends are hiding.", expr="surprised", look=1.0, eyes_all=True,
           shot=("wide",))
    tl.say("dino", "Can you help me find them?", shot=("dino",))
    tl.pause(2.2, "Can you help me find them?", shot=("dino",))
    tl.say("dino", "Yay! Thank you! Let's go!", excited=True, expr="happy", shot=("wide",))
    # 3. saklambac (dersler) + hareket molasi
    for i in range(3):
        lesson(tl, P, i)
        if i == 1:
            dance(tl, P)
    # 4. tekrar, ipucu, veda
    recap(tl, P)
    teaser(tl, P)
    song_seg(tl, "bye", BYE, [("wide",), ("wide",), ("dino",)])
    total = tl.t

    # ---- miks ----
    n = int(total * SR) + SR
    dino_sp = np.zeros(n)
    an_sp = [np.zeros(n) for _ in ANIMALS]
    songs_b, sfx = np.zeros(n), np.zeros(n)
    for who, sig, t0 in tl.audio:
        if who == "dino":
            _add(dino_sp, sig, t0)
        elif who == "song":
            _add(songs_b, sig / _active_rms(sig), t0)
        elif who == "sfx":
            _add(sfx, sig, t0)
        else:
            _add(an_sp[who], sig, t0)
    speech = dino_sp + sum(an_sp)
    nar = _active_rms(speech)
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
    elif kind == "bush":
        cx, cy, z = P.bush_x[spec[1]].at(t), GY - 160, 1.7
    elif kind == "two":
        cx, cy, z = (P.dino_x.at(t) + P.bush_x[spec[1]].at(t)) / 2, 610, 1.3
    elif kind == "animal":
        x, y, _ = P.animal[spec[1]].at(t)
        cx, cy, z = x, y - 40, 1.6
    else:                                   # ("pt", x, y, zoom)
        cx, cy, z = spec[1], spec[2], spec[3]
    hw, hh = r.W / 2 / z, r.H / 2 / z
    return min(max(cx, hw), r.W - hw), min(max(cy, hh), r.H - hh), z


def _dino_pose(P, s, t, tl, f):
    """Donus: (x, yukseklik, squash, asagi_kayma, dino() argumanlari)."""
    x = P.dino_x.at(t)
    kw = dict(t=t, mouth=float(P.dmouth[min(f, len(P.dmouth) - 1)]), expr=s.get("expr", "neutral"),
              look=s.get("look", 0.0), look_y=s.get("look_y", 0.0), arms=s.get("arms"),
              wave=s.get("wave", 0.0), excited=s.get("excited", False), lean=s.get("lean", 0.0))
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
    elif k == "fall":
        kw.update(expr="surprised", look=1.0)
        if tl < 0.35:
            hop, kw["arms"] = 120 * math.sin(tl / 0.35 * math.pi / 2), (150, 150)
        elif tl < 0.6:
            x2 = (tl - 0.35) / 0.25
            hop, kw["lean"], kw["arms"] = 120 * (1 - x2), -22 * x2, (150, 150)
        else:
            hop, sq, dy, kw["lean"] = 0.0, 0.14, 22.0, -22.0
            kw["dizzy"] = 1 - r.clamp01((tl - 1.2) / 0.4)
            kw["arms"] = (60, 60)
    elif k == "bushhop":
        kw.update(expr="surprised", look=1.0, lean=-8.0)
    elif k == "fly":
        kw.update(expr="surprised", look=1.0, look_y=-1.0 if tl > 0.4 else 0.0)
    elif k == "join":
        hop = abs(math.sin(tl * 10)) * 18
        kw["expr"] = "happy"
    elif k == "pause":
        kw.update(expr="listen", arms=(20, 165), look=0.0)
    if s.get("sit"):
        hop, sq, dy, kw["lean"] = 0.0, 0.14, 22.0, -22.0 * (1 - r.clamp01((tl - (s["dur"] - 0.4)) / 0.4))
        kw["dizzy"] = 0.0
    if s.get("surprise") and k == "say":
        kw.update(expr="surprised", look=1.0)
        if tl < 0.5:
            hop = 60 * math.sin(tl / 0.5 * math.pi)
    if kw["excited"] and k == "say":
        hop = abs(math.sin(tl * 7)) * 40
    return x, hop, sq, dy, kw


def _eyes_k(P, s, t, i):
    if t >= P.shown_from[i]:
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

    def animal_pos(i):
        x, y, size = P.animal[i].at(t)
        m = float(P.amouth[i][min(f, len(P.amouth[i]) - 1)])
        bob = beat_hop if t > P.front_from[i] else 0.0
        if s.get("recap") == i:
            size *= 1.12 + 0.04 * math.sin(t * 8)
        return x, y - bob - 6 * math.sin(t * 2.5 + i), size, m

    def draw_animal(i):
        x, y, size, m = animal_pos(i)
        spr.draw(c, ANIMALS[i]["name"], x, y, size, rot=6 * m * math.sin(t * 9) + 2 * math.sin(t * 1.7 + i),
                 sx=1 - 0.04 * m, sy=1 + 0.08 * m, shadow_y=GY + 8 if t > P.front_from[i] else None)

    on_head = P.on_head is not None and P.on_head[0] <= t < P.on_head[1]

    # hayvanlar (calinin arkasindakiler)
    for i in range(3):
        if P.shown_from[i] <= t < P.front_from[i]:
            draw_animal(i)
    # calilar
    for i in range(3):
        bx = P.bush_x[i].at(t)
        lift = 0.0
        for bi, a, d in P.bush_hops:
            if bi == i and a <= t < a + d:
                lift = 120 * math.sin(math.pi * (t - a) / d)
        wig = 1.0 if s.get("wiggle") == i else 0.0
        if s["kind"] == "song" and t < P.shown_from[i]:
            wig = max(wig, 0.6 * math.exp(-((tl + i * s["beat"] / 3) % s["beat"]) / 0.15))
        if lift:
            wig = 0.5
        r.bush(c, bx, GY + 10 - lift, 1.0, wiggle=wig, t=t)
        r.peek_eyes(c, bx, GY - 130 - lift, t, k=_eyes_k(P, s, t, i), look=-1.0)
    # hayvanlar (onde)
    for i in range(3):
        if t >= P.front_from[i] and not (on_head and P.on_head[2] == i):
            draw_animal(i)
    # dans molasi misafirleri
    for name, x, a, b in P.extras:
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
    if on_head:
        i = P.on_head[2]
        m = float(P.amouth[i][min(f, len(P.amouth[i]) - 1)])
        spr.draw(c, ANIMALS[i]["name"], x + 10, DINO_Y - 235 - hop + dy - 8 * abs(math.sin(t * 4)), 210,
                 rot=5 * math.sin(t * 3), sy=1 + 0.08 * m)

    # sonraki bolum ipucu: hediye kutusu
    if t >= P.gift:
        a = t - P.gift
        y = -200 + (GIFT[1] + 200) * r.ease_out_elastic(a / 1.0)
        spr.draw(c, "gift", GIFT[0], y, GIFT[2], rot=8 * math.sin(a * 9) * math.exp(-((a % 2.0) / 0.6)))
        r.sparkles(c, GIFT[0], GIFT[1], (a % 2.0) - 0.2, seed=77, radius=150, n=7)

    # efektler
    for kind, t0, ex, ey, seed in P.fx:
        age = t - t0
        if kind == "poof":
            r.poof(c, ex, ey, age)
        elif kind == "confetti":
            r.confetti(c, ex, ey, age, seed=seed)
        elif kind == "sparkle":
            r.sparkles(c, ex, ey, age, seed=seed, radius=210)
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


# ---------------- duman testi ----------------
def smoke(spr):
    """Agir ses kurulumundan ONCE: yeni cizim ogeleri tek sayfada (hata erken ciksin, gozle kontrol)."""
    t0 = time.time()
    meadow = r.Meadow()
    surf = r.new_surface()
    c = surf.getCanvas()
    meadow.draw(c, 1.0)
    r.bush(c, 1650, GY + 10, 1.0)
    r.peek_eyes(c, 1650, GY - 130, 1.0)
    poses = [dict(expr="neutral", wave=1.0), dict(expr="happy", excited=True), dict(expr="surprised", arms=(150, 150)),
             dict(expr="listen", arms=(20, 165), look=1.0), dict(expr="happy", lean=-22, dizzy=1.0, arms=(60, 60))]
    for k, p in enumerate(poses):
        x = 170 + k * 300
        r.dino_shadow(c, x, GY, s=0.75)
        r.dino(c, x, GY - 175 * 0.75 - 0, s=0.75, t=1.0, mouth=0.5, **p)
    for k, n in enumerate(["cow", "duck", "dog", "bunny", "elephant", "gift"]):
        spr.draw(c, n, 160 + k * 200, 180, 170)
    r.ask_bubble(c, 1450, 320, 1.0, 0.7)
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
        if s["kind"] in ("fall", "fly", "bushhop"):
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
