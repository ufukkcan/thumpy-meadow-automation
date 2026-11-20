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


def _silhouette_png(data):
    """Tum gorunur pikseller koyu renk, alfa korunur."""
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    sil = Image.new("RGBA", im.size, (70, 60, 95, 255))
    sil.putalpha(im.getchannel("A"))
    buf = io.BytesIO()
    sil.save(buf, "PNG")
    return buf.getvalue()


class Sprites:
    """Ad -> Skia goruntusu (512 px, mipmap'li). Ciziminde merkez noktasi verilir.
    outline > 0: 512 px olcekte kontur kalinligi (cizgi film stili)."""

    def __init__(self, px=512, outline=0):
        self.px = px
        self.outline = outline
        self._img = {}

    def get(self, name, sil=False):
        key = (name, sil)
        if key not in self._img:
            data, pad = assets.png(name, self.px), 0
            if sil:                                   # siluet: "sonraki bolumde kim gelecek?" merak ogesi
                data = _silhouette_png(data)
            if self.outline:
                data, pad = _outline_png(data, self.outline)
            img = skia.Image.MakeFromEncoded(skia.Data.MakeWithCopy(data))
            if img is None:
                raise RuntimeError(f"Goruntu cozulemedi: {name}")
            self._img[key] = (img.withDefaultMipmaps(), pad)
        return self._img[key]

    def draw(self, c, name, cx, cy, size, rot=0.0, sx=1.0, sy=1.0, alpha=1.0, shadow_y=None, sil=False):
        """size: piksel cinsinden genislik (kontur haric). shadow_y verilirse zemine yumusak golge."""
        if size <= 1 or alpha <= 0.01:
            return
        if shadow_y is not None:
            lift = max(0.0, shadow_y - (cy + size * 0.42))
            k = 1 / (1 + lift / 220)
            c.drawOval(oval(cx, shadow_y, size * 0.36 * k, size * 0.07 * k),
                       paint(rgb(40, 70, 40, 70 * alpha), blur=8))
        img, pad = self.get(name, sil)
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
    """waves tam sayi -> sol ve sag kenar ayni yukseklik (katman yan yana dosenebilir)."""
    p = skia.Path()
    p.moveTo(0, H + 40)          # alt kenar kadraj disinda: kontur gorunmesin
    yf = lambda x: base_y - amp * (0.55 + 0.45 * math.sin(x / width * waves * 2 * math.pi + phase))
    x = 0.0
    while x < width:
        p.lineTo(x, yf(x))
        x += step
    p.lineTo(width, yf(width))
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


def _round_tree(c, x, y, w):
    """Orta katmanin yuvarlak agaci; x kenara tasarsa karsi kenarda da cizilir (katman dosenebilir)."""
    for xx in (x - w, x, x + w):
        trunk = skia.Path()
        trunk.addRect(skia.Rect.MakeXYWH(xx - 9, y, 18, 60))
        inked(c, [trunk], paint(rgb(150, 105, 70)), w=8)
        inked(c, [oval_path(xx, y - 10, 58, 58)],
              paint(shader=radial((xx - 20, y - 35), 80, [rgb(130, 215, 120), rgb(75, 160, 90)])), w=8)


def _near_ground(c, w, rnd, grad, cols, n=70, tuft=rgb(80, 160, 75)):
    """On zemin: tepe + cicek/cimen tutamlari (karakterler GROUND_Y'de bunun ustunde durur)."""
    hill = _hill_path(GROUND_Y - 40, 26, 1, 0.3, w)
    c.drawPath(hill, paint(INK, stroke=LINE))
    c.drawPath(hill, paint(shader=linear((0, GROUND_Y - 70), (0, H), grad, [0.0, 0.45, 1.0])))
    for _ in range(n):
        x0, y = rnd.uniform(0, w), rnd.uniform(GROUND_Y + 10, H - 10)
        flower, s_, col = rnd.random() < 0.5, rnd.uniform(0.7, 1.2), rnd.choice(cols)
        for x in (x0 - w, x0, x0 + w):
            if flower:
                _flower(c, x, y, s_, col)
            else:            # cimen tutami
                for k in (-1, 0, 1):
                    c.drawLine(x, y, x + k * 8, y - 22, paint(tuft, stroke=4))


