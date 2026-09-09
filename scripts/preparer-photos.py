#!/usr/bin/env python3
"""
Prépare une photographie d'intervention pour le site.

    python3 scripts/preparer-photos.py <source> <identifiant du catalogue>

Exemple :

    python3 scripts/preparer-photos.py ~/photos/IMG_2043.jpg HERO

Le script lit src/images.conf, y trouve le chemin et les dimensions attendus
pour cet identifiant, puis écrit le fichier au bon endroit, au bon nom, au bon
format et aux bonnes proportions. Il produit aussi les variantes -800 et -1200
qui alimentent l'attribut srcset.

RECADRAGE — la photo est recadrée « au centre » pour atteindre les proportions
demandées, jamais déformée. Si un cadrage particulier est nécessaire, recadrez
la source à la main avant de lancer le script.

DONNÉES PERSONNELLES — les métadonnées EXIF (dont la position GPS) ne sont pas
recopiées : Pillow ne les transporte pas d'un format à l'autre.
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow est requis :  pip install Pillow")

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = os.path.join(RACINE, "static", "assets", "images")

QUALITE = 82          # WebP : au-delà, le gain visuel ne se voit plus
VARIANTES = (800, 1200)


def entree_catalogue(identifiant):
    with open(os.path.join(RACINE, "src", "images.conf"), encoding="utf-8") as f:
        for ligne in f:
            if not ligne[:1].isupper():
                continue
            champs = ligne.rstrip("\n").split("|")
            if len(champs) >= 7 and champs[0] == identifiant:
                return champs
    return None


def recadrer(image, largeur, hauteur):
    """Recadre au centre pour atteindre exactement les proportions voulues."""
    vise = largeur / hauteur
    actuel = image.width / image.height

    if actuel > vise:                      # source trop large : on rogne les côtés
        neuve = int(image.height * vise)
        marge = (image.width - neuve) // 2
        image = image.crop((marge, 0, marge + neuve, image.height))
    elif actuel < vise:                    # source trop haute : on rogne haut et bas
        neuve = int(image.width / vise)
        marge = (image.height - neuve) // 2
        image = image.crop((0, marge, image.width, marge + neuve))

    return image


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)

    source, identifiant = sys.argv[1], sys.argv[2]

    if not os.path.isfile(source):
        sys.exit(f"Fichier introuvable : {source}")

    champs = entree_catalogue(identifiant)
    if not champs:
        sys.exit(
            f"Identifiant « {identifiant} » absent de src/images.conf.\n"
            "Lancez « bash scripts/verifier-photos.sh » pour voir les emplacements."
        )

    _, chemin, repli, largeur, hauteur, alt_photo, _ = champs[:7]
    if not chemin:
        sys.exit(
            f"L'emplacement {identifiant} n'attend pas encore de photographie.\n"
            "Renseignez sa deuxième colonne dans src/images.conf (voir docs/photos.md)."
        )
    largeur, hauteur = int(largeur), int(hauteur)

    image = Image.open(source)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    image = recadrer(image, largeur, hauteur)

    destination = os.path.join(IMAGES, f"{chemin}.webp")
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    principale = image.resize((largeur, hauteur), Image.LANCZOS)
    principale.save(destination, "WEBP", quality=QUALITE, method=6)
    print(f"  {os.path.relpath(destination, RACINE)}  "
          f"{largeur}×{hauteur}  {os.path.getsize(destination) // 1024} Ko")

    for cible in VARIANTES:
        if cible >= largeur:
            continue
        h = round(hauteur * cible / largeur)
        chemin_variante = os.path.join(IMAGES, f"{chemin}-{cible}.webp")
        image.resize((cible, h), Image.LANCZOS).save(
            chemin_variante, "WEBP", quality=QUALITE, method=6
        )
        print(f"  {os.path.relpath(chemin_variante, RACINE)}  "
              f"{cible}×{h}  {os.path.getsize(chemin_variante) // 1024} Ko")

    print(f"\n  Texte alternatif enregistré pour cet emplacement :\n    « {alt_photo} »")
    print("  Relisez-le : il doit décrire la photographie que vous venez de déposer.")
    print("\n  Puis : bash scripts/build.sh")


if __name__ == "__main__":
    main()
