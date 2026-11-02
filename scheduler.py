"""
Yayin saati planlayici.

Hedef kitle: Ingilizce konusan 2-6 yas cocuklar -> en buyuk pazar ABD.
Baslangic varsayimi (genel olarak bilinen izleme oruntuleri, kanala ozel olcum DEGIL):
  - Hafta ici: ogleden sonra / aksamustu yogunluk (kres/okul sonrasi, aksam yemegi oncesi)
  - Hafta sonu: sabah yogunluk
Video, yogunluktan 1-2 saat ONCE yayina girmeli ki YouTube isleyip onermeye baslayabilsin.

Ogrenme: her hafta ici / hafta sonu icin 2 aday saat var. Sistem once her adayi en az
MIN_SAMPLES kez dener, sonra ilk 48 saatte en cok izlenen adayi agirlikli olarak kullanir
(her EXPLORE_EVERY yuklemede bir digerini de denemeye devam eder -- izleyici davranisi degisebilir).
Saatler America/New_York'a gore tanimli; yaz/kis saati gecisleri otomatik hesaplanir.
"""
import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

TARGET_TZ = ZoneInfo("America/New_York")
ISTANBUL = ZoneInfo("Europe/Istanbul")
STATE_FILE = Path(__file__).resolve().parent / "state" / "publish_log.json"

CANDIDATES = {
    "weekday": ["13:00", "15:30"],   # ABD Dogu saati
    "weekend": ["07:00", "09:00"],
}
MIN_SAMPLES = 3
EXPLORE_EVERY = 5
MIN_LEAD = timedelta(hours=1, minutes=30)  # YouTube isleme + zamanlama icin pay


def _load() -> list[dict]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8")).get("videos", [])
    return []


def _save(videos: list[dict]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"videos": videos}, ensure_ascii=False, indent=2), encoding="utf-8")


def _day_type(dt_local: datetime) -> str:
    return "weekend" if dt_local.weekday() >= 5 else "weekday"


def _choose_slot(day_type: str, videos: list[dict]) -> str:
    cands = CANDIDATES[day_type]
    measured = {c: [v["views_48h"] for v in videos
                    if v.get("day_type") == day_type and v.get("slot") == c and v.get("views_48h") is not None]
                for c in cands}
    # 1) yeterli veri yoksa: en az denenen adayi sec (kesif)
    tried = {c: sum(1 for v in videos if v.get("day_type") == day_type and v.get("slot") == c) for c in cands}
    if min(len(m) for m in measured.values()) < MIN_SAMPLES:
        return min(cands, key=lambda c: tried[c])
    # 2) yeterli veri varsa: medyani en yuksek olan (arada bir kesif devam eder)
    best = max(cands, key=lambda c: statistics.median(measured[c]))
    n_this_type = sum(tried.values())
    if n_this_type % EXPLORE_EVERY == EXPLORE_EVERY - 1:
        return next(c for c in cands if c != best)
    return best


def next_publish_time(now_utc: datetime | None = None) -> tuple[str, str, str]:
    """Donus: (publishAt_utc_iso, slot_etiketi, okunakli_aciklama)"""
    now_utc = now_utc or datetime.now(timezone.utc)
    earliest = now_utc + MIN_LEAD
    videos = _load()
    for day_offset in range(0, 8):
        day = (earliest.astimezone(TARGET_TZ) + timedelta(days=day_offset)).date()
        day_type = _day_type(datetime(day.year, day.month, day.day))
        slot = _choose_slot(day_type, videos)
        hh, mm = map(int, slot.split(":"))
        local = datetime(day.year, day.month, day.day, hh, mm, tzinfo=TARGET_TZ)
        if local.astimezone(timezone.utc) >= earliest:
            utc = local.astimezone(timezone.utc)
            ist = local.astimezone(ISTANBUL)
            human = (f"{local.strftime('%a %d %b %H:%M')} ABD Dogu = "
                     f"{ist.strftime('%d %b %H:%M')} Turkiye ({day_type}, aday saat {slot})")
            return utc.strftime("%Y-%m-%dT%H:%M:%SZ"), f"{day_type}:{slot}", human
    raise RuntimeError("Uygun yayin saati bulunamadi.")


def record_upload(video_id: str, publish_at_utc: str, slot_label: str) -> None:
    day_type, slot = slot_label.split(":", 1)
    videos = _load()
    videos.append({"video_id": video_id, "publish_at": publish_at_utc, "day_type": day_type,
                   "slot": slot, "views_48h": None})
    _save(videos)


def pending_measurements(now_utc: datetime | None = None) -> list[dict]:
    """Yayindan 48 saat gecmis ama izlenmesi henuz olculmemis videolar."""
    now_utc = now_utc or datetime.now(timezone.utc)
    out = []
    for v in _load():
        published = datetime.strptime(v["publish_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if v.get("views_48h") is None and now_utc - published >= timedelta(hours=48):
            out.append(v)
    return out


def store_measurement(video_id: str, views: int) -> None:
    videos = _load()
    for v in videos:
        if v["video_id"] == video_id:
            v["views_48h"] = int(views)
    _save(videos)


def report() -> str:
    """Telegram icin kisa ozet: her aday saatin ilk 48 saat izlenme medyani."""
    videos = _load()
    lines = ["Yayin saati raporu (ilk 48 saat izlenme, medyan):"]
    for day_type, cands in CANDIDATES.items():
        for c in cands:
            vals = [v["views_48h"] for v in videos
                    if v["day_type"] == day_type and v["slot"] == c and v.get("views_48h") is not None]
            med = f"{statistics.median(vals):.0f}" if vals else "-"
            lines.append(f"  {day_type} {c} ABD Dogu: {len(vals)} video, medyan {med}")
    return "\n".join(lines)
