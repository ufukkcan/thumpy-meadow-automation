"""
Konusan hayvan karakterleri (H1, todo 7h): ortak "govde kiti", Dino'nun stiliyle (render2) kodla cizilir.
Arastirma PoC'undan (scratchpad/research/teknik) uretime alindi.

- Ayni iskelet: govde, ayaklar, kollar (on bacak / kanat), bas, yuz (goz, goz kapagi, kas, agiz, yanak).
- Turu ayiran: renkler + kulak / boynuz / burun-gaga / kuyruk / desen (SPEC).
- Agiz sekilleri Rhubarb Lip Sync harfleri (X A B C D E F G H); v1'de ses genliginden secilir (talk 0..1).
- Gagali turlerde (ordek, civciv) agiz yerine gaga acilir.
- Olcek: s=1'de ayaktan basa ~400 px (Dino ile ayni boy); x, y = ayak hizasi (zemin).
Kurallar: maskot Dino ayridir (render2.dino); burada yalnizca yardimci karakterler.
"""
import math

import skia

import render2 as r

rgb, paint, oval, oval_path, inked, INK = r.rgb, r.paint, r.oval, r.oval_path, r.inked, r.INK
MOUTH_DARK = rgb(125, 45, 70)
TONGUE = rgb(250, 130, 150)
WHITE = rgb(255, 255, 255)
BEAK = rgb(255, 160, 40)
BEAK_DK = rgb(220, 110, 30)


def _spec(base, shade, hi, muzzle, foot, ears, nose, tail, patch=None, horns=False, spots=False, wings=False,
          tuft=False, wool=False, stripes=False, scale=1.0, cheek=rgb(255, 120, 150, 200)):
    return dict(base=base, shade=shade, hi=hi, muzzle=muzzle, foot=foot, ears=ears, nose=nose, tail=tail,
                patch=patch, horns=horns, spots=spots, wings=wings, tuft=tuft, wool=wool, stripes=stripes,
                scale=scale, cheek=cheek)


SPEC = {
    "cow": _spec(rgb(252, 250, 248), rgb(214, 206, 230), rgb(255, 255, 255), rgb(255, 188, 200),
                 rgb(120, 105, 130), "cow", "cow", "tuft", patch=rgb(92, 88, 108), horns=True, spots=True),
    "bunny": _spec(rgb(214, 204, 238), rgb(180, 166, 220), rgb(240, 236, 252), rgb(250, 248, 255),
                   rgb(190, 178, 228), "long", "bunny", "puff", scale=0.92),
    "puppy": _spec(rgb(250, 196, 122), rgb(232, 158, 92), rgb(255, 228, 180), rgb(255, 240, 214),
                   rgb(232, 158, 92), "floppy", "dog", "wag", patch=rgb(176, 108, 70), scale=0.95),
    "kitten": _spec(rgb(252, 178, 96), rgb(236, 140, 70), rgb(255, 214, 160), rgb(255, 240, 222),
                    rgb(236, 140, 70), "pointy", "cat", "curl", patch=rgb(222, 120, 55), stripes=True, scale=0.9),
    "piglet": _spec(rgb(255, 190, 205), rgb(240, 150, 175), rgb(255, 225, 232), rgb(255, 160, 185),
                    rgb(235, 140, 165), "pig", "pig", "curly", scale=0.92),
    "lamb": _spec(rgb(252, 249, 240), rgb(226, 218, 205), rgb(255, 255, 255), rgb(255, 236, 228),
                  rgb(120, 105, 115), "side", "sheep", "puff", wool=True, scale=0.92),
    "duck": _spec(rgb(255, 255, 255), rgb(220, 226, 240), rgb(255, 255, 255), rgb(255, 255, 255),
                  BEAK, "none", "beak_flat", "duck", wings=True, tuft=True, scale=0.9),
    "chick": _spec(rgb(255, 220, 80), rgb(245, 185, 40), rgb(255, 240, 160), rgb(255, 230, 120),
                   BEAK, "none", "beak_small", "none", wings=True, tuft=True, scale=0.72),
}
NAMES = list(SPEC)
COLOR = {"cow": rgb(150, 90, 200), "bunny": rgb(150, 110, 220), "puppy": rgb(215, 95, 40),
         "kitten": rgb(240, 120, 40), "piglet": rgb(235, 100, 150), "lamb": rgb(120, 140, 220),
         "duck": rgb(230, 150, 20), "chick": rgb(230, 170, 0)}

