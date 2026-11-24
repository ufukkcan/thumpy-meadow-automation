"""
Traktor yolculugu bolumu (H14 T3): Dino kirmizi traktoruyla duraktan duraga gider, sorundaki arkadasi kurtarir,
arkadas romorktaki numarali koltuga biner ("One friend on my tractor!"). Senaryo bicimi hikaye-sarki ile ayni
("stories" = duraklar, "format": "trip"); ses/sarki/konusma story.py ile ayni (story.mix).

Durak akisi (H13 dersi: sorun ilk saniyelerde, rakip olcumu: arac hic durmaz, 2-4 sn'de bir cekim):
  in   : traktor surer (jingle / kisa surus) + kanca (arkadasin sesi) -> yavaslayip arkadasin yaninda durur
  hold : sorun kitalari (cekim satir basinda degisir) -> kurtarma (halat + korna + firlama + romorka ziplama)
         -> sayma cumlesi
  out  : kutlama cumlesi + kalan kitalar (surerek) + siradaki ipucu -> traktor saga cikar
Son durak cikmaz: kutlama + veda + abone cagrisi traktor dururken.
"""
import math
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

import critters as cr
import render2 as r
import show
import story
import trip
import vehicles as v
from show import FPS, SR

FR_S = 0.9                       # duraktaki arkadasin olcegi
FRIEND_SX = 1690                 # durakta arkadasin ekran x'i (traktorun onunde)
RESCUE = 3.6                     # kurtarma sahnesi: halat 0-1.2, firlama 1.2, romorka ziplama 1.5-2.7
POP, HOP0, HOP1 = 1.2, 1.5, 2.7
SEATS = 4
NUMS = ["One", "Two", "Three", "Four"]
HOLD_SHOTS = ("wide", "friend", "dino", "face", "wide", "trailer")
DRIVE_SHOTS = ("wide", "dino", "wheel", "wide", "trailer")


# ---------------- zaman cizelgesi + ses ----------------
def build(ep, work, estimate=False):
    if not estimate:
        import samples
        samples.ensure()
    tl = show.TL(work, estimate)
    stories = []
    for k, st in enumerate(ep["stories"][:SEATS]):
        cast = ["dino"] + [c for c in st["cast"] if c != "dino"][:3]
        trb = story.trouble_of(st, cast) or (cast[1], "scared", len(st["verses"]))
        stories.append(SimpleNamespace(k=k, name=st["name"], place=st["place"], weather=st.get("weather"),
                                       cast=cast, melody=st.get("melody"), hook=st.get("hook", []),
                                       all_props=st.get("props", []), friend=trb[0], look=trb[1], until=trb[2],
                                       start=0.0, end=0.0, trouble=None, t_rescue=1e9, wfx=0.0))
    story._xmas_flags(stories)
    P = SimpleNamespace(stories=stories, legs=[], fx=[], mouth={}, title=ep.get("title_rest") or "",
                        cta_t=None)
    last = len(stories) - 1
    for k, (st, S) in enumerate(zip(ep["stories"], stories)):
        tl.chapter(S.name)
        t_in = tl.t
        S.start = tl.t
        if k == 0:                                     # jingle: traktor 0. sn'de soldan giriyor
            s = tl.seg("intro", 2.6, story=0)
            tl.tada(s["start"] + 0.75)
            tl.claps(s["start"] + 1.5, 3)
        tl.seg("drive", 1.6 if k == 0 else 3.0, story=k)
        for beat in st.get("hook", []):
            story._talk(tl, k, beat)
        leg_in = trip.leg(S.sky_place, t_in, tl.t, "in", weather=S.weather, x_from=420.0 if k == 0 else None)
        P.legs.append(leg_in)
        S.wfx = trip.cam_end(leg_in) + FRIEND_SX
        t_hold = tl.t
        verses = st["verses"]
        for vi in range(min(S.until, len(verses))):
            _verse(tl, k, st, S, vi)
        for beat in (verses[S.until].get("talk", [])[:2] if S.until < len(verses) else []):
            story._talk(tl, k, beat)
        s = tl.seg("rescue", RESCUE, story=k)
        S.t_rescue = s["start"]
        S.trouble = (S.friend, S.look, 0.0 if k == 0 else t_in, s["start"] + POP)
        tl.boing(s["start"] + POP)
        tl.bell(s["start"] + HOP1)
        P.fx.append(("sparkle", s["start"] + POP, S.wfx, trip.GROUND - 120, 40 + k))
        story.say(tl, "dino", f"{NUMS[k]} friend{'s' if k else ''} on my tractor!", story=k, count=k + 1)
        end = st.get("ending") or {"who": "dino", "say": "Hooray! We did it!"}
        if k < last:
            P.legs.append(trip.leg(S.sky_place, t_hold, tl.t, "hold", cam0=trip.cam_end(leg_in), weather=S.weather))
            t_out = tl.t
        story.say(tl, end.get("who", "dino") if end.get("who") in S.cast else "dino", end["say"], story=k)
        e = tl.seg("act", 1.6, story=k)
        tl.tada(e["start"] + 0.2)
        P.fx.append(("confetti", e["start"] + 0.2, None, 380, 10 + k))
        for vi in range(S.until + 1, len(verses)):     # kurtulus kitasinin konusmasi yukarida; sozleri burada
            _verse(tl, k, st, S, vi)
        if S.until < len(verses):
            _verse(tl, k, st, S, S.until, talk=False)
        if k < last:
            if st.get("next"):
                story.say(tl, "dino", st["next"], story=k)
            tl.seg("drive", 1.8, story=k)              # cikis payi
            P.legs.append(trip.leg(S.sky_place, t_out, tl.t, "out", cam0=trip.cam_end(leg_in), weather=S.weather))
        S.end = tl.t
    S = stories[last]
    story.say(tl, "dino", ep.get("goodbye") or "Bye bye, friends! See you next time!", story=last)
    s = story.say(tl, "dino", story.CTA_LINE, gap=0.9, story=last)
    P.cta_t = s["start"]
    tl.bell(s["start"] + story.CTA_CLICK)
    tl.slide(s["start"] + story.CTA_THUMB)
    tl.seg("outro", 1.6, story=last)
    S.end = tl.t
    P.legs.append(trip.leg(S.sky_place, P.legs[-1].t1, tl.t, "hold", cam0=trip.cam_end(P.legs[-1]),
                           weather=S.weather))
    P.segs, P.total, P.chapters = tl.segs, tl.t, tl.chapters
    if estimate:
        return P
    story.mix(tl, P, P.total)
    return P


