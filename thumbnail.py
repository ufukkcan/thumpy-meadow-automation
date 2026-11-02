"""
Profesyonel cocuk kanali kucuk resmi (1280x720 JPEG).

Tiklanma icin kullanilan teknikler:
- Merkezden yayilan parlak isinlar (sunburst): gozu objelere ceker
- Heyecanli karakter: acik agiz, kollar havada, parlak gozler
- Sticker efekti: her objenin etrafinda kalin beyaz kenar + yumusak golge
- Birden fazla obje, hafif acili ve farkli boyutlarda (enerji ve hareket hissi)
- Her harfi farkli renkte, kalin konturlu, hafif egik baslik
- Parilti ve konfeti
3 varyasyon uretilir (YouTube Studio'daki "Test & Compare" icin).
YANILTICI DEGIL: sadece bolumde gercekten gecen objeler kullanilir.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import props
import scene2d as s

TW, TH = 1280, 720
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LETTER_COLORS = [(255, 85, 85), (255, 185, 40), (90, 200, 95), (70, 155, 255), (200, 110, 240)]
STROKE = (45, 30, 70)

VARIANTS = {
    "A": {"rays": ((255, 214, 90), (255, 192, 60)), "dino_left": True},
    "B": {"rays": ((125, 210, 255), (90, 180, 250)), "dino_left": False},
    "C": {"rays": ((255, 160, 200), (255, 128, 175)), "dino_left": True},
}


def _sunburst(img, cx, cy, colors, n=18):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, TW, TH], fill=colors[0])
    r = 1600
    for i in range(n):
        if i % 2:
            continue
        a0 = 2 * math.pi * i / n
        a1 = 2 * math.pi * (i + 1) / n
        d.polygon([(cx, cy), (cx + math.cos(a0) * r, cy + math.sin(a0) * r),
                   (cx + math.cos(a1) * r, cy + math.sin(a1) * r)], fill=colors[1])
    # merkezde yumusak parlama
    glow = Image.new("L", (TW, TH), 0)
    ImageDraw.Draw(glow).ellipse([cx - 330, cy - 330, cx + 330, cy + 330], fill=150)
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img.paste((255, 250, 225), (0, 0), glow)


def _sticker(draw_fn, box, outline=14, angle=0.0):
    """draw_fn(draw, cx, cy) seffaf katmana cizer -> beyaz kenarli, golgeli, dondurulmus sticker."""
    pad = outline * 3
    W = H = box + pad * 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer), W / 2, H / 2)
    alpha = layer.split()[3]
    grown = alpha
    for _ in range(max(1, outline // 4)):
        grown = grown.filter(ImageFilter.MaxFilter(9))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, H), (40, 30, 60, 0))
    shadow.putalpha(grown.point(lambda v: int(v * 0.35)).filter(ImageFilter.GaussianBlur(8)))
    out.alpha_composite(shadow, (6, 10))
    white = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    white.putalpha(grown)
    out.alpha_composite(white)
    out.alpha_composite(layer)
    return out.rotate(angle, resample=Image.BICUBIC, expand=True)


def _paste_center(base, sticker, cx, cy):
    base.alpha_composite(sticker, (int(cx - sticker.width / 2), int(cy - sticker.height / 2)))


def _title(text, max_w):
    """Her harfi farkli renkte, koyu kontur + beyaz dis kenarli baslik katmani."""
    size = 150
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    while size > 60:
        font = ImageFont.truetype(FONT, size)
        if probe.textlength(text, font=font) + 60 <= max_w:
            break
        size -= 6
    width = int(probe.textlength(text, font=font)) + 120
    layer = Image.new("RGBA", (width, size + 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, ci = 60, 0
    for ch in text:
        color = LETTER_COLORS[ci % len(LETTER_COLORS)] if ch.strip() else None
        if color:
            d.text((x, 40), ch, font=font, fill=color, stroke_width=max(8, size // 14), stroke_fill=STROKE)
            ci += 1
        x += probe.textlength(ch, font=font)
    return _outline_layer(layer)


def _outline_layer(layer, outline=12):
    alpha = layer.split()[3]
    grown = alpha
    for _ in range(outline // 4):
        grown = grown.filter(ImageFilter.MaxFilter(9))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shadow = Image.new("RGBA", layer.size, (40, 30, 60, 0))
    shadow.putalpha(grown.point(lambda v: int(v * 0.45)).filter(ImageFilter.GaussianBlur(6)))
    out.alpha_composite(shadow, (5, 9))
    white = Image.new("RGBA", layer.size, (255, 255, 255, 0))
    white.putalpha(grown)
    out.alpha_composite(white)
    out.alpha_composite(layer)
    return out


def _sparkle(d, x, y, r, color):
    d.polygon([(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25),
               (x, y + r), (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)], fill=color)


CLUSTER = {
    1: [(0.0, 0.0, 1.0, -6)],
    2: [(-0.5, 0.08, 0.82, -10), (0.5, -0.08, 0.82, 9)],
    3: [(-0.62, 0.22, 0.7, -12), (0.0, -0.22, 0.86, 5), (0.62, 0.22, 0.7, 12)],
    4: [(-0.55, -0.25, 0.66, -10), (0.55, -0.25, 0.66, 10), (-0.3, 0.42, 0.66, 6), (0.45, 0.42, 0.66, -7)],
}


def make_thumbnail(text: str, prop_list: list[dict], out_path: str, variant: str = "A", seed: int = 0) -> str:
    v = VARIANTS[variant]
    rng = random.Random(seed + ord(variant))
    dino_x = 335 if v["dino_left"] else TW - 335
    cluster_x = TW - 380 if v["dino_left"] else 380
    cluster_y = 440

    img = Image.new("RGBA", (TW, TH))
    _sunburst(img, cluster_x, cluster_y, v["rays"])

    # parilti + konfeti (arka planda, objelerin altinda kalir)
    d = ImageDraw.Draw(img)
    for _ in range(9):
        x, y = rng.randint(40, TW - 40), rng.randint(170, TH - 40)
        _sparkle(d, x, y, rng.randint(14, 30), rng.choice([(255, 255, 255), (255, 240, 120)]))
    for _ in range(18):
        x, y = rng.randint(20, TW - 20), rng.randint(150, TH - 20)
        r = rng.randint(5, 10)
        d.ellipse([x - r, y - r, x + r, y + r], fill=rng.choice(LETTER_COLORS))

    # objeler (sticker)
    items = [p for p in prop_list if p][:4] or [{"kind": "shape", "shape": "star", "color": "yellow"}]
    for (dx, dy, sc, ang), prop in zip(CLUSTER[len(items)], items):
        size = int(330 * sc)
        if prop["kind"] == "count":
            n = min(int(prop["n"]), 6)
            fn = lambda dd, cx, cy, p=prop, n=n, sz=size: props.draw_count(
                dd, cx, cy, n, p["item"], 0.5, t_local=99, per_row=3, size=sz * 0.38)
        else:
            fn = lambda dd, cx, cy, p=prop, sz=size: props.draw_prop(dd, p, cx, cy, sz, t=0.5)
        st = _sticker(fn, int(size * 1.35), outline=14, angle=ang)
        _paste_center(img, st, cluster_x + dx * 300, cluster_y + dy * 290)

    # heyecanli karakter (sticker)
    dino = _sticker(lambda dd, cx, cy: s._dino(dd, cx, cy + 20, 1.0, False, 0.5, mood="excited"), 560,
                    outline=16, angle=-6 if v["dino_left"] else 6)
    _paste_center(img, dino, dino_x, 450)

    # baslik (ustte, hafif egik)
    title = _title(text, TW - 80).rotate(-3 if v["dino_left"] else 3, resample=Image.BICUBIC, expand=True)
    if title.width > TW - 20:
        k = (TW - 20) / title.width
        title = title.resize((int(title.width * k), int(title.height * k)), Image.LANCZOS)
    img.alpha_composite(title, (int((TW - title.width) / 2), -18))

    img.convert("RGB").save(out_path, "JPEG", quality=92)
    return out_path


def make_variants(text: str, prop_list: list[dict], out_prefix: str) -> list[str]:
    return [make_thumbnail(text, prop_list, f"{out_prefix}_{k}.jpg", k) for k in VARIANTS]