# Rhubarb agiz sekilleri -> parametreler (acilim, genislik, yuvarlaklik, dis, dil)
MOUTH = {
    "X": dict(op=0.0),
    "A": dict(op=0.0, press=True),
    "B": dict(op=0.26, w=0.85, teeth=0.55, low=0.45),
    "C": dict(op=0.55, w=0.9, teeth=0.22),
    "D": dict(op=1.0, w=1.0, teeth=0.18, tongue=True),
    "E": dict(op=0.6, w=0.62, rnd=True),
    "F": dict(op=0.42, w=0.34, rnd=True),
    "G": dict(op=0.3, w=0.75, teeth=0.9),
    "H": dict(op=0.55, w=0.85, tongue_up=True),
}
SMILE = {"neutral": 0.5, "happy": 1.0, "surprised": 0.0, "sad": -0.8, "think": 0.1, "listen": 0.4,
         "scared": -0.3}


def shape_for(talk, t):
    """Ses genligi (0..1) -> agiz sekli. Ayni genlikte bile cesitlilik icin E/F araya serpilir."""
    if talk < 0.08:
        return "X"
    if talk < 0.3:
        return "B" if int(t * 9) % 4 else "G"
    if talk < 0.62:
        return "E" if int(t * 7) % 3 == 0 else "C"
    return "D" if int(t * 6) % 4 else "F"


def _mouth(c, mx, my, shape, expr, k=1.0):
    m = MOUTH[shape]
    sm = SMILE.get(expr, 0.5)
    W0, H0 = 36 * k, 56 * k
    if m["op"] <= 0.01:
        p = skia.Path()
        if m.get("press"):
            p.moveTo(mx - W0 * 0.8, my + 2 * k)
            p.quadTo(mx, my + 6 * k * sm, mx + W0 * 0.8, my + 2 * k)
            c.drawPath(p, paint(INK, stroke=11 * k))
        else:
            p.moveTo(mx - W0, my - 6 * k * sm)
            p.quadTo(mx, my + 26 * k * sm, mx + W0, my - 6 * k * sm)
            c.drawPath(p, paint(INK, stroke=8 * k))
        return
    w, h = W0 * m.get("w", 1.0), H0 * m["op"]
    if m.get("rnd"):
        p = oval_path(mx, my + h * 0.45, w, h * 0.6)
    else:
        corner = my - 8 * k * sm
        p = skia.Path()
        p.moveTo(mx - w, corner)
        p.quadTo(mx, my - h * 0.35 * max(0.0, -sm) + h * 0.12 * max(0.0, sm), mx + w, corner)
        p.quadTo(mx, my + h * (1.9 - 0.5 * max(0.0, -sm)), mx - w, corner)
        p.close()
    c.drawPath(p, paint(INK, stroke=9 * k))
    c.drawPath(p, paint(MOUTH_DARK))
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    b = p.getBounds()
    if m.get("teeth"):
        c.drawRect(skia.Rect.MakeLTRB(b.left(), b.top() - 2, b.right(), b.top() + b.height() * m["teeth"] * 0.55),
                   paint(WHITE))
    if m.get("low"):
        c.drawRect(skia.Rect.MakeLTRB(b.left(), b.bottom() - b.height() * m["low"] * 0.5, b.right(), b.bottom() + 2),
                   paint(WHITE))
    if m.get("tongue"):
        c.drawOval(oval(mx, b.bottom(), w * 0.62, h * 0.42), paint(TONGUE))
    if m.get("tongue_up"):
        c.drawOval(oval(mx, b.top() + h * 0.35, w * 0.45, h * 0.32), paint(TONGUE))
    c.restore()