def _verse(tl, k, st, S, vi, talk=True):
    vv = st["verses"][vi]
    if talk:
        for beat in vv.get("talk", [])[:2]:
            story._talk(tl, k, beat)
    s = show.song_seg(tl, "story", st["melody"], vv["lines"], [("wide",)] * (len(vv["lines"]) + 1), story=k,
                      focus=vv.get("focus"), do=vv.get("do", "dance"), feel=vv.get("feel", "happy"))
    if vi == 0:
        tl.bell(s["start"])
    return s


def estimate_seconds(ep):
    return build(ep, "/tmp", estimate=True).total


# ---------------- cizim ----------------
class Scene:
    def __init__(self):
        self._m = {}

    def bg(self, kind):
        if kind not in self._m:
            self._m[kind] = r.Meadow(kind=kind)
        return self._m[kind]


def _leg_story(P, g):
    for S in P.stories:
        if S.start - 1e-6 <= g.t0 < S.end + 1e-6:
            return S
    return P.stories[-1]


def _seat_screen(sx, n):
    """n. koltuktaki (1'den) binicinin ekran ayak noktasi + olcegi."""
    left = -(120 + SEATS * 150) - 40
    lx = left + 100 + (n - 1) * 150
    return sx + v.HITCH * trip.S + lx * trip.S, trip.GROUND - 240 * trip.S, 0.62 * trip.S


def _sing(s, tl_):
    if s["kind"] != "song":
        return 0.0
    cw = show._cur_word(s, tl_)
    return 0.85 * math.exp(-(tl_ - cw[0]) / 0.22) if cw and tl_ - cw[0] < 1.0 else 0.0


def _mouth(P, who, f):
    m = P.mouth.get(who)
    return float(m[min(f, len(m) - 1)]) if m is not None else 0.0


def _friend_state(S, t):
    """(durum, a): trouble | pop | hop | ride; a = kurtarma basindan gecen sure."""
    a = t - S.t_rescue
    if a < POP:
        return "trouble", a
    if a < HOP0:
        return "pop", a
    if a < HOP1:
        return "hop", a
    return "ride", a


