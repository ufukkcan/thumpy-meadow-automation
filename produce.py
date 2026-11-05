"""
Onaylanmis senaryodan tam bolum uretir (7d): seslendirme + gercek hayvan sesleri + sarkilar -> render
(show.py) -> 3 kucuk resim (thumbs.py).
"""
from pathlib import Path


def estimate_minutes(ep: dict) -> float:
    import show
    return show.estimate_seconds(ep) / 60


def produce(ep: dict, work_dir: Path, frames_dir: str | None = None) -> dict:
    import show
    import thumbs
    work_dir.mkdir(parents=True, exist_ok=True)
    video_path = str(work_dir / "episode.mp4")
    res = show.render(ep, work_dir, video_path, frames_dir=frames_dir)
    print(f"Render tamam: {res['total'] / 60:.1f} dakika", flush=True)
    paths, preview = thumbs.make_three(ep, str(work_dir / "thumb"))
    return {"video": video_path, "thumbnails": paths, "thumb_preview": preview, "total": res["total"],
            "chapters": res["chapters"]}
