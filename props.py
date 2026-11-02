"""
Thumpy Meadow obje kutuphanesi -- hepsi kodla, duz renkli, sevimli stilde ciziliyor.
Claude'un yazdigi senaryolar SADECE buradaki objeleri kullanabilir (ALLOWED),
boylece cizilemeyen bir sey istenmez.
"""
import math

from PIL import ImageDraw

COLORS = {
    "red": (235, 70, 70), "blue": (70, 130, 235), "yellow": (250, 205, 50),
    "green": (80, 190, 100), "orange": (250, 150, 50), "purple": (160, 100, 220),
    "pink": (245, 140, 190),
}

ALLOWED = {
    "balloon": {"color": list(COLORS)},
    "shape": {"shape": ["circle", "square", "triangle", "rectangle", "star", "heart", "oval"],
              "color": list(COLORS)},
    "fruit": {"fruit": ["apple", "banana", "orange", "strawberry", "grapes", "pear", "watermelon"]},
    "animal": {"animal": ["duck", "fish", "bunny", "cat", "pig", "frog"]},
    "count": {"item": ["apple", "orange", "star", "heart", "balloon"], "n": list(range(1, 11))},
}

DARK = (60, 55, 60)
WHITE = (255, 255, 255)


def _lighter(c, k=70):
    return tuple(min(255, v + k) for v in c)


def _darker(c, k=50):
    return tuple(max(0, v - k) for v in c)


def _eye(d, x, y, r):
    d.ellipse([x - r, y - r * 1.15, x + r, y + r * 1.15], fill=DARK)
    d.ellipse([x - r * 0.25, y - r * 0.85, x + r * 0.45, y - r * 0.15], fill=WHITE)


# ---------------- sekiller ----------------
def _star_points(cx, cy, r_out, r_in, n=5, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def _heart(d, cx, cy, s, color):
    r = s * 0.27
    d.ellipse([cx - 2 * r, cy - r * 1.4, cx, cy + r * 0.6], fill=color)
    d.ellipse([cx, cy - r * 1.4, cx + 2 * r, cy + r * 0.6], fill=color)
    d.polygon([(cx - 1.95 * r, cy - 0.2 * r), (cx + 1.95 * r, cy - 0.2 * r), (cx, cy + s * 0.5)], fill=color)


def draw_shape(d, cx, cy, s, shape, color):
    h = s / 2
    if shape == "circle":
        d.ellipse([cx - h, cy - h, cx + h, cy + h], fill=color)
    elif shape == "square":
        d.rounded_rectangle([cx - h, cy - h, cx + h, cy + h], radius=s * 0.08, fill=color)
    elif shape == "rectangle":
        d.rounded_rectangle([cx - h * 1.35, cy - h * 0.75, cx + h * 1.35, cy + h * 0.75], radius=s * 0.07, fill=color)
    elif shape == "triangle":
        d.polygon([(cx, cy - h), (cx + h * 1.1, cy + h * 0.85), (cx - h * 1.1, cy + h * 0.85)], fill=color)
    elif shape == "star":
        d.polygon(_star_points(cx, cy + s * 0.04, h * 1.1, h * 0.46), fill=color)
    elif shape == "heart":
        _heart(d, cx, cy, s, color)
    elif shape == "oval":
        d.ellipse([cx - h * 1.3, cy - h * 0.8, cx + h * 1.3, cy + h * 0.8], fill=color)


# ---------------- balon ----------------
def draw_balloon(d, cx, cy, s, color, t=0.0):
    rw, rh = s * 0.4, s * 0.5
    pts = [(cx + math.sin(t * 2 + k * 0.6) * s * 0.03, cy + rh + k * s * 0.09) for k in range(10)]
    d.line(pts, fill=(110, 100, 90), width=max(2, int(s * 0.013)))
    d.polygon([(cx - s * 0.05, cy + rh + 4), (cx + s * 0.05, cy + rh + 4), (cx, cy + rh - s * 0.04)], fill=color)
    d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=color)
    d.ellipse([cx - rw * 0.6, cy - rh * 0.7, cx - rw * 0.25, cy - rh * 0.3], fill=_lighter(color))


