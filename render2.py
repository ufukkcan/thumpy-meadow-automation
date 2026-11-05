"""
Yeni cizim motoru (K-19, prototip): Skia (kenar yumusatma, gradyan, golge, bulaniklik).

- Nesneler: Fluent Color SVG -> resvg -> PNG -> Skia goruntusu (assets.py), bir kez rasterlestirilir.
- Dino ve arka plan bizim (maskot asla emoji olmaz). Dino'nun formu eski Dino ile ayni (taninirlik),
  sadece isik/golge/hareket eklendi.
- Tum koordinatlar 1920x1080; kamera yakinlasmasi canvas donusumuyle.
"""
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
class Sprites:
    """Ad -> Skia goruntusu (512 px, mipmap'li). Ciziminde merkez noktasi verilir."""

    def __init__(self, px=512):
        self.px = px
        self._img = {}

    def get(self, name):
        if name not in self._img:
            data = skia.Data.MakeWithCopy(assets.png(name, self.px))
            img = skia.Image.MakeFromEncoded(data)
            if img is None:
                raise RuntimeError(f"Goruntu cozulemedi: {name}")
            self._img[name] = img.withDefaultMipmaps()
        return self._img[name]

    def draw(self, c, name, cx, cy, size, rot=0.0, sx=1.0, sy=1.0, alpha=1.0, shadow_y=None):
        """size: piksel cinsinden genislik. shadow_y verilirse zemine yumusak golge."""
        if size <= 1 or alpha <= 0.01:
            return
        if shadow_y is not None:
            lift = max(0.0, shadow_y - (cy + size * 0.42))
            k = 1 / (1 + lift / 220)
            c.drawOval(oval(cx, shadow_y, size * 0.36 * k, size * 0.07 * k),
                       paint(rgb(40, 70, 40, 70 * alpha), blur=8))
        img = self.get(name)
        k = size / self.px
        c.save()
        c.translate(cx, cy)
        c.rotate(rot)
        c.scale(k * sx, k * sy)
        c.drawImage(img, -self.px / 2, -self.px / 2,
                    skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear),
                    paint(rgb(255, 255, 255), alpha=alpha))
        c.restore()


# ---------------- arka plan (bizim) ----------------
def _cloud(c, x, y, s, a=1.0):
    blobs = ((0, 0, 60), (55, -20, 70), (115, 0, 55), (60, 22, 58), (-45, 12, 42), (165, 16, 40))
    for dx, dy, r in blobs:     # alt golge
        c.drawCircle(x + dx * s, y + dy * s + 10 * s, r * s, paint(rgb(170, 200, 230, 90 * a), blur=6 * s))
    for dx, dy, r in blobs:
        c.drawCircle(x + dx * s, y + dy * s, r * s,
                     paint(shader=linear((0, y - 70 * s), (0, y + 70 * s),
                                         [rgb(255, 255, 255, 255 * a), rgb(232, 242, 252, 255 * a)])))


