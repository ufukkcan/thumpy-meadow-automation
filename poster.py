"""
Kucuk resim afisleri v2 (K-26; docs/arastirma-kesif.md, rakip panolari 11-22).

Rakiplerden olculen kurallar: yuzler kadrajin %60-80'i ve kenardan tasar; gozler acik, agiz acik; doygun renk;
sol altta sabit kanal logosu; Noel disi yazisiz, Noel'de 1-2 kelime sarki adi + gece mavisi zemin (soluk
beyaz kar degil; H13: arka plan videonun ilk sahnesi); mevsim aksesuari (Noel sapkasi). Yaniltici olmayan: yalnizca bolumdeki karakter/obje/mekan.

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


def _story_xmas(S):
    return S.melody == "jingle" or bool(XMAS_PROPS & set(S.all_props))


def is_xmas(stories):
    """Bolumun en az yarisi Noel/kis temali ise (tek bir karli hikaye tum bolumu Noel yapmaz)."""
    return sum(map(_story_xmas, stories)) * 2 >= len(stories)


def _flakes(c, n=46, seed=9):
    rnd = random.Random(seed)
    for _ in range(n):
        rr = rnd.uniform(7, 20)
        c.drawCircle(rnd.uniform(0, W), rnd.uniform(0, H), rr, paint(rgb(255, 255, 255, 230), blur=rr * 0.25))


def _scene(c, S):
    """Afis = video (H13): arka plan, hikayenin videodaki ilk sahnesinin kendisi (mekan kiti + gokyuzu).
    Donus: gece mi (vinyet rengi icin)."""
    kind = getattr(S, "sky_place", S.place)
    r.Meadow(kind=kind).draw(c, 0.0, 0.0)
    return r.SKY.get(kind, "day") in ("night", "xmas") or kind == "homex"


# ---------------- ogeler ----------------
santa_hat = r.santa_hat                                   # videoda da ayni sapka (render2'ye tasindi)


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
    surf = r.new_surface()
    c = surf.getCanvas()
    night = _scene(c, S)
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
    if S.weather == "snow" or (xmas and S.place != "home"):     # ev icinde kar yagmaz (video ile ayni)
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
    surf = r.new_surface()
    c = surf.getCanvas()
    night = _scene(c, S)
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
    if S.weather == "snow" or (xmas and S.place != "home"):     # ev icinde kar yagmaz (video ile ayni)
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