def _shot(P, s, g, S, t, tl_):
    k = s["kind"]
    if k in ("intro", "drive", "rescue", "act", "outro") or P.cta_t and t >= P.cta_t:
        return "wide"
    st, _ = _friend_state(S, t)
    if k == "say":
        if s.get("who") == S.friend and st == "trouble" and g.mode != "in":
            return "friend"
        return "dino" if s.get("who") == "dino" and not s.get("count") else ("trailer" if s.get("count") else "wide")
    if k == "song":
        idx = sum(1 for x in s["starts"] if x <= tl_)
        seq = HOLD_SHOTS if g.mode == "hold" else DRIVE_SHOTS
        spec = seq[idx % len(seq)]
        if spec == "friend" and st != "trouble":
            spec = "trailer"
        return spec
    return "wide"


def _cam(spec, sx, S, cam):
    if spec == "dino":
        return sx + v.SEAT[0] * trip.S + 60, trip.GROUND + v.SEAT[1] * trip.S + 40, 2.1
    if spec == "face":
        return sx + 380 * trip.S, trip.GROUND - 250 * trip.S, 2.0
    if spec == "wheel":
        return sx + 60, trip.GROUND - 170, 2.3
    if spec == "trailer":
        return sx + v.HITCH * trip.S - 330, trip.GROUND - 260, 1.8
    if spec == "friend":
        dy = _sink(S)[0]
        return S.wfx - cam, trip.GROUND - 190 + dy, 1.9
    return r.W / 2, r.H / 2, 1.0


def _sink(S, t=None):
    """stuck: gomulme derinligi (px) ve yigin olcegi."""
    h = cr.height(S.friend, FR_S)
    if S.look != "stuck":
        return 0.0, 0.0
    if t is None:
        return story.SINK * h, 1.0
    a = t - (S.t_rescue + POP)
    if a < 0:
        return story.SINK * h, 1.0
    return story.SINK * h * max(0.0, 1 - r.ease_out_back(r.clamp01(a / 0.4))), 1 - r.clamp01(a / 0.6)


def _mound(c, x, S, k):
    if k <= 0:
        return
    h = cr.height(S.friend, FR_S)
    surf = trip.GROUND - 6
    w, hh = 0.58 * h * (0.4 + 0.6 * k), 0.10 * h * k
    p = r.oval_path(x, surf, w, hh)
    for ox, oy, rr in ((-0.55, 0.25, 0.5), (0.55, 0.3, 0.48)):
        p = r.skia.Op(p, r.oval_path(x + ox * w, surf + oy * hh, rr * w, 0.8 * hh), r.skia.PathOp.kUnion_PathOp)
    snowy = S.place == "snow" or S.weather == "snow"
    cols = [r.rgb(255, 255, 255), r.rgb(214, 228, 248)] if snowy else [r.rgb(160, 110, 70), r.rgb(115, 75, 45)]
    r.inked(c, [p], r.paint(shader=r.linear((0, surf - hh), (0, surf + hh), cols)), w=9)


def _draw_friend(c, P, S, s, t, tl_, f, sx, cam):
    st, a = _friend_state(S, t)
    if st == "ride":
        return
    x = S.wfx - cam
    talk = _mouth(P, S.friend, f) if s["kind"] == "say" and s.get("who") == S.friend else \
        (_sing(s, tl_) if s["kind"] == "song" and s.get("focus") == S.friend else 0.0)
    if st == "hop":                                     # romorka yay cizerek ziplar
        k = r.ease_in_out((a - HOP0) / (HOP1 - HOP0))
        x1, y1, s1 = _seat_screen(sx, S.k + 1)
        xx = x + (x1 - x) * k
        yy = trip.GROUND + (y1 - trip.GROUND) * k - 300 * math.sin(math.pi * k)
        cr.draw(c, S.friend, xx, yy, s=FR_S + (s1 - FR_S) * k, t=t, expr="happy", arms=(150, 150), hat=S.xmas)
        return
    if st == "pop":
        h, sq = show.jump(r.clamp01((a - POP) / (HOP0 - POP)))
        cr.shadow(c, x, trip.GROUND, FR_S)
        cr.draw(c, S.friend, x, trip.GROUND - h * 90, s=FR_S, t=t, expr="happy", arms=(140, 140), squash=sq,
                hat=S.xmas)
        _mound(c, x, S, _sink(S, t)[1])
        return
    depth, mk = _sink(S, t)
    expr = {"stuck": "scared", "scared": "scared", "sad": "sad"}[S.look]
    dx = 4 * math.sin(t * 55) if S.look in ("stuck", "scared") else 0.0
    arms = (50 + 95 * abs(math.sin(t * 8)),) * 2 if S.look == "stuck" else ((-10, -10) if S.look == "scared" else (-5, -5))
    tilt = 7 * math.sin(t * 5) if S.look == "stuck" else (-9 if S.look == "sad" else 0.0)
    if depth > 0:
        c.save()
        c.clipRect(r.skia.Rect.MakeLTRB(-5000, -5000, 5000, trip.GROUND - 6))
    else:
        cr.shadow(c, x, trip.GROUND, FR_S)
    cr.draw(c, S.friend, x + dx, trip.GROUND + depth, s=FR_S, t=t, expr=expr, talk=talk, look=-0.8, arms=arms,
            tilt=tilt, hat=S.xmas)
    if depth > 0:
        c.restore()
        _mound(c, x, S, mk)


