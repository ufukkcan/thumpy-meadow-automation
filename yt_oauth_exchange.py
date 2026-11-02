"""
TEK SEFERLIK YARDIMCI: tarayicidan alinan yetkilendirme kodunu refresh_token'a cevirir
ve token'in HANGI KANALA ait oldugunu yazdirir (yanlis kanala yukleme riskine karsi).
"""
import os

import requests

CLIENT_ID = os.environ["YT_CLIENT_ID"]
CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
CODE = os.environ["YT_AUTH_CODE"].strip()
REDIRECT_URI = "https://ufukkcan.github.io/tiktok-legal-pages/callback.html"

resp = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": CODE,
    "grant_type": "authorization_code", "redirect_uri": REDIRECT_URI,
}, timeout=20)
data = resp.json()
print("HTTP durum kodu:", resp.status_code)

if "refresh_token" not in data:
    print("refresh_token gelmedi. Yanit:", data)
    raise SystemExit(1)

ch = requests.get("https://www.googleapis.com/youtube/v3/channels",
                  params={"part": "snippet", "mine": "true"},
                  headers={"Authorization": f"Bearer {data['access_token']}"}, timeout=20).json()
names = [i["snippet"]["title"] for i in ch.get("items", [])]
print("\n=== BU TOKEN SU KANALA AIT:", ", ".join(names) or "(bulunamadi)", "===")
print("Kanal 'Thumpy Meadow' DEGILSE bu token'i KULLANMA, yetkilendirmeyi tekrarla.\n")
print("=== GITHUB SECRETS'A YT_REFRESH_TOKEN OLARAK EKLE ===")
print(data["refresh_token"])
