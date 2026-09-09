#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Prépare les polices du site : sous-ensemble latin + WOFF2.
#
#   python3 scripts/generer-polices.py
#
# Script FACULTATIF. Les fichiers qu'il produit sont versionnés dans
# static/assets/fonts/ : le site se construit et se déploie sans lui.
# À relancer uniquement si l'on change de police.
#
# Pourquoi auto-héberger plutôt que Google Fonts :
#   - zéro requête vers un domaine tiers, donc zéro résolution DNS et zéro
#     négociation TLS supplémentaires avant le premier rendu du texte ;
#   - aucune dépendance à un service extérieur pour afficher le site ;
#   - la Content-Security-Policy du .htaccess peut rester stricte
#     (style-src 'self'), sans ouvrir de domaine externe.
#
# Le sous-ensemble ne conserve que le latin et les diacritiques utiles au
# français : cela divise le poids par trois environ.
#
# Dépendance : fonttools[woff]  (pip install "fonttools[woff]" brotli)
# Licences : Outfit et Work Sans sont sous SIL Open Font License 1.1, qui
# autorise l'usage commercial et l'auto-hébergement. Les fichiers de licence
# sont conservés à côté des polices, comme l'exige la OFL.
# ---------------------------------------------------------------------------

import sys
from pathlib import Path

try:
    from fontTools.ttLib import TTFont
    from fontTools.subset import Subsetter, Options, parse_unicodes
except ImportError:
    sys.exit('fonttools est absent. Installez-le : pip install "fonttools[woff]" brotli')

RACINE = Path(__file__).resolve().parent.parent
SOURCE = Path("/mnt/skills/examples/canvas-design/canvas-fonts")
SORTIE = RACINE / "static" / "assets" / "fonts"

# Outfit pour les titres — géométrique, contemporaine, très lisible en gros.
# Work Sans pour le texte courant — dessinée pour les longues lectures.
POLICES = [
    ("Outfit-Regular", "outfit-400"),
    ("Outfit-Bold", "outfit-700"),
    ("WorkSans-Regular", "worksans-400"),
    ("WorkSans-Bold", "worksans-700"),
]

# Latin de base, supplément latin-1 (accents français), guillemets typographiques,
# tirets cadratins, symboles monétaires, flèches employées dans l'interface.
PLAGES = (
    "U+0020-007E,U+00A0-00FF,U+0152-0153,U+0178,U+02C6,U+2013-2014,"
    "U+2018-201A,U+201C-201E,U+2020-2022,U+2026,U+2030,U+2039-203A,"
    "U+20AC,U+2122,U+2190-2193,U+00D7"
)


def preparer(nom_source: str, nom_sortie: str) -> Path | None:
    chemin = SOURCE / f"{nom_source}.ttf"
    if not chemin.exists():
        print(f"  police introuvable : {chemin}")
        return None

    options = Options()
    options.layout_features = ["kern", "liga", "calt", "ccmp", "locl"]
    options.desubroutinize = True
    options.name_IDs = ["*"]
    options.notdef_outline = True

    fonte = TTFont(chemin)
    sous_ensemble = Subsetter(options=options)
    sous_ensemble.populate(unicodes=parse_unicodes(PLAGES))
    sous_ensemble.subset(fonte)

    fonte.flavor = "woff2"
    destination = SORTIE / f"{nom_sortie}.woff2"
    fonte.save(destination)
    return destination


if __name__ == "__main__":
    SORTIE.mkdir(parents=True, exist_ok=True)

    for source, sortie in POLICES:
        fichier = preparer(source, sortie)
        if fichier:
            avant = (SOURCE / f"{source}.ttf").stat().st_size
            apres = fichier.stat().st_size
            print(f"  {fichier.name:<20} {apres // 1024:>3} Ko   (source {avant // 1024} Ko)")

    # La OFL impose de distribuer la licence avec les fichiers de police.
    for licence in ("Outfit-OFL.txt", "WorkSans-OFL.txt"):
        source = SOURCE / licence
        if source.exists():
            (SORTIE / licence).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  {licence:<20}     licence conservée")

    print(f"\nPolices prêtes dans {SORTIE.relative_to(RACINE)}/")