def _riders(P, s, t, tl_, f, hat):
    out = []
    sing = _sing(s, tl_)
    for S in P.stories:
        if t >= S.t_rescue + HOP1:
            kind = S.friend

            def d(c, x, y, sc, kind=kind, S=S):
                hop = 10 * abs(math.sin(tl_ / s["beat"] * math.pi)) if s["kind"] == "song" else 0.0
                talk = sing if s["kind"] == "song" else (_mouth(P, kind, f) if s.get("who") == kind else 0.0)
                cr.draw(c, kind, x, y - hop, s=sc, t=t, expr="happy", talk=talk, arms=(110, 40),
                        hat=hat)
            out.append((d, S.k + 1))
    return out


def draw(c, t, P, scene, spr, f, fw=r.W, fh=r.H, short=False, hud=True):
    s = show._seg_at(P.segs, t)
    tl_ = t - s["start"]
    g = trip.leg_at(P.legs, t)
    S = _leg_story(P, g)
    sx, cam, sp = trip.kin(g, t)
    if s["kind"] == "rescue":                           # halat: traktor biraz geri ceker
        sx -= 70 * r.ease_in_out(r.clamp01((tl_ - 0.3) / 0.9)) * (1 - r.ease_in_out(r.clamp01((tl_ - POP - 0.4) / 0.8)))
    dist = cam + sx
    spec = _shot(P, s, g, S, t, tl_)
    cx, cy, z = _cam(spec, sx, S, cam)
    if short:
        z = max(z, fh / r.H)
        if spec == "wide":
            st_, _ = _friend_state(S, t)
            cx = (S.wfx - cam) if st_ == "trouble" and g.mode == "hold" else sx + 120
    hw, hh = fw / 2 / z, fh / 2 / z
    cx, cy = min(max(cx, hw), r.W - hw), min(max(cy, hh), r.H - hh)
    c.save()
    c.translate(fw / 2, fh / 2)
    c.scale(z, z)
    c.translate(-cx, -cy)
    scene.bg(g.place).draw(c, t, cam)
    _draw_friend(c, P, S, s, t, tl_, f, sx, cam)
    bounce = (5 + 4 * sp) * abs(math.sin(dist / 55.0)) * (0.4 + 0.6 * sp)
    boarded = sum(1 for X in P.stories if t >= X.t_rescue + HOP1)
    gifts = (SEATS - boarded) if P.stories[0].xmas else 0
    v.trailer(c, sx + v.HITCH * trip.S, trip.GROUND, s=trip.S, dist=dist, seats=SEATS,
              riders=_riders(P, s, t, tl_, f, S.xmas), gifts=gifts, bounce=bounce * 0.6)
    st_, a = _friend_state(S, t)
    worried = st_ == "trouble" and (g.mode == "hold" or (g.mode == "in" and s["kind"] == "say"))
    honk = max(0.0, 1 - abs(tl_ - 0.4) / 0.4) if s["kind"] == "rescue" else 0.0
    dino_talk = _mouth(P, "dino", f) if s["kind"] == "say" and s.get("who") == "dino" else _sing(s, tl_)

    def driver(cc, x, y, sc):
        r.dino(cc, x, y, s=sc, expr="surprised" if worried else "happy", mouth=dino_talk, arms=(30, 95),
               look=0.8, hat=S.xmas)
    v.tractor(c, sx, trip.GROUND, s=trip.S, t=t, dist=dist, bounce=bounce, expr="worried" if worried else "happy",
              honk=honk, driver=driver, hat=S.xmas, puff=0.35 + 0.65 * sp)
    if s["kind"] == "rescue" and tl_ < POP + 0.3:       # halat: on tampondan arkadasa
        x0, y0 = sx + 470 * trip.S, trip.GROUND - 150 * trip.S
        x1, y1 = S.wfx - cam - 40, trip.GROUND - 70
        rope = r.skia.Path()
        rope.moveTo(x0, y0)
        sag = 40 * (1 - r.clamp01(tl_ / 0.8))
        rope.quadTo((x0 + x1) / 2, (y0 + y1) / 2 + sag, x1, y1)
        c.drawPath(rope, r.paint(r.INK, stroke=14))
        c.drawPath(rope, r.paint(r.rgb(230, 190, 120), stroke=8))
    for kind, t0, wx, wy, seed in P.fx:
        age = t - t0
        if 0 <= age <= 2.0:
            if kind == "confetti":
                r.confetti(c, r.W / 2, wy, age, seed=seed)
            else:
                r.sparkles(c, wx - cam, wy, age, seed=seed, radius=210)
    c.restore()
    if g.weather == "snow":
        r.snowfall(c, t, w=fw, h=fh)
    if not hud:
        return
    if short:
        y = int(fh * 0.24)
        if s["kind"] == "song":
            li = max(0, sum(1 for x in s["starts"] if x <= tl_) - 1)
            cw = show._cur_word(s, tl_)
            r.caption(c, s["lines"][min(li, len(s["lines"]) - 1)], key=cw[2] if cw else None,
                      key_color=r.rgb(255, 140, 30), y=y, cw=fw)
        elif "text" in s:
            r.caption(c, s["text"], y=y, cw=fw)
        return
    import thumbs
    if s["kind"] == "intro" and P.title:
        c.save()
        c.translate(r.W / 2, 175)
        k = max(0.01, r.ease_out_back(r.clamp01((tl_ - 0.2) / 0.5)))
        c.scale(k, k)
        thumbs._text(c, P.title, 0, 0, 1500, size=124, rot=-3)
        c.restore()
    if s.get("count"):                                  # sayma: buyuk rakam
        k = r.ease_out_back(r.clamp01(tl_ / 0.4))
        c.save()
        c.translate(250, 250)
        c.scale(k, k)
        thumbs._text(c, str(s["count"]), 0, 0, 300, size=260, rot=-4, fill=r.rgb(255, 214, 40))
        c.restore()
    if P.cta_t is not None and t >= P.cta_t:
        story._cta(c, t - P.cta_t)
    n = len(P.stories)
    for i in range(n):                                  # durak gostergesi
        x, y = r.W / 2 + (i - (n - 1) / 2) * 70, 42
        done = t >= P.stories[i].t_rescue + HOP1
        cur = P.stories[i].start <= t < P.stories[i].end
        rad = 22 + (3 * math.sin(t * 6) if cur else 0)
        c.drawCircle(x, y, rad, r.paint(r.rgb(255, 255, 255, 210)))
        c.drawCircle(x, y, rad, r.paint(r.INK, stroke=5))
        if done or cur:
            spr.draw(c, "star", x, y, 40 if done else 30, alpha=1.0 if done else 0.6)
    if s["kind"] == "song":
        r.karaoke(c, s["lines"], s["timings"], tl_)
    elif "text" in s:
        r.caption(c, s["text"])