def _beak(c, R, spec, shape):
    """Gaga: ust parca sabit, alt parca agiz acikligi kadar iner."""
    op = MOUTH[shape]["op"]
    flat = spec["nose"] == "beak_flat"
    w, h = (R * 0.42, R * 0.16) if flat else (R * 0.22, R * 0.13)
    y0 = R * 0.3
    low = skia.Path()
    low.addOval(skia.Rect.MakeLTRB(-w * 0.85, y0 - h * 0.2 + op * h * 0.9, w * 0.85, y0 + h * 1.3 + op * h * 1.6))
    if op > 0.05:
        c.drawOval(oval(0, y0 + h * 0.6 + op * h * 0.5, w * 0.7, h * 0.5 + op * h * 0.8), paint(MOUTH_DARK))
    inked(c, [low], paint(BEAK_DK), w=9)
    up = skia.Path()
    up.addOval(skia.Rect.MakeLTRB(-w, y0 - h, w, y0 + h))
    inked(c, [up], paint(BEAK), w=9)
    c.drawOval(oval(-w * 0.35, y0 - h * 0.35, w * 0.3, h * 0.25), paint(rgb(255, 215, 150)))


def _eyes(c, R, spec, expr, blink, look, look_y):
    big = 1.12 if expr in ("surprised", "scared") else 1.0
    pup = 0.7 if expr in ("surprised", "scared") else 1.0
    lid = max(blink, 0.32 if expr == "sad" else 0.0, 0.18 if expr == "think" else 0.0)
    for side in (-1, 1):
        ex, ey = side * R * 0.36, -R * 0.12
        rx, ry = R * 0.25 * big, R * 0.29 * big
        if expr == "happy" or lid > 0.93:
            a = skia.Path()
            if expr == "happy" and lid <= 0.93:
                a.moveTo(ex - rx * 0.8, ey + ry * 0.25)
                a.quadTo(ex, ey - ry * 0.85, ex + rx * 0.8, ey + ry * 0.25)
            else:
                a.moveTo(ex - rx * 0.8, ey + ry * 0.1)
                a.quadTo(ex, ey + ry * 0.6, ex + rx * 0.8, ey + ry * 0.1)
            c.drawPath(a, paint(INK, stroke=10))
        else:
            eye = oval_path(ex, ey, rx, ry)
            inked(c, [eye], paint(WHITE), w=9)
            px, py = ex + look * rx * 0.32, ey + ry * 0.12 + look_y * ry * 0.3
            c.save()
            c.clipPath(eye, skia.ClipOp.kIntersect, True)
            c.drawOval(oval(px, py, rx * 0.64 * pup, ry * 0.68 * pup),
                       paint(shader=r.radial((px, py + 8), rx * 0.8, [rgb(80, 65, 100), rgb(30, 25, 40)])))
            c.drawCircle(px + rx * 0.22 * pup, py - ry * 0.25 * pup, rx * 0.25 * pup, paint(WHITE))
            c.drawCircle(px - rx * 0.2 * pup, py + ry * 0.3 * pup, rx * 0.12 * pup, paint(rgb(255, 255, 255, 220)))
            if lid > 0.02:
                ly = ey - ry + 2 * ry * lid
                tilt = (side * 8 if expr == "sad" else 0)
                c.drawRect(skia.Rect.MakeLTRB(ex - rx - 4, ey - ry - 4, ex + rx + 4, ly), paint(spec["base"]))
                c.drawLine(ex - rx, ly - tilt * 0.5, ex + rx, ly + tilt * 0.5, paint(INK, stroke=8))
            c.restore()
            c.drawPath(eye, paint(INK, stroke=4.5))
        if spec["wool"] or spec["nose"].startswith("beak"):
            by = ey - ry - 16 - (14 if expr == "surprised" else 0)
        else:
            by = ey - ry - 20 - (16 if expr in ("surprised", "scared") else 0) - (12 if expr == "think" and side == 1 else 0)
        inner = {"sad": -14, "scared": -10, "surprised": 0, "happy": 2}.get(expr, 0)
        ix, ox = ex - side * rx * 0.75, ex + side * rx * 0.75
        brow = skia.Path()
        brow.moveTo(ix, by + inner)
        brow.quadTo(ex, by - 10, ox, by + 4)
        c.drawPath(brow, paint(INK, stroke=8))