# Mekan kitleri (S1, todo 7g): her biri (uzak, orta, on) katman cizicileri dondurur.
# Konum notu: mekana varista kamera sifirlanir (show.Places) -> orta katmanda x = ekran_x + PAD/2.
def _kit_meadow(rnd):
    def far(c, w):
        c.drawPath(_hill_path(560, 120, 2, 0.6, w),
                   paint(shader=linear((0, 420), (0, 760), [rgb(150, 205, 225), rgb(125, 185, 205)])))

    def mid(c, w):
        hill = _hill_path(650, 110, 2, 2.1, w)
        c.drawPath(hill, paint(rgb(60, 120, 80), stroke=8))
        c.drawPath(hill, paint(shader=linear((0, 520), (0, 800), [rgb(140, 215, 140), rgb(100, 180, 110)])))
        for i in range(9):
            _round_tree(c, 120 + i * (w - 200) / 8 + rnd.uniform(-40, 40), 640 + rnd.uniform(-20, 20), w)

    def near(c, w):
        _near_ground(c, w, rnd, [rgb(155, 225, 110), rgb(110, 195, 90), rgb(88, 170, 80)],
                     [rgb(255, 120, 150), rgb(255, 255, 255), rgb(170, 140, 255), rgb(255, 170, 90)])
    return far, mid, near


def _barn(c, x, y):
    """Kirmizi ahir + silo. x: ahirin ortasi, y: taban."""
    body = skia.Path()
    body.addRect(skia.Rect.MakeLTRB(x - 130, y - 170, x + 130, y + 10))
    roof = skia.Path()
    roof.addPoly([(x - 152, y - 165), (x - 118, y - 238), (x, y - 285), (x + 118, y - 238), (x + 152, y - 165)], True)
    sx = x + 215                                   # silo
    silo = skia.Path()
    silo.addRect(skia.Rect.MakeLTRB(sx - 42, y - 235, sx + 42, y + 10))
    dome = skia.Path()
    dome.addOval(skia.Rect.MakeLTRB(sx - 42, y - 280, sx + 42, y - 190))
    inked(c, [dome], paint(shader=linear((sx - 42, 0), (sx + 42, 0), [rgb(215, 225, 235), rgb(150, 165, 185)])), w=8)
    inked(c, [silo], paint(shader=linear((sx - 42, 0), (sx + 42, 0), [rgb(200, 210, 225), rgb(140, 155, 175)])), w=8)
    for k in range(4):
        c.drawLine(sx - 40, y - 190 + k * 50, sx + 40, y - 190 + k * 50, paint(rgb(120, 135, 160), stroke=4))
    inked(c, [body], paint(shader=linear((x - 130, 0), (x + 130, 0), [rgb(225, 80, 65), rgb(180, 50, 45)])), w=8)
    inked(c, [roof], paint(shader=linear((0, y - 285), (0, y - 165), [rgb(140, 85, 70), rgb(105, 60, 55)])), w=8)
    white = paint(rgb(255, 250, 240), stroke=9)
    c.drawRect(skia.Rect.MakeLTRB(x - 58, y - 118, x + 58, y + 4), paint(rgb(150, 40, 40)))
    c.drawRect(skia.Rect.MakeLTRB(x - 58, y - 118, x + 58, y + 4), white)
    c.drawLine(x - 58, y - 118, x + 58, y + 4, white)
    c.drawLine(x + 58, y - 118, x - 58, y + 4, white)
    c.drawRect(skia.Rect.MakeLTRB(x - 30, y - 232, x + 30, y - 182), paint(rgb(70, 40, 35)))
    c.drawRect(skia.Rect.MakeLTRB(x - 30, y - 232, x + 30, y - 182), white)


def _fence(c, w, y, col=rgb(250, 245, 230)):
    """Dosenebilir cit (direk araligi genislige tam bolunur)."""
    n = int(w // 70)
    step = w / n
    rail = paint(col, stroke=10)
    for yy in (y - 42, y - 18):
        c.drawLine(0, yy, w, yy, paint(INK, stroke=16))
        c.drawLine(0, yy, w, yy, rail)
    for k in range(n):
        p = skia.Path()
        p.addRoundRect(skia.Rect.MakeXYWH(k * step - 7, y - 62, 14, 70), 5, 5)
        inked(c, [p], paint(col), w=7)


def _kit_farm(rnd):
    def far(c, w):
        c.drawPath(_hill_path(575, 105, 2, 1.7, w),
                   paint(shader=linear((0, 440), (0, 760), [rgb(170, 210, 215), rgb(145, 190, 195)])))

    def mid(c, w):
        hill = _hill_path(665, 85, 2, 0.9, w)
        c.drawPath(hill, paint(rgb(150, 130, 50), stroke=8))
        c.drawPath(hill, paint(shader=linear((0, 560), (0, 800), [rgb(235, 215, 120), rgb(205, 180, 85)])))
        for k in range(14):                       # ekin sirasi cizgileri
            x0 = k * w / 14 + rnd.uniform(-20, 20)
            c.drawLine(x0, 700, x0 + 60, 620, paint(rgb(215, 190, 95), stroke=6))
        _round_tree(c, 1650, 655, w)
        _round_tree(c, 2150, 640, w)
        _round_tree(c, 2450, 660, w)
        _barn(c, 330 + 350, 725)
        _fence(c, w, 752)

    def near(c, w):
        _near_ground(c, w, rnd, [rgb(170, 225, 105), rgb(130, 200, 85), rgb(105, 175, 75)],
                     [rgb(255, 215, 70), rgb(255, 255, 255), rgb(255, 160, 60)], n=60, tuft=rgb(200, 170, 70))
    return far, mid, near


def _lily(c, x, y, s=1.0):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(x - 38 * s, y - 13 * s, x + 38 * s, y + 13 * s))
    notch = skia.Path()
    notch.addPoly([(x, y), (x + 40 * s, y - 16 * s), (x + 40 * s, y + 2 * s)], True)
    p = skia.Op(p, notch, skia.PathOp.kDifference_PathOp) or p
    inked(c, [p], paint(rgb(95, 185, 90)), w=6)