# ---------------- meyveler ----------------
def draw_fruit(d, cx, cy, s, fruit):
    h = s / 2
    if fruit == "apple":
        red = (225, 60, 55)
        d.ellipse([cx - h, cy - h * 0.8, cx + h * 0.4, cy + h * 0.9], fill=red)
        d.ellipse([cx - h * 0.4, cy - h * 0.8, cx + h, cy + h * 0.9], fill=red)
        d.ellipse([cx - h * 0.7, cy - h * 0.55, cx + h * 0.7, cy + h * 0.95], fill=red)
        d.rounded_rectangle([cx - s * 0.03, cy - h * 1.15, cx + s * 0.03, cy - h * 0.6], radius=5, fill=(120, 80, 45))
        d.ellipse([cx + s * 0.02, cy - h * 1.15, cx + h * 0.6, cy - h * 0.8], fill=(90, 180, 80))
        d.ellipse([cx - h * 0.6, cy - h * 0.45, cx - h * 0.3, cy - h * 0.05], fill=_lighter(red))
    elif fruit == "orange":
        o = (250, 150, 40)
        d.ellipse([cx - h, cy - h, cx + h, cy + h], fill=o)
        d.ellipse([cx - h * 0.55, cy - h * 0.6, cx - h * 0.2, cy - h * 0.25], fill=_lighter(o, 60))
        d.ellipse([cx + h * 0.05, cy - h * 1.15, cx + h * 0.6, cy - h * 0.8], fill=(90, 180, 80))
    elif fruit == "banana":
        y = (250, 215, 70)
        r1 = h * 1.05
        cy0 = cy - h * 0.55
        outer = [(cx + math.cos(math.radians(a)) * r1, cy0 - math.sin(math.radians(a)) * r1) for a in range(200, 341, 7)]
        inner = [(cx + math.cos(math.radians(a)) * r1 * 0.95, cy0 - h * 0.42 - math.sin(math.radians(a)) * r1 * 0.95)
                 for a in range(200, 341, 7)]
        d.polygon(outer + inner[::-1], fill=y)
        mid = len(outer) // 2
        d.line(outer[mid - 4: mid + 5], fill=(230, 190, 50), width=6)
        for o, i in ((outer[0], inner[0]), (outer[-1], inner[-1])):
            px, py = (o[0] + i[0]) / 2, (o[1] + i[1]) / 2
            d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=(110, 85, 40))
    elif fruit == "strawberry":
        r = (230, 50, 70)
        d.ellipse([cx - h * 0.9, cy - h * 0.75, cx + h * 0.9, cy + h * 0.35], fill=r)
        d.polygon([(cx - h * 0.88, cy - h * 0.2), (cx + h * 0.88, cy - h * 0.2), (cx + h * 0.12, cy + h * 0.88),
                   (cx - h * 0.12, cy + h * 0.88)], fill=r)
        d.ellipse([cx - h * 0.2, cy + h * 0.68, cx + h * 0.2, cy + h * 0.98], fill=r)
        for sx, sy in [(-0.45, -0.3), (0, -0.4), (0.45, -0.3), (-0.25, 0.1), (0.25, 0.1), (0, 0.5)]:
            d.ellipse([cx + sx * h - 6, cy + sy * h - 8, cx + sx * h + 6, cy + sy * h + 8], fill=(255, 225, 120))
        leaf = (80, 170, 80)
        for k in range(5):
            a = math.radians(-30 - k * 30)
            tip = (cx + math.cos(a) * h * 0.55, cy - h * 0.72 + math.sin(a) * h * 0.3)
            d.polygon([(cx - h * 0.12, cy - h * 0.72), tip, (cx + h * 0.12, cy - h * 0.72)], fill=leaf)
        d.ellipse([cx - h * 0.18, cy - h * 0.85, cx + h * 0.18, cy - h * 0.62], fill=leaf)
        d.rounded_rectangle([cx - 5, cy - h * 1.05, cx + 5, cy - h * 0.75], radius=4, fill=leaf)
    elif fruit == "grapes":
        p = (150, 90, 200)
        rr = h * 0.26
        rows = [(-1, 0, 1, 2), (-0.5, 0.5, 1.5), (0, 1), (0.5,)]
        for ri, row in enumerate(rows):
            for k in row:
                gx = cx + (k - 0.5) * rr * 1.8
                gy = cy - h * 0.45 + ri * rr * 1.6
                d.ellipse([gx - rr, gy - rr, gx + rr, gy + rr], fill=p)
                d.ellipse([gx - rr * 0.5, gy - rr * 0.55, gx - rr * 0.1, gy - rr * 0.15], fill=_lighter(p, 60))
        d.rounded_rectangle([cx - 5, cy - h * 1.05, cx + 5, cy - h * 0.65], radius=4, fill=(110, 80, 45))
        d.ellipse([cx + 4, cy - h * 1.05, cx + h * 0.55, cy - h * 0.72], fill=(90, 180, 80))
    elif fruit == "pear":
        g = (175, 210, 80)
        d.ellipse([cx - h * 0.45, cy - h * 0.95, cx + h * 0.45, cy - h * 0.05], fill=g)
        d.ellipse([cx - h * 0.8, cy - h * 0.35, cx + h * 0.8, cy + h], fill=g)
        d.rounded_rectangle([cx - 5, cy - h * 1.2, cx + 5, cy - h * 0.85], radius=4, fill=(110, 80, 45))
        d.ellipse([cx - h * 0.45, cy, cx - h * 0.15, cy + h * 0.35], fill=_lighter(g, 50))
    elif fruit == "watermelon":
        d.pieslice([cx - h * 1.15, cy - h * 1.0, cx + h * 1.15, cy + h * 1.3], 0, 180, fill=(80, 160, 80))
        d.pieslice([cx - h * 1.0, cy - h * 0.85, cx + h * 1.0, cy + h * 1.15], 0, 180, fill=(240, 90, 100))
        for sx, sy in [(-0.5, 0.35), (0, 0.55), (0.5, 0.35), (-0.25, 0.75), (0.25, 0.75)]:
            d.ellipse([cx + sx * h - 6, cy + sy * h - 9, cx + sx * h + 6, cy + sy * h + 9], fill=(50, 45, 50))