def _ears(c, R, spec, t, front):
    kind, wob = spec["ears"], 4 * math.sin(t * 2.3)
    for side in (-1, 1):
        c.save()
        if kind == "cow" and not front:
            c.translate(side * R * 1.0, -R * 0.38)
            c.rotate(side * (18 + wob))
            inked(c, [oval_path(side * R * 0.2, 0, R * 0.32, R * 0.15)], paint(spec["base"]), w=10)
            c.drawOval(oval(side * R * 0.23, 0, R * 0.2, R * 0.08), paint(spec["muzzle"]))
        elif kind == "long" and not front:
            c.translate(side * R * 0.36, -R * 0.62)
            c.rotate(side * (12 + wob * 1.5))
            e = skia.Path()
            e.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-R * 0.2, -R * 1.25, R * 0.2, R * 0.1), R * 0.2, R * 0.2))
            inked(c, [e], paint(spec["base"]), w=11)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-R * 0.09, -R * 1.1, R * 0.09, -R * 0.05),
                                              R * 0.09, R * 0.09), paint(rgb(255, 175, 200)))
        elif kind == "floppy" and front:
            c.translate(side * R * 0.92, -R * 0.62)
            c.scale(side, 1)
            c.rotate(-10 + wob * 2)
            e = skia.Path()
            e.moveTo(-R * 0.18, 0)
            e.cubicTo(-R * 0.1, R * 0.45, R * 0.05, R * 0.95, R * 0.28, R * 0.82)
            e.cubicTo(R * 0.46, R * 0.7, R * 0.36, R * 0.2, R * 0.2, -R * 0.05)
            e.close()
            inked(c, [e], paint(spec["patch"]), w=11)
        elif kind in ("pointy", "pig") and not front:
            c.translate(side * R * 0.62, -R * 0.7)
            c.rotate(side * (14 + wob))
            e = skia.Path()
            hgt = R * (0.62 if kind == "pointy" else 0.48)
            e.moveTo(-R * 0.3, R * 0.12)
            e.quadTo(-R * 0.12, -hgt * 0.6, side * R * 0.05, -hgt)
            e.quadTo(R * 0.18, -hgt * 0.5, R * 0.3, R * 0.12)
            e.close()
            inked(c, [e], paint(spec["base"]), w=10)
            inner = skia.Path()
            inner.moveTo(-R * 0.15, R * 0.05)
            inner.quadTo(-R * 0.05, -hgt * 0.45, side * R * 0.04, -hgt * 0.72)
            inner.quadTo(R * 0.09, -hgt * 0.4, R * 0.15, R * 0.05)
            inner.close()
            c.drawPath(inner, paint(rgb(255, 170, 190) if kind == "pointy" else spec["shade"]))
        elif kind == "side" and not front:
            c.translate(side * R * 1.02, -R * 0.2)
            c.rotate(side * (28 + wob))
            inked(c, [oval_path(side * R * 0.16, 0, R * 0.26, R * 0.12)], paint(rgb(236, 226, 214)), w=9)
            c.drawOval(oval(side * R * 0.18, 0, R * 0.15, R * 0.06), paint(rgb(255, 200, 205)))
        c.restore()