def _hill_path(base_y, amp, waves, phase, width, step=24):
    p = skia.Path()
    p.moveTo(0, H)
    x = 0.0
    while x <= width:
        y = base_y - amp * (0.55 + 0.45 * math.sin(x / width * waves * 2 * math.pi + phase))
        p.lineTo(x, y)
        x += step
    p.lineTo(width, H)
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
            c.drawPath(_hill_path(650, 110, 1.6, 2.1, w),
                       paint(shader=linear((0, 520), (0, 800), [rgb(140, 210, 140), rgb(100, 175, 110)])))
            for i in range(9):     # yuvarlak agaclar
                x, y = 120 + i * (w - 200) / 8 + rnd.uniform(-40, 40), 640 + rnd.uniform(-20, 20)
                c.drawRect(skia.Rect.MakeXYWH(x - 9, y, 18, 60), paint(rgb(140, 100, 70)))
                c.drawCircle(x, y - 10, 58, paint(shader=radial((x - 20, y - 35), 80,
                                                                [rgb(120, 200, 120), rgb(70, 150, 90)])))

        def near(c, w):
            c.drawPath(_hill_path(GROUND_Y - 40, 26, 1.1, 0.3, w),
                       paint(shader=linear((0, GROUND_Y - 70), (0, H),
                                           [rgb(150, 220, 110), rgb(105, 190, 90), rgb(85, 165, 80)],
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
        sx, sy = 1640, 170       # gunes: yumusak hale + disk
        c.drawCircle(sx, sy, 210, paint(shader=radial((sx, sy), 210,
                                                       [rgb(255, 245, 190, 150), rgb(255, 245, 190, 0)])))
        c.drawCircle(sx, sy, 80, paint(shader=radial((sx - 20, sy - 20), 90,
                                                      [rgb(255, 250, 200), rgb(255, 215, 90)])))
        for x0, y, s, v in self.clouds:
            x = (x0 + v * t) % (W + 600) - 300
            _cloud(c, x, y, s)
        for img, k in ((self.far, 0.15), (self.mid, 0.4), (self.near, 1.0)):
            c.drawImage(img, -self.PAD / 2 - cam_x * k, 0)


# ---------------- Dino (bizim maskot) ----------------
BODY_W, BODY_H = 300, 340


def dino(c, cx, cy, s=1.0, t=0.0, mouth=0.0, wave=0.0, excited=False, squash=0.0, look=0.0):
    """cx, cy: govde merkezi. mouth 0..1 (ses), wave 0..1 (sag el sallama),
    squash >0 basilma (zipla inis), <0 uzama."""
    bw, bh = BODY_W, BODY_H
    green_hi, green, green_dk = rgb(170, 238, 185), rgb(120, 205, 150), rgb(80, 165, 115)
    c.save()
    c.translate(cx, cy + bh * s * 0.5)              # ayak hizasindan esnet
    c.scale(s * (1 + 0.5 * squash), s * (1 - squash))
    c.translate(0, -bh * 0.5)

    # kuyruk
    tail = skia.Path()
    tail.moveTo(-bw * 0.30, bh * 0.05)
    tail.cubicTo(-bw * 0.75, bh * 0.20, -bw * 0.95, bh * 0.05, -bw * 1.02, -bh * 0.12 + 8 * math.sin(t * 3))
    tail.cubicTo(-bw * 0.85, bh * 0.25, -bw * 0.60, bh * 0.42, -bw * 0.20, bh * 0.38)
    tail.close()
    c.drawPath(tail, paint(shader=linear((-bw, 0), (-bw * 0.2, 0), [green_dk, green])))

    # sirt pullari (yuvarlatilmis)
    for px, py, pr in ((-0.22, -0.46, 0.13), (0.02, -0.56, 0.16), (0.26, -0.44, 0.13)):
        x, y, r = bw * px, bh * py, bw * pr
        sp = skia.Path()
        sp.moveTo(x - r * 0.75, y + bh * 0.10)
        sp.quadTo(x - r * 0.15, y - bh * 0.11, x, y - bh * 0.10)
        sp.quadTo(x + r * 0.15, y - bh * 0.11, x + r * 0.75, y + bh * 0.10)
        sp.close()
        c.drawPath(sp, paint(shader=linear((0, y - bh * 0.1), (0, y + bh * 0.1),
                                           [rgb(255, 215, 120), rgb(245, 165, 80)])))

    # ayaklar
    for side in (-1, 1):
        c.drawOval(oval(side * bw * 0.20, bh * 0.50, 48, 26),
                   paint(shader=linear((0, bh * 0.45), (0, bh * 0.58), [green, green_dk])))

    # govde: isik sol ustten
    c.drawOval(oval(0, 0, bw / 2, bh / 2),
               paint(shader=radial((-bw * 0.18, -bh * 0.25), bw * 0.85, [green_hi, green, green_dk],
                                   [0.0, 0.55, 1.0])))
    # karin
    c.drawOval(oval(0, bh * 0.19, bw * 0.30, bh * 0.27),
               paint(shader=linear((0, -bh * 0.05), (0, bh * 0.46),
                                   [rgb(245, 255, 232), rgb(215, 242, 200)])))

    # kollar (omuzdan donen kapsul). aci 0 = asagi sarkik; deger buyudukce kol disa/yukari kalkar
    for side in (-1, 1):
        if excited:
            lift = 150 + 12 * math.sin(t * 14 + side)
        elif side == 1 and wave > 0:
            lift = 20 + (125 + 25 * math.sin(t * 12)) * clamp01(wave)
        else:
            lift = 20 + 8 * math.sin(t * 3 + (0 if side > 0 else math.pi))
        c.save()
        c.translate(side * bw * 0.40, bh * 0.0)
        c.rotate(-side * lift)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-24, -8, 24, 92), 24, 24),
                    paint(shader=linear((-24, 0), (24, 0), [green, green_dk])))
        c.restore()

    # yanaklar
    for side in (-1, 1):
        c.drawOval(oval(side * bw * 0.33, bh * 0.02, 26, 18), paint(rgb(255, 160, 170, 170), blur=5))

    # gozler
    big = 1.12 if excited else 1.0
    blink = (t % 3.7) > 3.55
    for side in (-1, 1):
        ex, ey = side * bw * 0.17, -bh * 0.18
        if blink:
            arc = skia.Path()
            arc.moveTo(ex - 26, ey + 4)
            arc.quadTo(ex, ey + 22, ex + 26, ey + 4)
            c.drawPath(arc, paint(rgb(40, 45, 55), stroke=9))
            continue
        c.drawOval(oval(ex, ey, 29 * big, 34 * big),
                   paint(shader=linear((0, ey - 34), (0, ey + 34), [rgb(255, 255, 255), rgb(225, 232, 240)])))
        px = ex + look * 8
        c.drawOval(oval(px, ey + 3, 18 * big, 22 * big),
                   paint(shader=radial((px, ey + 10), 24, [rgb(70, 60, 90), rgb(25, 25, 35)])))
        c.drawCircle(px + 6, ey - 7, 7 * big, paint(rgb(255, 255, 255)))
        c.drawCircle(px - 6, ey + 12, 3.5 * big, paint(rgb(255, 255, 255, 220)))

    # agiz
    m = clamp01(mouth)
    my = bh * 0.03
    if m > 0.08 or excited:
        oh = 10 + 46 * max(m, 0.55 if excited else 0)
        ow = 40 + 14 * m
        mp = skia.Path()
        mp.moveTo(-ow, my - 4)
        mp.quadTo(0, my + 2 * oh, ow, my - 4)
        mp.quadTo(0, my + 6, -ow, my - 4)
        mp.close()
        c.drawPath(mp, paint(rgb(120, 45, 65)))
        c.save()
        c.clipPath(mp, skia.ClipOp.kIntersect, True)
        c.drawOval(oval(0, my + oh * 1.05, ow * 0.6, oh * 0.45), paint(rgb(250, 130, 150)))
        c.restore()
    else:
        sm = skia.Path()
        sm.moveTo(-40, my)
        sm.quadTo(0, my + 34, 40, my)
        c.drawPath(sm, paint(rgb(60, 60, 70), stroke=8))
    c.restore()