def _kit_pond(rnd):
    def far(c, w):
        c.drawPath(_hill_path(555, 125, 2, 2.6, w),
                   paint(shader=linear((0, 420), (0, 760), [rgb(140, 205, 215), rgb(115, 180, 195)])))

    def mid(c, w):
        hill = _hill_path(650, 100, 2, 0.4, w)
        c.drawPath(hill, paint(rgb(60, 120, 80), stroke=8))
        c.drawPath(hill, paint(shader=linear((0, 520), (0, 800), [rgb(150, 220, 140), rgb(105, 185, 115)])))
        for x in (120, 520, 2200, 2480):
            _round_tree(c, x + rnd.uniform(-30, 30), 625 + rnd.uniform(-15, 15), w)
        cx, cy, rx, ry = 1250 + 350, 705, 620, 74  # gol (varista ekranin ortasi-sagi)
        water = oval_path(cx, cy, rx, ry)
        inked(c, [water], paint(shader=linear((0, cy - ry), (0, cy + ry), [rgb(150, 220, 250), rgb(75, 160, 225)])))
        for dx, dy, L in ((-300, -18, 120), (60, -26, 160), (330, -8, 90), (-80, 12, 70)):
            c.drawLine(cx + dx, cy + dy, cx + dx + L, cy + dy, paint(rgb(235, 250, 255, 200), stroke=6))
        for dx, dy, s in ((-420, 10, 0.9), (-180, 20, 1.1), (200, 14, 1.0), (430, 6, 0.8)):
            _lily(c, cx + dx, cy + dy, s)
        c.drawCircle(cx - 170, cy + 12, 11, paint(rgb(255, 150, 190)))
        for side in (-1, 1):                       # sazliklar (golun iki ucu)
            for k in range(6):
                bx = cx + side * (rx - 40 - k * 26)
                top = cy - 120 - 30 * math.sin(k * 1.7)
                c.drawLine(bx, cy + 30, bx + side * 6, top, paint(rgb(70, 130, 60), stroke=6))
                inked(c, [oval_path(bx + side * 6, top + 22, 9, 24)], paint(rgb(140, 90, 55)), w=5)

    def near(c, w):
        _near_ground(c, w, rnd, [rgb(150, 225, 120), rgb(105, 195, 100), rgb(85, 170, 85)],
                     [rgb(120, 180, 255), rgb(255, 255, 255), rgb(200, 160, 255)])
        for _ in range(18):                        # cakil taslari
            x0, y = rnd.uniform(0, w), rnd.uniform(GROUND_Y + 30, H - 20)
            for x in (x0 - w, x0, x0 + w):
                inked(c, [oval_path(x, y, 16, 10)], paint(rgb(185, 185, 195)), w=5)
    return far, mid, near


def _pine(c, x, y, s=1.0, snow=False, w=None):
    """Cam agaci: govde + 3 kat ucgen; snow=True: karli uclar. x, y: taban. w verilirse dosenir."""
    for xx in ((x - w, x, x + w) if w else (x,)):
        trunk = skia.Path()
        trunk.addRect(skia.Rect.MakeXYWH(xx - 10 * s, y - 40 * s, 20 * s, 44 * s))
        inked(c, [trunk], paint(rgb(140, 95, 65)), w=7)
        for k, (hw, top, bot) in enumerate(((95, 175, 30), (75, 245, 120), (52, 300, 190))):
            p = skia.Path()
            p.addPoly([(xx - hw * s, y - bot * s), (xx, y - top * s - 40 * s), (xx + hw * s, y - bot * s)], True)
            inked(c, [p], paint(shader=linear((xx - hw * s, 0), (xx + hw * s, 0),
                                               [rgb(80, 165, 110), rgb(45, 125, 85)])), w=7)
            if snow:
                cap = skia.Path()
                cap.moveTo(xx - hw * s * 0.45, y - (top + 40) * s + (top + 40 - bot) * s * 0.45)
                cap.lineTo(xx, y - (top + 40) * s)
                cap.lineTo(xx + hw * s * 0.45, y - (top + 40) * s + (top + 40 - bot) * s * 0.45)
                cap.quadTo(xx, y - (top + 40) * s + (top + 40 - bot) * s * 0.3, xx - hw * s * 0.45,
                           y - (top + 40) * s + (top + 40 - bot) * s * 0.45)
                c.drawPath(cap, paint(rgb(250, 252, 255)))


