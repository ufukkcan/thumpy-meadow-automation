"""
Kucuk resimler (7d): videoyla AYNI cizgi film motoru (render2), 1280x720 JPEG, 3 farkli konsept.
Arastirma (docs/arastirma-cocuk-izleme.md, docs/arastirma-2d-kanallar.md):
  - buyuk, ifadeli yuz (bebek semasi) + tek kahraman nesne; 1-3 kelime; yuksek kontrast, sicak renk
  - yaniltici olmayan: yalnizca bolumde gercekten olan hayvanlar ve sahne
  A "PEEKABOO": sasirmis Dino + caliniin ustunden firlayan ilk hayvan
  B "FRIENDS" : sevincli Dino + bolumun 3 hayvani, konfeti
  C "MYSTERY" : kulak veren Dino + calida parlayan gozler + soru balonu
Ayrica telefon boyutunda (210x118) okunabilirlik onizlemesi uretilir.
"""
import math
from pathlib import Path

import skia
from PIL import Image

import render2 as r

TW, TH = 1280, 720
K = TW / r.W                                       # 1920'lik sahne koordinatlarindan olcek


def _text(c, s, cx, cy, max_w, size=150, fill=r.rgb(255, 214, 40), rot=-4.0):
    """Kalin konturlu buyuk yazi; sigmazsa iki satira boler / kucultur."""
    words = s.split()
    lines = [s]
    f = r.font(size)
    if f.measureText(s) > max_w and len(words) > 1:
        mid = max(1, len(words) // 2)
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    widest = max(f.measureText(x) for x in lines)
    if widest > max_w:
        f = r.font(size * max_w / widest)
    lh = f.getSize() * 1.02
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    y0 = -lh * (len(lines) - 1) / 2 + f.getSize() * 0.36
    for k, line in enumerate(lines):
        w = f.measureText(line)
        y = y0 + k * lh
        c.drawString(line, -w / 2 + 6, y + 8, f, r.paint(r.rgb(30, 20, 50, 120)))        # golge
        c.drawString(line, -w / 2, y, f, r.paint(r.INK, stroke=f.getSize() * 0.22))
        c.drawString(line, -w / 2, y, f, r.paint(fill))
    c.restore()


def _base(meadow, t=2.0):
    surf = skia.Surface(TW, TH)
    c = surf.getCanvas()
    c.save()
    c.scale(K, K)
    meadow.draw(c, t, 0.0)
    return surf, c


def _finish(surf, c, path):
    c.restore()
    img = surf.makeImageSnapshot()
    arr = img.toarray(colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    Image.fromarray(arr, "RGBA").convert("RGB").save(path, "JPEG", quality=92)
    return path


def concept_a(ep, spr, meadow, path):
    """Sasirmis Dino + calidan firlayan hayvan + PEEKABOO."""
    surf, c = _base(meadow)
    first = ep["finds"][0]["animal"]
    c.save()
    c.translate(1480, 0)
    spr.draw(c, first, 0, 470, 470, rot=-8)
    r.bush(c, 0, r.GROUND_Y + 160, 1.55)
    c.restore()
    r.sparkles(c, 1480, 430, 0.45, seed=3, radius=330, n=9)
    r.dino_shadow(c, 560, 1060, s=1.6)
    r.dino(c, 560, 690, s=1.6, t=1.0, expr="surprised", arms=(150, 150), look=1.0, mouth=0.6, sweat=1.0)
    _text(c, ep["thumbnail_texts"][0], 1350, 150, 1050, size=190)
    return _finish(surf, c, path)


def concept_b(ep, spr, meadow, path):
    """Sevincli Dino + 3 hayvan + konfeti + konu yazisi."""
    surf, c = _base(meadow, t=4.0)
    names = [f["animal"] for f in ep["finds"][:3]]
    # hayvanlar yere basar (ayak ~ y + 0.42*boy = zemin cizgisinin altinda), golge ayaginda
    for (x, y, s, rot), n in zip(((1130, 800, 340, -6), (1480, 760, 380, 5), (1780, 860, 320, -4)), names):
        spr.draw(c, n, x, y, s, rot=rot, shadow_y=y + s * 0.42 + 6)
    r.confetti(c, 960, 300, 0.55, seed=5, n=60)
    r.dino_shadow(c, 520, 1060, s=1.5)
    r.dino(c, 520, 700, s=1.5, t=1.0, expr="happy", excited=True, mouth=0.8)
    _text(c, ep["thumbnail_texts"][1], 1260, 270, 1250, size=165, fill=r.rgb(255, 255, 255), rot=3)
    return _finish(surf, c, path)


def concept_c(ep, spr, meadow, path):
    """Kulak veren Dino + calida parlayan gozler + buyuk soru balonu + merak sorusu."""
    surf, c = _base(meadow, t=6.0)
    c.save()
    c.translate(1450, 0)
    r.bush(c, 0, r.GROUND_Y + 150, 1.7)
    c.save()
    c.translate(0, r.GROUND_Y - 70)
    c.scale(2.0, 2.0)
    r.peek_eyes(c, 0, 0, 1.0, k=1.0, look=-1.0)
    c.restore()
    c.restore()
    r.ask_bubble(c, 1640, 330, 1.0, 1.0)
    r.dino_shadow(c, 520, 1060, s=1.6)
    r.dino(c, 520, 690, s=1.6, t=1.0, expr="listen", arms=(20, 165), look=1.0, mouth=0.0)
    _text(c, ep["thumbnail_texts"][2], 900, 250, 1500, size=160, fill=r.rgb(255, 214, 40), rot=-3)
    return _finish(surf, c, path)


def make_three(ep, out_prefix):
    """Donus: [A, B, C] JPEG yollari + onizleme (telefon boyutu) yolu."""
    spr = r.Sprites(outline=14)
    meadow = r.Meadow()
    paths = [concept_a(ep, spr, meadow, f"{out_prefix}_A.jpg"),
             concept_b(ep, spr, meadow, f"{out_prefix}_B.jpg"),
             concept_c(ep, spr, meadow, f"{out_prefix}_C.jpg")]
    sheet = Image.new("RGB", (3 * 330 + 40, 520), (240, 240, 245))
    for k, p in enumerate(paths):
        im = Image.open(p)
        sheet.paste(im.resize((320, 180), Image.LANCZOS), (10 + k * 340, 10))
        sheet.paste(im.resize((210, 118), Image.LANCZOS), (10 + k * 340, 220))
        sheet.paste(im.resize((168, 94), Image.LANCZOS), (10 + k * 340, 370))
    preview = f"{out_prefix}_onizleme.png"
    sheet.save(preview)
    return paths, preview
