#!/usr/bin/env python3
"""
get_youtube_token.py
-------------------------------------------------------------------
TEK SEFERLIK yardimci: YouTube'a yukleme icin gereken refresh token'i alir.
Bunu KENDI BILGISAYARINIZDA calistirin (GitHub Actions'ta degil).

Adimlar:
  1) Google Cloud Console'dan "OAuth Client ID -> Desktop app" olusturun
     ve inen dosyayi 'client_secret.json' adiyla bu klasore koyun.
  2) pip install -r requirements-youtube.txt
  3) python scripts/get_youtube_token.py
  4) Acilan tarayicida Google hesabinizla izin verin.
  5) Ekrana basilan REFRESH TOKEN'i (+ client id/secret) GitHub secret olarak girin:
        YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

Not: Bu betik token'i diske YAZMAZ; yalnizca ekrana basar (guvenlik).
-------------------------------------------------------------------
"""
import os
import sys

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE", "client_secret.json")


def main() -> None:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("HATA: Paketler yok. Kurun: pip install -r requirements-youtube.txt",
              file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(CLIENT_SECRET_FILE):
        print(f"HATA: '{CLIENT_SECRET_FILE}' bulunamadi.", file=sys.stderr)
        print("      Google Cloud Console -> Credentials -> OAuth Client ID -> Desktop app",
              file=sys.stderr)
        print("      olusturup inen JSON'u bu adla bu klasore koyun.", file=sys.stderr)
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    # access_type=offline + prompt=consent -> refresh_token'in donmesini garanti eder
    try:
        creds = flow.run_local_server(
            port=0, access_type="offline", prompt="consent",
            authorization_prompt_message="Tarayicida su adresi acin: {url}",
        )
    except Exception:  # tarayici acilamayan ortamlar icin konsol akisina dus
        creds = flow.run_console(access_type="offline", prompt="consent")

    if not creds.refresh_token:
        print("HATA: refresh_token alinamadi. Google hesabinizdan bu uygulamanin erisimini",
              file=sys.stderr)
        print("      kaldirip tekrar deneyin (https://myaccount.google.com/permissions).",
              file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 64)
    print("BASARILI ✓  Asagidakileri GitHub secret olarak ekleyin:")
    print("  (Settings -> Secrets and variables -> Actions -> New repository secret)")
    print("=" * 64)
    print(f"YT_CLIENT_ID      = {creds.client_id}")
    print(f"YT_CLIENT_SECRET  = {creds.client_secret}")
    print(f"YT_REFRESH_TOKEN  = {creds.refresh_token}")
    print("=" * 64)
    print("Bu degerleri gizli tutun, kimseyle paylasmayin.")


if __name__ == "__main__":
    main()
