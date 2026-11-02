"""
Thumpy Meadow bolum uretici (16:9, 1920x1080).

Bolum = segment listesi:
  - "narration": anlatim metni + istege bagli prop (or. renkli balon)
  - "music_break": ozgun sozler, karaoke tarzi kelime vurgusu, ozgun melodi

Kareler PIL ile cizilip dogrudan ffmpeg'e (stdin) akitilir; diske PNG yazilmaz.
Statik arka plan bir kez cizilip her karede kopyalanir (hiz icin).
"""
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import music
import scene2d as s

W, H = 1920, 1080
FPS = 24
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

COLORS = {
    "red": (235, 70, 70), "blue": (70, 130, 235), "yellow": (250, 205, 50),
    "green": (80, 190, 100), "orange": (250, 150, 50), "purple": (160, 100, 220),
    "pink": (245, 140, 190),
}


# ---------------- arka plan (bir kez cizilir) ----------------
def build_background() -> Image.Image:
    img = Image.new("RGB", (W, H), s.SKY_BOT)
    d = ImageDraw.Draw(img)
    horizon = int(H * 0.62)
    for y in range(horizon):
        r = y / horizon
        d.line([(0, y), (W, y)], fill=tuple(int(s.SKY_TOP[i] + (s.SKY_BOT[i] - s.SKY_TOP[i]) * r) for i in range(3)))
    for cx, w, h, col in ((260, 900, 330, s.HILL_FAR), (1000, 1150, 420, s.HILL_MID), (1720, 900, 320, s.HILL_FAR)):
        d.ellipse([cx - w // 2, horizon - h, cx + w // 2, horizon + h // 2], fill=col)
    d.rectangle([0, horizon, W, H], fill=s.GROUND)
    d.ellipse([-260, horizon - 50, W + 260, horizon + 180], fill=s.GROUND_DARK)
    s._bush(d, -40, horizon - 50, 1.3, s.TREE_DARK)
    s._bush(d, 1690, horizon - 70, 1.4, s.TREE_DARK)
    s._bush(d, 230, horizon - 5, 0.8, s.TREE_MID)
    return img


def _outlined(d, xy, text, font, fill, outline=(70, 50, 25), width=6):
    x, y = xy
    for dx in range(-width, width + 1, 2):
        for dy in range(-width, width + 1, 2):
            if dx * dx + dy * dy <= width * width:
                d.text((x + dx, y + dy), text, font=font, fill=outline)
    d.text((x, y), text, font=font, fill=fill)


def _wrap(d, text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if d.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------- hareketli ogeler ----------------
def _clouds(d, t):
    for base_x, y, sc, sp in ((200, 140, 1.1, 22), (900, 90, 0.8, 15), (1500, 200, 0.9, 28)):
        s._cloud(d, (base_x - t * sp) % (W + 400) - 200, y, sc)


def _balloon(d, cx, cy, color, t):
    bob = math.sin(t * 2.0) * 14
    cy += bob
    r_w, r_h = 120, 150
    # ip
    pts = [(cx + math.sin(t * 2 + k * 0.6) * 10, cy + r_h + k * 28) for k in range(10)]
    d.line(pts, fill=(110, 100, 90), width=4)
    d.polygon([(cx - 14, cy + r_h + 4), (cx + 14, cy + r_h + 4), (cx, cy + r_h - 12)], fill=color)
    d.ellipse([cx - r_w, cy - r_h, cx + r_w, cy + r_h], fill=color)
    d.ellipse([cx - 70, cy - 105, cx - 30, cy - 45], fill=tuple(min(255, c + 70) for c in color))


def _caption(d, text, t):
    font = ImageFont.truetype(FONT, 54)
    lines = _wrap(d, text, font, W - 360)[:2]
    lh = 70
    box_h = lh * len(lines) + 40
    y0 = H - box_h - 40
    d.rounded_rectangle([140, y0, W - 140, y0 + box_h], radius=36, fill=(255, 250, 235))
    for i, line in enumerate(lines):
        bb = d.textbbox((0, 0), line, font=font)
        x = (W - (bb[2] - bb[0])) / 2 - bb[0]
        d.text((x, y0 + 20 + i * lh - bb[1]), line, font=font, fill=(80, 60, 35))


def _karaoke(d, lines, timings, t_local):
    """Aktif satiri gosterir; calinmis kelimeler sari, gelecek kelimeler soluk."""
    font = ImageFont.truetype(FONT, 78)
    played = [(li, wi) for (li, wi, t0) in timings if t0 <= t_local]
    active_line = played[-1][0] if played else 0
    words = lines[active_line].split()
    done = {wi for (li, wi) in played if li == active_line}
    current = max(done) if done else -1

    space = d.textlength(" ", font=font)
    widths = [d.textlength(w, font=font) for w in words]
    total = sum(widths) + space * (len(words) - 1)
    x = (W - total) / 2
    y = 140
    for wi, w in enumerate(words):
        if wi == current:
            fill, lift = (255, 210, 60), -12
        elif wi in done:
            fill, lift = (255, 252, 240), 0
        else:
            fill, lift = (215, 230, 240), 0
        _outlined(d, (x, y + lift), w, font, fill)
        x += widths[wi] + space

    # suzulen nota isaretleri
    nfont = ImageFont.truetype(FONT, 60)
    for k in range(4):
        nx = 300 + k * 420 + math.sin(t_local * 1.5 + k) * 30
        ny = 110 - ((t_local * 60 + k * 90) % 110)
        _outlined(d, (nx, ny), "\u266a", nfont, (255, 255, 255), width=4)


# ---------------- zaman cizelgesi ----------------
def estimate_speech_seconds(text: str) -> float:
    """TTS yokken (yerel test) tahmini sure. GitHub'da gercek TTS suresi kullanilir."""
    return len(text.split()) / 2.4 + 0.8


def build_timeline(episode: dict, seed: int = 7):
    t = 0.0
    timeline = []
    for i, seg in enumerate(episode["segments"]):
        if seg["type"] == "narration":
            dur = seg.get("audio_seconds") or estimate_speech_seconds(seg["text"])
            timeline.append({**seg, "index": i, "start": t, "dur": dur})
        else:
            audio, timings, dur = music.music_break_track(seg["lines"], seed=seed + i)
            timeline.append({**seg, "index": i, "start": t, "dur": dur, "audio": audio, "timings": timings})
        t += dur
    return timeline, t


NARRATION_LEAD_IN = 0.25   # segment basladiktan sonra konusma ne zaman baslasin
NARRATION_TAIL = 0.5       # konusma bittikten sonra kisa nefes payi


def build_audio(timeline, total, narration_audio=None) -> np.ndarray:
    """Fon muzigi (anlatim sirasinda kisik) + muzik molalari + (varsa) anlatim sesleri."""
    out = np.zeros(int(music.SR * total) + music.SR)
    bg = music.background_track(total)
    gain = np.ones_like(bg) * 0.55
    for seg in timeline:
        if seg["type"] == "music_break":
            a, b = int(seg["start"] * music.SR), int((seg["start"] + seg["dur"]) * music.SR)
            gain[a:b] = 0.0
            music._add(out, seg["audio"], seg["start"])
    out[: len(bg)] += bg * gain[: len(bg)]
    for seg in timeline:
        samples = (narration_audio or {}).get(seg["index"])
        if samples is not None:
            music._add(out, samples * 0.9, seg["start"] + NARRATION_LEAD_IN)
    return out[: int(music.SR * total)]


# ---------------- render ----------------
def render(episode: dict, out_mp4: str, audio_wav: str, narration_audio=None) -> float:
    timeline, total = build_timeline(episode)
    music.write_wav(audio_wav, build_audio(timeline, total, narration_audio))

    bg = build_background()
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-i", audio_wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", out_mp4],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    n_frames = int(total * FPS)
    seg_i = 0
    for f in range(n_frames):
        t = f / FPS
        while seg_i < len(timeline) - 1 and t >= timeline[seg_i]["start"] + timeline[seg_i]["dur"]:
            seg_i += 1
        seg = timeline[seg_i]
        t_local = t - seg["start"]

        img = bg.copy()
        d = ImageDraw.Draw(img)
        _clouds(d, t)

        if seg["type"] == "narration":
            prop = seg.get("prop")
            dino_x = 620 if prop else W / 2
            bounce = abs(math.sin(t * 2.2)) * 22
            s._dino(d, dino_x, 610 - bounce, scale=1.35, blink=(t % 3.4) > 3.2, arm_swing=t * 3)
            if prop and prop.get("kind") == "balloon":
                color = COLORS.get(prop["color"], (200, 200, 200))
                appear = min(1.0, t_local / 0.5)
                _balloon(d, 1340, 330 + (1 - appear) * 500, color, t)
                if appear >= 1.0:
                    font = ImageFont.truetype(FONT, 110)
                    label = prop["color"].upper()
                    bb = d.textbbox((0, 0), label, font=font)
                    _outlined(d, (1560 - bb[0], 300), label, font, color, width=8)
            _caption(d, seg["text"], t_local)
        else:
            bounce = abs(math.sin(t * 5.0)) * 45
            s._dino(d, W / 2, 640 - bounce, scale=1.5, blink=False, arm_swing=t * 8)
            _karaoke(d, seg["lines"], seg["timings"], t_local)

        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    err = ff.stderr.read().decode(errors="ignore")
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg hatasi:\n" + err[-1500:])
    return total
