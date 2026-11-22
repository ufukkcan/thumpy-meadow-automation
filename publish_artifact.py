"""
Onceden render edilmis (ve kullanicinin IZLEYIP ONAYLADIGI) bir test ciktisini YouTube'a yukler; yeniden render yok.
Istek: publish/request.json -> {"id", "run_id", "title", "thumbnail"}. Artifact: published_in/ (is akisi indirir).
Ayni istek iki kez yuklenmez (state/published.json). Akis check_and_produce ile ayni: kanal dogrulamasi,
gizli + zamanlanmis (ayni gun, scheduler), made for kids, kucuk resim, Shorts +1/+2 gun, Telegram'a link.
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import generate_episode as gen
import scheduler
import telegram_bot as tg
import upload_youtube as yt

ROOT = Path(__file__).resolve().parent
REQ = ROOT / "publish" / "request.json"
IN = ROOT / "published_in"
DONE = ROOT / "state" / "published.json"


def chapters_from_report(text: str) -> list[tuple[float, str]]:
    line = next((x for x in text.splitlines() if x.startswith("Bolumler:")), "")
    out = []
    for part in line[len("Bolumler:"):].split("|"):
        m = re.match(r"\s*(\d+):(\d{2})\s+(.+?)\s*$", part)
        if m:
            out.append((int(m.group(1)) * 60 + int(m.group(2)), m.group(3)))
    return out


def main() -> None:
    req = json.loads(REQ.read_text(encoding="utf-8"))
    done = json.loads(DONE.read_text(encoding="utf-8")) if DONE.exists() else {}
    if req["id"] in done:
        print(f"Zaten yuklendi: {done[req['id']]}")
        return
    ep = json.loads((IN / "senaryo.json").read_text(encoding="utf-8"))
    chapters = chapters_from_report((IN / "rapor.txt").read_text(encoding="utf-8"))
    if len(chapters) < 3 or chapters[0][0] != 0:
        raise RuntimeError(f"Bolum listesi gecersiz: {chapters}")
    ep["title"] = req["title"]
    description = gen.build_description(ep, chapters)
    localizations = gen.build_localizations(ep, chapters)
    yt.verify_channel()
    publish_at, slot, human = scheduler.next_publish_time()
    video_id = yt.upload(str(IN / "episode.mp4"), ep["title"], description, ep["tags"], publish_at, localizations)
    thumb_ok, thumb_msg = yt.set_thumbnail(video_id, str(ROOT / req["thumbnail"]))
    scheduler.record_upload(video_id, publish_at, slot)
    lines = []
    base = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
    for k, sh in enumerate(sorted(IN.glob("short_*.mp4")), 1):
        try:
            idx = int(sh.stem.split("_")[1])
            meta = gen.short_meta(ep, idx, video_id)
            when = (base + timedelta(days=k)).strftime("%Y-%m-%dT%H:%M:%SZ")
            sid = yt.upload(str(sh), meta["title"], meta["description"], meta["tags"], when)
            lines.append(f"Short {k}: https://youtu.be/{sid} (yayin {when[:10]}) {meta['title']}")
        except Exception as exc:
            lines.append(f"Short {k} yuklenemedi: {str(exc)[:200]}")
    gen.remember_topic(ep["title"])
    gen.remember_story_episode(ep)
    done[req["id"]] = {"video_id": video_id, "publish_at": publish_at, "title": ep["title"], "run_id": req["run_id"]}
    DONE.parent.mkdir(parents=True, exist_ok=True)
    DONE.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    msg = (f"Yuklendi (gizli, zamanlanmis): https://youtu.be/{video_id}\nBaslik: {ep['title']}\n"
           f"Yayin: {human}\n{thumb_msg}\nDil basliklari: {', '.join(localizations) or 'yok'}\n" + "\n".join(lines))
    print(msg)
    try:
        tg.send_photo(str(ROOT / req["thumbnail"]), caption="Kucuk resim (YouTube'a yuklendi)")
        tg.send_message(msg)
    except Exception as exc:
        print(f"Telegram bildirimi gonderilemedi: {exc}")


if __name__ == "__main__":
    main()
