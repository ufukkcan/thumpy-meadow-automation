"""
Cocuklar icin duz-renkli 2D cizgi film sahneleri (Pinkfong/SuperSimple tarzinda
AMA tamamen OZGUN karakterlerle -- hicbir telifli varlik kullanilmiyor,
her sey kodla sifirdan ciziliyor).

Tasarim ilkeleri:
- Duz renkler, kontur yok, yumusak yuvarlak formlar
- Katmanli arka plan (uzak dagler -> agaclar -> zemin) = derinlik hissi
- Buyuk kapali/gulen gozler, yanak lekesi = sevimlilik
- Sakin, neseli renk paleti -- korkutucu/karanlik hicbir oge yok
"""
import math

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 24
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Sakin, cocuk dostu palet
SKY_TOP = (150, 215, 250)
SKY_BOT = (205, 240, 255)
HILL_FAR = (150, 200, 235)
HILL_MID = (120, 180, 220)
TREE_DARK = (58, 150, 110)
TREE_MID = (78, 180, 130)
GROUND = (245, 215, 140)
GROUND_DARK = (235, 198, 120)


def _sky(draw: ImageDraw.ImageDraw, horizon: int) -> None:
    for y in range(horizon):
        r = y / max(horizon, 1)
        draw.line([(0, y), (W, y)], fill=tuple(
            int(SKY_TOP[i] + (SKY_BOT[i] - SKY_TOP[i]) * r) for i in range(3)))


def _cloud(draw: ImageDraw.ImageDraw, x: float, y: float, s: float) -> None:
    for dx, dy, r in ((0, 0, 40), (36, -16, 50), (80, 0, 38), (42, 14, 42)):
        draw.ellipse([x + dx * s - r * s, y + dy * s - r * s,
                      x + dx * s + r * s, y + dy * s + r * s], fill=(255, 255, 255))


