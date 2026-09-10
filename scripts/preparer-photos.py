#!/usr/bin/env python3
"""
Prépare une photographie d'intervention pour le site.

    python3 scripts/preparer-photos.py <source> <identifiant> [cadrage]

Exemple :

    python3 scripts/preparer-photos.py ~/photos/IMG_2043.jpg HERO

Le script lit src/images.conf, y trouve le chemin et les dimensions attendus
pour cet identifiant, puis écrit le fichier au bon endroit, au bon nom, au bon
format et aux bonnes proportions. Il produit aussi les variantes -800 et -1200
qui alimentent l'attribut srcset.

RECADRAGE — la photo est recadrée pour atteindre les proportions demandées,
jamais déformée. Le troisième argument, facultatif, dit où prendre la matière :

    0.5   au centre (défaut)
    0.4   plus haut — garde les têtes quand on retire de la hauteur
    0.6   plus bas — garde le sol et l'outillage

C'est le seul réglage qui évite de couper une tête ou des mains sur une photo
d'intervention, où le sujet n'est presque jamais au centre géométrique.

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
VARIANTES = (600, 1000, 1200)


def entree_catalogue(identifiant):
    with open(os.path.join(RACINE, "src", "images.conf"), encoding="utf-8") as f:
        for ligne in f:
            if not ligne[:1].isupper():
                continue
            champs = ligne.rstrip("\n").split("|")
            if len(champs) >= 7 and champs[0] == identifiant:
                return champs
    return None


def recadrer(image, largeur, hauteur, cadrage=0.5):
    """Recadre aux proportions voulues sans jamais déformer.

    « cadrage » place la fenêtre dans la dimension rognée : 0 en haut ou à
    gauche, 1 en bas ou à droite, 0.5 au centre.
    """
    vise = largeur / hauteur
    actuel = image.width / image.height
    cadrage = min(1.0, max(0.0, cadrage))

    if actuel > vise:                      # source trop large : on rogne les côtés
        neuve = int(image.height * vise)
        marge = int((image.width - neuve) * cadrage)
        image = image.crop((marge, 0, marge + neuve, image.height))
    elif actuel < vise:                    # source trop haute : on rogne haut et bas
        neuve = int(image.width / vise)
        marge = int((image.height - neuve) * cadrage)
        image = image.crop((0, marge, image.width, marge + neuve))

    return image


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)

    source, identifiant = sys.argv[1], sys.argv[2]
    cadrage = float(sys.argv[3]) if len(sys.argv) == 4 else 0.5

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

    image = recadrer(image, largeur, hauteur, cadrage)

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
