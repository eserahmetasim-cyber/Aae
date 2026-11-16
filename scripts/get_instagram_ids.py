#!/usr/bin/env python3
"""
get_instagram_ids.py
-------------------------------------------------------------------
TEK SEFERLIK yardimci: Instagram'a yukleme icin gereken IG_USER_ID ve
uzun omurlu IG_ACCESS_TOKEN degerlerini bulur. KENDI BILGISAYARINIZDA calistirin.

On kosullar:
  - Instagram hesabi Business ya da Creator olmali ve bir Facebook Sayfasina bagli.
  - Meta uygulamaniza su izinler verilmis olmali:
      instagram_basic, instagram_content_publish, pages_show_list, pages_read_engagement

Adimlar:
  1) https://developers.facebook.com/tools/explorer adresinden uygulamanizi secip
     yukaridaki izinlerle KISA OMURLU bir kullanici jetonu uretin.
  2) Calistirin:
       FB_APP_ID=... FB_APP_SECRET=... FB_SHORT_TOKEN=... \
       python3 scripts/get_instagram_ids.py
  3) Ekrana basilan IG_USER_ID ve IG_ACCESS_TOKEN degerlerini GitHub Secrets'a girin.

Not: Betik hicbir seyi diske yazmaz; yalnizca ekrana basar.
-------------------------------------------------------------------
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com"
SURUM = os.getenv("IG_API_SURUM", "v23.0")


def die(msg: str) -> None:
    print(f"HATA: {msg}", file=sys.stderr)
    sys.exit(1)


def al(yol: str, **parametre):
    url = f"{GRAPH}/{SURUM}/{yol}?{urllib.parse.urlencode(parametre)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as yanit:
            return json.loads(yanit.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        ham = exc.read().decode("utf-8", "replace")
        try:
            hata = json.loads(ham).get("error", {})
            die(f"Graph API: {hata.get('message', ham)}")
        except ValueError:
            die(f"Graph API {exc.code}: {ham[:400]}")
    except urllib.error.URLError as exc:
        die(f"Baglanti hatasi: {exc.reason}")


def main() -> None:
    app_id = os.getenv("FB_APP_ID")
    app_secret = os.getenv("FB_APP_SECRET")
    kisa = os.getenv("FB_SHORT_TOKEN")
    eksik = [ad for ad, d in (("FB_APP_ID", app_id), ("FB_APP_SECRET", app_secret),
                              ("FB_SHORT_TOKEN", kisa)) if not d]
    if eksik:
        die("Su ortam degiskenleri eksik: " + ", ".join(eksik) +
            "\n      Kullanim ornegi icin bu dosyanin basindaki aciklamaya bakin.")

    print(">> 1/3 kisa omurlu jeton uzun omurluye cevriliyor")
    uzun = al("oauth/access_token", grant_type="fb_exchange_token",
              client_id=app_id, client_secret=app_secret, fb_exchange_token=kisa)
    uzun_jeton = uzun.get("access_token") or die(f"Uzun omurlu jeton gelmedi: {uzun}")

    print(">> 2/3 sayfalar listeleniyor")
    sayfalar = al("me/accounts", access_token=uzun_jeton, fields="id,name,access_token").get("data", [])
    if not sayfalar:
        die("Hicbir Facebook Sayfasi bulunamadi.\n"
            "      Instagram hesabinizin bir Sayfaya bagli oldugundan ve jetonda\n"
            "      pages_show_list izni bulundugundan emin olun.")

    print(">> 3/3 sayfalara bagli Instagram hesaplari araniyor\n")
    bulundu = 0
    for sayfa in sayfalar:
        bilgi = al(sayfa["id"], access_token=sayfa["access_token"],
                   fields="instagram_business_account{id,username}")
        ig = bilgi.get("instagram_business_account")
        if not ig:
            print(f"   - {sayfa.get('name')} (bagli Instagram hesabi yok)")
            continue
        bulundu += 1
        print("=" * 64)
        print(f"Sayfa     : {sayfa.get('name')}")
        print(f"Instagram : @{ig.get('username', '?')}")
        print("=" * 64)
        print(f"IG_USER_ID      = {ig['id']}")
        print(f"IG_ACCESS_TOKEN = {sayfa['access_token']}")
        print("=" * 64 + "\n")

    if not bulundu:
        die("Sayfalara bagli Instagram Business/Creator hesabi bulunamadi.")
    print("Bu degerleri GitHub Secrets'a girin:")
    print("  Settings -> Secrets and variables -> Actions -> New repository secret")
    print("Jetonu kimseyle paylasmayin, depoya commit etmeyin.")


if __name__ == "__main__":
    main()
