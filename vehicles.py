"""
Kod cizimi araclar (H14, todo 7h): Dino'nun kirmizi traktoru + numarali romork.

Ozgun tasarim (rakip "Sinij traktor" mavi; bizimki kirmizi, sari tavan, on yuzde gozler + gulumseme).
Yan gorunus, saga bakar. Koordinat: (x, ground_y) = arka tekerlegin yere degdigi nokta, s = olcek.
Arka tekerlek yaricapi 150*s; toplam boy ~620*s, tavan ~560*s.
Hareket: dist (katedilen yol, px) -> tekerlek donusu; bounce -> govde ziplamasi (tekerlekler yerde);
t -> egzoz dumani + goz kirpma. driver(c, x, y, s): koltuga oturan surucuyu cizen geri cagirma.
"""
import math

import skia

import render2 as r

rgb, paint, inked, oval_path, oval, INK = r.rgb, r.paint, r.inked, r.oval_path, r.oval, r.INK

RED, RED_SH, RED_HI = rgb(228, 58, 54), rgb(186, 36, 42), rgb(255, 150, 140)
ROOF, ROOF_SH = rgb(255, 206, 64), rgb(232, 168, 40)
TIRE, TREAD = rgb(64, 56, 78), rgb(44, 38, 56)
RIM, RIM_SH = rgb(255, 214, 86), rgb(226, 170, 50)
WOOD, WOOD_SH = rgb(214, 150, 92), rgb(176, 112, 66)
REAR_R, FRONT_R = 150, 88
FRONT_X = 330                      # on tekerlek merkezi (arka tekerlege gore)
SEAT = (-10, -458)                 # surucunun govde merkezi: yuzu panelin (-392) ustunde kalir
ROOF_Y = -690                      # tavanin ust kenari (surucunun Noel sapkasina yer)
HITCH = -190                       # romork baglanti noktasi


def _rrect(l, t, rr, b, rad):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(l, t, rr, b), rad, rad))
    return p


def wheel(c, cx, cy, R, angle, hub=RIM):
    """Lastik + dis tirtiklari + jant + 5 bijon; angle (derece) ile doner."""
    tire = oval_path(cx, cy, R, R)
    bumps = []
    for k in range(14):
        a = math.radians(angle + k * 360 / 14)
        bx, by = cx + math.cos(a) * R * 0.96, cy + math.sin(a) * R * 0.96
        bumps.append(oval_path(bx, by, R * 0.13, R * 0.13))
    inked(c, bumps + [tire], paint(TIRE), w=10)
    c.drawCircle(cx, cy, R * 0.80, paint(TREAD))
    inked(c, [oval_path(cx, cy, R * 0.56, R * 0.56)], paint(hub), w=9)
    c.drawCircle(cx + R * 0.06, cy + R * 0.06, R * 0.44, paint(RIM_SH))
    c.drawCircle(cx, cy, R * 0.42, paint(hub))
    for k in range(5):
        a = math.radians(angle + k * 72)
        bx, by = cx + math.cos(a) * R * 0.30, cy + math.sin(a) * R * 0.30
        c.drawCircle(bx, by, R * 0.06, paint(INK))
    inked(c, [oval_path(cx, cy, R * 0.14, R * 0.14)], paint(RED), w=8)


def puffs(c, x, y, t, strength=1.0, seed=0):
    """Egzoz dumani: yukari ve geriye (sola) suzulen, buyuyup solan bulutcuklar."""
    if strength <= 0:
        return
    for k in range(5):
        age = (t * 1.5 + k / 5 + seed * 0.13) % 1.0
        px, py = x - age * 170, y - age * 190
        rr = 14 + age * 38
        c.drawCircle(px, py, rr, paint(rgb(255, 255, 255), alpha=(1 - age) * 0.85 * strength))
        c.drawCircle(px, py, rr, paint(rgb(170, 175, 200), stroke=5, alpha=(1 - age) * 0.6 * strength))


