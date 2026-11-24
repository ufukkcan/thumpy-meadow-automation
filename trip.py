"""
Yolculuk kinematigi (H14 T2): Dino'nun kirmizi traktoru mekandan mekana surer.

Ayak (leg) = bir zaman araliginda tek mekan + tek hareket kipi:
  in   : traktor soldan girer (kamera sabit), seyreder (kamera izler, paralaks kayar), yavaslayip durur
  hold : durur (kamera sabit)
  out  : kalkar, seyreder, sonunda kamera durur ve traktor saga cikar
Mekan degisimi: traktor ekrandan cikinca kesme, yeni mekanda soldan girer (rakip olcumu: "10 Little Tractors"
yan gorunus; LBB 2-4 sn'de bir cekim). Kamera x'i paralaks arka planin kaymasidir; dunyaya bagli karakterler
ekranda (dunya_x - kamera_x) noktasinda cizilir.
"""
from types import SimpleNamespace

import render2 as r

S = 0.9                         # traktor olcegi
GROUND = 900                    # yer cizgisi (ekran)
CRUISE_X = 1060                 # seyirde traktorun ekrandaki yeri (arka teker)
SPEED = 430                     # px/sn
ENTER, EXIT, ACCEL, DECEL = 2.0, 1.6, 1.5, 3.0     # sn
X_IN, X_OUT = -900.0, 2700.0    # ekran disi sol / sag


def _ease_out(x):
    x = r.clamp01(x)
    return 1 - (1 - x) ** 3


def _ease_in(x):
    x = r.clamp01(x)
    return x ** 3


def leg(place, t0, t1, mode, cam0=0.0, weather=None, x_from=None):
    """x_from (yalnizca "in"): traktor bu ekran x'inden baslar ve kamera sabit kalir -> bolumun ilk karesinde
    traktor de duraktaki arkadas da ekranda (H13: ilk kare dolu)."""
    return SimpleNamespace(place=place, t0=t0, t1=t1, dur=t1 - t0, mode=mode, cam0=cam0, weather=weather,
                           x_from=x_from)


def leg_at(legs, t):
    for g in legs:
        if t < g.t1:
            return g
    return legs[-1]


def kin(g, t):
    """(traktorun ekran x'i, kamera x'i, hiz 0..1)."""
    a = min(max(t - g.t0, 0.0), g.dur)
    if g.mode == "hold":
        return CRUISE_X, g.cam0, 0.0
    if g.mode == "in" and g.x_from is not None:
        k = a / max(g.dur, 1e-3)
        return g.x_from + (CRUISE_X - g.x_from) * _ease_out(k), g.cam0, 1.0 - k
    if g.mode == "in":
        enter = min(ENTER, g.dur * 0.45)
        dec = min(DECEL, max(0.6, g.dur - enter))
        if a < enter:
            return X_IN + (CRUISE_X - X_IN) * _ease_out(a / enter), g.cam0, 1.0
        cruise = max(0.0, g.dur - enter - dec)
        if a < enter + cruise:
            return CRUISE_X, g.cam0 + (a - enter) * SPEED, 1.0
        b = r.clamp01((a - enter - cruise) / dec)
        return CRUISE_X, g.cam0 + cruise * SPEED + SPEED * dec * (b - b * b / 2), 1.0 - b
    # out: kalkis (hiz dogrusal artar) -> seyir -> cikis
    acc = min(ACCEL, g.dur * 0.3)
    ex = min(EXIT, g.dur * 0.35)
    if a < acc:
        k = a / acc
        return CRUISE_X, g.cam0 + SPEED * acc * k * k / 2, k
    cruise_end = g.dur - ex
    if a < cruise_end:
        return CRUISE_X, g.cam0 + SPEED * acc / 2 + (a - acc) * SPEED, 1.0
    cam = g.cam0 + SPEED * acc / 2 + (cruise_end - acc) * SPEED
    return CRUISE_X + (X_OUT - CRUISE_X) * _ease_in((a - cruise_end) / ex), cam, 1.0


def cam_end(g):
    return kin(g, g.t1 - 1e-3)[1]
