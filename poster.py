"""
Kucuk resim afisleri v2 (K-26; docs/arastirma-kesif.md, rakip panolari 11-22).

Rakiplerden olculen kurallar: yuzler kadrajin %60-80'i ve kenardan tasar; gozler acik, agiz acik; doygun renk;
sol altta sabit kanal logosu; Noel disi yazisiz, Noel'de 1-2 kelime sarki adi + gece mavisi zemin (soluk
beyaz kar degil); mevsim aksesuari (Noel sapkasi). Yaniltici olmayan: yalnizca bolumdeki karakter/obje/mekan.

Uc konsept: A sorun ani (Dino uzanir + kahraman saskin + parlayan obje), B nese uclusu (sarki), C ikinci
hikayenin sorun ani. Noel bolumunde A'ya sarki adi yazilir.
"""
import math
import random

import skia
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

import critters as cr
import render2 as r

rgb, paint, inked, oval_path, INK = r.rgb, r.paint, r.inked, r.oval_path, r.INK
W, H = r.W, r.H
XMAS_PROPS = {"christmas_tree", "snowman", "gift", "bell", "candy", "cookie", "cocoa", "sled", "scarf", "gloves"}
SONG_WORD = {"jingle": "Jingle Bells!"}            # yalnizca Noel'de yazi (arastirma: 14/24)
NIGHT_PLACES = {"snow", "night"}


def _story_xmas(S):
    return S.melody == "jingle" or bool(XMAS_PROPS & set(S.all_props))


def is_xmas(stories):
    """Bolumun en az yarisi Noel/kis temali ise (tek bir karli hikaye tum bolumu Noel yapmaz)."""
    return sum(map(_story_xmas, stories)) * 2 >= len(stories)


# ---------------- arka planlar ----------------
def _night(c, warm):
    c.drawRect(skia.Rect.MakeWH(W, H), paint(shader=r.linear((0, 0), (0, H), [rgb(18, 32, 96), rgb(52, 92, 196),
                                                                               rgb(120, 170, 240)], [0, 0.55, 1])))
    c.drawCircle(warm[0], warm[1], 620, paint(shader=r.radial(warm, 620, [rgb(255, 200, 120, 150), rgb(255, 160, 90, 0)])))
    rnd = random.Random(3)
    for _ in range(70):
        c.drawCircle(rnd.uniform(0, W), rnd.uniform(0, 420), rnd.uniform(1.5, 3.5), paint(rgb(255, 255, 230, rnd.randint(120, 230))))
    for k in range(9):
        col = [rgb(255, 210, 90), rgb(255, 120, 140), rgb(120, 230, 210)][k % 3]
        c.drawCircle(rnd.uniform(0, W), rnd.uniform(60, 520), rnd.uniform(28, 60), paint(col, alpha=0.28, blur=10))
    _hills(c, rgb(70, 110, 190), rgb(40, 80, 120), rgb(235, 245, 255), [rgb(250, 252, 255), rgb(200, 220, 250)])


def _day(c, place, warm):
    c.drawRect(skia.Rect.MakeWH(W, H), paint(shader=r.linear((0, 0), (0, H), [rgb(40, 140, 245), rgb(110, 195, 255),
                                                                               rgb(190, 235, 255)], [0, 0.5, 1])))
    c.drawCircle(warm[0], warm[1], 560, paint(shader=r.radial(warm, 560, [rgb(255, 240, 150, 170), rgb(255, 230, 120, 0)])))
    rnd = random.Random(5)
    for _ in range(5):                                       # bulutlar
        x, y, s = rnd.uniform(0, W), rnd.uniform(60, 330), rnd.uniform(0.8, 1.4)
        for dx, dy, rr in ((-70, 10, 55), (0, -15, 75), (75, 8, 58)):
            c.drawCircle(x + dx * s, y + dy * s, rr * s, paint(rgb(255, 255, 255), alpha=0.95))
    if place == "pond":
        ground = [rgb(90, 200, 120), rgb(60, 170, 100)]
    elif place in ("home",):
        ground = [rgb(255, 214, 150), rgb(240, 180, 120)]
    else:
        ground = [rgb(120, 220, 110), rgb(70, 180, 90)]
    _hills(c, rgb(95, 200, 120), rgb(40, 140, 80), None, ground)
    if place == "pond":
        c.drawOval(r.oval(1450, 880, 520, 120), paint(rgb(90, 190, 245)))