def tractor(c, x, ground_y, s=1.0, t=0.0, dist=0.0, bounce=0.0, expr="happy", look=0.0, puff=1.0,
            driver=None, hat=False, honk=0.0):
    """Kirmizi traktor. expr: happy | surprised | worried. honk 0..1: korna ani (gozler buyur, agiz acilir)."""
    c.save()
    c.translate(x, ground_y)
    c.scale(s, s)
    ang = math.degrees(dist / (REAR_R * s)) if s else 0.0
    by = -bounce
    puffs(c, 240, by - 430, t, puff)

    # --- kabin arka direk + koltuk sirti + surucu ---
    c.drawRect(skia.Rect.MakeLTRB(-142, by + ROOF_Y + 30, -122, by - 300), paint(INK))
    inked(c, [_rrect(-130, by - 520, -70, by - 300, 24)], paint(RED_SH), w=10)
    if driver is not None:
        driver(c, SEAT[0], by + SEAT[1], 0.55)

    # --- arka camurluk + kabin yan paneli ---
    fender = skia.Path()
    fender.addArc(oval(0, by - REAR_R, REAR_R + 30, REAR_R + 30), 180, 180)
    fender.lineTo(REAR_R + 30, by - REAR_R + 6)
    fender.lineTo(-REAR_R - 30, by - REAR_R + 6)
    fender.close()
    panel = _rrect(-150, by - 392, 96, by - 286, 22)
    inked(c, [fender, panel], paint(RED), w=12)
    c.drawRect(skia.Rect.MakeLTRB(-136, by - 372, 80, by - 352), paint(RED_HI, alpha=0.55))

    # --- motor kaputu (on yuz gozlu) ---
    hood = _rrect(70, by - 330, 440, by - 150, 60)
    stack = _rrect(222, by - 440, 258, by - 300, 10)
    inked(c, [stack], paint(rgb(110, 105, 125)), w=10)
    c.drawRect(skia.Rect.MakeLTRB(216, by - 446, 264, by - 430), paint(INK))
    inked(c, [hood], paint(RED), w=12)
    c.save()
    c.clipPath(hood, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeLTRB(70, by - 190, 440, by - 150), paint(RED_SH))
    c.drawOval(oval(220, by - 300, 120, 16), paint(RED_HI, alpha=0.6))
    for k in range(4):                                     # yan havalandirma
        gx = 130 + k * 26
        c.drawLine(gx, by - 270, gx, by - 205, paint(RED_SH, stroke=9))
    c.restore()
    # on yuz: izgara-agiz + farlar-gozler
    big = 1.18 if honk > 0 or expr == "surprised" else 1.0
    for ex, er, far in ((350, 42, False), (408, 34, True)):
        er *= big
        ey = by - 262
        inked(c, [oval_path(ex, ey, er, er * 1.08)], paint(rgb(255, 255, 255)), w=10)
        blink = (t % 4.1) > 3.95
        if blink and not honk:
            c.drawLine(ex - er * 0.7, ey, ex + er * 0.7, ey, paint(INK, stroke=8))
        elif expr == "happy" and not honk:
            arc = skia.Path()
            arc.moveTo(ex - er * 0.6, ey + er * 0.15)
            arc.quadTo(ex, ey - er * 0.75, ex + er * 0.6, ey + er * 0.15)
            c.drawPath(arc, paint(INK, stroke=9))
        else:
            px = ex + er * (0.28 + 0.12 * look)
            c.drawCircle(px, ey + er * 0.05, er * 0.48, paint(INK))
            c.drawCircle(px + er * 0.16, ey - er * 0.16, er * 0.16, paint(rgb(255, 255, 255)))
        if expr == "worried" and not far:
            brow = skia.Path()
            brow.moveTo(ex - er * 0.8, ey - er * 1.25)
            brow.lineTo(ex + er * 0.6, ey - er * 1.5)
            c.drawPath(brow, paint(INK, stroke=9))
    c.drawOval(oval(332, by - 205, 20, 11), paint(rgb(255, 130, 130), alpha=0.75))       # yanak
    mouth = skia.Path()
    if honk > 0:
        mouth.addOval(oval(402, by - 196, 22 * (0.6 + 0.4 * honk), 18 * (0.6 + 0.4 * honk)))
        inked(c, [mouth], paint(rgb(120, 30, 50)), w=8)
    else:
        sad = expr == "worried"
        mouth.moveTo(372, by - 200 + (8 if sad else 0))
        mouth.quadTo(404, by - (210 if sad else 176), 432, by - 200 + (8 if sad else 0))
        c.drawPath(mouth, paint(INK, stroke=9))
    inked(c, [_rrect(380, by - 166, 470, by - 140, 12)], paint(rgb(190, 190, 205)), w=9)   # tampon

    # --- direksiyon + on direk + tavan ---
    c.drawLine(100, by - 300, 82, by - 392, paint(INK, stroke=14))          # direksiyon: yuzun onunde degil
    c.save()
    c.translate(82, by - 396)
    c.rotate(-25)
    inked(c, [oval_path(0, 0, 38, 12)], paint(rgb(80, 72, 96)), w=9)
    c.restore()
    c.drawRect(skia.Rect.MakeLTRB(104, by + ROOF_Y + 30, 122, by - 320), paint(INK))
    roof = _rrect(-175, by + ROOF_Y, 150, by + ROOF_Y + 42, 18)
    inked(c, [roof], paint(ROOF), w=12)
    c.drawRect(skia.Rect.MakeLTRB(-165, by + ROOF_Y + 24, 140, by + ROOF_Y + 36), paint(ROOF_SH))
    if hat:                                                 # Noel: tavanda kucuk celenk
        for k, col in enumerate((rgb(60, 170, 90), rgb(230, 50, 60), rgb(60, 170, 90), rgb(255, 214, 60))):
            c.drawCircle(-120 + k * 75, by + ROOF_Y, 16, paint(col))
            c.drawCircle(-120 + k * 75, by + ROOF_Y, 16, paint(INK, stroke=6))

    # --- tekerlekler (en onde) + baglanti ---
    c.drawLine(-REAR_R - 10, -120, HITCH, -120, paint(INK, stroke=16))
    wheel(c, 0, -REAR_R, REAR_R, ang)
    wheel(c, FRONT_X, -FRONT_R, FRONT_R, ang * REAR_R / FRONT_R)
    c.restore()


