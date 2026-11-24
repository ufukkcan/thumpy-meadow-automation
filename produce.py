"""
Onaylanmis senaryodan tam bolum uretir: seslendirme + sarkilar -> render -> 3 kucuk resim -> 2 dikey Short.
Iki bicim: "stories" anahtari varsa hikaye-sarki bolumu (story.py, H3), yoksa eski saklambac (show.py, 7d).
"""
from pathlib import Path


def _engine(ep: dict):
    if ep.get("format") == "trip":                     # H14: traktor yolculugu (ayni "stories" bicimi)
        import tripshow
        return tripshow
    if ep.get("stories"):
        import story
        return story
    import show
    return show


def estimate_minutes(ep: dict) -> float:
    return _engine(ep).estimate_seconds(ep) / 60


def produce(ep: dict, work_dir: Path, frames_dir: str | None = None) -> dict:
    eng = _engine(ep)
    work_dir.mkdir(parents=True, exist_ok=True)
    video_path = str(work_dir / "episode.mp4")
    res = eng.render(ep, work_dir, video_path, frames_dir=frames_dir)
    print(f"Render tamam: {res['total'] / 60:.1f} dakika", flush=True)
    if ep.get("stories"):
        paths, preview = eng.thumbnails(res["P"], str(work_dir / "thumb"))
    else:
        import thumbs
        paths, preview = thumbs.make_three(ep, str(work_dir / "thumb"))
    try:                                               # Shorts hatasi ana bolumu durdurmaz
        shorts = eng.render_shorts(res["P"], work_dir, n=2, frames_dir=frames_dir)
    except Exception:
        import traceback
        traceback.print_exc()
        shorts = []
    return {"video": video_path, "thumbnails": paths, "thumb_preview": preview, "total": res["total"],
            "chapters": res["chapters"], "shorts": shorts}
