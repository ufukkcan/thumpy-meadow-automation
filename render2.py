"""
Yeni cizim motoru (K-19): Skia (kenar yumusatma, gradyan, golge, bulaniklik).

- Nesneler: Fluent Color SVG -> resvg -> PNG -> Skia goruntusu (assets.py), bir kez rasterlestirilir.
  Sprites(outline=...) verilirse nesnenin etrafina kalin koyu kontur eklenir (cizgi film stili, 7b).
- Dino ve arka plan bizim (maskot asla emoji olmaz). Cizgi film stili: koyu kontur, duz renk +
  tek golge tonu, iri gozler (bebek semasi), ifadeler (mutlu / saskin / dinliyor).
- Tum koordinatlar 1920x1080; kamera yakinlasmasi canvas donusumuyle.
"""
import io
import math
import random

import numpy as np
import skia

import assets

W, H = 1920, 1080
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GROUND_Y = 800


def rgb(r, g, b, a=255):
    return skia.ColorSetARGB(int(a), int(r), int(g), int(b))


INK = rgb(52, 42, 70)        # kontur rengi (koyu mor-lacivert, siyahtan yumusak)
LINE = 14                    # kontur kalemi; dolgu ustune cizildigi icin gorunen kalinlik LINE/2


def paint(color=None, shader=None, blur=0.0, stroke=0.0, alpha=1.0, cap_round=True):
    p = skia.Paint(AntiAlias=True)
    if color is not None:
        p.setColor(color)
    if shader is not None:
        p.setShader(shader)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeJoin(skia.Paint.kRound_Join)
        if cap_round:
            p.setStrokeCap(skia.Paint.kRound_Cap)
    if alpha < 1.0:
        p.setAlphaf(max(0.0, alpha) * p.getAlphaf())
    return p


def linear(p0, p1, colors, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], colors, pos)


def radial(c, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*c), r, colors, pos)


def oval(cx, cy, rx, ry):
    return skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry)


