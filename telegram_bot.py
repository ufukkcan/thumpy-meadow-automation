"""
Telegram Bot API yardimcilari (duz HTTP, kutuphane yok).
Sadece TELEGRAM_CHAT_ID'den gelen mesajlar/butonlar dikkate alinir.
"""
import json
import os

import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = str(os.environ["TELEGRAM_CHAT_ID"])
API = f"https://api.telegram.org/bot{TOKEN}"


def _call(method: str, data: dict | None = None, files: dict | None = None) -> dict:
    resp = requests.post(f"{API}/{method}", data=data, files=files, timeout=60)
    body = resp.json()
    if not body.get("ok"):
        raise RuntimeError(f"Telegram {method} hatasi: {body}")
    return body["result"]


def _keyboard(buttons):
    """buttons: [[("Yazi", "callback_data"), ...], ...]"""
    if not buttons:
        return None
    return json.dumps({"inline_keyboard": [[{"text": t, "callback_data": c} for t, c in row] for row in buttons]})


def send_message(text: str, buttons=None) -> int:
    data = {"chat_id": CHAT_ID, "text": text[:4000]}
    kb = _keyboard(buttons)
    if kb:
        data["reply_markup"] = kb
    return _call("sendMessage", data)["message_id"]


def edit_message(message_id: int, text: str) -> None:
    try:
        _call("editMessageText", {"chat_id": CHAT_ID, "message_id": message_id, "text": text[:4000]})
    except RuntimeError:
        pass  # mesaj zaten ayniysa ya da silinmisse onemli degil


def send_document(path: str, caption: str = "", buttons=None) -> int:
    data = {"chat_id": CHAT_ID, "caption": caption[:1000]}
    kb = _keyboard(buttons)
    if kb:
        data["reply_markup"] = kb
    with open(path, "rb") as f:
        return _call("sendDocument", data, files={"document": f})["message_id"]


def send_photo(path: str, caption: str = "") -> int:
    with open(path, "rb") as f:
        return _call("sendPhoto", {"chat_id": CHAT_ID, "caption": caption[:1000]}, files={"photo": f})["message_id"]


def get_updates(offset: int | None) -> list[dict]:
    params = {"timeout": 0}
    if offset is not None:
        params["offset"] = offset
    resp = requests.get(f"{API}/getUpdates", params=params, timeout=30).json()
    return resp.get("result", []) if resp.get("ok") else []


def events(updates: list[dict]) -> list[dict]:
    """Guncellemeleri sade olaylara cevirir: {"kind": "text"|"button", "value": ...}"""
    out = []
    for u in updates:
        if "message" in u and str(u["message"]["chat"]["id"]) == CHAT_ID:
            out.append({"kind": "text", "value": u["message"].get("text", "").strip().lower()})
        elif "callback_query" in u:
            cq = u["callback_query"]
            if str(cq["message"]["chat"]["id"]) == CHAT_ID:
                try:
                    _call("answerCallbackQuery", {"callback_query_id": cq["id"]})
                except RuntimeError:
                    pass
                out.append({"kind": "button", "value": cq.get("data", "")})
    return out