# ---------------- hayvanlar ----------------
def draw_animal(d, cx, cy, s, animal, t=0.0):
    h = s / 2
    blink = (t % 3.1) > 2.95
    if animal == "duck":
        y = (252, 215, 70)
        d.ellipse([cx - h * 0.95, cy - h * 0.05, cx + h * 0.85, cy + h], fill=y)          # govde
        d.ellipse([cx - h * 0.55, cy - h * 0.95, cx + h * 0.35, cy - h * 0.05], fill=y)   # bas
        d.ellipse([cx + h * 0.2, cy - h * 0.55, cx + h * 0.75, cy - h * 0.3], fill=(250, 150, 50))  # gaga
        d.ellipse([cx - h * 0.35, cy + h * 0.25, cx + h * 0.45, cy + h * 0.7], fill=_darker(y, 25))  # kanat
        _eye(d, cx, cy - h * 0.55, h * 0.09) if not blink else d.line([cx - 10, cy - h * 0.55, cx + 10, cy - h * 0.55], fill=DARK, width=5)
    elif animal == "fish":
        o = (250, 140, 60)
        wag = math.sin(t * 6) * h * 0.12
        d.polygon([(cx + h * 0.55, cy), (cx + h * 1.05, cy - h * 0.5 + wag), (cx + h * 1.05, cy + h * 0.5 + wag)], fill=_darker(o, 20))
        d.ellipse([cx - h * 0.95, cy - h * 0.6, cx + h * 0.7, cy + h * 0.6], fill=o)
        d.polygon([(cx - h * 0.1, cy - h * 0.55), (cx + h * 0.3, cy - h * 0.95), (cx + h * 0.35, cy - h * 0.45)], fill=_darker(o, 20))
        _eye(d, cx - h * 0.5, cy - h * 0.12, h * 0.1)
        d.arc([cx - h * 0.85, cy + h * 0.02, cx - h * 0.45, cy + h * 0.3], 20, 160, fill=DARK, width=5)
        for k in range(3):
            by = cy - h * 0.7 - ((t * 60 + k * 45) % 140)
            bx = cx - h * 1.05 + k * 10
            d.ellipse([bx - 9, by - 9, bx + 9, by + 9], outline=(200, 235, 255), width=4)
    elif animal == "bunny":
        w = (245, 245, 250)
        pink = (250, 185, 200)
        for side in (-1, 1):
            d.ellipse([cx + side * h * 0.35 - h * 0.2, cy - h * 1.15, cx + side * h * 0.35 + h * 0.2, cy - h * 0.15], fill=w)
            d.ellipse([cx + side * h * 0.35 - h * 0.1, cy - h * 1.0, cx + side * h * 0.35 + h * 0.1, cy - h * 0.3], fill=pink)
        d.ellipse([cx - h * 0.75, cy - h * 0.45, cx + h * 0.75, cy + h * 0.8], fill=w)
        for side in (-1, 1):
            _eye(d, cx + side * h * 0.3, cy + h * 0.05, h * 0.09)
            d.ellipse([cx + side * h * 0.5 - 14, cy + h * 0.25, cx + side * h * 0.5 + 14, cy + h * 0.4], fill=pink)
        d.ellipse([cx - h * 0.09, cy + h * 0.25, cx + h * 0.09, cy + h * 0.37], fill=(240, 130, 150))
    elif animal == "cat":
        o = (245, 170, 80)
        for side in (-1, 1):
            d.polygon([(cx + side * h * 0.75, cy - h * 0.2), (cx + side * h * 0.6, cy - h * 1.0), (cx + side * h * 0.15, cy - h * 0.45)], fill=o)
            d.polygon([(cx + side * h * 0.62, cy - h * 0.35), (cx + side * h * 0.57, cy - h * 0.8), (cx + side * h * 0.3, cy - h * 0.48)], fill=(250, 200, 200))
        d.ellipse([cx - h * 0.85, cy - h * 0.6, cx + h * 0.85, cy + h * 0.8], fill=o)
        for side in (-1, 1):
            _eye(d, cx + side * h * 0.32, cy, h * 0.1)
            for k in (-1, 1):
                d.line([cx + side * h * 0.25, cy + h * 0.35 + k * 8, cx + side * h * 0.95, cy + h * 0.28 + k * 22], fill=DARK, width=3)
        d.polygon([(cx - 12, cy + h * 0.22), (cx + 12, cy + h * 0.22), (cx, cy + h * 0.34)], fill=(240, 120, 140))
        d.arc([cx - h * 0.2, cy + h * 0.25, cx + h * 0.2, cy + h * 0.5], 20, 160, fill=DARK, width=4)
    elif animal == "pig":
        p = (250, 175, 190)
        for side in (-1, 1):
            d.polygon([(cx + side * h * 0.7, cy - h * 0.35), (cx + side * h * 0.85, cy - h * 0.95), (cx + side * h * 0.3, cy - h * 0.6)], fill=_darker(p, 20))
        d.ellipse([cx - h * 0.9, cy - h * 0.7, cx + h * 0.9, cy + h * 0.8], fill=p)
        d.ellipse([cx - h * 0.35, cy + h * 0.05, cx + h * 0.35, cy + h * 0.5], fill=_darker(p, 25))
        for side in (-1, 1):
            d.ellipse([cx + side * h * 0.13 - 9, cy + h * 0.2, cx + side * h * 0.13 + 9, cy + h * 0.36], fill=_darker(p, 80))
            _eye(d, cx + side * h * 0.38, cy - h * 0.2, h * 0.09)
    elif animal == "frog":
        g = (110, 200, 110)
        for side in (-1, 1):
            d.ellipse([cx + side * h * 0.45 - h * 0.3, cy - h * 0.85, cx + side * h * 0.45 + h * 0.3, cy - h * 0.25], fill=g)
            d.ellipse([cx + side * h * 0.45 - h * 0.2, cy - h * 0.75, cx + side * h * 0.45 + h * 0.2, cy - h * 0.35], fill=WHITE)
            _eye(d, cx + side * h * 0.45, cy - h * 0.55, h * 0.1)
        d.ellipse([cx - h, cy - h * 0.5, cx + h, cy + h * 0.75], fill=g)
        d.arc([cx - h * 0.6, cy - h * 0.15, cx + h * 0.6, cy + h * 0.45], 15, 165, fill=DARK, width=6)
        for side in (-1, 1):
            d.ellipse([cx + side * h * 0.72 - 16, cy + h * 0.1, cx + side * h * 0.72 + 16, cy + h * 0.25], fill=(245, 160, 170))


