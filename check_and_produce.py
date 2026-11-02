"""
Thumpy Meadow ana akisi (GitHub Actions ~5 dakikada bir calistirir).

  bos/done  -> "video uret" yazilinca ya da AUTO_TRIGGER_TIME gelince: 3 bolum fikri gonder
  choosing  -> fikir secilince: tam senaryoyu yaz, .txt olarak gonder (Onayla / Yeniden yaz)
  reviewing -> Onayla: seslendir + render + kucuk resim + SEO aciklama + zamanli yukleme
               Yeniden yaz: ayni fikirle yeni senaryo
  error     -> "Tekrar dene" butonuyla onaylanmis senaryo yeniden uretilir

COCUK ICERIGI GUVENLIGI: senaryo ASLA otomatik onaylanmaz. Insan onayi olmadan yukleme yok.
"""
import json
import os
import tempfile
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import generate_episode as gen
import scheduler
import telegram_bot as tg
import upload_youtube as yt
from produce import estimate_minutes, produce

STATE_DIR = Path(__file__).resolve().parent / "state"
PENDING = STATE_DIR / "pending.json"
OFFSET = STATE_DIR / "telegram_offset.json"
META = STATE_DIR / "meta.json"

ISTANBUL = ZoneInfo("Europe/Istanbul")
AUTO_TRIGGER_TIME = os.environ.get("AUTO_TRIGGER_TIME", "11:00")
MAX_REWRITES = int(os.environ.get("MAX_REWRITES", "5"))
TRIGGERS = {"video üret", "video uret", "/yeni", "yeni bölüm", "yeni bolum"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _save(path: Path, data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------- adimlar ----------------
def start_cycle(state: dict) -> dict:
    tg.send_message("Yeni Thumpy Meadow bolumu icin fikirler hazirlaniyor...")
    ideas = gen.generate_ideas()
    batch = uuid.uuid4().hex[:8]
    text = ["Bugunun bolum fikirleri -- birini sec:"]
    for i, idea in enumerate(ideas, 1):
        text.append(f"\n{i}) {idea.get('working_title', '')}\n   {idea.get('summary', '')}")
    buttons = [[(f"{i}", f"idea:{batch}:{i - 1}") for i in range(1, len(ideas) + 1)]]
    tg.send_message("\n".join(text), buttons)
    return {"status": "choosing", "batch": batch, "ideas": ideas,
            "trigger_date": datetime.now(ISTANBUL).date().isoformat()}


def send_script(state: dict) -> dict:
    tg.send_message("Senaryo yaziliyor (1-2 dakika)...")
    ep = gen.generate_script(state["idea"])
    minutes = estimate_minutes(ep)
    path = Path(tempfile.gettempdir()) / f"senaryo_{state['batch']}.txt"
    path.write_text(gen.script_as_text(ep, minutes), encoding="utf-8")
    tg.send_document(
        str(path),
        caption=f"{ep['title']}\nTahmini sure: ~{minutes:.1f} dk\n\nLutfen senaryoyu oku. "
                f"Onaylamadan hicbir sey yuklenmez.",
        buttons=[[("Onayla", f"ok:{state['batch']}"), ("Yeniden yaz", f"redo:{state['batch']}")]],
    )
    return {**state, "status": "reviewing", "episode": ep}


def produce_and_upload(state: dict) -> dict:
    ep = state["episode"]
    tg.send_message("Onaylandi! Seslendirme ve video uretimi basladi (yaklasik 30-40 dakika).")
    with tempfile.TemporaryDirectory() as tmp:
        result = produce(ep, Path(tmp))
        description = gen.build_description(ep, result["chapters"])
        publish_at, slot, human = scheduler.next_publish_time()
        video_id = yt.upload(result["video"], ep["title"], description, ep["tags"], publish_at)
        thumb_ok, thumb_msg = yt.set_thumbnail(video_id, result["thumbnail"])
        scheduler.record_upload(video_id, publish_at, slot)
        tg.send_photo(result["thumbnail"], caption="Kucuk resim")
    gen.remember_topic(ep["title"])
    tg.send_message(
        f"Yuklendi (gizli, zamanlanmis): https://youtu.be/{video_id}\n"
        f"Baslik: {ep['title']}\nSure: {result['total'] / 60:.1f} dk\n"
        f"Yayin: {human}\n{thumb_msg}\n\n"
        f"Yayindan once YouTube Studio'da izleyebilirsin; begenmezsen oradan silebilirsin."
    )
    return {**state, "status": "done", "video_id": video_id}


def measure_and_report() -> None:
    """Yayindan 48 saat gecen videolarin izlenmesini olc; haftada bir rapor gonder."""
    for v in scheduler.pending_measurements():
        views = yt.view_count(v["video_id"])
        if views is not None:
            scheduler.store_measurement(v["video_id"], views)
    meta = _load(META)
    last = meta.get("last_report")
    now = datetime.now(timezone.utc)
    if not last or now - datetime.fromisoformat(last) >= timedelta(days=7):
        if Path(scheduler.STATE_FILE).exists():
            tg.send_message(scheduler.report())
        meta["last_report"] = now.isoformat()
        _save(META, meta)


# ---------------- ana dongu ----------------
def handle(state: dict, evts: list[dict]) -> dict:
    texts = [e["value"] for e in evts if e["kind"] == "text"]
    buttons = [e["value"] for e in evts if e["kind"] == "button"]
    batch = state.get("batch")

    if any(t in TRIGGERS for t in texts):
        return start_cycle(state)

    status = state.get("status", "idle")
    if status == "choosing":
        for b in buttons:
            kind, b_batch, *rest = b.split(":")
            if kind == "idea" and b_batch == batch:
                idea = state["ideas"][int(rest[0])]
                tg.send_message(f"Secildi: {idea.get('working_title', '')}")
                return send_script({**state, "idea": idea, "rewrites": 0})
        return state

    if status == "reviewing":
        for b in buttons:
            kind, b_batch, *_ = b.split(":")
            if b_batch != batch:
                continue
            if kind == "ok":
                return produce_and_upload(state)
            if kind == "redo":
                if state.get("rewrites", 0) >= MAX_REWRITES:
                    tg.send_message("Yeniden yazma siniri doldu. Yeni fikirler icin 'video uret' yaz.")
                    return {**state, "status": "idle"}
                return send_script({**state, "rewrites": state.get("rewrites", 0) + 1})
        return state

    if status == "error":
        for b in buttons:
            kind, b_batch, *_ = b.split(":")
            if kind == "retry" and b_batch == batch and state.get("episode"):
                return produce_and_upload(state)

    # aktif dongu yok: gunluk otomatik tetikleme (gunde bir kez)
    today = datetime.now(ISTANBUL).date().isoformat()
    if status in ("idle", "done", "error") and state.get("trigger_date") != today \
            and datetime.now(ISTANBUL).strftime("%H:%M") >= AUTO_TRIGGER_TIME:
        return start_cycle(state)
    return state


def run() -> None:
    offset = _load(OFFSET).get("offset")
    updates = tg.get_updates(offset)
    if updates:
        _save(OFFSET, {"offset": updates[-1]["update_id"] + 1})
    state = _load(PENDING)

    try:
        measure_and_report()
    except Exception:
        traceback.print_exc()

    try:
        new_state = handle(state, tg.events(updates))
    except Exception as exc:
        traceback.print_exc()
        new_state = {**state, "status": "error"}
        buttons = [[("Tekrar dene", f"retry:{state.get('batch')}")]] if state.get("episode") else None
        tg.send_message(f"Hata olustu: {str(exc)[:500]}\n"
                        f"{'Onayli senaryoyu tekrar denemek icin butona bas, ' if buttons else ''}"
                        f"yeni baslamak icin 'video uret' yaz.", buttons)
    _save(PENDING, new_state)


if __name__ == "__main__":
    run()