def oval_path(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(oval(cx, cy, rx, ry))
    return p


def inked(c, paths, fill, w=LINE):
    """Cizgi film konturu: once tum parcalarin konturu, sonra dolgular -> birlesik sekle tek dis cizgi."""
    for p in paths:
        c.drawPath(p, paint(INK, stroke=w))
    for p in paths:
        c.drawPath(p, fill)


# ---------------- yumusak gecisler ----------------
def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_in_out(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out_back(x, k=1.70158):
    x = clamp01(x) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


def ease_out_elastic(x):
    x = clamp01(x)
    if x in (0.0, 1.0):
        return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


# ---------------- yazi ----------------
def _typeface():
    for make in (lambda: skia.Typeface.MakeFromFile(FONT_PATH),
                 lambda: skia.FontMgr.RefDefault().makeFromFile(FONT_PATH),
                 lambda: skia.Typeface("DejaVu Sans", skia.FontStyle.Bold())):
        try:
            tf = make()
            if tf is not None:
                return tf
        except Exception:
            continue
    raise RuntimeError("Skia yazi tipi yuklenemedi: " + FONT_PATH)


_TF = None


def font(size):
    global _TF
    if _TF is None:
        _TF = _typeface()
    return skia.Font(_TF, size)


def text_outlined(c, s, x, y, f, fill, outline=rgb(255, 255, 255), width=10):
    c.drawString(s, x, y, f, paint(outline, stroke=width))
    c.drawString(s, x, y, f, paint(fill))


# ---------------- nesneler (Fluent) ----------------
def _outline_png(data, w):
    """PNG'nin etrafina w piksel koyu kontur ekler (alfa esiklenip daire cekirdekle genisletilir).
    Donus: (png_bayt, kenar_payi)."""
    from PIL import Image, ImageFilter
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    pad = w + 4
    big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    big.paste(im, (pad, pad))
    a = np.asarray(big.getchannel("A")) > 90          # Fluent'in soluk golge kenarlari kontura dahil olmasin
    m = np.zeros_like(a)
    hh, ww = a.shape
    for dy in range(-w, w + 1):
        for dx in range(-w, w + 1):
            if dx * dx + dy * dy > w * w:
                continue
            m[max(0, dy):hh + min(0, dy), max(0, dx):ww + min(0, dx)] |= \
                a[max(0, -dy):hh + min(0, -dy), max(0, -dx):ww + min(0, -dx)]
    alpha = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    ink = Image.new("RGBA", big.size, (52, 42, 70, 0))
    ink.putalpha(alpha)
    out = Image.alpha_composite(ink, big)
    buf = io.BytesIO()
    out.save(buf, "PNG")
    return buf.getvalue(), pad


class Sprites:
    """Ad -> Skia goruntusu (512 px, mipmap'li). Ciziminde merkez noktasi verilir.
    outline > 0: 512 px olcekte kontur kalinligi (cizgi film stili)."""

    def __init__(self, px=512, outline=0):
        self.px = px
        self.outline = outline
        self._img = {}

    def get(self, name):
        if name not in self._img:
            data, pad = assets.png(name, self.px), 0
            if self.outline:
                data, pad = _outline_png(data, self.outline)
            img = skia.Image.MakeFromEncoded(skia.Data.MakeWithCopy(data))
            if img is None:
                raise RuntimeError(f"Goruntu cozulemedi: {name}")
            self._img[name] = (img.withDefaultMipmaps(), pad)
        return self._img[name]

    def draw(self, c, name, cx, cy, size, rot=0.0, sx=1.0, sy=1.0, alpha=1.0, shadow_y=None):
        """size: piksel cinsinden genislik (kontur haric). shadow_y verilirse zemine yumusak golge."""
        if size <= 1 or alpha <= 0.01:
            return
        if shadow_y is not None:
            lift = max(0.0, shadow_y - (cy + size * 0.42))
            k = 1 / (1 + lift / 220)
            c.drawOval(oval(cx, shadow_y, size * 0.36 * k, size * 0.07 * k),
                       paint(rgb(40, 70, 40, 70 * alpha), blur=8))
        img, pad = self.get(name)
        k = size / self.px
        c.save()
        c.translate(cx, cy)
        c.rotate(rot)
        c.scale(k * sx, k * sy)
        c.drawImage(img, -self.px / 2 - pad, -self.px / 2 - pad,
                    skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear),
                    paint(rgb(255, 255, 255), alpha=alpha))
        c.restore()


# ---------------- arka plan (bizim) ----------------
_CLOUD = ((0, 0, 60), (55, -20, 70), (115, 0, 55), (60, 22, 58), (-45, 12, 42), (165, 16, 40))


def _cloud(c, x, y, s, a=1.0):
    for dx, dy, r in _CLOUD:     # yumusak kontur (gokyuzunde koyu cizgi fazla sert durur)
        c.drawCircle(x + dx * s, y + dy * s, r * s, paint(rgb(140, 175, 215, 255 * a), stroke=10 * s))
    for dx, dy, r in _CLOUD:
        c.drawCircle(x + dx * s, y + dy * s, r * s,
                     paint(shader=linear((0, y - 70 * s), (0, y + 70 * s),
                                         [rgb(255, 255, 255, 255 * a), rgb(232, 242, 252, 255 * a)])))


def _hill_path(base_y, amp, waves, phase, width, step=24):
    p = skia.Path()
    p.moveTo(0, H + 40)          # alt kenar kadraj disinda: kontur gorunmesin
    x = 0.0
    while x <= width:
        y = base_y - amp * (0.55 + 0.45 * math.sin(x / width * waves * 2 * math.pi + phase))
        p.lineTo(x, y)
        x += step
    p.lineTo(width, H + 40)
    p.close()
    return p


def _flower(c, x, y, s, col):
    for i in range(5):
        a = i * 2 * math.pi / 5
        c.drawCircle(x + math.cos(a) * 9 * s, y + math.sin(a) * 9 * s, 7 * s, paint(col))
    c.drawCircle(x, y, 6 * s, paint(rgb(255, 210, 80)))


def _layer(width, draw):
    surf = skia.Surface(width, H)
    c = surf.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    draw(c, width)
    return surf.makeImageSnapshot()


class Meadow:
    """Paralaks cayir: gokyuzu sabit; uzak/orta tepe ve on cayir farkli hizda kayar."""
    PAD = 700

    def __init__(self, seed=3):
        rnd = random.Random(seed)
        wd = W + self.PAD

        def far(c, w):
            c.drawPath(_hill_path(560, 120, 2.2, 0.6, w),
                       paint(shader=linear((0, 420), (0, 760), [rgb(150, 205, 225), rgb(125, 185, 205)])))

        def mid(c, w):
            hill = _hill_path(650, 110, 1.6, 2.1, w)
            c.drawPath(hill, paint(rgb(60, 120, 80), stroke=8))
            c.drawPath(hill, paint(shader=linear((0, 520), (0, 800), [rgb(140, 215, 140), rgb(100, 180, 110)])))
            for i in range(9):     # yuvarlak agaclar
                x, y = 120 + i * (w - 200) / 8 + rnd.uniform(-40, 40), 640 + rnd.uniform(-20, 20)
                trunk = skia.Path()
                trunk.addRect(skia.Rect.MakeXYWH(x - 9, y, 18, 60))
                inked(c, [trunk], paint(rgb(150, 105, 70)), w=8)
                inked(c, [oval_path(x, y - 10, 58, 58)],
                      paint(shader=radial((x - 20, y - 35), 80, [rgb(130, 215, 120), rgb(75, 160, 90)])), w=8)

        def near(c, w):
            hill = _hill_path(GROUND_Y - 40, 26, 1.1, 0.3, w)
            c.drawPath(hill, paint(INK, stroke=LINE))
            c.drawPath(hill, paint(shader=linear((0, GROUND_Y - 70), (0, H),
                                                 [rgb(155, 225, 110), rgb(110, 195, 90), rgb(88, 170, 80)],
                                                 [0.0, 0.45, 1.0])))
            cols = [rgb(255, 120, 150), rgb(255, 255, 255), rgb(170, 140, 255), rgb(255, 170, 90)]
            for _ in range(70):
                x, y = rnd.uniform(0, w), rnd.uniform(GROUND_Y + 10, H - 10)
                if rnd.random() < 0.5:
                    _flower(c, x, y, rnd.uniform(0.7, 1.2), rnd.choice(cols))
                else:            # cimen tutami
                    for k in (-1, 0, 1):
                        c.drawLine(x, y, x + k * 8, y - 22, paint(rgb(80, 160, 75), stroke=4))

        self.far, self.mid, self.near = _layer(wd, far), _layer(wd, mid), _layer(wd, near)
        self.clouds = [(rnd.uniform(0, W + 400), rnd.uniform(90, 330), rnd.uniform(0.7, 1.15),
                        rnd.uniform(8, 20)) for _ in range(6)]

    def draw(self, c, t, cam_x=0.0):
        c.drawRect(skia.Rect.MakeWH(W, H),
                   paint(shader=linear((0, 0), (0, 700), [rgb(105, 185, 245), rgb(205, 236, 255)])))
        sx, sy = 1640, 170       # gunes: yumusak hale + konturlu disk + gulen yuz
        c.drawCircle(sx, sy, 210, paint(shader=radial((sx, sy), 210,
                                                       [rgb(255, 245, 190, 150), rgb(255, 245, 190, 0)])))
        inked(c, [oval_path(sx, sy, 80, 80)],
              paint(shader=radial((sx - 20, sy - 20), 90, [rgb(255, 250, 200), rgb(255, 205, 80)])), w=10)
        blink = (t % 5.3) > 5.15
        for ex in (-24, 24):
            if blink:
                c.drawLine(sx + ex - 8, sy - 10, sx + ex + 8, sy - 10, paint(INK, stroke=5))
            else:
                c.drawOval(oval(sx + ex, sy - 12, 6, 9), paint(INK))
        smile = skia.Path()
        smile.moveTo(sx - 26, sy + 14)
        smile.quadTo(sx, sy + 38, sx + 26, sy + 14)
        c.drawPath(smile, paint(INK, stroke=6))
        for ex in (-46, 46):
            c.drawOval(oval(sx + ex, sy + 12, 11, 7), paint(rgb(255, 140, 120, 160)))
        for x0, y, s, v in self.clouds:
            x = (x0 + v * t) % (W + 600) - 300
            _cloud(c, x, y, s)
        for img, k in ((self.far, 0.15), (self.mid, 0.4), (self.near, 1.0)):
            c.drawImage(img, -self.PAD / 2 - cam_x * k, 0)


# ---------------- Dino (bizim maskot) ----------------
BODY_W, BODY_H = 300, 340
D_BASE, D_SHADE, D_HI = rgb(118, 214, 138), rgb(80, 178, 112), rgb(200, 248, 205)


def _star4(cx, cy, r):
    p = skia.Path()
    p.moveTo(cx, cy - r)
    for a, b in ((cx + r * 0.22, cy - r * 0.22), (cx + r, cy), (cx + r * 0.22, cy + r * 0.22), (cx, cy + r),
                 (cx - r * 0.22, cy + r * 0.22), (cx - r, cy), (cx - r * 0.22, cy - r * 0.22), (cx, cy - r)):
        p.lineTo(a, b)
    p.close()
    return p


def _arm_lift(side, t, wave, excited, arms):
    if arms is not None:
        return arms[0 if side < 0 else 1]
    if excited:
        return 150 + 12 * math.sin(t * 14 + side)
    if side == 1 and wave > 0:
        return 20 + (125 + 25 * math.sin(t * 12)) * clamp01(wave)
    return 20 + 8 * math.sin(t * 3 + (0 if side > 0 else math.pi))


def dino(c, cx, cy, s=1.0, t=0.0, mouth=0.0, wave=0.0, excited=False, squash=0.0, look=0.0,
         expr="neutral", arms=None, lean=0.0, look_y=0.0, dizzy=0.0):
    """cx, cy: govde merkezi. mouth 0..1 (ses), wave 0..1 (sag el sallama),
    squash >0 basilma (zipla inis), <0 uzama. expr: neutral | happy | surprised | listen.
    arms: (sol, sag) kol acisi (derece; 0 asagi, 150 yukari, eksi = iceri / alkis).
    lean: ayak noktasi etrafinda egilme (derece). dizzy 0..1: basin etrafinda donen yildizlar."""
    bw, bh = BODY_W, BODY_H
    c.save()
    c.translate(cx, cy + bh * s * 0.5)              # ayak hizasindan esnet / egil
    c.rotate(lean)
    c.scale(s * (1 + 0.5 * squash), s * (1 - squash))
    c.translate(0, -bh * 0.5)

    # kuyruk
    tail = skia.Path()
    tail.moveTo(-bw * 0.30, bh * 0.05)
    tail.cubicTo(-bw * 0.75, bh * 0.20, -bw * 0.95, bh * 0.05, -bw * 1.02, -bh * 0.12 + 8 * math.sin(t * 3))
    tail.cubicTo(-bw * 0.85, bh * 0.25, -bw * 0.60, bh * 0.42, -bw * 0.20, bh * 0.38)
    tail.close()
    inked(c, [tail], paint(D_BASE))

    # sirt pullari
    spikes = []
    for px, py, pr in ((-0.22, -0.46, 0.13), (0.02, -0.56, 0.16), (0.26, -0.44, 0.13)):
        x, y, r = bw * px, bh * py, bw * pr
        sp = skia.Path()
        sp.moveTo(x - r * 0.75, y + bh * 0.10)
        sp.quadTo(x - r * 0.15, y - bh * 0.11, x, y - bh * 0.10)
        sp.quadTo(x + r * 0.15, y - bh * 0.11, x + r * 0.75, y + bh * 0.10)
        sp.close()
        spikes.append(sp)
    inked(c, spikes, paint(rgb(255, 178, 70)))

    # ayaklar
    inked(c, [oval_path(side * bw * 0.20, bh * 0.50, 50, 27) for side in (-1, 1)], paint(D_SHADE))

    # govde: duz renk + tek golge tonu (sag alt hilal) + parlama
    body = oval_path(0, 0, bw / 2, bh / 2)
    inked(c, [body], paint(D_BASE))
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    c.drawOval(oval(0, 0, bw / 2, bh / 2), paint(D_SHADE))
    c.drawOval(oval(-bw * 0.07, -bh * 0.06, bw * 0.47, bh * 0.47), paint(D_BASE))
    c.save()
    c.translate(-bw * 0.24, -bh * 0.30)
    c.rotate(-35)
    c.drawOval(oval(0, 0, bw * 0.10, bh * 0.05), paint(D_HI, alpha=0.9))
    c.restore()
    c.restore()

    # karin
    inked(c, [oval_path(0, bh * 0.20, bw * 0.29, bh * 0.26)], paint(rgb(252, 246, 214)), w=10)

    # kollar: omuzdan donen kapsul + yuvarlak el
    for side in (-1, 1):
        lift = _arm_lift(side, t, wave, excited, arms)
        c.save()
        c.translate(side * bw * 0.40, -bh * 0.02)
        c.rotate(-side * lift)
        arm = skia.Path()
        arm.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-20, -10, 20, 80), 20, 20))
        inked(c, [arm, oval_path(0, 82, 25, 25)], paint(D_BASE), w=12)
        c.restore()

    # yanaklar (duz, doygun pembe)
    for side in (-1, 1):
        c.drawOval(oval(side * bw * 0.34, bh * 0.0, 27, 17), paint(rgb(255, 120, 150, 220), blur=2))

    # gozler (bebek semasi: iri, parlak)
    blink = (t % 3.7) > 3.55 and expr != "surprised"
    big = 1.15 if (excited or expr == "surprised") else 1.0
    pup = 0.72 if expr == "surprised" else 1.0
    for side in (-1, 1):
        ex, ey = side * bw * 0.17, -bh * 0.17
        if expr == "happy" or blink:
            arc = skia.Path()
            if expr == "happy":                    # "^ ^" gulen gozler
                arc.moveTo(ex - 28, ey + 10)
                arc.quadTo(ex, ey - 28, ex + 28, ey + 10)
            else:
                arc.moveTo(ex - 28, ey + 4)
                arc.quadTo(ex, ey + 24, ex + 28, ey + 4)
            c.drawPath(arc, paint(INK, stroke=10))
        else:
            inked(c, [oval_path(ex, ey, 36 * big, 42 * big)], paint(rgb(255, 255, 255)), w=9)
            px, py = ex + look * 11, ey + 4 + look_y * 10
            c.drawOval(oval(px, py, 23 * pup * big, 28 * pup * big),
                       paint(shader=radial((px, py + 8), 30, [rgb(80, 65, 100), rgb(30, 25, 40)])))
            c.drawCircle(px + 8 * pup, py - 10 * pup, 9 * big * pup, paint(rgb(255, 255, 255)))
            c.drawCircle(px - 7 * pup, py + 12 * pup, 4.5 * big * pup, paint(rgb(255, 255, 255, 220)))
        # kaslar
        by = ey - 58 - (14 if expr == "surprised" else 0) - (12 if expr == "listen" and side == 1 else 0)
        brow = skia.Path()
        brow.moveTo(ex - 22, by + 6)
        brow.quadTo(ex, by - 8, ex + 22, by + 6)
        c.drawPath(brow, paint(INK, stroke=8))

    # agiz
    m = clamp01(mouth)
    my = bh * 0.05
    if expr == "surprised":
        inked(c, [oval_path(0, my + 16, 18 + 10 * m, 22 + 14 * m)], paint(rgb(125, 45, 70)), w=10)
    elif m > 0.08 or excited or expr == "happy":
        oh = 8 + 40 * max(m, 0.5 if (excited or expr == "happy") else 0)
        ow = 32 + 12 * m
        mp = skia.Path()
        mp.moveTo(-ow, my - 4)
        mp.quadTo(0, my + 2 * oh, ow, my - 4)
        mp.quadTo(0, my + 6, -ow, my - 4)
        mp.close()
        c.drawPath(mp, paint(INK, stroke=9))
        c.drawPath(mp, paint(rgb(125, 45, 70)))
        c.save()
        c.clipPath(mp, skia.ClipOp.kIntersect, True)
        c.drawOval(oval(0, my + oh * 1.05, ow * 0.6, oh * 0.45), paint(rgb(250, 130, 150)))
        c.restore()
    else:
        sm = skia.Path()
        sm.moveTo(-32, my)
        sm.quadTo(0, my + 28, 32, my)
        c.drawPath(sm, paint(INK, stroke=8))

    # bas donmesi yildizlari
    if dizzy > 0:
        for i in range(3):
            a = t * 5 + i * 2 * math.pi / 3
            x, y = math.cos(a) * 95, -bh * 0.62 + math.sin(a) * 24
            st = _star4(x, y, 22)
            c.drawPath(st, paint(INK, stroke=8, alpha=dizzy))
            c.drawPath(st, paint(rgb(255, 215, 60), alpha=dizzy))
    c.restore()