def dino_shadow(c, cx, ground_y, s=1.0, lift=0.0):
    k = 1 / (1 + lift / 260)
    c.drawOval(oval(cx, ground_y, 150 * s * k, 26 * s * k), paint(rgb(40, 70, 40, 80), blur=10))


# ---------------- efektler ----------------
def _star4(cx, cy, r):
    p = skia.Path()
    p.moveTo(cx, cy - r)
    for a, b in ((cx + r * 0.22, cy - r * 0.22), (cx + r, cy), (cx + r * 0.22, cy + r * 0.22), (cx, cy + r),
                 (cx - r * 0.22, cy + r * 0.22), (cx - r, cy), (cx - r * 0.22, cy - r * 0.22), (cx, cy - r)):
        p.lineTo(a, b)
    p.close()
    return p


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
        col = rgb(255, 230, 120) if i % 2 else rgb(255, 255, 255)
        c.drawPath(_star4(x, y, r * 1.6), paint(rgb(255, 240, 160, 120 * fade), blur=8))
        c.drawPath(_star4(x, y, r), paint(col, alpha=fade))


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
def caption(c, text, key=None, key_color=rgb(235, 70, 70), y=985):
    """Alt yazi: beyaz yuvarlak kutu; anahtar kelime renkli."""
    f = font(62)
    words = text.split()
    widths = [f.measureText(w + " ") for w in words]
    tw = sum(widths) - f.measureText(" ")
    x0 = (W - tw) / 2
    box = skia.Rect.MakeLTRB(x0 - 44, y - 64, x0 + tw + 44, y + 28)
    c.drawRRect(skia.RRect.MakeRectXY(box.makeOffset(0, 8), 46, 46), paint(rgb(30, 60, 30, 70), blur=12))
    c.drawRRect(skia.RRect.MakeRectXY(box, 46, 46), paint(rgb(255, 255, 255, 240)))
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
    f = font(76)
    words = lines[cur].split()
    starts = {wi: st for li, wi, st in timings if li == cur}
    widths = [f.measureText(w + " ") for w in words]
    tw = sum(widths) - f.measureText(" ")
    x = (W - tw) / 2
    box = skia.Rect.MakeLTRB(x - 50, y0 - 82, x + tw + 50, y0 + 34)
    c.drawRRect(skia.RRect.MakeRectXY(box.makeOffset(0, 8), 54, 54), paint(rgb(30, 60, 30, 70), blur=12))
    c.drawRRect(skia.RRect.MakeRectXY(box, 54, 54), paint(rgb(255, 255, 255, 240)))
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