# ---------------- uretim ----------------
def render(ep, work, out_mp4, frames_dir=None):
    import subprocess
    from PIL import Image
    import music
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    P = build(ep, work)
    print(f"Ses hazirligi: {time.time() - t0:.0f} sn; sure {P.total / 60:.2f} dk; segment {len(P.segs)}", flush=True)
    wav = work / "audio.wav"
    music.write_wav(str(wav), P.audio)
    spr, scene = r.Sprites(outline=14), Scene()
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
            draw(c, fr / FPS, P, scene, spr, fr)
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


def render_shorts(P, work, n=2, frames_dir=None):
    """Her duragin kancasi + ilk kitasi (<=58 sn), dikey."""
    import subprocess
    import music
    from PIL import Image
    SW, SH = 1080, 1920
    work = Path(work)
    spr, scene = r.Sprites(outline=14), Scene()
    surf = r.skia.Surface(SW, SH)
    c = surf.getCanvas()
    out = []
    for i in range(min(n, len(P.stories))):
        S = P.stories[i]
        t0, t1 = S.start, min(S.end, S.start + 58.0)
        songs_k = [s for s in P.segs if s["kind"] == "song" and s.get("story") == i]
        if songs_k and songs_k[0]["end"] <= S.start + 58.0:
            t1 = max(x for x in [s["end"] for s in songs_k] if x <= S.start + 58.0) + 0.3
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
                draw(c, fr / FPS, P, scene, spr, fr, fw=SW, fh=SH, short=True)
                arr = surf.makeImageSnapshot().toarray(colorType=r.skia.kRGBA_8888_ColorType,
                                                       alphaType=r.skia.kUnpremul_AlphaType)
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
        out.append({"path": str(mp4), "story": i, "find": i, "dur": t1 - t0})
        print(f"Short {i} ({S.name}): {t1 - t0:.1f} sn", flush=True)
    return out