def dino_shadow(c, cx, ground_y, s=1.0, lift=0.0):
    k = 1 / (1 + lift / 260)
    c.drawOval(oval(cx, ground_y, 150 * s * k, 26 * s * k), paint(rgb(40, 70, 40, 80), blur=10))


# ---------------- sahne ogeleri ----------------
_BUSH = ((-0.62, 0.05, 0.42), (-0.30, -0.25, 0.48), (0.10, -0.38, 0.52), (0.45, -0.18, 0.46),
         (0.68, 0.08, 0.38), (0.0, 0.05, 0.60))


def bush(c, x, y, s=1.0, wiggle=0.0, t=0.0):
    """x, y: tabanin ortasi (zemin). wiggle 0..1: sallanma siddeti. Yukseklik ~220*s."""
    R = 150 * s
    c.save()
    c.translate(x, y)
    c.rotate(wiggle * 6 * math.sin(t * 28))
    c.scale(1 + wiggle * 0.05 * math.sin(t * 31), 1)
    blobs = [(dx * R, -R * 0.55 + dy * R, r * R) for dx, dy, r in _BUSH]
    for bx, by, br in blobs:
        c.drawCircle(bx, by, br, paint(INK, stroke=LINE))
    for bx, by, br in blobs:
        c.drawCircle(bx, by, br, paint(shader=radial((bx - br * 0.3, by - br * 0.4), br * 1.4,
                                                      [rgb(125, 215, 105), rgb(70, 160, 80)])))
    for bx, by, br in blobs[:5]:      # yaprak parlamasi
        arc = skia.Path()
        arc.moveTo(bx - br * 0.45, by - br * 0.25)
        arc.quadTo(bx - br * 0.2, by - br * 0.6, bx + br * 0.15, by - br * 0.55)
        c.drawPath(arc, paint(rgb(190, 245, 160), stroke=6))
    c.restore()