def _hills(c, hill_col, pine_col, cap_col, ground_cols):
    hill = skia.Path()
    hill.moveTo(0, 640)
    hill.cubicTo(500, 560, 1100, 690, W, 590)
    hill.lineTo(W, H)
    hill.lineTo(0, H)
    hill.close()
    c.drawPath(hill, paint(hill_col))
    for x, s in ((120, 1.0), (300, 0.75), (1700, 0.9), (1860, 1.1), (980, 0.6)):
        for k, (wd, ht) in enumerate(((150, 120), (120, 110), (85, 100))):
            yy = 640 - k * 70 * s
            p = skia.Path()
            p.moveTo(x - wd * s, yy)
            p.lineTo(x, yy - ht * 1.3 * s)
            p.lineTo(x + wd * s, yy)
            p.close()
            c.drawPath(p, paint(pine_col))
            if cap_col is not None:
                cap = skia.Path()
                cap.moveTo(x - wd * 0.45 * s, yy - ht * 0.75 * s)
                cap.lineTo(x, yy - ht * 1.3 * s)
                cap.lineTo(x + wd * 0.45 * s, yy - ht * 0.75 * s)
                cap.close()
                c.drawPath(cap, paint(cap_col))
    ground = skia.Path()
    ground.moveTo(0, 760)
    ground.cubicTo(600, 700, 1300, 790, W, 720)
    ground.lineTo(W, H)
    ground.lineTo(0, H)
    ground.close()
    c.drawPath(ground, paint(shader=r.linear((0, 700), (0, H), ground_cols)))


def _cabin(c, x, y, s=1.0):
    w, h = 520 * s, 330 * s
    inked(c, [skia.Path().addRect(skia.Rect.MakeXYWH(x, y - h, w, h))], paint(rgb(170, 90, 60)))
    for k in range(1, 6):
        c.drawLine(x + 8, y - h + k * h / 6, x + w - 8, y - h + k * h / 6, paint(rgb(130, 65, 45), stroke=6))
    roof = skia.Path()
    roof.moveTo(x - 50 * s, y - h + 10)
    roof.lineTo(x + w / 2, y - h - 190 * s)
    roof.lineTo(x + w + 50 * s, y - h + 10)
    roof.close()
    inked(c, [roof], paint(rgb(240, 248, 255)))
    win = skia.Rect.MakeXYWH(x + 60 * s, y - h + 70 * s, 140 * s, 120 * s)
    c.drawRect(win.makeOutset(40, 40), paint(rgb(255, 200, 90), alpha=0.45, blur=30))
    inked(c, [skia.Path().addRect(win)], paint(rgb(255, 214, 110)))
    c.drawLine(win.centerX(), win.top(), win.centerX(), win.bottom(), paint(INK, stroke=10))
    c.drawLine(win.left(), win.centerY(), win.right(), win.centerY(), paint(INK, stroke=10))


def _flakes(c, n=46, seed=9):
    rnd = random.Random(seed)
    for _ in range(n):
        rr = rnd.uniform(7, 20)
        c.drawCircle(rnd.uniform(0, W), rnd.uniform(0, H), rr, paint(rgb(255, 255, 255, 230), blur=rr * 0.25))


# ---------------- ogeler ----------------
def santa_hat(c, cx, cy, w, tilt=0.0, flop=1, red=(225, 38, 52), dark=(180, 20, 40)):
    """(cx, cy): kurk bandin merkezi, w: bant genisligi."""
    c.save()
    c.translate(cx, cy)
    c.rotate(tilt)
    cone = skia.Path()
    cone.moveTo(-w * 0.46, 0)
    cone.cubicTo(-w * 0.40, -w * 0.62, flop * w * 0.10, -w * 0.95, flop * w * 0.62, -w * 0.70)
    cone.cubicTo(flop * w * 0.40, -w * 0.55, w * 0.42, -w * 0.30, w * 0.46, 0)
    cone.close()
    inked(c, [cone], paint(rgb(*red)), w=12)
    c.save()
    c.clipPath(cone, skia.ClipOp.kIntersect, True)
    c.drawOval(r.oval(w * 0.30, -w * 0.20, w * 0.35, w * 0.55), paint(rgb(*dark)))
    c.drawOval(r.oval(-w * 0.18, -w * 0.38, w * 0.06, w * 0.18), paint(rgb(255, 120, 120), alpha=0.7))
    c.restore()
    band = skia.Path()
    band.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-w * 0.56, -w * 0.11, w * 0.56, w * 0.12), w * 0.11, w * 0.11))
    inked(c, [band], paint(rgb(255, 255, 255)), w=12)
    c.drawOval(r.oval(0, w * 0.05, w * 0.50, w * 0.05), paint(rgb(210, 225, 245)))
    inked(c, [oval_path(flop * w * 0.64, -w * 0.70, w * 0.14, w * 0.14)], paint(rgb(255, 255, 255)), w=12)
    c.restore()


