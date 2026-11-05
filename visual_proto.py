"""
Gorsel prototip (todo 7a, K-19): ~40 sn'lik ornek sahne. Uretim koduna dokunmaz, YUKLEME YOK.

Akis: 0. sn sarki nakarati + ziplayan objeler -> Dino selam -> 3 hediye kutusu surprizi
-> sarkiyla kapanis + daire kapanisi.
Once duman testi (tek kare + nesne sayfasi) yapilir ki Skia/resvg hatalari agir vokal
kurulumundan ONCE ortaya ciksin.
Cikti: out/visual_proto.mp4, out/proto_*.png, out/assets_sheet.png, out/visual_proto_report.txt
"""
import math
import os
import subprocess
import time
from pathlib import Path

import numpy as np
from PIL import Image

import assets
import render2 as r

OUT = Path("out")
FPS = 24
SR = 44100
VOICE = os.environ.get("TTS_VOICE", "en-US-AnaNeural")

SONG_KEY = "twinkle"
LYRICS = ["Open up the box with me", "What a big surprise to see"]    # 7 + 7 hece (twinkle)
BOXES = [  # (nesne, cevap cumlesi, anahtar kelime, kelime rengi)
    ("apple", "An apple! A red, red apple!", "apple", r.rgb(230, 60, 60)),
    ("duck", "A duck! Quack, quack, quack!", "duck", r.rgb(230, 170, 20)),
    ("star", "A star! A shiny yellow star!", "star", r.rgb(230, 170, 20)),
]
GREET = "Hi friends! I'm Dino! Let's open the surprise boxes!"
QUESTION = "What's inside the box?"
DANCERS = ["apple", "banana", "duck", "strawberry"]          # sarkida Dino'nun iki yaninda

DINO_C, DINO_L = r.W / 2, 470          # ortada / oyunda solda
DINO_Y = r.GROUND_Y - 175              # govde merkezi (ayaklar zeminde)
BOX_X, BOX_Y = 1250, r.GROUND_Y - 130
REVEAL_Y, REVEAL_SIZE = 470, 380
SHELF = [(170 + i * 185, 150) for i in range(3)]
DANCE_X = [250, 590, 1330, 1670]


def save_png(surface, path):
    Image.frombytes("RGBA", (r.W, r.H), r.frame_bytes(surface)).convert("RGB").save(path)