def peek_eyes(c, x, y, t, k=1.0, look=0.0):
    """Calinin icinden bakan gozler. x, y: gozlerin ortasi. k 0..1 gorunurluk."""
    if k <= 0.01:
        return
    c.drawOval(oval(x, y, 74 * k, 36 * k), paint(rgb(35, 70, 40)))
    blink = (t % 2.9) > 2.75
    for ex in (-26, 26):
        if blink:
            c.drawLine(x + ex - 14, y, x + ex + 14, y, paint(rgb(255, 255, 255), stroke=6))
            continue
        c.drawOval(oval(x + ex, y, 17 * k, 21 * k), paint(rgb(255, 255, 255)))
        c.drawCircle(x + ex + look * 6, y + 3, 9 * k, paint(rgb(30, 25, 40)))
        c.drawCircle(x + ex + look * 6 + 3, y - 1, 3 * k, paint(rgb(255, 255, 255)))


def ask_bubble(c, x, y, k, prog, t=0.0):
    """Soru balonu: buyuk '?' + bekleme sayaci (3 nokta, prog 0..1 ile dolar)."""
    if k <= 0.01:
        return
    s = ease_out_back(k)
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.rotate(4 * math.sin(t * 3))
    box = skia.Path()
    box.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-130, -120, 130, 100), 70, 70))
    tail = skia.Path()
    tail.moveTo(-60, 80)
    tail.lineTo(-120, 160)
    tail.lineTo(0, 92)
    tail.close()
    inked(c, [box, tail], paint(rgb(255, 255, 255)))
    f = font(170)
    q = "?"
    text_outlined(c, q, -f.measureText(q) / 2, 40, f, rgb(255, 130, 40), outline=INK, width=12)
    for i in range(3):
        on = prog > (i + 1) / 3.0 - 0.001
        c.drawCircle(-44 + i * 44, 72, 12, paint(INK, stroke=6))
        c.drawCircle(-44 + i * 44, 72, 12, paint(rgb(255, 130, 40) if on else rgb(225, 225, 235)))
    c.restore()


