"""
BOLUM TESTI (yeni muzik molasi uretim hattinda) -- YOUTUBE'A / TELEGRAM'A HICBIR SEY GONDERMEZ.

1) Senaryo: gercek Claude API ile tam senaryo (sabit fikir) -> muzik molalari, hece kontrolu,
   duzeltme turu, aciklamadaki kaynak satiri. -> out/test_script.txt
2) Kisa bolum: ornek bolum (sample_episode, 1 vokalli mola) gercek Ana sesiyle uretim yoluyla
   (produce.produce) render edilir. -> out/episode_test.mp4
3) Olcum: sure, anlatim ve mola ses yuksekligi (LUFS), mola karelerinden goruntuler (PNG).
   -> out/episode_test_report.txt, out/frame_*.png
"""
import json
import os
import re
import subprocess
import time
from pathlib import Path

import generate_episode as gen
import produce
from sample_episode import EPISODE

OUT = Path("out")
IDEA = {"working_title": "Learn Colors with Balloons | Colors for Kids | Thumpy Meadow",
        "summary": "Renkli balonlarla temel renkleri ogrenme",
        "lessons": ["red", "blue", "yellow", "green"]}


def lufs(path: Path, start: float, dur: float) -> float:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{start:.2f}", "-t", f"{dur:.2f}",
                        "-i", str(path), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", p.stderr[p.stderr.rfind("Summary:"):])
    return float(m.group(1)) if m else float("nan")


def frame(path: Path, t: float, name: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1",
                    str(OUT / f"frame_{name}.png")], check=True)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rep = ["== Bolum testi: yeni muzik molasi uretim hattinda (yukleme YOK) =="]

    # 1) senaryo
    if os.environ.get("ANTHROPIC_API_KEY"):
        t = time.time()
        ep = gen.generate_script(IDEA)
        minutes = produce.estimate_minutes(ep)
        (OUT / "test_script.txt").write_text(gen.script_as_text(ep, minutes), encoding="utf-8")
        breaks = gen._breaks(ep)
        rep.append(f"\n1) Senaryo ({time.time() - t:.0f} sn): {ep['title']}, tahmini {minutes:.1f} dk, "
                   f"{len(breaks)} muzik molasi, kalan sarki uyarisi: {len(ep['song_issues'])}")
        for br in breaks:
            rep.append(f"   [{br['melody']}] " + " / ".join(br["lines"]))
        rep += [f"   UYARI: {x}" for x in ep["song_issues"]]
        desc = gen.build_description(ep, [])
        rep.append(f"   Aciklamada kaynak satiri: {'EVET' if 'Lotte V' in desc else 'HAYIR'}")
    else:
        rep.append("\n1) Senaryo: ANTHROPIC_API_KEY yok, atlandi")
    (OUT / "episode_test_report.txt").write_text("\n".join(rep) + "\n", encoding="utf-8")

    # 2) kisa bolum, uretimle ayni yol
    ep = gen.normalize_episode(json.loads(json.dumps(EPISODE)))
    t = time.time()
    res = produce.produce(ep, OUT / "work")
    mp4 = OUT / "episode_test.mp4"
    Path(res["video"]).replace(mp4)
    rep.append(f"\n2) Render: {res['total']:.1f} sn video, {time.time() - t:.0f} sn surdu")

    # 3) olcum: uretimin kendi zaman cizelgesiyle
    timeline, total = res["timeline"], res["total"]
    for seg in timeline:
        a, d = seg["start"], seg["dur"]
        if seg["type"] == "music_break":
            rep.append(f"3) Mola [{seg.get('melody')}] {a:.1f}-{a + d:.1f} sn: {lufs(mp4, a, d):.1f} LUFS, "
                       f"{len(seg['timings'])} karaoke kelimesi")
            for name, tt in (("mola_bas", a + 2.0), ("mola_orta", a + d / 2), ("mola_son", a + d - 3.0)):
                frame(mp4, tt, name)
        else:
            rep.append(f"   Anlatim {a:.1f}-{a + d:.1f} sn: {lufs(mp4, a, d):.1f} LUFS  \"{seg['text'][:40]}\"")
    frame(mp4, timeline[1]["start"] + 1.0, "anlatim")
    rep.append(f"\n   Toplam (dosya): {lufs(mp4, 0, total):.1f} LUFS")
    text = "\n".join(rep)
    (OUT / "episode_test_report.txt").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