# ---------------- duman testi ----------------
def smoke(spr):
    t0 = time.time()
    meadow = r.Meadow()
    surf = r.new_surface()
    c = surf.getCanvas()
    meadow.draw(c, 1.0)
    r.dino_shadow(c, DINO_L, r.GROUND_Y)
    r.dino(c, DINO_L, DINO_Y, t=1.0, mouth=0.6, wave=1.0)
    spr.draw(c, "gift", BOX_X, BOX_Y, 260, shadow_y=r.GROUND_Y)
    spr.draw(c, "apple", 1250, REVEAL_Y, REVEAL_SIZE)
    r.sparkles(c, 1250, REVEAL_Y, 0.4, seed=1)
    r.caption(c, "An apple! A red, red apple!", key="apple")
    save_png(surf, OUT / "smoke.png")

    names = list(assets.NAMES)               # nesne sayfasi: resvg'nin Fluent filtrelerini dogru cizdigini gormek icin
    cols, cell = 8, 230
    rows = math.ceil(len(names) / cols)
    surf2 = r.new_surface()
    c2 = surf2.getCanvas()
    c2.clear(r.rgb(235, 240, 245))
    f = r.font(24)
    for i, n in enumerate(names):
        x, y = 40 + (i % cols) * cell + cell / 2, 30 + (i // cols) * (r.H - 60) / rows + 100
        spr.draw(c2, n, x, y, 170)
        c2.drawString(n, x - f.measureText(n) / 2, y + 112, f, r.paint(r.rgb(60, 60, 70)))
    save_png(surf2, OUT / "assets_sheet.png")
    return time.time() - t0


# ---------------- ses ----------------
def _active_rms(x):
    a = x[np.abs(x) > 0.05 * (np.max(np.abs(x)) or 1.0)]
    return float(np.sqrt(np.mean(a ** 2))) if len(a) else 1e-6


def _add(buf, sig, start_s):
    i = int(start_s * SR)
    end = min(len(buf), i + len(sig))
    if i < end:
        buf[i:end] += sig[: end - i]


def tts(text, name):
    import voice
    return voice.synthesize(text, VOICE, str(OUT / f"{name}.mp3"), rate="-5%")


def mouth_track(speech, n_frames):
    """Kare basina agiz acikligi 0..1 (konusma zarfi, hizli acilip yavas kapanir)."""
    hop = SR // FPS
    env = np.array([np.sqrt(np.mean(speech[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(speech) else 0.0
                    for i in range(n_frames)])
    ref = np.percentile(env[env > 1e-4], 90) if np.any(env > 1e-4) else 1.0
    raw = np.clip(env / ref, 0, 1)
    out, v = np.zeros(n_frames), 0.0
    for i, x in enumerate(raw):
        v = x if x > v else v * 0.55
        out[i] = v
    return out


# ---------------- zaman cizelgesi ----------------
def build():
    import kidsong
    import music
    import samples
    import vocal_break
    song, timings, song_dur = vocal_break.render(LYRICS, SONG_KEY)
    beat = kidsong.timing(SONG_KEY, len(LYRICS))[0]

    clips = {"greet": tts(GREET, "greet")}
    for i, (_, ans, _, _) in enumerate(BOXES):
        clips[f"q{i}"] = tts(QUESTION, f"q{i}")
        clips[f"a{i}"] = tts(ans, f"a{i}")

    segs, t = [], 0.0

    def seg(kind, dur, **kw):
        nonlocal t
        segs.append(dict(kind=kind, start=t, dur=dur, **kw))
        t += dur

    seg("song", song_dur, phase="open")
    seg("talk", len(clips["greet"]) / SR + 0.5, clip="greet", text=GREET)
    for i, (name, ans, key, col) in enumerate(BOXES):
        seg("ask", len(clips[f"q{i}"]) / SR + 0.6, clip=f"q{i}", box=i, text=QUESTION)
        seg("open", 1.0, box=i)
        seg("reveal", len(clips[f"a{i}"]) / SR + 0.9, clip=f"a{i}", box=i, text=ans, key=key, key_color=col)
    seg("song", song_dur, phase="close")
    total = t

    n = int(total * SR) + SR
    speech, buf = np.zeros(n), np.zeros(n)
    sfx = np.zeros(n)
    for s in segs:
        if "clip" in s:
            _add(speech, clips[s["clip"]], s["start"] + 0.15)
        if s["kind"] == "song":
            _add(buf, song * (0.9 * _active_rms(np.concatenate(list(clips.values()))) / _active_rms(song)), s["start"])
        if s["kind"] == "ask":
            _add(sfx, samples.hit("boing", 0.5), s["start"] + 0.45)
        if s["kind"] == "open":
            for k in range(7):
                _add(sfx, samples.hit("shaker_down" if k % 2 == 0 else "shaker_up", 0.6), s["start"] + k * 0.12)
        if s["kind"] == "reveal":
            _add(sfx, samples.hit("belltree", 0.5), s["start"])
            for k, m in enumerate((72, 76, 79, 84)):        # "ta-da" glokenspiel arpeji
                _add(sfx, samples.note("glock", m, 0.45, max_dur=0.6), s["start"] + 0.02 + k * 0.07)

    bg = music.background_track(total)
    gain = np.full(len(bg), 0.22)
    for s in segs:                       # sarki sirasinda fon muzigi sussun (yumusak gecis)
        if s["kind"] == "song":
            a, b = int(s["start"] * SR), int((s["start"] + s["dur"]) * SR)
            gain[a:b] = 0.0
    gain = np.convolve(gain, np.ones(SR // 4) / (SR // 4), mode="same")
    nar = _active_rms(speech)
    buf[:len(bg)] += bg * gain * (nar / _active_rms(bg))
    buf += speech + sfx * (nar / (_active_rms(sfx) or 1e-6)) * 0.5

    n_frames = int(total * FPS)
    talk_mouth = mouth_track(speech, n_frames)
    word_starts = [st for _, _, st in timings]
    return dict(segs=segs, total=total, audio=buf[: int(total * SR)], mouth=talk_mouth,
                timings=timings, word_starts=word_starts, beat=beat, song_dur=song_dur)


# ---------------- sahne ----------------
def _seg_at(segs, t):
    for s in segs:
        if s["start"] <= t < s["start"] + s["dur"]:
            return s
    return segs[-1]


def _box_times(segs, i):
    ask = next(s for s in segs if s["kind"] == "ask" and s["box"] == i)
    opn = next(s for s in segs if s["kind"] == "open" and s["box"] == i)
    rev = next(s for s in segs if s["kind"] == "reveal" and s["box"] == i)
    return ask["start"], opn["start"], rev["start"], rev["start"] + rev["dur"]


def _hop(t, beat, t0=0.0):
    ph = max(0.0, (t - t0) / beat)
    frac = ph % 1.0
    return abs(math.sin(math.pi * frac)) * 46, 0.16 * (1 - min(1.0, frac * 5)) ** 2


def draw(c, t, plan, meadow, spr, frame):
    segs, s = plan["segs"], _seg_at(plan["segs"], t)
    tl = t - s["start"]
    mouth = plan["mouth"][min(frame, len(plan["mouth"]) - 1)]

    # kamera: kutu acilirken ve nesne cikarken kutuya yakinlas
    zoom, cam_x = 1.0, 30 * math.sin(t * 0.25)
    if s["kind"] == "open":
        zoom = 1 + 0.10 * r.ease_in_out(tl / s["dur"])
    elif s["kind"] == "reveal":
        zoom = 1 + 0.10 * (1 - r.ease_in_out((tl - 1.4) / 0.8))
    c.save()
    fx, fy = BOX_X - 150, 560
    c.translate(fx, fy)
    c.scale(zoom, zoom)
    c.translate(-fx, -fy)
    meadow.draw(c, t, cam_x)

    # ---- Dino ----
    if s["kind"] == "song":
        hop, squash = _hop(tl, plan["beat"])
        dx = DINO_C if s["phase"] == "open" else DINO_L + (DINO_C - DINO_L) * r.ease_in_out(tl / 0.6)
        sm = [math.exp(-(tl - st) / 0.18) for st in plan["word_starts"] if st <= tl]
        r.dino_shadow(c, dx, r.GROUND_Y, lift=hop)
        r.dino(c, dx, DINO_Y - hop, t=t, mouth=max(sm) if sm else 0.0, squash=squash,
               excited=(s["phase"] == "open" and tl < 0.8))
    else:
        first_ask = next(x for x in segs if x["kind"] == "ask")["start"]
        k = r.ease_in_out((t - first_ask) / 0.6)
        dx = DINO_C + (DINO_L - DINO_C) * k
        excited = s["kind"] == "reveal" and tl < 1.6
        hop = abs(math.sin(tl * 7)) * 50 if excited else abs(math.sin(t * 2.2)) * 12
        r.dino_shadow(c, dx, r.GROUND_Y, lift=hop)
        r.dino(c, dx, DINO_Y - hop, t=t, mouth=mouth, excited=excited,
               wave=1.0 if s["kind"] == "talk" else 0.0, look=1.0 if s["kind"] in ("ask", "open") else 0.0)

    # ---- sarki: ziplayan nesneler ----
    if s["kind"] == "song":
        names = DANCERS if s["phase"] == "open" else [b[0] for b in BOXES] + ["gift"]
        for i, (n, x) in enumerate(zip(names, DANCE_X)):
            appear = r.ease_out_back((tl - i * plan["beat"] * 0.5) / 0.45)
            hop, sq = _hop(tl + i * 0.5 * plan["beat"], plan["beat"])
            spr.draw(c, n, x, r.GROUND_Y - 100 - hop * 1.3, 200 * appear, rot=8 * math.sin(t * 4 + i),
                     sx=1 + sq, sy=1 - sq, shadow_y=r.GROUND_Y + 8)
        if s["phase"] == "open":
            r.sparkles(c, DINO_C, 420, tl, seed=5, radius=300, n=12)

    # ---- hediye kutulari ----
    for i, (name, _, _, _) in enumerate(BOXES):
        t_ask, t_open, t_rev, t_end = _box_times(segs, i)
        if t_ask <= t < t_rev:                       # kutu duser, sallanir
            drop = r.ease_out_elastic((t - t_ask) / 0.9)
            y = -300 + (BOX_Y + 300) * drop
            rot, sq = 0.0, 0.0
            if t >= t_open:
                amp = 4 + 14 * (t - t_open)
                rot = amp * math.sin((t - t_open) * 38)
                sq = 0.06 * math.sin((t - t_open) * 30)
            spr.draw(c, "gift", BOX_X, y, 280, rot=rot, sx=1 + sq, sy=1 - sq, shadow_y=r.GROUND_Y)
        if t_rev <= t:
            age = t - t_rev
            r.poof(c, BOX_X, BOX_Y, age)
            r.confetti(c, BOX_X, BOX_Y - 40, age, seed=11 + i)
            if t < t_end:
                k = r.ease_out_back(age / 0.7)
                y = BOX_Y + (REVEAL_Y - BOX_Y) * r.ease_in_out(age / 0.7) + 10 * math.sin(age * 3)
                r.sparkles(c, BOX_X, y, age - 0.15, seed=i, radius=230)
                spr.draw(c, name, BOX_X, y, REVEAL_SIZE * k, rot=6 * math.sin(age * 2.5),
                         shadow_y=r.GROUND_Y)
    c.restore()

    # ---- UI (kamera disi): raf, yazilar, kapanis ----
    for i, (name, _, _, _) in enumerate(BOXES):
        _, _, _, t_end = _box_times(segs, i)
        if t >= t_end and not (s["kind"] == "song" and s["phase"] == "close"):
            k = r.ease_in_out((t - t_end) / 0.6)
            x = BOX_X + (SHELF[i][0] - BOX_X) * k
            y = REVEAL_Y + (SHELF[i][1] - REVEAL_Y) * k
            spr.draw(c, name, x, y + 6 * math.sin(t * 3 + i), REVEAL_SIZE + (150 - REVEAL_SIZE) * k)
    if s["kind"] == "song":
        r.karaoke(c, LYRICS, plan["timings"], tl)
        if s["phase"] == "close":
            r.iris(c, DINO_C, DINO_Y - 60, (tl - (s["dur"] - 1.3)) / 1.2)
    elif "text" in s:
        r.caption(c, s["text"], key=s.get("key"), key_color=s.get("key_color", r.rgb(235, 70, 70)))


# ---------------- render ----------------
def main():
    OUT.mkdir(exist_ok=True)
    spr = r.Sprites()
    report = [f"Fluent commit: {assets.SHA}"]
    report.append(f"Duman testi: {smoke(spr):.1f} sn (out/smoke.png, out/assets_sheet.png)")
    print(report[-1], flush=True)

    t0 = time.time()
    plan = build()
    report.append(f"Ses hazirligi: {time.time() - t0:.0f} sn; toplam sure {plan['total']:.1f} sn; "
                  f"sarki {plan['song_dur']:.1f} sn")
    for s in plan["segs"]:
        report.append(f"  {s['start']:6.2f}  {s['kind']:6s} {s['dur']:5.2f}  {s.get('text', s.get('phase', ''))}")
    print("\n".join(report), flush=True)

    import music
    wav = OUT / "visual_proto.wav"
    music.write_wav(str(wav), plan["audio"])

    meadow = r.Meadow()
    surf = r.new_surface()
    c = surf.getCanvas()
    n_frames = int(plan["total"] * FPS)
    keys = {}
    for s in plan["segs"]:
        mid = s["start"] + s["dur"] * (0.25 if s["kind"] == "reveal" else 0.5)
        keys[int(mid * FPS)] = f"{len(keys):02d}_{s['kind']}"
    keys[int(0.3 * FPS)] = "00a_baslangic"
    keys[n_frames - int(0.6 * FPS)] = "99_kapanis"

    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{r.W}x{r.H}",
         "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
         "-ar", str(SR), "-shortest", str(OUT / "visual_proto.mp4")],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    t1 = time.time()
    try:
        for f in range(n_frames):
            t = f / FPS
            c.clear(r.rgb(0, 0, 0))
            draw(c, t, plan, meadow, spr, f)
            data = r.frame_bytes(surf)
            ff.stdin.write(data)
            if f in keys:
                Image.frombytes("RGBA", (r.W, r.H), data).convert("RGB").save(OUT / f"proto_{keys[f]}.png")
    finally:
        ff.stdin.close()
    err = ff.stderr.read().decode(errors="ignore")
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg hatasi:\n" + err[-1500:])
    spf = (time.time() - t1) / n_frames
    report.append(f"Render: {n_frames} kare, {spf * 1000:.0f} ms/kare -> 12 dk bolum ~"
                  f"{spf * 12 * 60 * FPS / 60:.0f} dk")
    (OUT / "visual_proto_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(report[-1])


if __name__ == "__main__":
    main()
