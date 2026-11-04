"""
MUZIK MOLASI TESTI (enstrumantal, CC0 kayitli seslerle) -- hicbir yere yukleme yapmaz.

Uretir:  out/music_test.mp3          (Twinkle + London Bridge duzenlemesi, ~1 dk)
         out/music_test_report.txt   (olcumler)
Olcer:   1) orneklerin gercek perdesi (beklenenden sapma, cent)
         2) melodi notalarinin vurus izgarasindan sapmasi (ms ve vurus)
         3) ses yuksekligi (LUFS, hedef -14) ve gercek tepe (dBTP, hedef <= -1)
"""
import json
import re
import subprocess
import wave
from pathlib import Path

import numpy as np

import kidsong
import samples

OUT = Path("out")
SONGS = [("twinkle", 6), ("london", 4)]
TARGET_LUFS, TARGET_TP = -14.0, -1.0


def write_wav_stereo(path: Path, x: np.ndarray) -> None:
    peak = np.max(np.abs(x)) or 1.0
    data = (x / peak * 0.89 * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(samples.SR)
        w.writeframes(data.tobytes())


def onset_deviation(stem: np.ndarray, note_times: list, beat: float) -> tuple[float, float, float]:
    """Her notanin beklenen zamanina +-60 ms icinde en guclu enerji artisini bulur.
    Donus: (ortalama |sapma| ms, en buyuk |sapma| ms, en buyuk |sapma| vurus)."""
    hop = int(0.002 * samples.SR)
    n = len(stem) // hop
    e = np.sqrt(np.mean(stem[: n * hop].reshape(n, hop) ** 2, axis=1))
    flux = np.maximum(0.0, np.diff(e, prepend=0.0))
    devs = []
    for _, _, t in note_times:
        a, b = int((t - 0.06) * samples.SR / hop), int((t + 0.06) * samples.SR / hop)
        a, b = max(a, 0), min(b, n)
        k = a + int(np.argmax(flux[a:b]))
        devs.append(k * hop / samples.SR - t)
    d = np.abs(np.array(devs)) * 1000
    return float(d.mean()), float(d.max()), float(d.max() / 1000 / beat)


def loudnorm(src: Path, dst: Path) -> None:
    """Iki gecisli EBU R128 normalizasyonu (YouTube ~-14 LUFS'e ceker)."""
    flt = f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA=11"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", flt + ":print_format=json",
                        "-f", "null", "-"], capture_output=True)
    err = p.stderr.decode(errors="ignore")
    if p.returncode != 0:
        raise RuntimeError("loudnorm 1. gecis basarisiz:\n" + "\n".join(err.splitlines()[-25:]))
    js = json.loads(err[err.rfind("{"): err.rfind("}") + 1])
    second = (f"{flt}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
              f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    samples._run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", second, "-ar", "44100",
                  "-c:a", "libmp3lame", "-b:a", "192k", str(dst)])


def measure_loudness(path: Path) -> tuple[float, float]:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
                        "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True)
    err = p.stderr.decode(errors="ignore")
    if p.returncode != 0 or "Summary:" not in err:
        raise RuntimeError("ebur128 olcumu basarisiz:\n" + "\n".join(err.splitlines()[-25:]))
    summary = err[err.rfind("Summary:"):]
    i = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary).group(1))
    return i, tp


def main() -> None:
    OUT.mkdir(exist_ok=True)
    report = []
    samples.ensure()
    report.append("== 1) Orneklerin perdesi (beklenen ile fark) ==")
    report += samples.pitch_report()

    report.append("\n== 2) Ritim: melodi notalarinin vurus izgarasindan sapmasi ==")
    parts = []
    for key, n_lines in SONGS:
        song = kidsong.arrange(key, n_lines)
        mean_ms, max_ms, max_beat = onset_deviation(song["melody_stem"], song["note_times"], song["beat"])
        report.append(f"{key:8s} {len(song['note_times'])} nota, tempo {60 / song['beat']:.0f} bpm, "
                      f"sure {len(song['audio']) / samples.SR:.1f} sn: ortalama {mean_ms:.1f} ms, "
                      f"en kotu {max_ms:.1f} ms ({max_beat:.3f} vurus)")
        parts += [song["audio"], np.zeros((samples.SR, 2))]

    wav = OUT / "music_test.wav"
    mp3 = OUT / "music_test.mp3"
    write_wav_stereo(wav, np.concatenate(parts))
    loudnorm(wav, mp3)
    lufs, tp = measure_loudness(mp3)
    report.append("\n== 3) Ses yuksekligi (mp3 uzerinde) ==")
    report.append(f"Entegre: {lufs:.1f} LUFS (hedef {TARGET_LUFS}), gercek tepe: {tp:.1f} dBFS (hedef <= {TARGET_TP})")

    text = "\n".join(report)
    print(text)
    (OUT / "music_test_report.txt").write_text(text + "\n", encoding="utf-8")
    print(f"\n{mp3} hazir")


if __name__ == "__main__":
    main()