def glow_prop(c, spr, name, x, y, size, rot=-14, ring=False):
    c.drawCircle(x, y, size * 0.95, paint(shader=r.radial((x, y), size * 0.95, [rgb(255, 230, 120, 210), rgb(255, 190, 60, 0)])))
    spr.draw(c, name, x, y, size, rot=rot)
    if ring:                                                  # calma cizgileri (zil)
        for side in (-1, 1):
            for k in range(3):
                a = skia.Path()
                rad = size * (0.62 + 0.13 * k)
                a.addArc(skia.Rect.MakeLTRB(x - rad, y - rad, x + rad, y + rad), (-25 if side > 0 else 155) + 8, 40)
                c.drawPath(a, paint(rgb(255, 255, 255), stroke=12 - 2 * k, alpha=0.9 - 0.2 * k))
    r.sparkles(c, x, y, 0.6, seed=5, radius=size * 0.8, n=9)


def logo(c, x=40, y=H - 40):
    """Kanal logosu (sol alt): yesil daire icinde Dino + 'Thumpy Meadow'."""
    R = 92
    cx, cy = x + R, y - R
    circ = oval_path(cx, cy, R, R)
    inked(c, [circ], paint(rgb(120, 214, 120)), w=14)
    c.save()
    c.clipPath(circ, skia.ClipOp.kIntersect, True)
    r.dino(c, cx, cy + 70, s=0.62, expr="happy", mouth=0.6)
    c.restore()
    c.drawPath(circ, paint(rgb(255, 255, 255), stroke=10))
    f = r.font(76)
    for k, word in enumerate(("Thumpy", "Meadow")):
        tx, ty = cx + R + 22, cy - 8 + k * 74
        c.drawString(word, tx, ty, f, paint(INK, stroke=22))
        c.drawString(word, tx, ty, f, paint((rgb(255, 214, 40), rgb(120, 214, 120))[k]))


def _word(c, word):
    import thumbs
    big = len(word) > 8
    thumbs._text(c, word, 1460 if big else 1500, 175 if big else 150, 900 if big else 760,
                 size=170 if big else 190, rot=-5, fill=rgb(255, 214, 40))