def trailer(c, x_hitch, ground_y, s=1.0, dist=0.0, seats=4, riders=None, gifts=0, bounce=0.0, number_from=1):
    """Tahta romork. x_hitch: traktorun baglanti noktasi (dunya). riders: [(cizici, koltuk_no)]; cizici(c, x, y, s)
    hayvanin ayak hizasini alir (alt govdesi kenarin arkasinda kalir). gifts: kasada hediye kutusu sayisi."""
    c.save()
    c.translate(x_hitch, ground_y)
    c.scale(s, s)
    by = -bounce
    L = 120 + seats * 150
    left = -L - 40
    ang = math.degrees(dist / (62 * s)) if s else 0.0
    c.drawLine(-40, -120, 0, -120, paint(INK, stroke=14))
    # binenler (kenarin arkasinda)
    seat_x = [left + 100 + k * 150 for k in range(seats)]
    taken = {n - number_from for _, n in (riders or [])}
    free = [k for k in range(seats - 1, -1, -1) if k not in taken]
    for k in range(min(gifts, len(free) * 2)):              # hediye kutulari: bos koltuklarda, en fazla 2 kat
        gx = seat_x[free[k // 2]]
        gift(c, gx, by - 262 - (k % 2) * 92, 110, seed=k)
    for draw, n in (riders or []):
        k = n - number_from
        if 0 <= k < seats:
            draw(c, seat_x[k], by - 240, 0.62)
    # kasa
    box = _rrect(left, by - 280, -30, by - 120, 18)
    inked(c, [box], paint(WOOD), w=12)
    c.save()
    c.clipPath(box, skia.ClipOp.kIntersect, True)
    for k in range(1, 3):
        yy = by - 280 + k * 54
        c.drawLine(left, yy, -30, yy, paint(WOOD_SH, stroke=8))
    c.restore()
    # koltuk numaralari (sayma)
    f = r.font(56)
    for k, sx in enumerate(seat_x):
        cy = by - 200
        inked(c, [oval_path(sx, cy, 38, 38)], paint(rgb(255, 255, 255)), w=9)
        txt = str(number_from + k)
        wdt = f.measureText(txt)
        c.drawString(txt, sx - wdt / 2, cy + 20, f, paint(RED))
    wheel(c, left + 110, -62, 62, ang)
    wheel(c, -150, -62, 62, ang)
    c.restore()


def gift(c, x, y, size, seed=0):
    """Hediye kutusu (kurdele + fiyonk). (x, y): kutunun alt-orta noktasi."""
    cols = [(rgb(80, 170, 255), rgb(255, 214, 60)), (rgb(120, 210, 120), rgb(230, 50, 60)),
            (rgb(250, 120, 170), rgb(255, 255, 255)), (rgb(255, 180, 60), rgb(120, 80, 200))]
    body, rib = cols[seed % len(cols)]
    w = size
    box = _rrect(x - w / 2, y - w * 0.8, x + w / 2, y, 8)
    inked(c, [box], paint(body), w=8)
    c.drawRect(skia.Rect.MakeLTRB(x - w * 0.09, y - w * 0.8, x + w * 0.09, y), paint(rib))
    for side in (-1, 1):
        inked(c, [oval_path(x + side * w * 0.17, y - w * 0.88, w * 0.17, w * 0.11)], paint(rib), w=7)