def _head(c, R, spec, t, expr, shape, blink, look, look_y):
    _ears(c, R, spec, t, front=False)
    if spec["horns"]:
        for side in (-1, 1):
            h = skia.Path()
            h.moveTo(side * R * 0.42, -R * 0.72)
            h.quadTo(side * R * 0.62, -R * 1.18, side * R * 0.48, -R * 1.22)
            h.quadTo(side * R * 0.52, -R * 1.0, side * R * 0.25, -R * 0.82)
            h.close()
            inked(c, [h], paint(rgb(255, 236, 180)), w=10)
    if spec["tuft"]:                                       # tuy perçemi (ordek, civciv)
        for k, a in enumerate((-18, 0, 18)):
            c.save()
            c.translate(0, -R * 0.9)
            c.rotate(a + 6 * math.sin(t * 3 + k))
            f = skia.Path()
            f.moveTo(-R * 0.09, 0)
            f.quadTo(0, -R * 0.6, R * 0.09, 0)
            f.close()
            inked(c, [f], paint(spec["shade"]), w=8)
            c.restore()
    jaw = 0.0 if spec["nose"].startswith("beak") else MOUTH[shape]["op"]
    hp = skia.Op(oval_path(0, 0, R * 1.08, R * 0.96), oval_path(0, R * 0.3 + jaw * R * 0.12, R * 0.92, R * 0.68),
                 skia.PathOp.kUnion_PathOp)
    if spec["wool"]:                                       # yun: basin etrafinda kabarik halka
        for k in range(11):
            a = math.pi * (0.95 + 1.1 * k / 10)
            inked(c, [oval_path(math.cos(a) * R * 0.98, math.sin(a) * R * 0.86 - R * 0.05, R * 0.28, R * 0.26)],
                  paint(rgb(255, 253, 246)), w=9)
    inked(c, [hp], paint(spec["base"]))
    c.save()
    c.clipPath(hp, skia.ClipOp.kIntersect, True)
    c.drawOval(oval(0, 0, R * 1.08, R * 0.96), paint(spec["shade"]))
    c.drawOval(oval(-R * 0.08, -R * 0.07, R * 1.0, R * 0.88), paint(spec["base"]))
    if spec["spots"]:
        c.drawOval(oval(-R * 0.82, -R * 0.72, R * 0.42, R * 0.3), paint(spec["patch"]))
    if spec["stripes"]:
        for dx in (-0.22, 0.0, 0.22):
            c.drawOval(oval(dx * R, -R * 0.8, R * 0.06, R * 0.2), paint(spec["patch"]))
    if spec["wool"]:
        c.drawOval(oval(0, -R * 0.78, R * 0.6, R * 0.28), paint(rgb(255, 253, 246)))
    c.save()
    c.translate(-R * 0.55, -R * 0.55)
    c.rotate(-35)
    c.drawOval(oval(0, 0, R * 0.16, R * 0.07), paint(spec["hi"], alpha=0.9))
    c.restore()
    c.restore()
    _ears(c, R, spec, t, front=True)
    for side in (-1, 1):
        c.drawOval(oval(side * R * 0.66, R * 0.24, R * 0.17, R * 0.1), paint(spec["cheek"], blur=2))
    nose = spec["nose"]
    if nose.startswith("beak"):
        _beak(c, R, spec, shape)
        _eyes(c, R, spec, expr, blink, look, look_y)
        return
    if nose == "cow":
        inked(c, [oval_path(0, R * 0.5 + jaw * R * 0.07, R * 0.64, R * 0.4 + jaw * R * 0.08)], paint(spec["muzzle"]), w=10)
        for side in (-1, 1):
            c.drawOval(oval(side * R * 0.26, R * 0.34, R * 0.07, R * 0.1), paint(rgb(200, 110, 130)))
        my, k = R * 0.56 + jaw * R * 0.04, 0.85
    elif nose == "pig":
        inked(c, [oval_path(0, R * 0.22, R * 0.34, R * 0.24)], paint(spec["muzzle"]), w=10)
        for side in (-1, 1):
            c.drawOval(oval(side * R * 0.12, R * 0.22, R * 0.06, R * 0.1), paint(rgb(190, 80, 110)))
        my, k = R * 0.6, 0.72
    elif nose == "bunny" or nose == "cat":
        for side in (-1, 1):
            c.drawOval(oval(side * R * 0.14, R * 0.36, R * 0.17, R * 0.13), paint(spec["muzzle"]))
        tri = skia.Path()
        tri.moveTo(-R * 0.1, R * 0.2)
        tri.lineTo(R * 0.1, R * 0.2)
        tri.lineTo(0, R * 0.32)
        tri.close()
        c.drawPath(tri, paint(INK, stroke=6))
        c.drawPath(tri, paint(rgb(255, 140, 170)))
        if nose == "cat":                                  # biyiklar
            for side in (-1, 1):
                for dy in (-0.04, 0.08):
                    c.drawLine(side * R * 0.32, R * (0.34 + dy), side * R * 0.78, R * (0.28 + dy * 2.2),
                               paint(INK, stroke=4))
        my, k = R * 0.5, 0.8
    elif nose == "sheep":
        inked(c, [oval_path(0, R * 0.4 + jaw * R * 0.06, R * 0.44, R * 0.32 + jaw * R * 0.08)], paint(spec["muzzle"]), w=9)
        c.drawOval(oval(0, R * 0.26, R * 0.13, R * 0.09), paint(rgb(110, 80, 95)))
        my, k = R * 0.5, 0.75
    else:
        inked(c, [oval_path(0, R * 0.42 + jaw * R * 0.06, R * 0.48, R * 0.34 + jaw * R * 0.08)], paint(spec["muzzle"]), w=10)
        c.drawOval(oval(0, R * 0.25, R * 0.17, R * 0.12), paint(rgb(60, 45, 60)))
        c.drawOval(oval(-R * 0.05, R * 0.21, R * 0.06, R * 0.03), paint(rgb(255, 255, 255, 180)))
        my, k = R * 0.5, 0.8
    _mouth(c, 0, my, shape, expr, k=k * R / 105)
    _eyes(c, R, spec, expr, blink, look, look_y)