# ---------------- efektler ----------------
def sparkles(c, cx, cy, age, seed=0, radius=200, n=9, life=1.6):
    if age < 0 or age > life:
        return
    rnd = random.Random(seed)
    fade = 1 - (age / life) ** 2
    for i in range(n):
        a = i / n * 2 * math.pi + rnd.uniform(-0.3, 0.3)
        d = radius * (0.5 + 0.6 * ease_out_back(age / 0.6)) * rnd.uniform(0.8, 1.2)
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        r = (18 + 14 * math.sin(age * 12 + i)) * rnd.uniform(0.7, 1.3)
        col = rgb(255, 215, 60) if i % 2 else rgb(255, 255, 255)
        st = _star4(x, y, r)
        c.drawPath(st, paint(INK, stroke=7, alpha=fade))      # kontur: acik gokyuzunde de secilsin
        c.drawPath(st, paint(col, alpha=fade))


CONFETTI = [rgb(255, 90, 110), rgb(255, 200, 60), rgb(80, 180, 255), rgb(120, 220, 120), rgb(200, 120, 255)]


def confetti(c, cx, cy, age, seed=0, n=46, life=1.9):
    if age < 0 or age > life:
        return
    rnd = random.Random(seed)
    fade = 1 - clamp01((age - life * 0.6) / (life * 0.4))
    for i in range(n):
        a = rnd.uniform(-math.pi * 0.95, -math.pi * 0.05)
        v = rnd.uniform(500, 1100)
        x = cx + math.cos(a) * v * age
        y = cy + math.sin(a) * v * age + 0.5 * 1500 * age * age
        c.save()
        c.translate(x, y)
        c.rotate(rnd.uniform(0, 360) + age * rnd.uniform(-720, 720))
        c.scale(1, abs(math.sin(age * rnd.uniform(6, 14) + i)) + 0.2)
        c.drawRect(skia.Rect.MakeXYWH(-9, -5, 18, 10), paint(CONFETTI[i % len(CONFETTI)], alpha=fade))
        c.restore()