def _far_hills(draw: ImageDraw.ImageDraw, horizon: int) -> None:
    """Uzaktaki yumusak tepeler -- derinligin en arka katmani."""
    for cx, w, h, col in ((150, 460, 230, HILL_FAR), (560, 540, 300, HILL_MID),
                          (950, 430, 210, HILL_FAR)):
        draw.ellipse([cx - w // 2, horizon - h, cx + w // 2, horizon + h // 2], fill=col)


def _bush(draw: ImageDraw.ImageDraw, x: float, y: float, s: float, col) -> None:
    """Yuvarlak, kabarik calilik/agac."""
    for dx, dy, r in ((0, 0, 70), (62, -36, 86), (128, 0, 68), (66, 28, 74)):
        draw.ellipse([x + dx * s - r * s, y + dy * s - r * s,
                      x + dx * s + r * s, y + dy * s + r * s], fill=col)


def _dino(draw: ImageDraw.ImageDraw, cx: float, cy: float, scale: float,
          blink: bool, arm_swing: float) -> None:
    """OZGUN sevimli dinozor: yumurta govde, sirt pullari, buyuk gulen gozler.
    Hicbir mevcut karakterin kopyasi degil -- basit geometrik formlardan
    olusturulmus kendi tasarimimiz."""
    s = scale
    body_w, body_h = 300 * s, 340 * s

    # kuyruk: kuculen elipslerden olusan yumusak kivrim (keskin kose yok)
    for i in range(6):
        p = i / 5.0
        tx = cx - body_w * (0.34 + p * 0.62)
        ty = cy + body_h * (0.26 - p * p * 0.34)
        tr = (58 - i * 8) * s
        draw.ellipse([tx - tr, ty - tr, tx + tr, ty + tr], fill=(126, 208, 152))

    # sirt pullari (ucgen, yumusak renkte)
    for i, (px, py, pr) in enumerate((
        (-0.22, -0.46, 0.13), (0.02, -0.56, 0.16), (0.26, -0.44, 0.13),
    )):
        draw.polygon([
            (cx + body_w * px - body_w * pr * 0.6, cy + body_h * py + body_h * 0.10),
            (cx + body_w * px, cy + body_h * py - body_h * 0.08),
            (cx + body_w * px + body_w * pr * 0.6, cy + body_h * py + body_h * 0.10),
        ], fill=(255, 200, 110))

    # govde
    draw.ellipse([cx - body_w / 2, cy - body_h / 2, cx + body_w / 2, cy + body_h / 2],
                 fill=(140, 220, 165))
    # karin (acik ton)
    draw.ellipse([cx - body_w * 0.30, cy - body_h * 0.08,
                  cx + body_w * 0.30, cy + body_h * 0.46], fill=(230, 250, 215))

    # kollar (sallanan)
    for side in (-1, 1):
        ax = cx + side * body_w * 0.46
        ay = cy + body_h * 0.02
        swing = math.sin(arm_swing + (0 if side > 0 else math.pi)) * 16 * s
        draw.ellipse([ax - 34 * s, ay - 26 * s + swing, ax + 34 * s, ay + 42 * s + swing],
                     fill=(132, 212, 158))

    # ayaklar
    for side in (-1, 1):
        fx = cx + side * body_w * 0.20
        draw.ellipse([fx - 46 * s, cy + body_h * 0.40, fx + 46 * s, cy + body_h * 0.60],
                     fill=(120, 202, 148))

    # gozler -- buyuk, neseli
    for side in (-1, 1):
        ex = cx + side * body_w * 0.17
        ey = cy - body_h * 0.18
        if blink:
            draw.arc([ex - 30 * s, ey - 20 * s, ex + 30 * s, ey + 22 * s],
                     start=200, end=340, fill=(40, 45, 50), width=int(9 * s))
        else:
            draw.ellipse([ex - 27 * s, ey - 31 * s, ex + 27 * s, ey + 31 * s], fill=(255, 255, 255))
            draw.ellipse([ex - 16 * s, ey - 18 * s, ex + 16 * s, ey + 20 * s], fill=(45, 50, 58))
            draw.ellipse([ex - 4 * s, ey - 13 * s, ex + 10 * s, ey + 1 * s], fill=(255, 255, 255))

    # yanak lekeleri
    for side in (-1, 1):
        chx = cx + side * body_w * 0.33
        draw.ellipse([chx - 22 * s, cy - body_h * 0.03, chx + 22 * s, cy + body_h * 0.08],
                     fill=(255, 175, 180))

    # gulumseme
    draw.arc([cx - 44 * s, cy - body_h * 0.10, cx + 44 * s, cy + body_h * 0.10],
             start=15, end=165, fill=(60, 60, 68), width=int(8 * s))


def _caption(draw: ImageDraw.ImageDraw, text: str, bounce: float) -> None:
    max_w = W - 130
    size = 94
    while size > 46:
        font = ImageFont.truetype(FONT_PATH, size)
        lines, cur = [], ""
        for word in text.split():
            trial = f"{cur} {word}".strip()
            if draw.textlength(trial, font=font) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        if len(lines) <= 2:
            break
        size -= 6

    line_h = size + 20
    start_y = H - 290 - line_h * len(lines) + bounce
    for i, line in enumerate(lines):
        bb = draw.textbbox((0, 0), line, font=font)
        x = (W - (bb[2] - bb[0])) / 2 - bb[0]
        y = start_y + i * line_h - bb[1]
        for ox, oy in ((-7, 0), (7, 0), (0, -7), (0, 7), (-5, -5), (5, 5), (-5, 5), (5, -5)):
            draw.text((x + ox, y + oy), line, font=font, fill=(70, 50, 25))
        draw.text((x, y), line, font=font, fill=(255, 252, 240))


def render_frame(t: float, caption: str) -> Image.Image:
    img = Image.new("RGB", (W, H), SKY_BOT)
    draw = ImageDraw.Draw(img)

    horizon = int(H * 0.47)
    _sky(draw, horizon)
    _far_hills(draw, horizon)

    # zemin
    draw.rectangle([0, horizon, W, H], fill=GROUND)
    draw.ellipse([-200, horizon - 40, W + 200, horizon + 150], fill=GROUND_DARK)

    # kayan bulutlar
    for base_x, y, sc, sp in ((120, 300, 1.0, 26), (660, 200, 0.7, 18), (400, 420, 0.55, 34)):
        _cloud(draw, (base_x - t * sp) % (W + 400) - 200, y, sc)

    # agaclar (iki katman -> derinlik)
    _bush(draw, -30, horizon - 70, 1.15, TREE_DARK)
    _bush(draw, 830, horizon - 100, 1.2, TREE_DARK)
    _bush(draw, 150, horizon - 20, 0.7, TREE_MID)

    # karakter: yumusakca zipliyor, goz kirpiyor
    bounce = abs(math.sin(t * 2.2)) * 42
    blink = (t % 3.4) > 3.15   # arada bir goz kirpma
    _dino(draw, W / 2, horizon + 150 - bounce, scale=1.75, blink=blink, arm_swing=t * 4.0)

    _caption(draw, caption, bounce=math.sin(t * 2.6) * 8)
    return img


if __name__ == "__main__":
    render_frame(0.6, "Hello little dino!").save("scene_preview.png")
    print("onizleme uretildi")
