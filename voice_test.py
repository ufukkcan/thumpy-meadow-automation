"""SES TESTI: ornek bolumu secili sesle uretir (out/ klasorune). Hicbir yere yukleme yapmaz."""
import os
from pathlib import Path

import episode
import voice
from sample_episode import EPISODE

VOICE = os.environ.get("TTS_VOICE", "en-US-AnaNeural")

if __name__ == "__main__":
    out = Path("out"); out.mkdir(exist_ok=True)
    segments = episode.flatten(EPISODE)
    narration = {}
    for i, seg in enumerate(segments):
        if seg["type"] == "narration":
            samples = voice.synthesize(seg["text"], VOICE, str(out / f"tmp_{i}.mp3"))
            seg["audio_seconds"] = len(samples) / voice.SR + episode.NARRATION_LEAD_IN + episode.NARRATION_TAIL
            narration[i] = samples
    total, _ = episode.render(segments, str(out / "test_voice.mp4"), str(out / "tmp.wav"), narration)
    for tmp in out.glob("tmp*"):
        tmp.unlink()
    print(f"{total:.1f} sn test videosu uretildi")
