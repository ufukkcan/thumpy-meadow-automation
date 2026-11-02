"""
Onaylanmis senaryodan tam bolum uretir: seslendirme -> render -> kucuk resim.
"""
import os
from pathlib import Path

import episode
import thumbnail
import voice

TTS_VOICE = os.environ.get("TTS_VOICE", "en-US-AnaNeural")


def estimate_minutes(ep: dict) -> float:
    _, total = episode.build_timeline(episode.flatten(ep))
    return total / 60


def produce(ep: dict, work_dir: Path) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    segments = episode.flatten(ep)
    narration = {}
    for i, seg in enumerate(segments):
        if seg["type"] != "narration":
            continue
        samples = voice.synthesize(seg["text"], TTS_VOICE, str(work_dir / f"n_{i}.mp3"))
        seg["audio_seconds"] = len(samples) / voice.SR + episode.NARRATION_LEAD_IN + episode.NARRATION_TAIL
        narration[i] = samples
    print(f"Seslendirme tamam: {len(narration)} cumle")

    video_path = str(work_dir / "episode.mp4")
    total, timeline = episode.render(segments, video_path, str(work_dir / "audio.wav"), narration)
    print(f"Render tamam: {total / 60:.1f} dakika")

    thumbs = thumbnail.make_variants(ep["thumbnail_text"], ep["thumbnail_props"], str(work_dir / "thumb"))
    return {"video": video_path, "thumbnails": thumbs, "total": total,
            "chapters": episode.chapters(timeline)}
