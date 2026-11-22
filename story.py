"""
Hikaye-sarki bolum motoru (H3, todo 7h; K-24/K-25).

Arastirma (docs/arastirma-hikaye-buyume.md): sarkiyla anlatilan hikayeler konusmali hikayelerden kat kat cok
izleniyor; kucuk kanal hitleri ayni kadroyla arka arkaya 2-3 dk'lik 3-7 hikaye-sarki; sorun ilk 10 sn'de;
sonu kurtarma + sarilma/kutlama; selam sarkisi yok.

Bicim: 2,6 sn jingle -> Hikaye 1..N (her biri: kanca konusmasi <=20 sn -> sarki kitalari (araya en fazla
1-2 konusma satiri) -> sonuc satiri + sarilma -> siradaki hikayenin ipucu) -> iris + yeni mekan -> ... -> veda.
Karakterler: Dino (render2.dino) + kod kiti hayvanlari (critters.py), her birinin kendi sesi (VOICES).
Sarkilar: kamu mali melodi + Claude'un ozgun sozleri, Hanami vokali (vocal_break), karaoke.
"""
import math
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

import critters as cr
import render2 as r
import show
from show import FPS, SR, Track, jump

FEET = 835                                    # karakterlerin ayak hizasi (zemin)
DINO_S = 1.0
CRIT_S = 0.86
# karakter -> (edge-tts sesi, perde, hiz). Lisans riski: K-25 (Azure'a gecis planli).
VOICES = {
    "dino": ("en-US-AnaNeural", "+0Hz", "-5%"),
    "bunny": ("en-GB-MaisieNeural", "+0Hz", "-5%"),
    "cow": ("en-US-JennyNeural", "-10Hz", "-8%"),
    "puppy": ("en-US-RogerNeural", "+10Hz", "+0%"),
    "kitten": ("en-US-EmmaNeural", "+15Hz", "-3%"),
    "piglet": ("en-US-GuyNeural", "+12Hz", "-3%"),
    "lamb": ("en-NZ-MollyNeural", "+10Hz", "-6%"),
    "duck": ("en-IE-ConnorNeural", "+15Hz", "+0%"),
    "chick": ("en-GB-MaisieNeural", "+28Hz", "+3%"),
    "narrator": ("en-US-AvaNeural", "+0Hz", "-6%"),
}
CAST = ["dino"] + cr.NAMES
SOUND = {"cow": "cow", "puppy": "dog", "kitten": "cat", "lamb": "sheep", "duck": "duck", "chick": "chick"}
ACTIONS = ("jump", "dance", "clap", "wave", "spin", "shiver", "run", "point", "think", "sleep", "cry", "laugh",
           "hop", "stomp", "flap", "march", "look", "hug", "none")
FEELS = ("happy", "sad", "surprised", "scared", "think", "neutral")
WEATHER = ("rain", "snow")
PLACES = ("meadow", "farm", "pond", "snow", "forest", "home", "night")
BIG_PROPS = {"christmas_tree": 520, "snowman": 380, "house": 460, "tractor": 380, "train": 380, "boat": 360,
             "bed": 380, "pine": 480, "sunflower": 360, "bathtub": 340, "bicycle": 320, "sled": 300}
DINO_EXPR = {"happy": "happy", "surprised": "surprised", "scared": "surprised", "sad": "listen", "think": "listen",
             "neutral": "neutral", "listen": "listen"}


def _xs(n):
    return {1: [960], 2: [640, 1280], 3: [470, 960, 1450], 4: [390, 800, 1210, 1600]}[n]


def say(tl, who, text, gap=0.3, **kw):
    tl.n += 1
    if tl.estimate:
        clip = np.zeros(int((len(text.split()) / 2.4 + 0.4) * SR))
    else:
        v, pitch, rate = VOICES.get(who, VOICES["dino"])
        clip = show.tts(text, tl.work / "tts" / f"{tl.n:03d}_{who}.mp3", rate=rate, pitch=pitch, voice=v)
    s = tl.seg("say", len(clip) / SR + gap, who=who, text=text, **kw)
    tl.audio.append((who, clip, s["start"] + 0.05))
    return s


