#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Audit des images du site.
#
#   python3 scripts/audit-images.py
#
# Contrôle ce que ni le navigateur ni le contrôle SEO ne voient : une image
# référencée mais absente, un texte alternatif manquant, un fichier trop
# lourd, un nom de fichier qui n'apprend rien à Google Images, un visuel
# livré mais jamais utilisé.
#
# Sortie 1 si un défaut bloquant est trouvé. Les recommandations, elles, ne
# font pas échouer l'audit.
# ---------------------------------------------------------------------------

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PUBLIC = RACINE / "public"

# Un fichier au-delà de ce poids ralentit l'affichage sur une connexion mobile
# moyenne, quel que soit son intérêt visuel.
POIDS_MAX_KO = 250
POIDS_ALERTE_KO = 150

# Noms qui ne décrivent rien : Google Images s'appuie sur le nom du fichier
# comme signal, au même titre que le texte alternatif.
NOMS_GENERIQUES = re.compile(
    r"^(img|image|photo|picture|dsc|dcim|capture|screenshot|sans-titre|untitled)"
    r"[-_ ]?\d*$",
    re.I,
)

ROUGE, JAUNE, VERT, GRAS, FIN = "\033[31m", "\033[33m", "\033[32m", "\033[1m", "\033[0m"


class Audit:
    def __init__(self):
        self.erreurs = []
        self.avertissements = []
        self.notes = []

    def erreur(self, m):
        self.erreurs.append(m)

    def avertit(self, m):
        self.avertissements.append(m)

    def note(self, m):
        self.notes.append(m)


def analyser_balises(html: str):
    """Retourne les balises <img> d'un document, avec leurs attributs."""
    for balise in re.findall(r"<img\b[^>]*>", html, re.I):
        attributs = dict(re.findall(r'([a-zA-Z-]+)="([^"]*)"', balise))
        yield balise, attributs


def main() -> int:
    if not PUBLIC.is_dir():
        sys.exit("public/ absent — lancez d'abord : bash scripts/build.sh")

    a = Audit()
    pages = sorted(PUBLIC.rglob("*.html"))
    utilisees = set()
    total_balises = 0

    # --- 1. Les images posées dans les pages -------------------------------
    for page in pages:
        rel = page.relative_to(PUBLIC)
        html = page.read_text(encoding="utf-8")

        for balise, attr in analyser_balises(html):
            total_balises += 1
            src = attr.get("src", "")
            extrait = balise[:72] + ("…" if len(balise) > 72 else "")

            if not src:
                a.erreur(f"{rel} : <img> sans src — {extrait}")
                continue

            if src.startswith("/"):
                fichier = PUBLIC / src.lstrip("/")
                utilisees.add(src)
                if not fichier.is_file():
                    a.erreur(f"{rel} : image absente du disque — {src}")
            elif src.startswith(("http://", "https://")):
                # Une image chargée depuis un autre domaine échappe à notre
                # contrôle : disponibilité, licence, performance.
                a.avertit(f"{rel} : image externe, à rapatrier — {src}")

            if "alt" not in attr:
                a.erreur(f"{rel} : image sans attribut alt — {src}")
            elif not attr["alt"].strip():
                # alt="" est légitime pour une image purement décorative.
                a.note(f"{rel} : alt vide, image traitée comme décorative — {src}")
            elif len(attr["alt"]) < 12:
                a.avertit(f'{rel} : alt très court ("{attr["alt"]}") — {src}')
            elif len(attr["alt"]) > 160:
                a.avertit(f"{rel} : alt de {len(attr['alt'])} caractères, trop long — {src}")

            if "width" not in attr or "height" not in attr:
                a.erreur(
                    f"{rel} : width/height absents, la page sautera au chargement — {src}"
                )

            if "loading" not in attr and "fetchpriority" not in attr:
                a.avertit(f"{rel} : ni loading ni fetchpriority — {src}")

    # --- 2. Les fichiers présents sur le disque ----------------------------
    extensions = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".svg", ".gif", ".ico"}
    fichiers = [
        f
        for f in sorted((PUBLIC / "assets").rglob("*"))
        if f.is_file() and f.suffix.lower() in extensions
    ]

    poids_total = 0
    for f in fichiers:
        rel_web = "/" + str(f.relative_to(PUBLIC))
        ko = f.stat().st_size // 1024
        poids_total += f.stat().st_size

        if ko > POIDS_MAX_KO:
            a.erreur(f"{rel_web} : {ko} Ko, au-delà de {POIDS_MAX_KO} Ko")
        elif ko > POIDS_ALERTE_KO:
            a.avertit(f"{rel_web} : {ko} Ko, à compresser si possible")

        if NOMS_GENERIQUES.match(f.stem):
            a.avertit(
                f"{rel_web} : nom de fichier sans signification, "
                "Google Images s'appuie dessus"
            )

        # Certains fichiers ne sont jamais posés en <img> dans une page :
        #   - icônes, favicons et vignettes sociales, référencés dans <head> ;
        #   - ressources d'une bibliothèque tierce (Leaflet), chargées par sa
        #     propre feuille de style au moment où le visiteur ouvre la carte
        #     détaillée.
        # Les compter comme inutilisés serait un faux positif.
        exempt = any(
            p in rel_web
            for p in ("/img/favicon", "/img/icone-", "/img/apple-touch",
                      "/images/og/", "/img/og-", "/vendor/")
        )
        if rel_web not in utilisees and not exempt:
            a.note(f"{rel_web} : présent mais utilisé dans aucune page")

    # --- 3. Les vignettes de partage social --------------------------------
    for page in pages:
        rel = page.relative_to(PUBLIC)
        html = page.read_text(encoding="utf-8")
        m = re.search(r'<meta property="og:image" content="([^"]*)"', html)
        if not m:
            a.erreur(f"{rel} : aucune og:image déclarée")
            continue
        chemin = m.group(1).split("//", 1)[-1].split("/", 1)[-1]
        fichier = PUBLIC / chemin
        if not fichier.is_file():
            a.erreur(f"{rel} : og:image introuvable — {m.group(1)}")
        elif fichier.suffix.lower() == ".svg":
            a.erreur(
                f"{rel} : og:image au format SVG, ignoré par les réseaux sociaux — {m.group(1)}"
            )

    # --- Bilan --------------------------------------------------------------
    print(f"\n{GRAS}Audit des images{FIN}")
    print(f"  {total_balises} balises <img> dans {len(pages)} pages")
    print(f"  {len(fichiers)} fichiers image, {poids_total // 1024} Ko au total")

    for titre, liste, couleur, marque in (
        ("Défauts", a.erreurs, ROUGE, "x"),
        ("Avertissements", a.avertissements, JAUNE, "!"),
        ("Remarques", a.notes, JAUNE, "·"),
    ):
        if liste:
            print(f"\n{GRAS}{titre} ({len(liste)}){FIN}")
            for m in liste[:40]:
                print(f"  {couleur}{marque}{FIN} {m}")
            if len(liste) > 40:
                print(f"  … et {len(liste) - 40} autres")

    print()
    if not a.erreurs:
        print(f"  {VERT}Aucun défaut bloquant.{FIN}")
    print()
    return 1 if a.erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