def _tail(c, spec, BW, by, t):
    tail = spec["tail"]
    if tail == "tuft":                                     # inek: asagi sarkan kuyruk + puskul
        p = skia.Path()
        p.moveTo(BW * 0.4, by + 5)
        p.cubicTo(BW * 0.62, by - 10, BW * 0.68 + 6 * math.sin(t * 3), by + 30, BW * 0.64, by + 62)
        c.drawPath(p, paint(INK, stroke=18))
        c.drawPath(p, paint(spec["base"], stroke=9))
        inked(c, [oval_path(BW * 0.64 + 6 * math.sin(t * 3), by + 72, 14, 18)], paint(spec["patch"]), w=9)
    elif tail == "puff":
        inked(c, [oval_path(BW * 0.5, by + 30, 34, 32)], paint(spec["hi"]), w=11)
    elif tail in ("wag", "curl"):
        c.save()
        c.translate(BW * 0.36, by + 20)
        c.rotate((-30 + 22 * math.sin(t * 9)) if tail == "wag" else (-15 + 8 * math.sin(t * 2)))
        p = skia.Path()
        if tail == "wag":
            p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-13, -90, 13, 0), 13, 13))
            inked(c, [p], paint(spec["base"]), w=11)
        else:
            p.moveTo(0, 0)
            p.cubicTo(40, -20, 70, -90, 30, -130)
            c.drawPath(p, paint(INK, stroke=26))
            c.drawPath(p, paint(spec["base"], stroke=14))
        c.restore()
    elif tail == "curly":
        p = skia.Path()
        x0, y0 = BW * 0.45, by + 5
        p.moveTo(x0, y0)
        for k in range(1, 13):
            a = k / 12 * 2.2 * math.pi
            p.lineTo(x0 + 18 + 16 * math.cos(a) + k * 1.5, y0 - 14 * math.sin(a) - k * 1.2)
        c.drawPath(p, paint(INK, stroke=14))
        c.drawPath(p, paint(spec["base"], stroke=7))
    elif tail == "duck":
        p = skia.Path()
        p.moveTo(BW * 0.35, by - 10)
        p.quadTo(BW * 0.62, by - 40, BW * 0.66, by - 70 + 5 * math.sin(t * 4))
        p.quadTo(BW * 0.56, by - 10, BW * 0.4, by + 25)
        p.close()
        inked(c, [p], paint(spec["base"]), w=10)


