"""
Nesne cizimleri: Microsoft Fluent UI Emoji "Color" SVG seti (MIT, K-19).

- Sabit commit'ten indirilir (raw URL), asset_cache/'e onbelleklenir.
- SVG'ler SVG filtresi (golge, bulaniklik) kullaniyor; en dogru cizen resvg ile PNG'ye cevrilir.
- Lisans metni: licenses/fluentui-emoji-LICENSE (MIT sarti: metin saklanir).
- Kurallar: maskot asla emoji olmaz; bayrak ve marka benzeri semboller kullanilmaz.
"""
import base64
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = "microsoft/fluentui-emoji"
SHA = "1ffb34c752ecf5d402f04cfb4b392c77f57c54bc"
CACHE = Path(__file__).resolve().parent / "asset_cache" / "fluent"

# bizim ad -> Fluent klasor adi (assets/<klasor>/Color/<dosya>_color.svg)
NAMES = {
    "apple": "Red apple", "green_apple": "Green apple", "banana": "Banana", "orange": "Tangerine",
    "strawberry": "Strawberry", "grapes": "Grapes", "pear": "Pear", "watermelon": "Watermelon",
    "duck": "Duck", "fish": "Tropical fish", "bunny": "Rabbit", "cat": "Cat", "pig": "Pig",
    "frog": "Frog", "cow": "Cow", "dog": "Dog", "chick": "Baby chick", "lion": "Lion",
    "elephant": "Elephant", "monkey": "Monkey", "butterfly": "Butterfly",
    "car": "Automobile", "bus": "Bus", "teddy": "Teddy bear", "balloon": "Balloon",
    "gift": "Wrapped gift", "star": "Glowing star", "heart": "Red heart", "sun": "Sun",
    "rainbow": "Rainbow",
    "cake": "Birthday cake", "crown": "Crown",          # 7c: dogum gunu finali (kullanici onayi 11-05)
}


def _path(name: str) -> str:
    folder = NAMES[name]
    return f"assets/{folder}/Color/{folder.lower().replace(' ', '_')}_color.svg"


def svg(name: str) -> str:
    dst = CACHE / (name + ".svg")
    if not (dst.exists() and dst.stat().st_size > 0):
        url = f"https://raw.githubusercontent.com/{REPO}/{SHA}/{urllib.parse.quote(_path(name))}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    dst.write_bytes(r.read())
                break
            except Exception as exc:
                if attempt == 3:
                    raise RuntimeError(f"Indirilemedi: {url}\n{exc}") from exc
                time.sleep(2 * (attempt + 1))
    return dst.read_text(encoding="utf-8")


def png(name: str, px: int) -> bytes:
    """SVG'yi px x px PNG'ye cevirir (resvg). Boyut, kok <svg> etiketinin width/height'i ile verilir."""
    dst = CACHE / f"{name}_{px}.png"
    if dst.exists() and dst.stat().st_size > 0:
        return dst.read_bytes()
    import resvg_py
    text = svg(name)
    head = re.search(r"<svg\b[^>]*>", text).group(0)
    new = re.sub(r'\s(width|height)="[^"]*"', "", head).replace("<svg", f'<svg width="{px}" height="{px}"', 1)
    out = resvg_py.svg_to_bytes(svg_string=text.replace(head, new, 1))
    if isinstance(out, str):           # bazi surumler base64 dondurur
        out = base64.b64decode(out)
    out = bytes(out)
    if out[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"resvg PNG uretmedi: {name}")
    dst.write_bytes(out)
    return out
