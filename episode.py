"""
Thumpy Meadow bolum uretici (16:9, 1920x1080).

Bolum yapisi (Claude'un yazdigi senaryo):
  sections: [{"title": "...", "segments": [...]}, ...]
  segment tipleri:
    - "narration": {"text": "...", "prop": {...} | null}
    - "music_break": {"lines": ["...", ...]}

Kareler PIL ile cizilip dogrudan ffmpeg'e (stdin) akitilir.
Statik arka plan bir kez cizilip her karede kopyalanir (hiz icin).
"""
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import music
import props
import scene2d as s
import vocal_break

W, H = 1920, 1080
FPS = 24
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

NARRATION_LEAD_IN = 0.25   # segment basladiktan sonra konusma ne zaman baslasin
NARRATION_TAIL = 0.5       # konusma bittikten sonra kisa nefes payi

PROP_X, PROP_Y, PROP_SIZE = 1300, 470, 330
DINO_X_WITH_PROP = 560


# ---------------- arka plan (bir kez cizilir) ----------------
def build_background(w: int = W, h: int = H) -> Image.Image:
    img = Image.new("RGB", (w, h), s.SKY_BOT)
    d = ImageDraw.Draw(img)
    horizon = int(h * 0.62)
    for y in range(horizon):
        r = y / horizon
        d.line([(0, y), (w, y)], fill=tuple(int(s.SKY_TOP[i] + (s.SKY_BOT[i] - s.SKY_TOP[i]) * r) for i in range(3)))
    k = w / W
    for cx, hw, hh, col in ((260, 900, 330, s.HILL_FAR), (1000, 1150, 420, s.HILL_MID), (1720, 900, 320, s.HILL_FAR)):
        d.ellipse([(cx - hw // 2) * k, horizon - hh * k, (cx + hw // 2) * k, horizon + hh * k / 2], fill=col)
    d.rectangle([0, horizon, w, h], fill=s.GROUND)
    d.ellipse([-260 * k, horizon - 50 * k, w + 260 * k, horizon + 180 * k], fill=s.GROUND_DARK)
    s._bush(d, -40 * k, horizon - 50 * k, 1.3 * k, s.TREE_DARK)
    s._bush(d, 1690 * k, horizon - 70 * k, 1.4 * k, s.TREE_DARK)
    s._bush(d, 230 * k, horizon - 5 * k, 0.8 * k, s.TREE_MID)
    return img


def outlined(d, xy, text, font, fill, outline=(70, 50, 25), width=6):
    x, y = xy
    for dx in range(-width, width + 1, 2):
        for dy in range(-width, width + 1, 2):
            if dx * dx + dy * dy <= width * width:
                d.text((x + dx, y + dy), text, font=font, fill=outline)
    d.text((x, y), text, font=font, fill=fill)


def fit_font(d, text, max_w, start=120, minimum=48):
    size = start
    while size > minimum:
        font = ImageFont.truetype(FONT, size)
        if d.textlength(text, font=font) <= max_w:
            return font
        size -= 4
    return ImageFont.truetype(FONT, minimum)


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


def _caption(d, text):
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


def _prop_with_label(d, prop, t, t_local):
    appear = min(1.0, t_local / 0.5)
    y = PROP_Y + (1 - appear) * 500
    props.draw_prop(d, prop, PROP_X, y, PROP_SIZE, t=t, t_local=t_local)
    if appear >= 1.0:
        label, color = props.prop_label(prop)
        if label:
            font = fit_font(d, label, 820, start=120)
            bb = d.textbbox((0, 0), label, font=font)
            outlined(d, (PROP_X - (bb[2] - bb[0]) / 2 - bb[0], 70 - bb[1]), label, font, color, width=8)


def _karaoke(d, lines, timings, t_local):
    """Aktif satiri gosterir; calinmis kelimeler beyaz, o anki kelime sari, gelecekler soluk."""
    played = [(li, wi) for (li, wi, t0) in timings if t0 <= t_local]
    active_line = played[-1][0] if played else 0
    words = lines[active_line].split()
    done = {wi for (li, wi) in played if li == active_line}
    current = max(done) if done else -1

    font = fit_font(d, lines[active_line], W - 200, start=78)
    space = d.textlength(" ", font=font)
    widths = [d.textlength(w, font=font) for w in words]
    x = (W - (sum(widths) + space * (len(words) - 1))) / 2
    for wi, w in enumerate(words):
        if wi == current:
            fill, lift = (255, 210, 60), -12
        elif wi in done:
            fill, lift = (255, 252, 240), 0
        else:
            fill, lift = (215, 230, 240), 0
        outlined(d, (x, 140 + lift), w, font, fill)
        x += widths[wi] + space

    nfont = ImageFont.truetype(FONT, 60)
    for k in range(4):
        nx = 300 + k * 420 + math.sin(t_local * 1.5 + k) * 30
        ny = 110 - ((t_local * 60 + k * 90) % 110)
        outlined(d, (nx, ny), "\u266a", nfont, (255, 255, 255), width=4)


# ---------------- senaryo -> duz segment listesi ----------------
def flatten(episode: dict) -> list[dict]:
    segs = []
    for sec in episode["sections"]:
        for seg in sec["segments"]:
            segs.append({**seg, "section": sec["title"]})
    return segs


def estimate_speech_seconds(text: str) -> float:
    """TTS yokken (yerel test) tahmini sure. Gercek uretimde TTS suresi kullanilir."""
    return len(text.split()) / 2.3 + 0.8


def build_timeline(segments: list[dict], with_audio: bool = False):
    """with_audio=False: sadece zamanlama (senaryo onayinda sure tahmini, hizli).
    with_audio=True: muzik molalarinin sesi de uretilir (vokal: birkac dakika surer)."""
    t = 0.0
    timeline = []
    k = 0
    for i, seg in enumerate(segments):
        if seg["type"] == "narration":
            dur = seg.get("audio_seconds") or estimate_speech_seconds(seg["text"])
            timeline.append({**seg, "index": i, "start": t, "dur": dur})
        else:
            key = seg.get("melody") or vocal_break.melody_for(k)
            k += 1
            if with_audio:
                audio, timings, dur = vocal_break.render(seg["lines"], key)
            else:
                audio, timings, dur = None, vocal_break.word_timings(seg["lines"], key), \
                    vocal_break.duration(seg["lines"], key)
            timeline.append({**seg, "index": i, "start": t, "dur": dur, "audio": audio, "timings": timings})
        t += dur
    return timeline, t


def chapters(timeline) -> list[tuple[float, str]]:
    """Her bolum (section) basinin zamani -> YouTube 'chapters' icin.
    YouTube kurallari: ilki 00:00, en az 3 tane, her biri en az 10 sn."""
    out, last = [], None
    for seg in timeline:
        if seg["section"] != last:
            out.append((seg["start"], seg["section"]))
            last = seg["section"]
    cleaned = []
    for i, (start, title) in enumerate(out):
        nxt = out[i + 1][0] if i + 1 < len(out) else float("inf")
        if cleaned and nxt - start < 10:
            continue
        cleaned.append((start, title))
    if cleaned:
        cleaned[0] = (0.0, cleaned[0][1])
    return cleaned if len(cleaned) >= 3 else []


def _active_rms(x: np.ndarray) -> float:
    """Sessiz kisimlar haric RMS (tepe degerin %5'inin ustundeki ornekler)."""
    a = x[np.abs(x) > 0.05 * (np.max(np.abs(x)) or 1.0)]
    return float(np.sqrt(np.mean(a ** 2))) if len(a) else 0.0


def build_audio(timeline, total, narration_audio=None) -> np.ndarray:
    """Fon muzigi (anlatim sirasinda kisik) + muzik molalari + anlatim sesleri."""
    out = np.zeros(int(music.SR * total) + music.SR)
    bg = music.background_track(total)
    gain = np.ones_like(bg) * 0.55
    # muzik molasi seviyesi = anlatim seviyesi (etkin bolumlerin RMS'i); yoksa mola cok sessiz/yuksek kalir
    nar = [s for s in (narration_audio or {}).values() if s is not None and len(s)]
    nar_rms = _active_rms(np.concatenate(nar)) * 0.9 if nar else 0.1
    for seg in timeline:
        if seg["type"] == "music_break":
            a, b = int(seg["start"] * music.SR), int((seg["start"] + seg["dur"]) * music.SR)
            gain[a:b] = 0.0
            brk = seg["audio"]
            music._add(out, brk * (nar_rms / (_active_rms(brk) or 1e-6)), seg["start"])
    out[: len(bg)] += bg * gain[: len(bg)]
    for seg in timeline:
        samples = (narration_audio or {}).get(seg["index"])
        if samples is not None:
            music._add(out, samples * 0.9, seg["start"] + NARRATION_LEAD_IN)
    return out[: int(music.SR * total)]


# ---------------- render ----------------
def render(segments: list[dict], out_mp4: str, audio_wav: str, narration_audio=None):
    """Donus: (toplam_sure, timeline)"""
    timeline, total = build_timeline(segments, with_audio=True)
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
    try:
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
                dino_x = DINO_X_WITH_PROP if prop else W / 2
                bounce = abs(math.sin(t * 2.2)) * 22
                s._dino(d, dino_x, 610 - bounce, scale=1.35, blink=(t % 3.4) > 3.2, arm_swing=t * 3)
                if prop:
                    _prop_with_label(d, prop, t, t_local)
                _caption(d, seg["text"])
            else:
                bounce = abs(math.sin(t * 5.0)) * 45
                s._dino(d, W / 2, 640 - bounce, scale=1.5, blink=False, arm_swing=t * 8)
                _karaoke(d, seg["lines"], seg["timings"], t_local)

            ff.stdin.write(img.tobytes())
    finally:
        ff.stdin.close()
    err = ff.stderr.read().decode(errors="ignore")
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg hatasi:\n" + err[-1500:])
    return total, timeline
