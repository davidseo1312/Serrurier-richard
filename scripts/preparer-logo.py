#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Prépare le logo de l'entreprise pour le site, à partir du fichier fourni.
#
#   python3 scripts/preparer-logo.py chemin/vers/logo-fourni.webp
#
# Le fichier livré est un « lockup » complet : la marque (cadenas, bouclier,
# hermines), le mot-symbole sur trois lignes, et une bande de services en bas.
# Tel quel il est inutilisable dans un en-tête : la bande de services y serait
# illisible, et le fond blanc opaque interdit tout autre fond derrière.
#
# Ce script en tire DEUX fichiers, et rien d'autre :
#
#   logo-serrurier-richard.webp   marque + mot-symbole, bande retirée
#                                 → l'en-tête sur ordinateur
#   logo-marque.webp              la marque seule, carrée
#                                 → l'en-tête sur mobile, et les icônes
#
# Chacun en trois définitions (1x, 2x, 3x) pour les écrans à forte densité.
#
# Le détourage se fait par propagation depuis les bords : seuls les pixels
# blancs REJOINTS DEPUIS L'EXTÉRIEUR deviennent transparents. Le blanc
# enfermé — le trou de serrure au centre du bouclier, les contre-formes des
# lettres — est conservé. Un simple « tout le blanc devient transparent »
# aurait percé le trou de serrure.
#
# Dépendance : Pillow. Volontairement hors du build.
# ---------------------------------------------------------------------------

import sys
from collections import deque
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow est absent. Installez-le avec : pip install Pillow")

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "static" / "assets" / "img"

SEUIL_BLANC = 738          # somme R+G+B au-delà de laquelle on considère blanc
DEFINITIONS = (1, 2, 3)    # 1x, 2x, 3x


def est_blanc(px):
    return px[0] + px[1] + px[2] >= SEUIL_BLANC


def boite_encre(im):
    """Rectangle qui contient tout ce qui n'est pas blanc."""
    L, H = im.size
    px = im.load()
    x0, y0, x1, y1 = L, H, 0, 0
    for y in range(H):
        for x in range(L):
            if not est_blanc(px[x, y]):
                x0 = min(x0, x); y0 = min(y0, y)
                x1 = max(x1, x); y1 = max(y1, y)
    return (x0, y0, x1 + 1, y1 + 1)


def bandes_vides_horizontales(im, mini=15):
    """Les lignes entièrement blanches, regroupées. Sert à séparer le bloc
    principal de la bande de services."""
    L, H = im.size
    px = im.load()
    vides = []
    for y in range(H):
        if all(est_blanc(px[x, y]) for x in range(0, L, 3)):
            vides.append(y)
    groupes = []
    for y in vides:
        if groupes and y == groupes[-1][-1] + 1:
            groupes[-1].append(y)
        else:
            groupes.append([y])
    return [g for g in groupes if len(g) >= mini]


def detourer(im):
    """Rend transparent le blanc atteignable depuis les bords, et lui seul."""
    im = im.convert("RGBA")
    L, H = im.size
    px = im.load()
    vu = bytearray(L * H)
    file = deque()

    def pousser(x, y):
        i = y * L + x
        if not vu[i] and est_blanc(px[x, y]):
            vu[i] = 1
            file.append((x, y))

    for x in range(L):
        pousser(x, 0); pousser(x, H - 1)
    for y in range(H):
        pousser(0, y); pousser(L - 1, y)

    while file:
        x, y = file.popleft()
        px[x, y] = (255, 255, 255, 0)
        if x > 0:     pousser(x - 1, y)
        if x < L - 1: pousser(x + 1, y)
        if y > 0:     pousser(x, y - 1)
        if y < H - 1: pousser(x, y + 1)
    return im


def exporter(im, nom, largeur_base):
    """Écrit les trois définitions. La plus grande n'agrandit jamais la
    source : agrandir une image, c'est la rendre floue."""
    produits = []
    for d in DEFINITIONS:
        largeur = largeur_base * d
        if largeur > im.width:
            largeur = im.width
        hauteur = round(im.height * largeur / im.width)
        suffixe = "" if d == 1 else f"@{d}x"
        chemin = SORTIE / f"{nom}{suffixe}.webp"
        im.resize((largeur, hauteur), Image.LANCZOS).save(
            chemin, "WEBP", quality=92, method=6
        )
        produits.append((chemin, largeur, hauteur))
        if largeur == im.width and d > 1:
            break
    return produits


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage : python3 scripts/preparer-logo.py <logo-fourni>")
    source = Path(sys.argv[1])
    if not source.exists():
        sys.exit(f"Fichier introuvable : {source}")

    im = Image.open(source).convert("RGB")
    print(f"Source : {source.name}  {im.width}×{im.height}")

    boite = boite_encre(im)
    bandes = bandes_vides_horizontales(im.crop(boite))
    if not bandes:
        sys.exit("Aucune séparation trouvée : le fichier n'a pas la forme attendue.")
    coupure = boite[1] + bandes[-1][0]
    print(f"  bloc principal  : y {boite[1]} → {coupure}")
    print(f"  bande retirée   : y {coupure} → {boite[3]}")

    principal = im.crop((boite[0], boite[1], boite[2], coupure))
    principal = principal.crop(boite_encre(principal))
    principal = detourer(principal)
    print(f"  lockup          : {principal.width}×{principal.height}"
          f"  ratio {principal.width / principal.height:.2f}")

    # La marque : tout ce qui précède la plus large colonne vide du lockup.
    px = principal.load()
    colonnes_vides = [
        x for x in range(principal.width)
        if all(px[x, y][3] == 0 for y in range(0, principal.height, 3))
    ]
    groupes = []
    for x in colonnes_vides:
        if groupes and x == groupes[-1][-1] + 1:
            groupes[-1].append(x)
        else:
            groupes.append([x])
    separation = max(groupes, key=len)
    marque = principal.crop((0, 0, separation[0], principal.height))
    bb = marque.getbbox()
    marque = marque.crop(bb)
    print(f"  marque seule    : {marque.width}×{marque.height}"
          f"  ratio {marque.width / marque.height:.2f}")

    produits = exporter(principal, "logo-serrurier-richard", 220)
    produits += exporter(marque, "logo-marque", 64)

    print()
    for chemin, l, h in produits:
        print(f"  {chemin.relative_to(RACINE)} — {l}×{h}, "
              f"{chemin.stat().st_size // 1024 or 1} Ko")
    print(f"\n{len(produits)} fichier(s) produit(s).")


if __name__ == "__main__":
    main()