def _cottage(c, x, y, s=1.0, snow=False):
    """Kucuk ev: sicak isikli pencere, kapi, baca. x: orta, y: taban."""
    body = skia.Path()
    body.addRect(skia.Rect.MakeLTRB(x - 120 * s, y - 150 * s, x + 120 * s, y + 6))
    roof = skia.Path()
    roof.addPoly([(x - 150 * s, y - 145 * s), (x, y - 265 * s), (x + 150 * s, y - 145 * s)], True)
    chim = skia.Path()
    chim.addRect(skia.Rect.MakeLTRB(x + 55 * s, y - 250 * s, x + 90 * s, y - 185 * s))
    inked(c, [chim], paint(rgb(170, 90, 75)), w=7)
    inked(c, [body], paint(shader=linear((x - 120 * s, 0), (x + 120 * s, 0), [rgb(250, 215, 160), rgb(225, 180, 125)])), w=8)
    inked(c, [roof], paint(rgb(190, 75, 70) if not snow else rgb(245, 248, 255)), w=8)
    for wx in (-65, 65):
        win = skia.Rect.MakeLTRB(x + (wx - 32) * s, y - 115 * s, x + (wx + 32) * s, y - 55 * s)
        c.drawRect(win, paint(rgb(255, 210, 90)))
        c.drawRect(win, paint(INK, stroke=7))
        c.drawLine(x + wx * s, y - 115 * s, x + wx * s, y - 55 * s, paint(INK, stroke=5))
    door = skia.Path()
    door.addRoundRect(skia.Rect.MakeLTRB(x - 26 * s, y - 95 * s, x + 26 * s, y + 4), 18 * s, 18 * s)
    inked(c, [door], paint(rgb(150, 95, 70)), w=7)


def _kit_snow(rnd):
    def far(c, w):
        for k in range(7):                          # karli daglar
            mx = k * w / 7 + rnd.uniform(-60, 60)
            for xx in (mx - w, mx, mx + w):
                p = skia.Path()
                p.addPoly([(xx - 260, 640), (xx, 400 + rnd.uniform(-40, 40) * 0), (xx + 260, 640)], True)
                c.drawPath(p, paint(shader=linear((0, 400), (0, 640), [rgb(235, 242, 252), rgb(170, 195, 225)])))
                c.drawPath(p, paint(rgb(150, 175, 210), stroke=5))

    def mid(c, w):
        hill = _hill_path(660, 90, 2, 1.1, w)
        c.drawPath(hill, paint(rgb(170, 190, 220), stroke=8))
        c.drawPath(hill, paint(shader=linear((0, 560), (0, 800), [rgb(255, 255, 255), rgb(222, 232, 248)])))
        _cottage(c, 360 + 350, 705, 0.95, snow=True)
        for x in (1150, 1600, 1900, 2250, 2500):
            _pine(c, x + rnd.uniform(-30, 30), 700 + rnd.uniform(-10, 10), 0.75, snow=True, w=w)

    def near(c, w):
        hill = _hill_path(GROUND_Y - 40, 26, 1, 0.3, w)
        c.drawPath(hill, paint(rgb(150, 170, 205), stroke=LINE))
        c.drawPath(hill, paint(shader=linear((0, GROUND_Y - 70), (0, H),
                                             [rgb(255, 255, 255), rgb(236, 242, 252), rgb(214, 226, 245)],
                                             [0.0, 0.45, 1.0])))
        for _ in range(26):
            x0, y = rnd.uniform(0, w), rnd.uniform(GROUND_Y + 30, H - 20)
            for x in (x0 - w, x0, x0 + w):
                c.drawOval(oval(x, y, 38, 9), paint(rgb(200, 215, 240, 160)))
    return far, mid, near


def _kit_forest(rnd):
    def far(c, w):
        c.drawPath(_hill_path(560, 130, 3, 0.2, w),
                   paint(shader=linear((0, 400), (0, 760), [rgb(120, 175, 170), rgb(95, 150, 145)])))

    def mid(c, w):
        hill = _hill_path(660, 70, 2, 1.6, w)
        c.drawPath(hill, paint(rgb(50, 110, 70), stroke=8))
        c.drawPath(hill, paint(shader=linear((0, 560), (0, 800), [rgb(110, 190, 120), rgb(80, 160, 95)])))
        for k in range(16):
            x = 40 + k * (w - 80) / 15 + rnd.uniform(-35, 35)
            if k % 3 == 1:
                _round_tree(c, x, 640 + rnd.uniform(-15, 15), w)
            else:
                _pine(c, x, 715 + rnd.uniform(-10, 10), 0.7 + rnd.uniform(-0.08, 0.12), w=w)

    def near(c, w):
        _near_ground(c, w, rnd, [rgb(130, 205, 105), rgb(95, 175, 85), rgb(75, 150, 75)],
                     [rgb(255, 255, 255), rgb(255, 220, 90)], n=40, tuft=rgb(60, 130, 60))
        for _ in range(9):                         # mantarlar
            x0, y = rnd.uniform(0, w), rnd.uniform(GROUND_Y + 40, H - 40)
            for x in (x0 - w, x0, x0 + w):
                stem = skia.Path()
                stem.addRoundRect(skia.Rect.MakeXYWH(x - 9, y - 26, 18, 30), 7, 7)
                inked(c, [stem], paint(rgb(250, 240, 225)), w=5)
                cap = skia.Path()
                cap.addArc(skia.Rect.MakeXYWH(x - 26, y - 50, 52, 46), 180, 180)
                cap.close()
                inked(c, [cap], paint(rgb(230, 70, 70)), w=5)
                c.drawCircle(x - 8, y - 36, 4, paint(rgb(255, 255, 255)))
                c.drawCircle(x + 9, y - 32, 3, paint(rgb(255, 255, 255)))
    return far, mid, near