def poof(c, cx, cy, age, life=0.45):
    if 0 <= age <= life:
        k = age / life
        c.drawCircle(cx, cy, 60 + 220 * ease_in_out(k), paint(rgb(255, 255, 255), stroke=24 * (1 - k), alpha=1 - k))


def iris(c, cx, cy, k):
    """Klasik cizgi film kapanisi: k=0 acik, k=1 tamamen kapali."""
    if k <= 0:
        return
    r = (1 - ease_in_out(k)) * math.hypot(W, H)
    p = skia.Path()
    p.addRect(skia.Rect.MakeWH(W, H))
    p.addCircle(cx, cy, max(r, 0.1))
    p.setFillType(skia.PathFillType.kEvenOdd)
    c.drawPath(p, paint(rgb(20, 20, 30)))


# ---------------- yazi kutulari ----------------
def _fit(words, size, max_w=W - 220):
    """Satir ekrana sigmazsa yazi boyutunu kucult."""
    f = font(size)
    tw = sum(f.measureText(w + " ") for w in words) - f.measureText(" ")
    if tw > max_w:
        f = font(size * max_w / tw)
    return f


def caption(c, text, key=None, key_color=rgb(235, 70, 70), y=985):
    """Alt yazi: konturlu beyaz yuvarlak kutu; anahtar kelime renkli."""
    words = text.split()
    f = _fit(words, 62)
    widths = [f.measureText(w + " ") for w in words]
    tw = sum(widths) - f.measureText(" ")
    x0 = (W - tw) / 2
    box = skia.Rect.MakeLTRB(x0 - 44, y - 64, x0 + tw + 44, y + 28)
    c.drawRRect(skia.RRect.MakeRectXY(box, 46, 46), paint(INK, stroke=10))
    c.drawRRect(skia.RRect.MakeRectXY(box, 46, 46), paint(rgb(255, 255, 255, 245)))
    x = x0
    for w, wd in zip(words, widths):
        bare = w.strip(".,!?").lower()
        col = key_color if key and bare == key else rgb(70, 55, 80)
        c.drawString(w, x, y, f, paint(col))
        x += wd