def thumbnails(P, out_prefix):
    """T5: A = 1. durak sorun ani (traktor + Dino + sorundaki arkadas), B = romork dolu nese,
    C = 2. durak sorun ani. Arka plan videodaki sahnenin kendisi (A12)."""
    import poster
    from PIL import Image
    spr, scene = r.Sprites(outline=14), Scene()
    paths, ims = [f"{out_prefix}_{k}.jpg" for k in "ABC"], []
    for k, (si, mode) in enumerate(((0, "problem"), (0, "full"), (1 % len(P.stories), "problem"))):
        S = P.stories[si]
        surf = r.new_surface()
        c = surf.getCanvas()
        scene.bg(S.sky_place).draw(c, 0.0, 0.0)
        # yakin: sorun anisinda traktorun yuzu + Dino sol-orta, arkadas sag; nese anisinda romork dolu
        tx, gy, ts_ = (420, 1150, 1.44) if mode == "problem" else (1180, 1120, 1.2)
        riders = []
        if mode == "full":
            for X in P.stories:
                riders.append((lambda cc, x, y, sc, X=X: cr.draw(cc, X.friend, x, y, s=sc, expr="happy", talk=0.9,
                                                                 arms=(150, 60), blink=0.0, hat=X.xmas), X.k + 1))
        v.trailer(c, tx + v.HITCH * ts_, gy, s=ts_, seats=SEATS, riders=riders,
                  gifts=0 if mode == "full" else (SEATS if S.xmas else 0))
        v.tractor(c, tx, gy, s=ts_, t=0.3, expr="worried" if mode == "problem" else "happy",
                  honk=0.0, hat=S.xmas,
                  driver=lambda cc, x, y, sc: r.dino(cc, x, y, s=sc, expr="surprised" if mode == "problem" else "happy",
                                                     mouth=0.8, arms=(30, 130), look=1.0, hat=S.xmas))
        if mode == "problem":
            depth = story.SINK * cr.height(S.friend, 1.9) if S.look == "stuck" else 0.0
            c.save()
            if depth:
                c.clipRect(r.skia.Rect.MakeLTRB(-5000, -5000, 5000, 1000))
            cr.draw(c, S.friend, 1560, 1000 + depth, s=1.9, t=0.0, expr="scared" if S.look != "sad" else "sad",
                    talk=0.7, blink=0.0, look=-0.9, arms=(150, 150), tilt=6, hat=S.xmas)
            c.restore()
            if depth:
                h = cr.height(S.friend, 1.9)
                p = r.oval_path(1560, 1000, 0.6 * h, 0.1 * h)
                snowy = S.place == "snow" or S.weather == "snow"
                r.inked(c, [p], r.paint(r.rgb(255, 255, 255) if snowy else r.rgb(150, 100, 60)), w=12)
        if S.weather == "snow":                         # videoda kar yagiyorsa (afis = video)
            poster._flakes(c)
        if k == 0 and S.xmas and S.melody == "jingle":
            poster._word(c, poster.SONG_WORD["jingle"])
        poster.logo(c)
        ims.append(poster._finish(surf, paths[k], r.SKY.get(S.sky_place) in ("night", "xmas") or S.sky_place == "homex"))
    prev = Image.new("RGB", (3 * 220, 128), "white")
    for k, im in enumerate(ims):
        prev.paste(im.resize((210, 118), Image.LANCZOS), (5 + k * 220, 5))
    pp = f"{out_prefix}_onizleme.png"
    prev.save(pp)
    return paths, pp
