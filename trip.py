"""
Yolculuk motoru (H14 T2): Dino'nun kirmizi traktoru mekandan mekana surer.

Ayak (leg) = bir mekanda gecen sure. Her ayak: GIRIS (traktor soldan girer, yavaslar) -> SEYIR (kamera
traktoru izler, paralaks arka plan kayar) -> CIKIS (kamera durur, traktor saga cikar) ya da DURAK (yavaslayip
arkadasin yaninda durur). Mekan degisimi: traktor ekrandan cikinca kesme, yeni mekanda soldan girer
(rakip olcumu: "10 Little Tractors" yan gorunus; LBB 2-4 sn'de bir cekim).
Cekimler (seyirde ~4 sn'de bir): genis, Dino yakin, tekerlek yakin, romork yakin.
"""
import math
from types import SimpleNamespace

import render2 as r
import vehicles as v

S = 0.9                         # traktor olcegi
GROUND = 900                    # yer cizgisi (ekran)
CRUISE_X = 1060                 # seyirde traktorun ekrandaki yeri (arka teker)
SPEED = 430                     # px/sn
ENTER, EXIT = 2.0, 1.6          # sn
SHOT_EVERY = 4.0
SHOT_CYCLE = ("wide", "dino", "wheel", "wide", "trailer")


def _ease_out(x):
    x = r.clamp01(x)
    return 1 - (1 - x) ** 3


def _ease_in(x):
    x = r.clamp01(x)
    return x ** 3


def plan(legs):
    """legs: [{"place", "dur", "stop": bool}] -> zaman cizelgesi (her ayagin t0/t1)."""
    t = 0.0
    out = []
    for g in legs:
        out.append(SimpleNamespace(place=g["place"], t0=t, t1=t + g["dur"], dur=g["dur"], stop=g.get("stop", False),
                                   weather=g.get("weather")))
        t += g["dur"]
    return out, t


def leg_at(legs, t):
    for g in legs:
        if t < g.t1:
            return g
    return legs[-1]


def kin(g, t):
    """(traktorun ekran x'i, kamera x'i, hiz 0..1) -- ayak icindeki zamana gore."""
    a = t - g.t0
    cruise_end = g.dur - (0.0 if g.stop else EXIT)
    x_in = -900.0                                   # ekran disi (sol)
    if a < ENTER:                                   # giris: kamera sabit, traktor yavaslayarak gelir
        return x_in + (CRUISE_X - x_in) * _ease_out(a / ENTER), 0.0, 1.0
    if g.stop:                                      # durak: seyir sonra yavaslayip durma (son 2 sn duruyor)
        slow0 = max(ENTER, g.dur - 4.0)
        if a < slow0:
            return CRUISE_X, (a - ENTER) * SPEED, 1.0
        b = min(a, g.dur - 1.5) - slow0
        span = max(0.01, (g.dur - 1.5) - slow0)
        k = r.clamp01(b / span)
        cam = (slow0 - ENTER) * SPEED + SPEED * span * (k - k * k / 2)       # hiz dogrusal azalir
        return CRUISE_X, cam, max(0.0, 1 - k)
    if a < cruise_end:                              # seyir: kamera izler
        return CRUISE_X, (a - ENTER) * SPEED, 1.0
    cam = (cruise_end - ENTER) * SPEED              # cikis: kamera durur, traktor hizlanarak cikar
    k = _ease_in((a - cruise_end) / EXIT)
    return CRUISE_X + (2700 - CRUISE_X) * k, cam, 1.0


def stop_cam(g):
    """Durak ayaginin son kamera x'i: duraktaki karakterin dunya x'i = stop_cam + ekran x'i."""
    return kin(g, g.t1 - 1e-3)[1]


def shot(g, t):
    a = t - g.t0
    if a < ENTER or (not g.stop and a > g.dur - EXIT) or (g.stop and a > g.dur - 4.0):
        return "wide"
    return SHOT_CYCLE[int((a - ENTER) / SHOT_EVERY) % len(SHOT_CYCLE)]


def cam_for(spec, sx):
    """(merkez x, merkez y, zum) ekran koordinatinda."""
    if spec == "dino":
        return sx + v.SEAT[0] * S + 60, GROUND + v.SEAT[1] * S + 40, 2.1
    if spec == "wheel":
        return sx + 60, GROUND - 170, 2.3
    if spec == "trailer":
        return sx + v.HITCH * S - 330, GROUND - 260, 1.8
    return r.W / 2, r.H / 2, 1.0


class Scene:
    def __init__(self):
        self._m = {}

    def bg(self, kind):
        if kind not in self._m:
            self._m[kind] = r.Meadow(kind=kind)
        return self._m[kind]


def draw(c, t, legs, scene, driver, riders=(), gifts=0, hat=False, expr="happy", honk=0.0, extra=None):
    """Bir kare. extra(c, g, t, cam_x): durak karakterleri gibi dunyaya bagli cizimler."""
    g = leg_at(legs, t)
    sx, cam, sp = kin(g, t)
    dist = cam + sx                                 # dunya yolu (tekerlek donusu)
    spec = shot(g, t)
    cx, cy, z = cam_for(spec, sx)
    hw, hh = r.W / 2 / z, r.H / 2 / z
    cx, cy = min(max(cx, hw), r.W - hw), min(max(cy, hh), r.H - hh)
    c.save()
    c.translate(r.W / 2, r.H / 2)
    c.scale(z, z)
    c.translate(-cx, -cy)
    scene.bg(g.place).draw(c, t, cam)
    if extra:
        extra(c, g, t, cam)
    bounce = (5 + 4 * sp) * abs(math.sin(dist / 55.0)) * (0.4 + 0.6 * sp)
    v.trailer(c, sx + v.HITCH * S, GROUND, s=S, dist=dist, seats=4, riders=list(riders), gifts=gifts,
              bounce=bounce * 0.6)
    v.tractor(c, sx, GROUND, s=S, t=t, dist=dist, bounce=bounce, expr=expr, honk=honk, driver=driver, hat=hat,
              puff=0.35 + 0.65 * sp)
    c.restore()
    if g.weather == "snow" or g.place in ("snowx",):
        r.snowfall(c, t)
    return spec