def draw(c, kind, x, y, s=1.0, t=0.0, expr="neutral", talk=0.0, blink=None, look=0.0, look_y=0.0,
         arms=(18, 18), tilt=0.0, squash=0.0, sx=1.0, alpha=1.0, hat=False):
    """Bir karakter. x, y: ayak hizasi. talk: konusma genligi 0..1 (agiz sekli). blink=None: otomatik.
    arms: (sol, sag) kol kaldirma acisi (derece). tilt: bas egimi. sx: -1 aynalar."""
    spec = SPEC[kind]
    if blink is None:
        ph = (t + (sum(map(ord, kind)) % 97) / 31.0) % 3.9
        blink = max(0.0, 1 - abs(ph - 3.75) / 0.12) if ph > 3.6 else 0.0
    shape = shape_for(talk, t)
    s *= spec["scale"]
    R, BW, BH = 105, 200, 175
    if alpha < 1.0:
        c.saveLayerAlpha(None, int(255 * alpha))
    c.save()
    c.translate(x, y)
    c.scale(s * sx * (1 + 0.5 * squash), s * (1 - squash))
    by = -BH * 0.5 - 22
    _tail(c, spec, BW, by, t)
    foot = [oval_path(side * 52, -18, 44, 24) for side in (-1, 1)]
    inked(c, foot, paint(spec["foot"]))
    body = oval_path(0, by, BW / 2, BH / 2)
    if spec["wool"]:
        for k in range(12):
            a = 2 * math.pi * k / 12
            inked(c, [oval_path(math.cos(a) * BW * 0.45, by + math.sin(a) * BH * 0.42, 34, 32)],
                  paint(spec["base"]), w=9)
    inked(c, [body], paint(spec["base"]))
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    c.drawOval(oval(0, by, BW / 2, BH / 2), paint(spec["shade"]))
    c.drawOval(oval(-BW * 0.07, by - BH * 0.06, BW * 0.47, BH * 0.47), paint(spec["base"]))
    if spec["spots"]:
        c.drawOval(oval(BW * 0.32, by + 10, 40, 34), paint(spec["patch"]))
        c.drawOval(oval(-BW * 0.38, by + 40, 30, 26), paint(spec["patch"]))
    if spec["stripes"]:
        for dx in (-0.36, 0.36):
            for dy in (-0.15, 0.12):
                c.drawOval(oval(dx * BW, by + dy * BH, 12, 26), paint(spec["patch"]))
    c.restore()
    belly = rgb(255, 250, 245) if kind in ("cow", "duck", "lamb") else spec["muzzle"]
    if kind != "duck":
        inked(c, [oval_path(0, by + BH * 0.12, BW * 0.27, BH * 0.28)], paint(belly), w=10)
    for side, lift in ((-1, arms[0]), (1, arms[1])):
        c.save()
        c.translate(side * BW * 0.4, by - BH * 0.18)
        c.rotate(-side * lift)
        a = skia.Path()
        if spec["wings"]:                                  # kanat: genis yaprak
            a.moveTo(0, -8)
            a.cubicTo(side * 34, 10, side * 30, 70, side * 6, 84)
            a.cubicTo(-side * 14, 60, -side * 12, 12, 0, -8)
            inked(c, [a], paint(spec["shade"]), w=10)
        else:
            a.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-18, -10, 18, 62), 18, 18))
            inked(c, [a], paint(spec["base"]), w=12)
            inked(c, [oval_path(0, 66, 21, 19)], paint(spec["foot"]), w=10)
        c.restore()
    c.save()
    c.translate(0, by - BH * 0.5 - R * 0.45)
    c.rotate(tilt)
    _head(c, R, spec, t, expr, shape, blink, look, look_y)
    if hat:                                            # Noel sapkasi (afis v2 trio ile ayni yer/oran)
        r.santa_hat(c, 20, -84, 132, tilt=12, flop=1)
    c.restore()
    c.restore()
    if alpha < 1.0:
        c.restore()


def shadow(c, x, y, s=1.0, lift=0.0):
    k = 1 / (1 + lift / 260)
    c.drawOval(oval(x, y, 125 * s * k, 22 * s * k), paint(rgb(40, 70, 40, 80), blur=10))


def height(kind, s=1.0):
    """Ayaktan bas tepesine yaklasik yukseklik (kamera/konusma balonu icin)."""
    return 400 * s * SPEC[kind]["scale"]
