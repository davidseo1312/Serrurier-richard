#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Génère les images matricielles que le format vectoriel ne peut pas couvrir :
# la vignette de partage social et les icônes d'application.
#
#   python3 scripts/generer-images.py
#
# Ce script est FACULTATIF. Les fichiers qu'il produit sont déjà versionnés
# dans static/assets/img/ : le site se construit et se déploie sans lui.
# Relancez-le seulement après avoir changé le nom commercial, la baseline ou
# les couleurs de la marque.
#
# Dépendance : Pillow (pip install Pillow). Volontairement hors du build, qui
# doit rester exécutable avec bash seul.
#
# Le numéro de téléphone n'est PAS incrusté dans la vignette : une image est
# mise en cache des mois par les réseaux sociaux, et un numéro périmé y ferait
# plus de dégâts que son absence.
# ---------------------------------------------------------------------------

import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow est absent. Installez-le avec : pip install Pillow")

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "static" / "assets" / "img"

# --- Charte ----------------------------------------------------------------
BLEU_900 = (7, 29, 51)
BLEU_800 = (11, 42, 74)
BLEU_700 = (18, 60, 104)
AMBRE = (245, 165, 36)
BLANC = (255, 255, 255)
BLEU_CLAIR = (185, 210, 232)

POLICES = [
    "/mnt/skills/examples/canvas-design/canvas-fonts/WorkSans-{poids}.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans{suffixe}.ttf",
]


def police(taille: int, gras: bool = False):
    for gabarit in POLICES:
        chemin = gabarit.format(
            poids="Bold" if gras else "Regular",
            suffixe="-Bold" if gras else "",
        )
        if Path(chemin).exists():
            return ImageFont.truetype(chemin, taille)
    return ImageFont.load_default()


def lire_config(cle: str, defaut: str) -> str:
    """Lit une valeur de src/config.sh, pour que la vignette suive le nom
    commercial sans qu'on ait à l'écrire deux fois."""
    fichier = RACINE / "src" / "config.sh"
    if not fichier.exists():
        return defaut
    trouve = re.search(
        rf'^{cle}="([^"]*)"', fichier.read_text(encoding="utf-8"), re.M
    )
    return trouve.group(1) if trouve and trouve.group(1) else defaut


def degrade(largeur: int, hauteur: int, haut, bas) -> Image.Image:
    """Dégradé vertical, dessiné ligne à ligne."""
    image = Image.new("RGB", (largeur, hauteur), haut)
    pinceau = ImageDraw.Draw(image)
    for y in range(hauteur):
        t = y / max(1, hauteur - 1)
        pinceau.line(
            [(0, y), (largeur, y)],
            fill=tuple(int(haut[i] + (bas[i] - haut[i]) * t) for i in range(3)),
        )
    return image


def dessiner_marque(pinceau, cx: int, cy: int, rayon: int, epaisseur: int, couleur):
    """Le symbole de la marque : anse de cadenas surmontant une tige et son
    ergot — la même forme que le favicon et le logo de l'en-tête."""
    pinceau.ellipse(
        [cx - rayon, cy - rayon, cx + rayon, cy + rayon],
        outline=couleur,
        width=epaisseur,
    )
    tige_haut = cy + rayon
    tige_bas = cy + rayon + int(rayon * 1.75)
    demi = epaisseur // 2
    pinceau.rounded_rectangle(
        [cx - demi, tige_haut, cx + demi, tige_bas], radius=demi, fill=couleur
    )
    ergot_y = tige_bas - int(rayon * 0.55)
    pinceau.rounded_rectangle(
        [cx, ergot_y - demi, cx + int(rayon * 0.85), ergot_y + demi],
        radius=demi,
        fill=couleur,
    )


# --- 1. Vignette de partage social (Open Graph, 1200 x 630) ----------------

def vignette_sociale():
    L, H = 1200, 630
    image = degrade(L, H, BLEU_700, BLEU_900)
    pinceau = ImageDraw.Draw(image, "RGBA")

    # Halo diffus, pour éviter un aplat de couleur trop plat.
    pinceau.ellipse([-160, 120, 620, 900], fill=(42, 107, 168, 40))

    # Filet ambre à gauche : rappelle la charte sans surcharger.
    pinceau.rectangle([0, 0, 14, H], fill=AMBRE)

    dessiner_marque(pinceau, 132, 168, 46, 20, AMBRE)

    nom = lire_config("NOM_COMMERCIAL", "Serrurier")
    baseline = lire_config("BASELINE", "Dépannage serrurerie")
    zone = lire_config("ZONE_COURTE", "")

    pinceau.text((92, 300), nom, font=police(78, gras=True), fill=BLANC)
    pinceau.text((92, 400), baseline, font=police(38), fill=BLEU_CLAIR)

    prestations = "Ouverture de porte · Changement de serrure · Blindage · Après effraction"
    pinceau.text((92, 486), prestations, font=police(25), fill=(150, 180, 210))

    if zone:
        pinceau.text((92, 528), zone, font=police(25, gras=True), fill=AMBRE)

    chemin = SORTIE / "og-default.jpg"
    image.save(chemin, "JPEG", quality=86, optimize=True, progressive=True)
    return chemin


# --- 2. Icônes d'application et favicon ------------------------------------

def icone(taille: int, marge_ratio: float = 0.0) -> Image.Image:
    """Icône carrée. La marge sert aux icônes « maskable » d'Android, dont le
    système rogne les bords : le symbole doit tenir dans le cercle central."""
    image = Image.new("RGB", (taille, taille), BLEU_800)
    pinceau = ImageDraw.Draw(image)

    utile = taille * (1 - 2 * marge_ratio)
    rayon = int(utile * 0.20)
    epaisseur = max(2, int(utile * 0.095))
    cx = taille // 2
    cy = int(taille * 0.40)

    dessiner_marque(pinceau, cx, cy, rayon, epaisseur, AMBRE)
    return image


def icones():
    produits = []

    for taille, nom in ((192, "icone-192.png"), (512, "icone-512.png")):
        chemin = SORTIE / nom
        icone(taille).save(chemin, "PNG", optimize=True)
        produits.append(chemin)

    # Maskable : 20 % de marge de sécurité, comme le recommande la spécification.
    chemin = SORTIE / "icone-512-maskable.png"
    icone(512, marge_ratio=0.20).save(chemin, "PNG", optimize=True)
    produits.append(chemin)

    # iOS n'applique pas de coins arrondis lui-même sur toutes les versions,
    # mais l'image doit rester opaque : pas de transparence ici.
    chemin = SORTIE / "apple-touch-icon.png"
    icone(180).save(chemin, "PNG", optimize=True)
    produits.append(chemin)

    # favicon.ico : repli pour les navigateurs et outils qui ignorent le SVG.
    chemin = SORTIE / "favicon.ico"
    icone(64).save(chemin, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    produits.append(chemin)

    return produits


if __name__ == "__main__":
    SORTIE.mkdir(parents=True, exist_ok=True)
    fichiers = [vignette_sociale()] + icones()
    for f in fichiers:
        print(f"  {f.relative_to(RACINE)} — {f.stat().st_size // 1024} Ko")
    print(f"\n{len(fichiers)} images générées.")