# ---------------- sayma ----------------
def _count_item(d, cx, cy, s, item, t):
    if item in ("apple", "orange"):
        draw_fruit(d, cx, cy, s, item)
    elif item == "star":
        draw_shape(d, cx, cy, s, "star", COLORS["yellow"])
    elif item == "heart":
        draw_shape(d, cx, cy, s, "heart", COLORS["pink"])
    elif item == "balloon":
        draw_balloon(d, cx, cy - s * 0.15, s * 0.9, COLORS["red"], t)


def draw_count(d, cx, cy, n, item, t, t_local, step=0.45, per_row=5, size=None):
    """n adet objeyi sirayla belirtir (sayarken birer birer ortaya cikar)."""
    rows = (n + per_row - 1) // per_row
    s = size or (120 if n > 5 else 150)
    gap = s * 1.15
    shown = min(n, int(t_local / step) + 1)
    for i in range(shown):
        r, c = divmod(i, per_row)
        in_row = min(per_row, n - r * per_row)
        x = cx + (c - (in_row - 1) / 2) * gap
        y = cy + (r - (rows - 1) / 2) * gap * 1.05
        pop = min(1.0, (t_local - i * step) / 0.2) if t_local >= i * step else 0
        _count_item(d, x, y, s * (0.6 + 0.4 * pop), item, t)


