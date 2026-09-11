#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Contrôle d'indexabilité : ce qu'un moteur voit du site.
#
#   python3 scripts/audit-indexation.py
#
# Il ne juge pas le contenu, il vérifie la mécanique — celle qui, mal réglée,
# fait qu'une page n'apparaît jamais dans Google quelle que soit sa qualité :
#
#   · robots.txt cohérent avec ROBOTS_POLICY, et déclarant le sitemap ;
#   · une balise meta robots sur chaque page ;
#   · une canonique absolue, en https, sans www, qui pointe sur la page
#     elle-même — une canonique qui pointe ailleurs efface la page ;
#   · sitemap et pages indexables qui se correspondent exactement, dans les
#     deux sens : aucune page indexable oubliée, aucune URL fantôme ;
#   · aucune page en noindex présente au sitemap — Google le signale ;
#   · titres et descriptions présents et uniques ;
#   · aucune valeur d'attente entre crochets publiée.
#
# Sortie : code 1 s'il reste un défaut. Aucune dépendance.
# ---------------------------------------------------------------------------

import collections
import os
import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PUBLIC = RACINE / "public"

V, X, G, R = "\033[32mv\033[0m", "\033[31mx\033[0m", "\033[1m", "\033[0m"


def config(cle: str, defaut: str = "") -> str:
    fichier = RACINE / "src" / "config.sh"
    m = re.search(rf'^{cle}="([^"]*)"', fichier.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else defaut


def main() -> int:
    base = config("BASE_URL", "https://example.fr").rstrip("/")
    politique = config("ROBOTS_POLICY", "noindex")
    defauts = []

    pages = sorted(PUBLIC.glob("**/*.html"))
    if not pages:
        print("public/ est vide : lancez d'abord bash scripts/build.sh")
        return 1

    robots = (PUBLIC / "robots.txt").read_text(encoding="utf-8")
    plan = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8")
    urls_plan = re.findall(r"<loc>([^<]+)</loc>", plan)

    # --- robots.txt --------------------------------------------------------
    bloque = re.search(r"^\s*Disallow:\s*/\s*$", robots, re.M) is not None
    if politique == "index":
        if bloque:
            defauts.append("robots.txt interdit tout le site alors que ROBOTS_POLICY=index")
        if f"Sitemap: {base}/sitemap.xml" not in robots:
            defauts.append("robots.txt ne déclare pas le sitemap")
    elif not bloque:
        defauts.append("robots.txt autorise l'exploration alors que ROBOTS_POLICY=noindex")

    # --- page par page -----------------------------------------------------
    indexables, titres, descriptions = {}, collections.Counter(), collections.Counter()
    for page in pages:
        rel = page.relative_to(PUBLIC).as_posix()
        html = page.read_text(encoding="utf-8")

        if rel == "index.html":
            attendue = base + "/"
        elif rel.endswith("/index.html"):
            attendue = f"{base}/{rel[:-len('index.html')]}"
        else:
            attendue = f"{base}/{rel[:-len('.html')]}"

        crochets = re.findall(r"\[[A-ZÀ-Ÿ][^\]]{5,90}\]", html)
        for c in crochets:
            defauts.append(f"{rel} : valeur d'attente publiée — {c}")

        rob = re.search(r'<meta name="robots" content="([^"]*)"', html)
        if not rob:
            defauts.append(f"{rel} : aucune balise meta robots")
            continue

        if not re.search(r'<html[^>]*\slang="', html):
            defauts.append(f"{rel} : <html> sans attribut lang")

        can = re.search(r'<link rel="canonical" href="([^"]+)"', html)
        if not can:
            defauts.append(f"{rel} : aucune canonique")
        elif can.group(1) != attendue:
            defauts.append(f"{rel} : canonique « {can.group(1)} » au lieu de « {attendue} »")

        if "noindex" in rob.group(1):
            if attendue in urls_plan:
                defauts.append(f"{rel} : en noindex mais présente au sitemap")
            continue

        if politique == "index" and "index" not in rob.group(1):
            defauts.append(f"{rel} : ni index ni noindex dans la balise robots")

        indexables[attendue] = rel

        tit = re.search(r"<title>(.*?)</title>", html, re.S)
        des = re.search(r'<meta name="description" content="([^"]*)"', html)
        if not tit or not tit.group(1).strip():
            defauts.append(f"{rel} : titre absent ou vide")
        else:
            titres[re.sub(r"\s+", " ", tit.group(1)).strip()] += 1
        if not des or not des.group(1).strip():
            defauts.append(f"{rel} : meta description absente ou vide")
        else:
            descriptions[des.group(1).strip()] += 1

        if attendue not in urls_plan:
            defauts.append(f"{rel} : indexable mais absente du sitemap")

    for u in urls_plan:
        if u not in indexables:
            defauts.append(f"sitemap : {u} ne correspond à aucune page indexable")

    for t, n in titres.items():
        if n > 1:
            defauts.append(f"titre identique sur {n} pages — « {t[:70]} »")
    for d, n in descriptions.items():
        if n > 1:
            defauts.append(f"meta description identique sur {n} pages — « {d[:70]} »")

    # --- bilan -------------------------------------------------------------
    print(f"\n{G}Audit d'indexation{R}")
    print(f"  politique : {politique}")
    print(f"  {len(pages)} pages · {len(indexables)} indexables · {len(urls_plan)} au sitemap")
    if defauts:
        print(f"\n{G}Défauts ({len(defauts)}){R}")
        for d in defauts[:40]:
            print(f"  {X} {d}")
        if len(defauts) > 40:
            print(f"  … et {len(defauts) - 40} autres")
        return 1
    print(f"\n  {V} Rien ne s'oppose à l'indexation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
