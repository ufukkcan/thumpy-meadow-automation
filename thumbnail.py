"""
YouTube kucuk resmi (1280x720 JPEG, <2MB).
Tiklanma orani icin: buyuk sevimli karakter, buyuk tek obje, arkasinda parlak hale,
ustte 2-3 kelimelik kalin ve okunakli yazi. Kucuk ekranda (telefon) bile secilebilir olmali.
"""
from PIL import Image, ImageDraw

import episode
import props
import scene2d as s

TW, TH = 1280, 720


def make_thumbnail(text: str, prop: dict | None, out_path: str) -> str:
    img = episode.build_background(TW, TH)
    d = ImageDraw.Draw(img)

    # obje arkasinda parlak hale (kontrast icin)
    hx, hy = 900, 430
    for r, col in ((260, (255, 245, 200)), (215, (255, 236, 160))):
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=col)

    s._dino(d, 360, 470, scale=1.25, blink=False, arm_swing=0.8)
    if prop:
        size = 300 if prop.get("kind") != "count" else 1
        if prop.get("kind") == "count":
            n = min(int(prop["n"]), 6)
            props.draw_count(d, hx, hy, n, prop["item"], 0.5, t_local=99, per_row=3, size=125)
        else:
            props.draw_prop(d, prop, hx, hy, size, t=0.5)

    font = episode.fit_font(d, text, TW - 120, start=150, minimum=70)
    bb = d.textbbox((0, 0), text, font=font)
    x = (TW - (bb[2] - bb[0])) / 2 - bb[0]
    episode.outlined(d, (x, 30 - bb[1]), text, font, (255, 214, 50), outline=(60, 40, 20), width=12)

    img.save(out_path, "JPEG", quality=90)
    return out_path