def _finish(surf, path, night):
    im = Image.frombytes("RGBA", (W, H), r.frame_bytes(surf)).convert("RGB")
    im = ImageEnhance.Color(im).enhance(1.12)
    im = ImageEnhance.Contrast(im).enhance(1.05)
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse((-W * 0.15, -H * 0.2, W * 1.15, H * 1.2), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(160))
    edge = (10, 15, 50) if night else (20, 60, 90)
    im = Image.composite(im, Image.new("RGB", (W, H), edge), vig.point(lambda v: 150 + v * 105 // 255))
    im = im.resize((1280, 720), Image.LANCZOS)
    im.save(path, "JPEG", quality=93)
    return im


# ---------------- konseptler ----------------
def _hero(S):
    for b in S.hook:
        if b.get("who") in cr.SPEC:
            return b["who"]
    others = [n for n in S.cast if n in cr.SPEC]
    return others[0] if others else "lamb"


def _prop(S, xmas):
    names = [p for p in S.all_props if p not in {"christmas_tree", "pine", "house", "snowman"}]
    if "bell" in S.all_props or (xmas and S.melody == "jingle"):
        return "bell"
    return names[0] if names else ("bell" if xmas else ("umbrella" if S.weather == "rain" else "star"))


def problem(S, path, spr, xmas, word=None):
    """Sorun ani: Dino on planda uzanir, kahraman saskin (yakin), sorun objesi parlar."""
    night = xmas or S.place in NIGHT_PLACES
    surf = r.new_surface()
    c = surf.getCanvas()
    (_night if night else (lambda cc, warm: _day(cc, S.place, warm)))(c, (1450, 420))
    if S.place == "snow":
        _cabin(c, 1190, 760, 1.25)
    prop = _prop(S, xmas)
    glow_prop(c, spr, prop, 1060, 300, 240, ring=prop == "bell")
    hero = _hero(S)
    cr.draw(c, hero, 1480, 1250, s=2.6, t=0.0, expr="surprised", talk=0.8, blink=0.0, look=-0.8, look_y=-0.2,
            arms=(165, 150), tilt=8)
    s = 2.45
    cx, cy = 470, 820
    r.dino(c, cx, cy, s=s, expr="surprised", mouth=0.7, look=1.0, look_y=-0.1, arms=(40, 120), lean=6)
    if xmas:
        santa_hat(c, cx + 62, cy - 0.50 * r.BODY_H * s, 300 * s * 0.66, tilt=8, flop=-1)
    if S.weather == "snow" or xmas:
        _flakes(c)
    elif S.weather == "rain":
        c.drawRect(skia.Rect.MakeWH(W, H), paint(rgb(60, 70, 95, 60)))
        r.rainfall(c, 0.5)
    if word:
        _word(c, word)
    logo(c)
    return _finish(surf, path, night)


def trio(S, path, spr, xmas):
    """Nese uclusu: Dino ortada, iki arkadas yanlarda, hepsi sarki soyluyor (gozler acik)."""
    night = xmas or S.place in NIGHT_PLACES
    surf = r.new_surface()
    c = surf.getCanvas()
    (_night if night else (lambda cc, warm: _day(cc, S.place, warm)))(c, (960, 420))
    glow_prop(c, spr, _prop(S, xmas), 1330, 210, 230, rot=12, ring=_prop(S, xmas) == "bell")
    pals = [n for n in S.cast if n in cr.SPEC][:2]
    while len(pals) < 2:
        pals.append(["lamb", "puppy"][len(pals)])
    for name, x, look, arms, tilt, flop, col in ((pals[0], 330, 0.5, (150, 60), -8, -1, ((60, 180, 90), (30, 130, 60))),
                                                 (pals[1], 1600, -0.5, (60, 150), 8, 1, ((225, 38, 52), (180, 20, 40)))):
        cr.draw(c, name, x, 1180, s=2.05, t=0.2, expr="listen", talk=0.95, blink=0.0, look=look, arms=arms, tilt=tilt)
        if xmas:
            sc = 2.05 * cr.SPEC[name]["scale"]
            santa_hat(c, x + (-20 if flop < 0 else 20), 1180 - 244 * sc - 160 * sc / 1.9, 250 * sc / 1.9,
                      tilt=-14 if flop < 0 else 12, flop=flop, red=col[0], dark=col[1])
    s = 2.3
    cx, cy = 960, 930
    r.dino(c, cx, cy, s=s, mouth=0.9, excited=True, look=0.0, arms=(150, 150))
    if xmas:
        santa_hat(c, cx + 10, cy - 0.52 * r.BODY_H * s, 300 * s * 0.56, tilt=-8, flop=-1)
    if S.weather == "snow" or xmas:
        _flakes(c)
    elif S.weather == "rain":
        c.drawRect(skia.Rect.MakeWH(W, H), paint(rgb(60, 70, 95, 60)))
        r.rainfall(c, 0.5)
    logo(c)
    return _finish(surf, path, night)


def make_three(P, out_prefix):
    """A: 1. hikayenin sorun ani (Noel'de sarki adi yazili), B: nese uclusu, C: 2. hikayenin sorun ani.
    Donus: ([yol x3], telefon_onizleme_yolu)."""
    spr = r.Sprites(outline=14)
    st = P.stories
    ep_x = is_xmas(st)
    s0, s1 = st[0], st[1 % len(st)]
    x0, x1 = ep_x and _story_xmas(s0), ep_x and _story_xmas(s1)   # yalnizca gosterilen hikaye Noel ise
    paths = [f"{out_prefix}_{k}.jpg" for k in "ABC"]
    ims = [problem(s0, paths[0], spr, x0, word=SONG_WORD.get(s0.melody) if x0 else None),
           trio(s0, paths[1], spr, x0),
           problem(s1, paths[2], spr, x1)]
    prev = Image.new("RGB", (3 * 220, 128), "white")
    for k, im in enumerate(ims):
        prev.paste(im.resize((210, 118), Image.LANCZOS), (5 + k * 220, 5))
    pp = f"{out_prefix}_onizleme.png"
    prev.save(pp)
    return paths, pp
