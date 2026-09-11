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
# Licence : Inter est sous SIL Open Font License 1.1, qui autorise l'usage
# commercial et l'auto-hébergement. Le fichier de licence est conservé à côté
# de la police, comme l'exige la OFL.
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
# Les fichiers d'origine sont versionnés dans le dépôt : ce script tourne donc
# sans réseau, et sur n'importe quelle machine.
AMONT = RACINE / "src" / "polices"

# INTER, pour tout le site — titres comme texte courant.
#
# Une seule famille, et c'est un choix, pas une économie. Inter est dessinée
# pour les écrans : hauteur d'x généreuse, formes ouvertes, et surtout des
# lettres qu'on ne confond pas — le I majuscule, le l minuscule et le chiffre 1
# sont trois dessins distincts, ce qui n'est pas le cas de toutes les
# grotesques. Sur un site où l'on lit un numéro de téléphone et des prix,
# cela compte plus que le caractère.
#
# Le fichier est VARIABLE : un seul téléchargement couvre les graisses 100 à
# 900. Les quatre fichiers d'avant (Outfit 400/700, Work Sans 400/700) sont
# remplacés par un seul, plus léger que les quatre réunis.
#
# Le fichier « latin » de Fontsource couvre déjà tout le français, œ et Œ
# compris : le « latin-ext » est inutile ici, et n'est donc pas embarqué.
POLICES = [
    ("inter-latin-wght-normal", "inter-variable"),
]

# Latin de base, supplément latin-1 (accents français), guillemets typographiques,
# tirets cadratins, symboles monétaires, flèches employées dans l'interface.
PLAGES = (
    "U+0020-007E,U+00A0-00FF,U+0152-0153,U+0178,U+02C6,U+2013-2014,"
    "U+2018-201A,U+201C-201E,U+2020-2022,U+2026,U+2030,U+2039-203A,"
    "U+20AC,U+2122,U+2190-2193,U+00D7"
)


def preparer(nom_source: str, nom_sortie: str) -> Path | None:
    chemin = AMONT / f"{nom_source}.woff2"
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
            avant = (AMONT / f"{source}.woff2").stat().st_size
            apres = fichier.stat().st_size
            print(f"  {fichier.name:<22} {apres // 1024:>3} Ko   (source {avant // 1024} Ko)")

    # La OFL impose de distribuer la licence avec les fichiers de police.
    licence = AMONT / "Inter-OFL.txt"
    if licence.exists():
        (SORTIE / "Inter-OFL.txt").write_text(
            licence.read_text(encoding="utf-8"), encoding="utf-8"
        )

    # Les anciennes polices ne servent plus à rien : les laisser dans
    # static/ les ferait publier à chaque déploiement.
    for perime in ("outfit-400.woff2", "outfit-700.woff2",
                   "worksans-400.woff2", "worksans-700.woff2",
                   "Outfit-OFL.txt", "WorkSans-OFL.txt"):
        chemin = SORTIE / perime
        if chemin.exists():
            chemin.unlink()
            print(f"  {perime:<22} retiré")

    print(f"\nPolices prêtes dans {SORTIE.relative_to(RACINE)}/")
