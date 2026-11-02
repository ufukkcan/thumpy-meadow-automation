"""
SES TESTI: ayni ornek bolumu iki farkli sesle uretir, out/ klasorune kaydeder.
GitHub Actions bu videolari "artifact" olarak indirilebilir hale getirir.
YouTube'a ya da baska bir yere HICBIR SEY yuklemez.
"""
import copy
from pathlib import Path

import episode
import voice
from sample_episode import EPISODE

VOICES = {
    "ana_child_voice": "en-US-AnaNeural",
    "jenny_narrator": "en-US-JennyNeural",
}


def build(name: str, voice_id: str, out_dir: Path) -> None:
    ep = copy.deepcopy(EPISODE)
    narration = {}
    for i, seg in enumerate(ep["segments"]):
        if seg["type"] != "narration":
            continue
        samples = voice.synthesize(seg["text"], voice_id, str(out_dir / f"tmp_{name}_{i}.mp3"))
        seg["audio_seconds"] = len(samples) / voice.SR + episode.NARRATION_LEAD_IN + episode.NARRATION_TAIL
        narration[i] = samples
        print(f"  [{name}] segment {i}: {seg['audio_seconds']:.1f} sn")

    total = episode.render(ep, str(out_dir / f"test_{name}.mp4"), str(out_dir / f"tmp_{name}.wav"), narration)
    print(f"{name}: {total:.1f} sn video uretildi")


if __name__ == "__main__":
    out = Path("out")
    out.mkdir(exist_ok=True)
    for name, voice_id in VOICES.items():
        build(name, voice_id, out)
    for tmp in out.glob("tmp_*"):
        tmp.unlink()
