#!/usr/bin/env python3
"""
youtube_upload.py
-------------------------------------------------------------------
Render edilmis bir videoyu YouTube'a (Short olarak) yukler.

Kimlik bilgileri ORTAM DEGISKENLERINDEN okunur (kod icine sir yazilmaz):
  YT_CLIENT_ID       OAuth client id
  YT_CLIENT_SECRET   OAuth client secret
  YT_REFRESH_TOKEN   Bir kez alinmis refresh token (scripts/get_youtube_token.py)

Meta veri 'youtube_meta.json'dan okunur; su ortam degiskenleri varsa onceligi alir:
  YT_TITLE, YT_DESC, YT_TAGS (virgulle ayrilmis), YT_PRIVACY (private|unlisted|public)

Kullanim:
  python scripts/youtube_upload.py [VIDEO_YOLU]
  (varsayilan: output/cuma_video.mp4)
-------------------------------------------------------------------
"""
import json
import os
import sys

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_URI = "https://oauth2.googleapis.com/token"
DEFAULT_VIDEO = "output/cuma_video.mp4"
META_FILE = "youtube_meta.json"


def die(msg: str, code: int = 1) -> None:
    print(f"HATA: {msg}", file=sys.stderr)
    sys.exit(code)


def load_meta() -> dict:
    meta = {
        "title": "Cuma Mübarek 🤲 Hayırlı Cumalar #Shorts",
        "description": "Hayırlı cumalar 🤲\n\n#CumaMübarek #HayırlıCumalar #Shorts",
        "tags": ["cuma", "cuma mübarek", "hayırlı cumalar", "shorts"],
        "categoryId": "22",
        "privacyStatus": "private",
    }
    if os.path.exists(META_FILE):
        try:
            with open(META_FILE, encoding="utf-8") as fh:
                meta.update({k: v for k, v in json.load(fh).items() if v is not None})
        except (OSError, ValueError) as exc:
            print(f"UYARI: {META_FILE} okunamadi ({exc}); varsayilanlar kullanilacak.",
                  file=sys.stderr)

    # Ortam degiskenleri meta dosyasini gecersiz kilar (workflow girdileri icin)
    if os.getenv("YT_TITLE"):
        meta["title"] = os.environ["YT_TITLE"]
    if os.getenv("YT_DESC"):
        meta["description"] = os.environ["YT_DESC"]
    if os.getenv("YT_TAGS"):
        meta["tags"] = [t.strip() for t in os.environ["YT_TAGS"].split(",") if t.strip()]
    if os.getenv("YT_PRIVACY"):
        meta["privacyStatus"] = os.environ["YT_PRIVACY"].strip()

    # Short olarak islenmesi icin baslik/aciklamada #Shorts bulunsun
    if "#Shorts" not in meta["title"] and "#shorts" not in meta["title"].lower():
        meta["title"] = f"{meta['title']} #Shorts"
    if "#shorts" not in meta["description"].lower():
        meta["description"] = f"{meta['description']}\n#Shorts"

    if meta["privacyStatus"] not in ("private", "unlisted", "public"):
        print(f"UYARI: gecersiz privacyStatus '{meta['privacyStatus']}', 'private' kullaniliyor.",
              file=sys.stderr)
        meta["privacyStatus"] = "private"
    return meta


def build_service():
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        die("Gerekli paketler yok. Kurun: pip install -r requirements-youtube.txt")

    client_id = os.getenv("YT_CLIENT_ID")
    client_secret = os.getenv("YT_CLIENT_SECRET")
    refresh_token = os.getenv("YT_REFRESH_TOKEN")
    missing = [n for n, v in (
        ("YT_CLIENT_ID", client_id),
        ("YT_CLIENT_SECRET", client_secret),
        ("YT_REFRESH_TOKEN", refresh_token),
    ) if not v]
    if missing:
        die("Su ortam degiskenleri/secret'lar eksik: " + ", ".join(missing) +
            "\n      README'deki 'YouTube Otomatik Yukleme Kurulumu' bolumune bakin.")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri=TOKEN_URI,
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload(video_path: str) -> None:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    if not os.path.isfile(video_path):
        die(f"Video bulunamadi: {video_path}\n      Once render adimi calismali (output/ bos).")

    meta = load_meta()
    body = {
        "snippet": {
            "title": meta["title"][:100],  # YouTube baslik siniri 100 karakter
            "description": meta["description"],
            "tags": meta.get("tags", []),
            "categoryId": str(meta.get("categoryId", "22")),
        },
        "status": {
            "privacyStatus": meta["privacyStatus"],
            "selfDeclaredMadeForKids": False,
        },
    }

    print(f">> Yukleniyor : {video_path}")
    print(f">> Baslik     : {body['snippet']['title']}")
    print(f">> Gizlilik   : {body['status']['privacyStatus']}")

    service = build_service()
    media = MediaFileUpload(video_path, mimetype="video/*", chunksize=-1, resumable=True)
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    try:
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"   ... %{int(status.progress() * 100)}")
    except HttpError as exc:
        die(f"YouTube API hatasi: {exc}")

    video_id = response.get("id")
    print("")
    print(f"TAMAM ✓  Video yuklendi: https://youtu.be/{video_id}")
    print(f"         Studio: https://studio.youtube.com/video/{video_id}/edit")
    if body["status"]["privacyStatus"] == "private":
        print("         (Gizli olarak yuklendi — herkese acmak icin Studio'dan public yapin.)")


def main() -> None:
    video_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VIDEO
    upload(video_path)


if __name__ == "__main__":
    main()
