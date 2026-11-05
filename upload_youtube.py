"""
YouTube Data API v3 ile yukleme.
- Once kanal dogrulamasi: token "Thumpy Meadow" kanalina ait degilse HICBIR sey yuklenmez
  (bir Google hesabi altinda birden fazla kanal var; bkz. docs/lessons.md).
- selfDeclaredMadeForKids = True (COPPA -- zorunlu)
- Kategori 27 (Education), dil Ingilizce; localizations ile es/pt/tr/id baslik + aciklama
- Gizli yuklenir + publishAt ile zamanlanmis yayin
- Ozel kucuk resim (thumbnails.set; API tek kucuk resim kabul eder)
- 48 saatlik izlenme olcumu (yayin saati ogrenmesi icin)
"""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

CHANNEL_TITLE = "Thumpy Meadow"
CHANNEL_ID = "UC9_bFi-Pyp8hTlclZYkcz-Q"


def _youtube():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def verify_channel() -> None:
    """Token'in bagli oldugu kanal Thumpy Meadow degilse hata (yukleme yapilmaz)."""
    items = _youtube().channels().list(part="snippet", mine=True).execute().get("items", [])
    found = [(it["id"], it["snippet"]["title"]) for it in items]
    if not any(cid == CHANNEL_ID and title == CHANNEL_TITLE for cid, title in found):
        raise RuntimeError(f"YANLIS KANAL: token su kanallara ait: {found}. Yukleme iptal edildi.")


def upload(video_path: str, title: str, description: str, tags: list[str], publish_at_utc: str,
           localizations: dict | None = None) -> str:
    verify_channel()
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": "27",
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at_utc,
            "selfDeclaredMadeForKids": True,
            "embeddable": True,
        },
    }
    parts = "snippet,status"
    if localizations:
        body["localizations"] = localizations
        parts += ",localizations"
    media = MediaFileUpload(video_path, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    request = _youtube().videos().insert(part=parts, body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Yukleniyor: %{int(status.progress() * 100)}")
    return response["id"]


def set_thumbnail(video_id: str, jpg_path: str) -> tuple[bool, str]:
    try:
        _youtube().thumbnails().set(
            videoId=video_id, media_body=MediaFileUpload(jpg_path, mimetype="image/jpeg")
        ).execute()
        return True, "Kucuk resim yuklendi."
    except HttpError as e:
        return False, f"Kucuk resim yuklenemedi: {e.reason if hasattr(e, 'reason') else e}"


def view_count(video_id: str) -> int | None:
    try:
        items = _youtube().videos().list(part="statistics", id=video_id).execute().get("items", [])
        return int(items[0]["statistics"].get("viewCount", 0)) if items else None
    except HttpError:
        return None