def animal_sound(tl, who, n=2, **kw):
    import animal_sounds
    src = SOUND[who]
    clip = np.zeros(int(0.8 * n * SR)) if tl.estimate else animal_sounds.clip(src, n)
    says = animal_sounds.SOURCES[src]["says"].capitalize() + "!"
    s = tl.seg("say", len(clip) / SR + 0.3, who=who, text=" ".join([says] * n), do="jump", feel="happy", **kw)
    tl.audio.append((who, clip, s["start"] + 0.05))
    return s


def _verse_shots(n, focus, others):
    seq = [("wide",), ("char", focus), ("wide",)]
    if others:
        seq.append(("two", focus, others[0]))
    seq += [("char", focus), ("wide",)] + [("char", o) for o in others[1:]] + [("wide",)]
    return (seq * 3)[:n + 1]


def _talk(tl, k, beat):
    who = beat["who"]
    if beat.get("sound") and who in SOUND:
        animal_sound(tl, who, story=k, shot=("char", who))
        return
    shot = ("wide",) if who in ("narrator", "all") else ("char", who)
    speaker = "dino" if who == "all" else who
    say(tl, speaker, beat["say"], story=k, feel=beat.get("feel", "neutral"), do=beat.get("do", "none"),
        everyone=who == "all", shot=shot)