def _kit_home(rnd):
    """Ev ici (oturma odasi): duvar + pencere + cerceve + raf; ahsap zemin + hali. Gokyuzu cizilmez."""
    def far(c, w):
        c.drawRect(skia.Rect.MakeWH(w, H), paint(shader=linear((0, 0), (0, 760),
                                                               [rgb(255, 236, 205), rgb(250, 220, 180)])))
        for k in range(int(w // 120) + 1):         # duvar kagidi seritleri
            c.drawRect(skia.Rect.MakeXYWH(k * 120 + 40, 0, 26, 700), paint(rgb(255, 228, 190)))
        c.drawRect(skia.Rect.MakeXYWH(0, 640, w, 30), paint(rgb(235, 190, 150)))      # supurgelik

    def mid(c, w):
        wx, wy, ww, wh = 1250 + 350, 150, 360, 300  # pencere (varista ekranin sag-ortasi)
        c.drawRect(skia.Rect.MakeXYWH(wx - ww / 2, wy, ww, wh),
                   paint(shader=linear((0, wy), (0, wy + wh), [rgb(110, 185, 245), rgb(205, 236, 255)])))
        c.drawCircle(wx + 90, wy + 80, 34, paint(rgb(255, 225, 110)))
        _cloud(c, wx - 90, wy + 120, 0.6)
        frame = skia.Rect.MakeXYWH(wx - ww / 2, wy, ww, wh)
        c.drawRect(frame, paint(rgb(255, 255, 255), stroke=22))
        c.drawRect(frame, paint(INK, stroke=6))
        c.drawLine(wx, wy, wx, wy + wh, paint(rgb(255, 255, 255), stroke=14))
        c.drawLine(wx - ww / 2, wy + wh / 2, wx + ww / 2, wy + wh / 2, paint(rgb(255, 255, 255), stroke=14))
        for side in (-1, 1):                       # perdeler
            cur = skia.Path()
            cx0 = wx + side * (ww / 2 + 20)
            cur.moveTo(cx0 - 45, wy - 30)
            cur.lineTo(cx0 + 45, wy - 30)
            cur.quadTo(cx0 + 20 * side, wy + wh * 0.6, cx0 + 50 * side, wy + wh + 40)
            cur.lineTo(cx0 - 50 * side, wy + wh + 40)
            cur.close()
            inked(c, [cur], paint(rgb(240, 120, 130)), w=7)
        px, py = 330 + 350, 210                    # resim cercevesi
        pic = skia.Rect.MakeXYWH(px - 110, py, 220, 160)
        c.drawRect(pic, paint(rgb(170, 220, 160)))
        c.drawCircle(px + 40, py + 50, 22, paint(rgb(255, 210, 80)))
        c.drawPath(_hill_path(py + 160, 50, 1, 0.5, 220), paint(rgb(120, 190, 110)))  # (kucuk tepe, sol ust kose)
        c.drawRect(pic, paint(rgb(190, 130, 80), stroke=16))
        c.drawRect(pic, paint(INK, stroke=5))
        shelf = skia.Path()                        # raf
        shelf.addRect(skia.Rect.MakeXYWH(820 + 350, 330, 230, 18))
        inked(c, [shelf], paint(rgb(190, 130, 80)), w=6)

    def near(c, w):
        floor = skia.Path()
        floor.addRect(skia.Rect.MakeLTRB(0, GROUND_Y - 60, w, H + 40))
        c.drawPath(floor, paint(shader=linear((0, GROUND_Y - 60), (0, H), [rgb(215, 160, 110), rgb(185, 125, 85)])))
        c.drawLine(0, GROUND_Y - 60, w, GROUND_Y - 60, paint(INK, stroke=LINE))
        for k in range(int(w // 160) + 1):
            c.drawLine(k * 160, GROUND_Y - 53, k * 160 - 120, H, paint(rgb(170, 115, 78), stroke=5))
        c.drawOval(oval(960 + 350, GROUND_Y + 70, 620, 95), paint(rgb(120, 170, 230)))
        c.drawOval(oval(960 + 350, GROUND_Y + 70, 620, 95), paint(INK, stroke=8))
        c.drawOval(oval(960 + 350, GROUND_Y + 70, 520, 70), paint(rgb(160, 200, 245), stroke=10))
    return far, mid, near


PLACES = {"meadow": _kit_meadow, "farm": _kit_farm, "pond": _kit_pond, "snow": _kit_snow,
          "forest": _kit_forest, "home": _kit_home, "night": _kit_meadow}
SKY = {"snow": "winter", "home": None, "night": "night"}     # digerleri "day"


def _sun(c, t, sx=1640, sy=170, pale=False):
    """Gunes: yumusak hale + konturlu disk + gulen yuz."""
    c.drawCircle(sx, sy, 210, paint(shader=radial((sx, sy), 210,
                                                   [rgb(255, 245, 190, 110 if pale else 150), rgb(255, 245, 190, 0)])))
    inked(c, [oval_path(sx, sy, 80, 80)],
          paint(shader=radial((sx - 20, sy - 20), 90, [rgb(255, 250, 215), rgb(255, 220, 120) if pale else
                                                       rgb(255, 205, 80)])), w=10)
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


def _moon(c, t, sx=1600, sy=180):
    c.drawCircle(sx, sy, 190, paint(shader=radial((sx, sy), 190, [rgb(255, 250, 210, 90), rgb(255, 250, 210, 0)])))
    m = skia.Op(oval_path(sx, sy, 85, 85), oval_path(sx + 48, sy - 25, 75, 75), skia.PathOp.kDifference_PathOp)
    inked(c, [m], paint(shader=radial((sx - 30, sy), 100, [rgb(255, 252, 220), rgb(255, 230, 140)])), w=10)
    blink = (t % 6.1) > 5.95
    ex, ey = sx - 48, sy - 5
    if blink:
        c.drawLine(ex - 8, ey, ex + 8, ey, paint(INK, stroke=5))
    else:
        c.drawLine(ex - 9, ey, ex + 9, ey, paint(INK, stroke=5))          # uykulu kapali goz
    smile = skia.Path()
    smile.moveTo(sx - 62, sy + 30)
    smile.quadTo(sx - 50, sy + 42, sx - 36, sy + 30)
    c.drawPath(smile, paint(INK, stroke=5))


def snowfall(c, t, n=90, seed=7, w=W, h=H):
    """Yagan kar (ekran koordinati): yavas dusus + sallanma, 3 buyukluk (paralaks hissi)."""
    rnd = random.Random(seed)
    for _ in range(n):
        x0, y0, sp, sz, ph = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(40, 110), rnd.choice((4, 6, 9)), rnd.uniform(0, 6)
        y = (y0 + sp * t) % (h + 40) - 20
        x = (x0 + 30 * math.sin(t * 0.9 + ph)) % w
        c.drawCircle(x, y, sz + 2.5, paint(rgb(140, 165, 205, 150)))      # acik gokyuzunde de secilsin
        c.drawCircle(x, y, sz, paint(rgb(255, 255, 255, 240)))


def rainfall(c, t, n=110, seed=8, w=W, h=H):
    rnd = random.Random(seed)
    for _ in range(n):
        x0, y0, sp = rnd.uniform(0, w + 200), rnd.uniform(0, h), rnd.uniform(900, 1300)
        y = (y0 + sp * t) % (h + 80) - 40
        x = (x0 - 0.25 * sp * t) % (w + 200) - 100
        c.drawLine(x, y, x - 9, y + 34, paint(rgb(200, 225, 255, 200), stroke=4))


class Meadow:
    """Paralaks sahne: gokyuzu sabit; uzak/orta tepe ve on zemin farkli hizda kayar.
    kind: mekan kiti (PLACES). "meadow" eski cayirla birebir ayni (rastgele sayi sirasi korunur)."""
    PAD = 700

    def __init__(self, seed=3, kind="meadow"):
        rnd = random.Random(seed)
        wd = W + self.PAD
        far, mid, near = PLACES[kind](rnd)
        self.far, self.mid, self.near = _layer(wd, far), _layer(wd, mid), _layer(wd, near)
        self.clouds = [(rnd.uniform(0, W + 400), rnd.uniform(90, 330), rnd.uniform(0.7, 1.15),
                        rnd.uniform(8, 20)) for _ in range(6)]
        self.sky = SKY.get(kind, "day")
        if self.sky == "night":
            self.stars = [(rnd.uniform(0, W), rnd.uniform(20, 520), rnd.uniform(2, 5), rnd.uniform(0, 6))
                          for _ in range(70)]

    def draw(self, c, t, cam_x=0.0):
        if self.sky == "day":
            self._day(c, t)
        elif self.sky == "winter":
            c.drawRect(skia.Rect.MakeWH(W, H),
                       paint(shader=linear((0, 0), (0, 700), [rgb(150, 190, 230), rgb(225, 238, 250)])))
            _sun(c, t, pale=True)
            for x0, y, s, v in self.clouds:
                _cloud(c, (x0 + v * t) % (W + 600) - 300, y, s)
        elif self.sky == "night":
            c.drawRect(skia.Rect.MakeWH(W, H),
                       paint(shader=linear((0, 0), (0, 720), [rgb(30, 40, 95), rgb(85, 90, 165)])))
            for x, y, s, ph in self.stars:
                c.drawCircle(x, y, s * (0.75 + 0.25 * math.sin(t * 2 + ph)), paint(rgb(255, 250, 220)))
            _moon(c, t)
        for img, k in ((self.far, 0.15), (self.mid, 0.4), (self.near, 1.0)):
            wd = img.width()
            off = (-self.PAD / 2 - cam_x * k) % wd - wd        # yan yana dose: kamera ne kadar kayarsa kaysin
            while off < W + 800:
                c.drawImage(img, off, 0)
                off += wd
        if self.sky == "night":                                 # gece: zemine lacivert tul
            c.drawRect(skia.Rect.MakeWH(W, H), paint(rgb(25, 35, 100, 95)))

    def _day(self, c, t):
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
         expr="neutral", arms=None, lean=0.0, look_y=0.0, dizzy=0.0, sweat=0.0):
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

    # ter damlasi (saskinlik / telas)
    if sweat > 0:
        sx_, sy_ = bw * 0.44, -bh * 0.36 + 10 * math.sin(t * 5)
        drop = skia.Path()
        drop.moveTo(sx_, sy_ - 30)
        drop.quadTo(sx_ + 20, sy_, sx_, sy_ + 14)
        drop.quadTo(sx_ - 20, sy_, sx_, sy_ - 30)
        drop.close()
        c.drawPath(drop, paint(INK, stroke=7, alpha=sweat))
        c.drawPath(drop, paint(rgb(150, 210, 255), alpha=sweat))
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


def peek_eyes(c, x, y, t, k=1.0, look=0.0, hollow=rgb(35, 70, 40)):
    """Saklanma yerinden bakan gozler. x, y: gozlerin ortasi. k 0..1 gorunurluk.
    hollow: arkadaki karanlik bosluk rengi (cali: koyu yesil, bulut: acik mavi, agac kovugu: kahve)."""
    if k <= 0.01:
        return
    c.drawOval(oval(x, y, 74 * k, 36 * k), paint(hollow))
    blink = (t % 2.9) > 2.75
    for ex in (-26 * k, 26 * k):
        if blink:
            c.drawLine(x + ex - 14 * k, y, x + ex + 14 * k, y, paint(INK, stroke=6 * k))
            continue
        c.drawOval(oval(x + ex, y, 17 * k, 21 * k), paint(INK, stroke=5 * k))
        c.drawOval(oval(x + ex, y, 17 * k, 21 * k), paint(rgb(255, 255, 255)))
        c.drawCircle(x + ex + look * 6 * k, y + 3 * k, 9 * k, paint(rgb(30, 25, 40)))
        c.drawCircle(x + ex + (look * 6 + 3) * k, y - k, 3 * k, paint(rgb(255, 255, 255)))


def cloud(c, cx, cy, s=1.0, wiggle=0.0, t=0.0):
    """Saklanma bulutu (gokyuzundeki suruklenen bulutlardan ayri, sabit). cx, cy: orta nokta."""
    c.save()
    c.translate(cx, cy)
    c.rotate(wiggle * 5 * math.sin(t * 26))
    c.scale(1 + wiggle * 0.05 * math.sin(t * 31), 1)
    _cloud(c, -60 * s, 0, s)
    c.restore()


def big_tree(c, x, y, s=1.0, shake=0.0, t=0.0):
    """Saklanma agaci. x, y: govdenin zemindeki ortasi. Govde ~150*s genis, tepe ~y-560*s."""
    tw, th = 150 * s, 300 * s
    trunk = skia.Path()
    trunk.moveTo(x - tw * 0.5, y + 6)
    trunk.quadTo(x - tw * 0.42, y - th * 0.5, x - tw * 0.36, y - th)
    trunk.lineTo(x + tw * 0.36, y - th)
    trunk.quadTo(x + tw * 0.42, y - th * 0.5, x + tw * 0.5, y + 6)
    trunk.close()
    inked(c, [trunk], paint(shader=linear((x - tw / 2, 0), (x + tw / 2, 0), [rgb(170, 115, 70), rgb(125, 80, 50)])))
    for k in range(3):                     # kabuk cizgileri
        bx = x - tw * 0.2 + k * tw * 0.2
        c.drawLine(bx, y - th * (0.25 + 0.2 * k), bx + 6, y - th * (0.4 + 0.2 * k), paint(rgb(100, 65, 40), stroke=5))
    c.save()
    c.translate(x, y - th - 120 * s)
    c.rotate(shake * 3 * math.sin(t * 24))
    blobs = [(-170, 40, 130), (-90, -70, 150), (40, -110, 160), (160, -30, 140), (170, 70, 120), (0, 40, 170)]
    paths = [oval_path(dx * s, dy * s, r * s, r * s) for dx, dy, r in blobs]
    inked(c, paths, paint(shader=radial((-60 * s, -120 * s), 330 * s, [rgb(130, 215, 115), rgb(65, 150, 80)])))
    for dx, dy, r in blobs[:5]:
        arc = skia.Path()
        arc.moveTo((dx - r * 0.45) * s, (dy - r * 0.25) * s)
        arc.quadTo((dx - r * 0.2) * s, (dy - r * 0.6) * s, (dx + r * 0.15) * s, (dy - r * 0.55) * s)
        c.drawPath(arc, paint(rgb(190, 245, 160), stroke=6))
    c.restore()


def leaf(c, x, y, rot=0.0, s=1.0, alpha=1.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(s, s)
    p = skia.Path()
    p.moveTo(-22, 0)
    p.quadTo(0, -16, 22, 0)
    p.quadTo(0, 16, -22, 0)
    p.close()
    c.drawPath(p, paint(INK, stroke=6, alpha=alpha))
    c.drawPath(p, paint(rgb(120, 205, 95), alpha=alpha))
    c.drawLine(-16, 0, 16, 0, paint(rgb(70, 150, 70), stroke=3, alpha=alpha))
    c.restore()


def leaves(c, x, y, age, seed=0, n=7, life=1.6):
    """Sallanan cali/agactan dusen yapraklar."""
    if age < 0 or age > life:
        return
    rnd = random.Random(seed)
    fade = 1 - clamp01((age - life * 0.7) / (life * 0.3))
    for i in range(n):
        vx, vy = rnd.uniform(-160, 160), rnd.uniform(-260, -120)
        px = x + vx * age + 18 * math.sin(age * 6 + i)
        py = y + vy * age + 0.5 * 600 * age * age
        leaf(c, px, py, rot=rnd.uniform(0, 360) + age * 200, s=rnd.uniform(0.7, 1.1), alpha=fade)


def dust(c, x, y, age, seed=0, life=0.6, spread=1.0):
    """Inis/kosu toz bulutu: iki yana acilan yumusak puflar."""
    if age < 0 or age > life:
        return
    e = age / life
    rnd = random.Random(seed)
    for i in range(6):
        side = -1 if i % 2 else 1
        dx = side * (30 + 110 * ease_out_back(e) * rnd.uniform(0.6, 1.0)) * spread
        dy = -20 * e * rnd.uniform(0.5, 1.5)
        r = (20 + 12 * rnd.random()) * (1 - 0.4 * e)
        c.drawCircle(x + dx, y + dy, r, paint(rgb(150, 135, 120), stroke=5, alpha=1 - e))
        c.drawCircle(x + dx, y + dy, r, paint(rgb(240, 232, 215), alpha=1 - e))


def speed_lines(c, x, y, k, direction=1, length=170, seed=0):
    """Hizli hareketin arkasinda yatay cizgiler. direction: hareket yonu (+1 saga)."""
    if k <= 0.01:
        return
    rnd = random.Random(seed)
    for i in range(4):
        yy = y - 60 + i * 40 + rnd.uniform(-8, 8)
        x0 = x - direction * (90 + rnd.uniform(0, 40))
        c.drawLine(x0, yy, x0 - direction * length * rnd.uniform(0.6, 1.0), yy, paint(INK, stroke=6, alpha=k * 0.7))


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


def caption(c, text, key=None, key_color=rgb(235, 70, 70), y=985, cw=W):
    """Alt yazi: konturlu beyaz yuvarlak kutu; anahtar kelime renkli. cw: tuval genisligi (Shorts 1080)."""
    words = text.split()
    f = _fit(words, 62, cw - 220)
    widths = [f.measureText(w + " ") for w in words]
    tw = sum(widths) - f.measureText(" ")
    x0 = (cw - tw) / 2
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
        lift = 12 * pop * (1 - clamp01((t_local - st - 0.25) / 0.3))   # buyutme yerine ziplama: komsuya binmez
        c.drawString(w, x, y0 - lift, f, paint(rgb(255, 130, 40) if sung else rgb(120, 110, 130)))
        x += wd


# ---------------- kare -> bayt ----------------
def new_surface():
    return skia.Surface(W, H)


def frame_bytes(surface):
    """RGBA baytlari (ffmpeg -pix_fmt rgba)."""
    img = surface.makeImageSnapshot()
    arr = img.toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    return np.ascontiguousarray(arr).tobytes()