# ---------------- ortak giris ----------------
def draw_prop(d, prop, cx, cy, size, t=0.0, t_local=10.0):
    kind = prop.get("kind")
    if kind == "balloon":
        draw_balloon(d, cx, cy, size, COLORS.get(prop["color"], (200, 200, 200)), t)
    elif kind == "shape":
        draw_shape(d, cx, cy, size, prop["shape"], COLORS.get(prop.get("color", "blue"), (200, 200, 200)))
    elif kind == "fruit":
        draw_fruit(d, cx, cy, size, prop["fruit"])
    elif kind == "animal":
        draw_animal(d, cx, cy, size, prop["animal"], t)
    elif kind == "count":
        draw_count(d, cx, cy, int(prop["n"]), prop["item"], t, t_local)


def prop_label(prop) -> tuple[str, tuple]:
    """Objenin yaninda buyuk harflerle yazilacak kelime ve rengi."""
    kind = prop.get("kind")
    if kind == "balloon":
        return prop["color"].upper(), COLORS[prop["color"]]
    if kind == "shape":
        return prop["shape"].upper(), COLORS.get(prop.get("color", "blue"))
    if kind == "fruit":
        return prop["fruit"].upper(), (255, 252, 240)
    if kind == "animal":
        return prop["animal"].upper(), (255, 252, 240)
    if kind == "count":
        return str(prop["n"]), (255, 210, 60)
    return "", (255, 255, 255)


def validate_prop(prop):
    """Claude'dan gelen prop'u ALLOWED'a gore dogrular; gecersizse None dondurur."""
    if not isinstance(prop, dict):
        return None
    kind = prop.get("kind")
    spec = ALLOWED.get(kind)
    if not spec:
        return None
    clean = {"kind": kind}
    for key, allowed_values in spec.items():
        value = prop.get(key)
        if key == "n":
            try:
                value = int(value)
            except (TypeError, ValueError):
                return None
        if key == "color" and kind == "shape" and value is None:
            value = "blue"
        if value not in allowed_values:
            return None
        clean[key] = value
    return clean