def build(ep, work, estimate=False):
    """Senaryo -> zaman cizelgesi + ses. estimate=True: ses uretmeden sure (Telegram onayi icin)."""
    import music
    if not estimate:
        import samples
        samples.ensure()
    tl = show.TL(work, estimate)
    stories = []
    for k, st in enumerate(ep["stories"]):
        cast = ["dino"] + [c for c in st["cast"] if c != "dino"][:3]
        stories.append(SimpleNamespace(k=k, name=st["name"], place=st["place"], weather=st.get("weather"),
                                       clears=bool(st.get("clears")), cast=cast,
                                       xs=dict(zip(cast, _xs(len(cast)))), props=st.get("props", [])[:2],
                                       shows=[], start=0.0, end=0.0, clear_t=1e9))
    P = SimpleNamespace(stories=stories, cam=Track(0.0), places=[(0.0, stories[0].place, 0.0)], spans=[],
                        title=ep.get("title_rest") or "", fx=[], mouth={})

    # ---- jingle: Dino firlar + bolum adi; mekan zaten ilk hikayenin mekani ----
    tl.chapter(stories[0].name)
    s = tl.seg("intro", 2.6, story=0, shot=("wide",))
    tl.slide(s["start"] + 0.05)
    tl.tada(s["start"] + 0.75)
    tl.claps(s["start"] + 1.5, 3)
    P.fx.append(("sparkle", s["start"] + 0.75, stories[0].xs["dino"], FEET - 300, 3))

    for k, (st, S) in enumerate(zip(ep["stories"], stories)):
        if k > 0:
            tl.chapter(S.name)
            s = tl.seg("card", 2.0, story=k, shot=("wide",), iris=True)
            P.places.append((s["start"] + show.IRIS_SWITCH, S.place, 0.0))
            tl.slide(s["start"] + 0.15, up=False)
            tl.slide(s["start"] + 1.2)
        S.start = tl.t
        for beat in st.get("hook", []):
            _talk(tl, k, beat)
        others = [c for c in S.cast if c != "dino"]
        for vi, v in enumerate(st["verses"]):
            for beat in v.get("talk", [])[:2]:
                _talk(tl, k, beat)
            focus = v.get("focus") if v.get("focus") in S.cast else S.cast[min(vi + 1, len(S.cast) - 1)]
            shots = _verse_shots(len(v["lines"]), focus, [o for o in S.cast if o != focus])
            s = show.song_seg(tl, "story", st["melody"], v["lines"], shots, story=k, focus=focus,
                              do=v.get("do", "dance"), feel=v.get("feel", "happy"))
            if v.get("clear") and S.weather and S.clear_t > 1e8:
                S.clear_t = s["start"]
            if v.get("show"):
                S.shows.append((s["start"] + 0.4, v["show"], focus))
                tl.bell(s["start"] + 0.4)
            if vi == 0:
                tl.bell(s["start"])
        end = st.get("ending") or {"who": "dino", "say": "Hooray! We did it!", "do": "hug"}
        if S.clears and S.clear_t > 1e8:
            S.clear_t = tl.t
        say(tl, end.get("who", "dino") if end.get("who") in S.cast else "dino", end["say"], story=k,
            feel="happy", do="laugh", everyone=True, shot=("wide",))
        s = tl.seg("act", 2.4, story=k, do=end.get("do", "hug"), shot=("wide",))
        tl.tada(s["start"] + 0.3)
        P.fx += [("confetti", s["start"] + 0.3, 960, 420, 10 + k), ("sparkle", s["start"] + 0.5, 960, FEET - 260, 20 + k)]
        if k < len(ep["stories"]) - 1 and st.get("next"):
            say(tl, "dino", st["next"], story=k, feel="surprised", do="look", shot=("char", "dino"))
        S.end = tl.t
        P.spans.append((S.start, S.end))
    s = say(tl, "dino", ep.get("goodbye") or "Bye bye, friends! See you next time!", story=len(stories) - 1,
            feel="happy", do="wave", everyone=True, shot=("wide",))
    tl.seg("outro", 1.6, story=len(stories) - 1, do="wave", shot=("char", "dino"))
    total = tl.t
    P.segs, P.total, P.chapters = tl.segs, total, tl.chapters
    if estimate:
        return P

    # ---- miks ----
    n = int(total * SR) + SR
    speech = {}
    songs_b, sfx = np.zeros(n), np.zeros(n)
    for who, sig, t0 in tl.audio:
        if who == "song":
            show._add(songs_b, sig / show._active_rms(sig), t0)
        elif who == "sfx":
            show._add(sfx, sig, t0)
        else:
            speech.setdefault(who, np.zeros(n))
            show._add(speech[who], sig, t0)
    ref = show._active_rms(speech.get("dino", next(iter(speech.values()))))
    for who in speech:
        speech[who] *= ref / show._active_rms(speech[who])
    bg = music.background_track(total)
    gain = np.full(len(bg), 0.18)
    for s in tl.segs:
        if s["kind"] == "song":
            gain[int(s["start"] * SR):int(s["end"] * SR)] = 0.0
    gain = np.convolve(gain, np.ones(SR // 4) / (SR // 4), mode="same")
    buf = np.zeros(n)
    buf[:len(bg)] += bg * gain * (ref / show._active_rms(bg))
    buf += sum(speech.values()) + songs_b * 0.9 * ref + sfx * (ref / show._active_rms(sfx)) * 0.5
    nf = int(total * FPS)
    P.audio = buf[: int(total * SR)]
    P.mouth = {who: show.mouth_track(sig, nf) for who, sig in speech.items()}
    return P


# ---------------- cizim ----------------
def _cam(spec, S, fw=r.W, fh=r.H):
    if spec[0] == "face" and spec[1] in S.xs:                       # kucuk resim: yuz yakin plani
        cx, cy, z = S.xs[spec[1]] + 120, FEET - 300, 2.0
    elif spec[0] == "char" and spec[1] in S.xs:
        cx, cy, z = S.xs[spec[1]], FEET - 230, 1.45
    elif spec[0] == "two" and spec[1] in S.xs and spec[2] in S.xs:
        cx, cy, z = (S.xs[spec[1]] + S.xs[spec[2]]) / 2, FEET - 250, 1.2
    else:
        cx, cy, z = r.W / 2, r.H / 2, 1.0
    hw, hh = fw / 2 / z, fh / 2 / z
    return min(max(cx, hw), r.W - hw), min(max(cy, hh), r.H - hh), z


def _pose(name, s, t, tl, P, S, f):
    """Bir karakterin bu karedeki pozu: (dx, hop, squash, tilt, arms, sx, expr, talk, look, blink)."""
    k = s["kind"]
    speaker = s.get("who")
    everyone = s.get("everyone")
    me = speaker == name or everyone or (k == "song")
    do = "none"
    feel = "neutral"
    if k == "say":
        if speaker == name or everyone:
            do, feel = s.get("do", "none"), s.get("feel", "neutral")
        else:
            feel = "neutral"
    elif k == "song":
        do = s["do"] if name == s.get("focus") else "groove"
        feel = s.get("feel", "happy")
    elif k in ("act", "outro"):
        do, feel = s.get("do", "hug"), "happy"
    elif k == "intro":
        do, feel = ("intro" if name == "dino" else "groove"), "happy"
    talk = 0.0
    if k == "song":
        cw = show._cur_word(s, tl)
        if cw:
            talk = 0.85 * math.exp(-(tl - cw[0]) / 0.22) if tl - cw[0] < 1.0 else 0.0
    else:
        m = P.mouth.get(name)
        if m is not None:
            talk = float(m[min(f, len(m) - 1)])
    # bakis: konusana / sahne ortasina
    x = S.xs.get(name, 960)
    if k == "say" and speaker in S.xs and speaker != name:
        look = max(-1.0, min(1.0, (S.xs[speaker] - x) / 300))
    else:
        look = max(-1.0, min(1.0, (960 - x) / 600)) * 0.6
    dx = hop = sq = tilt = 0.0
    arms, sx, blink = (18, 18), 1.0, None
    ph = (t * 1.25 + (sum(map(ord, name)) % 7) * 0.13) % 1.0
    if k == "song":
        ph = (tl / s["beat"]) % 1.0
    if do in ("jump", "hop", "intro"):
        h, sq = jump(ph)
        hop, arms = h * (70 if do != "hop" else 50), (120, 120)
    elif do in ("dance", "groove"):
        amp = 1.0 if do == "dance" else 0.55
        tilt = 10 * amp * math.sin(t * 7)
        hop = 16 * amp * abs(math.sin(t * 7))
        arms = (70 + 50 * amp * math.sin(t * 7), 70 - 50 * amp * math.sin(t * 7))
        if do == "groove" and k == "song":
            h, sq = jump(ph)
            hop, sq = h * 18, sq * 0.5
    elif do == "clap":
        a = -20 - 35 * math.sin(math.pi * ph)
        arms = (a + 60, a + 60)
    elif do == "wave":
        arms = (20, 140 + 25 * math.sin(t * 12))
    elif do == "spin":
        sx = math.cos(2 * math.pi * ((t * 0.9) % 1.0))
        arms = (90, 90)
    elif do == "shiver":
        dx = 5 * math.sin(t * 55)
        arms, feel = (-10, -10), "scared" if feel == "neutral" else feel
    elif do == "run":
        hop = 22 * abs(math.sin(t * 13))
        tilt, arms = 6, (40 + 40 * math.sin(t * 13), 40 - 40 * math.sin(t * 13))
    elif do == "point":
        arms = (18, 110)
    elif do == "think":
        arms, tilt, feel = (18, 70), -8, "think"
    elif do == "sleep":
        blink, tilt, sq = 1.0, 10, 0.03 * math.sin(t * 2)
    elif do == "cry":
        feel, arms = "sad", (60, 60)
    elif do == "laugh":
        feel = "happy"
        hop = 10 * abs(math.sin(t * 10))
        tilt = 5 * math.sin(t * 10)
    elif do == "stomp":
        sq = 0.16 * math.exp(-((t % 0.6) / 0.12))
        arms = (110, 110)
    elif do == "flap":
        a = 40 + 100 * abs(math.sin(t * 9))
        arms = (a, a)
    elif do == "march":
        hop = 18 * abs(math.sin(t * 7))
        arms = (40 + 30 * math.sin(t * 7), 40 - 30 * math.sin(t * 7))
    elif do == "look":
        look = math.sin(t * 2.5)
        feel = "surprised" if feel == "neutral" else feel
    elif do == "hug":
        e = r.ease_in_out(r.clamp01(tl / 0.6)) * (1 - r.ease_in_out(r.clamp01((tl - (s["dur"] - 0.5)) / 0.5)))
        dx = (960 - x) * 0.32 * e
        arms, sq = (150 * e + 18 * (1 - e),) * 2, 0.04 * e * math.sin(t * 8)
        feel = "happy"
    elif do == "none" and not me:
        hop = 3 * abs(math.sin(t * 2.2))
    return dx, hop, sq, tilt, arms, sx, feel, talk, look, blink


def _draw_char(c, name, s, t, tl, P, S, f):
    dx, hop, sq, tilt, arms, sx, feel, talk, look, blink = _pose(name, s, t, tl, P, S, f)
    x = S.xs[name] + dx
    if s["kind"] == "intro" and name == "dino":
        hop -= (1 - r.ease_out_back(r.clamp01(tl / 0.7))) * 420
    if name == "dino":
        r.dino_shadow(c, x, FEET, lift=max(0.0, hop))
        r.dino(c, x, FEET - 170 - hop, s=DINO_S, t=t, mouth=talk, expr=DINO_EXPR.get(feel, "neutral"),
               look=look, arms=arms, squash=sq, lean=tilt * 0.6)
    else:
        cr.shadow(c, x, FEET, CRIT_S * cr.SPEC[name]["scale"], lift=max(0.0, hop))
        cr.draw(c, name, x, FEET - hop, s=CRIT_S, t=t, expr=feel, talk=talk, blink=blink, look=look,
                arms=arms, tilt=tilt, squash=sq, sx=sx)


def _story_at(P, s, tl=0.0):
    k = s.get("story", 0)
    if s["kind"] == "card" and tl < show.IRIS_SWITCH and k > 0:     # iris kapanana dek onceki hikaye
        k -= 1
    return P.stories[k]


def draw(c, t, P, places, spr, f, fw=r.W, fh=r.H, short=None, hud=True, shot=None):
    """Bir kare. short=i: dikey Shorts kadraji. hud=False: yazisiz (kucuk resim icin)."""
    s = show._seg_at(P.segs, t)
    tl = t - s["start"]
    S = _story_at(P, s, tl)
    spec = s.get("shot", ("wide",))
    if s["kind"] == "song":
        idx = sum(1 for x in s["starts"] if x <= tl)
        spec = s["shots"][min(idx, len(s["shots"]) - 1)]
    if shot is not None:
        spec = shot
    if short is not None and spec[0] == "wide":
        spec = ("char", s.get("focus") or s.get("who") if (s.get("focus") or s.get("who")) in S.xs else "dino")
    cx, cy, z = _cam(spec, S, fw, fh)
    if short is not None:
        z = max(z, fh / r.H)
        hw, hh = fw / 2 / z, fh / 2 / z
        cx, cy = min(max(cx, hw), r.W - hw), min(max(cy, hh), r.H - hh)
    c.save()
    c.translate(fw / 2, fh / 2)
    c.scale(z, z)
    c.translate(-cx, -cy)
    places.draw(c, t, P)
    wx = S.weather
    wk = 1.0
    if wx and t >= S.clear_t:
        wk = 1 - r.clamp01((t - S.clear_t) / 1.5)
    if wx == "rain" and wk > 0:
        c.drawRect(r.skia.Rect.MakeWH(r.W, r.H), r.paint(r.rgb(60, 70, 95, int(80 * wk))))
    if wx == "rain" and S.clears and t >= S.clear_t:
        a = t - S.clear_t
        spr.draw(c, "rainbow", 1250, 250, 560 * r.ease_out_back(r.clamp01((a - 0.5) / 0.8)))
    for j, name in enumerate(S.props):
        big = BIG_PROPS.get(name)
        if big:
            spr.draw(c, name, (1790, 120)[j], FEET - big * 0.42, big, shadow_y=FEET + 6)
        else:
            spr.draw(c, name, (1790, 120)[j], FEET - 80 + 4 * math.sin(t * 1.7 + j), 190, shadow_y=FEET + 6)
    for t0, name, who in S.shows:
        if t >= t0 and who in S.xs:
            k = r.ease_out_back(r.clamp01((t - t0) / 0.45))
            px = S.xs[who] + (150 if S.xs[who] < 1500 else -150)
            spr.draw(c, name, px, FEET - 250 + 6 * math.sin(t * 2), 200 * k, rot=5 * math.sin(t * 2))
            if t - t0 < 1.6:
                r.sparkles(c, px, FEET - 230, t - t0, seed=int(t0 * 10), radius=120, n=7)
    order = sorted(S.cast, key=lambda n: 0 if n == s.get("who") or n == s.get("focus") else 1, reverse=True)
    for name in order:
        _draw_char(c, name, s, t, tl, P, S, f)
    for kind, t0, ex, ey, seed in P.fx:
        age = t - t0
        if 0 <= age <= 2.0:
            if kind == "confetti":
                r.confetti(c, ex, ey, age, seed=seed)
            elif kind == "sparkle":
                r.sparkles(c, ex, ey, age, seed=seed, radius=210)
    c.restore()
    if wx == "rain" and wk > 0.02:
        c.saveLayerAlpha(None, int(255 * wk))
        r.rainfall(c, t, w=fw, h=fh)
        c.restore()
    elif wx == "snow" and wk > 0.02:
        c.saveLayerAlpha(None, int(255 * wk))
        r.snowfall(c, t, w=fw, h=fh)
        c.restore()
    if not hud:
        return
    if short is not None:
        if s["kind"] == "song":
            li = max(0, sum(1 for x in s["starts"] if x <= tl) - 1)
            cw = show._cur_word(s, tl)
            r.caption(c, s["lines"][min(li, len(s["lines"]) - 1)], key=cw[2] if cw else None,
                      key_color=r.rgb(255, 140, 30), y=int(fh * 0.70), cw=fw)
        elif "text" in s:
            r.caption(c, s["text"], y=int(fh * 0.70), cw=fw)
        return
    # ---- ekran ustu ----
    import thumbs
    if s["kind"] == "intro" and P.title:
        c.save()
        c.translate(r.W / 2, 175)
        k = max(0.01, r.ease_out_back(r.clamp01((tl - 0.2) / 0.5)))
        c.scale(k, k)
        thumbs._text(c, P.title, 0, 0, 1500, size=124, rot=-3)
        c.restore()
    elif S.k > 0 and S.start <= t < S.start + 2.4 and s["kind"] == "say":       # hikaye adi seridi (kanca baslarken)
        a = t - S.start
        k = r.ease_out_back(r.clamp01(a / 0.4)) * (1 - r.clamp01((a - 2.0) / 0.4))
        if k > 0.02:
            c.save()
            c.translate(r.W / 2, 120)
            c.scale(k, k)
            thumbs._text(c, S.name, 0, 0, 1400, size=96, rot=-2, fill=r.rgb(255, 255, 255))
            c.restore()
    if s.get("iris"):
        r.iris(c, r.W / 2, r.H / 2, show._iris_k(tl))
    elif s["kind"] == "outro":
        dx = S.xs.get("dino", 960)
        r.iris(c, r.W / 2 + (dx - cx) * z, r.H / 2 + (FEET - 230 - cy) * z, (tl - 0.3) / 1.1)
    n = len(P.stories)                                       # hikaye gostergesi (biriken ilerleme)
    for i in range(n):
        x, y = r.W / 2 + (i - (n - 1) / 2) * 70, 42
        done = t >= P.stories[i].end and P.stories[i].end > 0
        cur = P.stories[i].start <= t < P.stories[i].end
        rad = 22 + (3 * math.sin(t * 6) if cur else 0)
        c.drawCircle(x, y, rad, r.paint(r.rgb(255, 255, 255, 210)))
        c.drawCircle(x, y, rad, r.paint(r.INK, stroke=5))
        if done or cur:
            spr.draw(c, "star", x, y, 40 if done else 30, alpha=1.0 if done else 0.6)
    if s["kind"] == "song":
        r.karaoke(c, s["lines"], s["timings"], tl)
    elif "text" in s:
        key = s.get("who") if s.get("who") in S.xs else None
        r.caption(c, s["text"], key=None, key_color=cr.COLOR.get(key, r.rgb(235, 70, 70)) if key else r.rgb(235, 70, 70))


# ---------------- render ----------------
def render(ep, work, out_mp4, frames_dir=None):
    """Tam uretim. Donus: {"total", "chapters", "P"}."""
    import subprocess
    from PIL import Image
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    P = build(ep, work)
    print(f"Ses hazirligi: {time.time() - t0:.0f} sn; sure {P.total / 60:.2f} dk; segment {len(P.segs)}", flush=True)
    import music
    wav = work / "audio.wav"
    music.write_wav(str(wav), P.audio)
    spr = r.Sprites(outline=14)
    places = show.Places()
    surf = r.new_surface()
    c = surf.getCanvas()
    nf = int(P.total * FPS)
    keys = {}
    if frames_dir:
        Path(frames_dir).mkdir(parents=True, exist_ok=True)
        for k, s in enumerate(P.segs):
            keys[int((s["start"] + s["dur"] * 0.5) * FPS)] = f"{k:03d}_{s['kind']}"
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{r.W}x{r.H}",
         "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
         "-ar", str(SR), "-shortest", "-movflags", "+faststart", str(out_mp4)],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    t1 = time.time()
    try:
        for fr in range(nf):
            c.clear(r.rgb(0, 0, 0))
            draw(c, fr / FPS, P, places, spr, fr)
            data = r.frame_bytes(surf)
            ff.stdin.write(data)
            if fr in keys:
                Image.frombytes("RGBA", (r.W, r.H), data).convert("RGB").save(Path(frames_dir) / f"kare_{keys[fr]}.png")
    finally:
        ff.stdin.close()
    err = ff.stderr.read().decode(errors="ignore")
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg hatasi:\n" + err[-1500:])
    print(f"Render: {nf} kare, {(time.time() - t1) / nf * 1000:.0f} ms/kare", flush=True)
    return {"total": P.total, "chapters": P.chapters, "P": P}


def estimate_seconds(ep):
    return build(ep, "/tmp", estimate=True).total


# ---------------- kucuk resim (arastirma: yazi yok, sorun ani + abartili duygu, yakin plan) ----------------
def thumbnails(P, out_prefix):
    """3 konsept: ilk 3 hikayenin kanca ani (sorun + duygulu yuz). Donus: ([yol x3], onizleme_yolu)."""
    from PIL import Image
    spr, places = r.Sprites(outline=14), show.Places()
    surf = r.new_surface()
    c = surf.getCanvas()
    paths, ims = [], []
    for k in range(3):
        S = P.stories[k % len(P.stories)]
        hook = [s for s in P.segs if s.get("story") == S.k and s["kind"] == "say" and S.start <= s["start"] < S.end]
        s = next((x for x in hook if x.get("feel") in ("scared", "sad", "surprised")), hook[0] if hook else P.segs[0])
        t = s["start"] + min(0.7, s["dur"] * 0.5)
        c.clear(r.rgb(0, 0, 0))
        who = s.get("who") if s.get("who") in S.xs else "dino"
        draw(c, t, P, places, spr, int(t * FPS), hud=False, shot=("face", who))
        im = Image.frombytes("RGBA", (r.W, r.H), r.frame_bytes(surf)).convert("RGB").resize((1280, 720), Image.LANCZOS)
        p = f"{out_prefix}_{'ABC'[k]}.jpg"
        im.save(p, "JPEG", quality=92)
        paths.append(p)
        ims.append(im)
    prev = Image.new("RGB", (3 * 220, 128), "white")
    for k, im in enumerate(ims):
        prev.paste(im.resize((210, 118), Image.LANCZOS), (5 + k * 220, 5))
    pp = f"{out_prefix}_onizleme.png"
    prev.save(pp)
    return paths, pp


def poster(st, path, hero=None, feel="surprised", prop=None, dino_feel="surprised", t=3.0, w=1280, h=720):
    """Kucuk resim afisi (videodan kare degil): mekan + hava, Dino solda buyuk, kahraman sagda buyuk ve
    duygulu (yuzler kadrajin ~%40'i), sorun objesi ortada. Arastirma: yazi yok, sorun ani, abartili duygu."""
    from PIL import Image
    spr = r.Sprites(outline=14)
    bg = r.Meadow(kind=st["place"])
    surf = r.new_surface()
    c = surf.getCanvas()
    bg.draw(c, t, 0.0)
    if st.get("weather") == "rain":
        c.drawRect(r.skia.Rect.MakeWH(r.W, r.H), r.paint(r.rgb(60, 70, 95, 70)))
    hero = hero or next((b["who"] for b in st.get("hook", []) if b.get("who") in cr.SPEC), st["cast"][0])
    if prop:
        spr.draw(c, prop, 960, 360, 380, rot=-10)
        r.sparkles(c, 960, 360, 0.6, seed=5, radius=230, n=9)
    r.dino(c, 440, 760, s=1.55, t=t, expr=DINO_EXPR.get(dino_feel, "surprised"), look=1.0, arms=(150, 150),
           mouth=0.6)
    cr.draw(c, hero, 1420, 1235, s=1.95, t=t, expr=feel, talk=0.75, blink=0.0, look=-0.7, arms=(145, 145), tilt=-6)
    if st.get("weather") == "snow":
        r.snowfall(c, t, n=120, seed=11)
    elif st.get("weather") == "rain":
        r.rainfall(c, t)
    im = Image.frombytes("RGBA", (r.W, r.H), r.frame_bytes(surf)).convert("RGB").resize((w, h), Image.LANCZOS)
    im.save(path, "JPEG", quality=92)
    return path


# ---------------- Shorts: hikayenin kancasi + ilk kitasi (<=58 sn), dikey ----------------
def render_shorts(P, work, n=2, frames_dir=None):
    import subprocess
    import music
    from PIL import Image
    SW, SH = 1080, 1920
    work = Path(work)
    spr, places = r.Sprites(outline=14), show.Places()
    surf = r.skia.Surface(SW, SH)
    c = surf.getCanvas()
    out = []
    for i in range(min(n, len(P.stories))):
        S = P.stories[i]
        t0, t1 = max(0.0, S.start - 0.1), min(S.end, S.start + 58.0)
        songs_k = [s for s in P.segs if s["kind"] == "song" and s.get("story") == i]
        if songs_k and songs_k[0]["end"] <= S.start + 58.0:
            t1 = max(t for t in [x["end"] for x in songs_k] if t <= S.start + 58.0) + 0.3
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
        keys = {f0 + 30: "a", (f0 + f1) // 2: "b", f1 - 12: "c"}
        try:
            for fr in range(f0, f1):
                c.clear(r.rgb(0, 0, 0))
                draw(c, fr / FPS, P, places, spr, fr, fw=SW, fh=SH, short=i)
                arr = surf.makeImageSnapshot().toarray(colorType=r.skia.kRGBA_8888_ColorType,
                                                       alphaType=r.skia.kUnpremul_AlphaType)
                data = np.ascontiguousarray(arr).tobytes()
                ff.stdin.write(data)
                if frames_dir and fr in keys:
                    Image.frombytes("RGBA", (SW, SH), data).convert("RGB").save(Path(frames_dir) / f"short_{i}_{keys[fr]}.png")
        finally:
            ff.stdin.close()
        err = ff.stderr.read().decode(errors="ignore")
        if ff.wait() != 0:
            raise RuntimeError("ffmpeg (short) hatasi:\n" + err[-1500:])
        out.append({"path": str(mp4), "story": i, "find": i, "dur": t1 - t0})
        print(f"Short {i} ({S.name}): {t1 - t0:.1f} sn", flush=True)
    return out