def karaoke(c, lines, timings, t_local, y0=900):
    """Sarki sozleri: soylenen kelime turuncu ve buyur. timings: [(satir, kelime, bas_sn)]."""
    if not timings:
        return
    cur = 0
    for li, wi, st in timings:
        if st <= t_local:
            cur = li
    words = lines[cur].split()
    f = _fit(words, 76)
    starts = {wi: st for li, wi, st in timings if li == cur}
    widths = [f.measureText(w + " ") for w in words]
    tw = sum(widths) - f.measureText(" ")
    x = (W - tw) / 2
    box = skia.Rect.MakeLTRB(x - 50, y0 - 82, x + tw + 50, y0 + 34)
    c.drawRRect(skia.RRect.MakeRectXY(box, 54, 54), paint(INK, stroke=10))
    c.drawRRect(skia.RRect.MakeRectXY(box, 54, 54), paint(rgb(255, 255, 255, 245)))
    for i, (w, wd) in enumerate(zip(words, widths)):
        st = starts.get(i, 1e9)
        sung = st <= t_local
        pop = ease_out_back(clamp01((t_local - st) / 0.25)) if sung else 0
        k = 1 + 0.18 * pop * (1 - clamp01((t_local - st - 0.25) / 0.3))
        c.save()
        c.translate(x + (wd - f.measureText(" ")) / 2, y0)
        c.scale(k, k)
        c.drawString(w, -(wd - f.measureText(" ")) / 2, 0, f,
                     paint(rgb(255, 130, 40) if sung else rgb(120, 110, 130)))
        c.restore()
        x += wd


# ---------------- kare -> bayt ----------------
def new_surface():
    return skia.Surface(W, H)


def frame_bytes(surface):
    """RGBA baytlari (ffmpeg -pix_fmt rgba)."""
    img = surface.makeImageSnapshot()
    arr = img.toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    return np.ascontiguousarray(arr).tobytes()
