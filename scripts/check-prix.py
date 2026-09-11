#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Règle de présentation des prix.
#
#   python3 scripts/check-prix.py
#
# Le site n'affiche QUE des prix de départ. Aucun plafond, aucune fourchette :
# le montant réel dépend de la serrure, de son état et de l'heure, et ne se
# décide qu'une fois le problème constaté sur place.
#
# La raison n'est pas esthétique. Un plafond affiché est lu comme un
# engagement : un client qui a vu « 120 – 250 € » et reçoit une facture de
# 280 € conteste, et il a de bons arguments. Un prix de départ, lui, annonce
# ce qu'il annonce.
#
# Deux montants échappent à la règle, et c'est volontaire : le taux horaire et
# les frais de déplacement. L'arrêté du 24 janvier 2017 impose de les afficher,
# et ce sont des prix fermes — les annoncer « à partir de » les rendrait vagues
# là où la loi demande de la précision.
#
# Sortie : code 1 s'il reste une fourchette. Aucune dépendance.
# ---------------------------------------------------------------------------

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PUBLIC = RACINE / "public"
V, X, G, R = "\033[32mv\033[0m", "\033[31mx\033[0m", "\033[1m", "\033[0m"

# Les trois écritures d'une fourchette. N = un montant, espaces de milliers
# comprises (« 1 500 » s'écrit avec une espace fine insécable dans les pages).
N = r"\d[\d\u00a0\u202f ]*"
FOURCHETTE = re.compile(
    rf"{N}\s*[–—-]\s*{N}\s*€"          # 120 – 250 €
    rf"|\b{N}\s+à\s+{N}\s*€"          # de 120 à 250 €, comptez 120 à 250 €
    rf"|\bentre\s+{N}\s+et\s+{N}\s*€",  # entre 120 et 250 €
    re.I,
)


def main() -> int:
    pages = sorted(PUBLIC.glob("**/*.html"))
    if not pages:
        print("public/ est vide : lancez d'abord bash scripts/build.sh")
        return 1

    defauts = []
    for page in pages:
        rel = page.relative_to(PUBLIC).as_posix()
        texte = re.sub(r"<[^>]+>", " ", page.read_text(encoding="utf-8"))
        texte = re.sub(r"\s+", " ", texte)
        for m in FOURCHETTE.finditer(texte):
            extrait = texte[max(0, m.start() - 60):m.end()].strip()
            defauts.append(f"{rel} : plafond de prix affiché — …{extrait[-72:]}")

    print(f"\n{G}Présentation des prix{R}")
    print(f"  {len(pages)} pages relues")
    if defauts:
        print(f"\n{G}Défauts ({len(defauts)}){R}")
        for d in defauts[:20]:
            print(f"  {X} {d}")
        if len(defauts) > 20:
            print(f"  … et {len(defauts) - 20} autres")
        print("\n  Un prix affiché doit être un prix de DÉPART, jamais une")
        print("  fourchette : un plafond est lu comme un engagement.")
        return 1
    print(f"  {V} Aucun plafond de prix : tous les montants sont des prix de départ.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
