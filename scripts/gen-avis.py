#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Fabrique les blocs d'avis clients à partir de src/avis.txt.
#
#   python3 scripts/gen-avis.py
#
# POURQUOI GÉNÉRER
#
# Les avis doivent apparaître à plusieurs endroits — accueil, pages de zones,
# pages de villes, pages de prestations, page /avis — mais ils ne doivent
# exister qu'à UN endroit dans le dépôt. Recopier un témoignage dans douze
# pages, c'est douze occasions de le déformer, et un avis déformé n'est plus
# un avis réel. Tout est donc dérivé de src/avis.txt.
#
# PLACEMENT : chaque page reçoit les avis qui la concernent, pas les seize.
# Une page de zone montre les avis de son département, une page de ville ceux
# de sa commune, une page de prestation ceux qui parlent de cette prestation.
# Afficher les mêmes seize témoignages sur soixante-dix pages produirait du
# contenu dupliqué et donnerait l'impression exactement inverse de celle
# recherchée.
#
# CE QUI N'EST PAS ÉMIS, ET POURQUOI
#
# Aucun balisage « aggregateRating ». Une note globale calculée par le site
# lui-même sur ses propres avis relève des avis auto-attribués : Google ne
# les affiche pas en résultat enrichi depuis 2019 et un tel balisage expose à
# une action manuelle. Les avis sont donc décrits individuellement, sur la
# page qui leur est consacrée, et nulle part ailleurs.
# ---------------------------------------------------------------------------

import html
import re
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "src" / "avis.txt"
SORTIE = RACINE / "build" / "avis"

DEPARTEMENTS = {
    "22": "Côtes-d'Armor",
    "29": "Finistère",
    "35": "Ille-et-Vilaine",
    "56": "Morbihan",
    "44": "Loire-Atlantique",
    "49": "Maine-et-Loire",
}


def slug(t):
    t = t.lower()
    for a, b in (("à", "a"), ("â", "a"), ("é", "e"), ("è", "e"), ("ê", "e"),
                 ("ë", "e"), ("î", "i"), ("ï", "i"), ("ô", "o"), ("ù", "u"),
                 ("û", "u"), ("ç", "c")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def lire():
    avis, sans_date = [], []
    for ligne in SOURCE.read_text().splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#"):
            continue
        champs = ligne.split("|")
        if len(champs) != 8:
            print(f"  ! avis ignoré, {len(champs)} colonnes au lieu de 8 : {ligne[:50]}…")
            continue
        i, nom, ville, dep, note, date, sujet, texte = (c.strip() for c in champs)
        if not date:
            sans_date.append(i)
        avis.append({
            "id": i, "nom": nom, "ville": ville, "dep": dep,
            "note": int(note), "date": date, "sujet": sujet, "texte": texte,
        })
    return avis, sans_date


def etoiles(n):
    """Les étoiles sont décoratives : la note est donnée en toutes lettres
    pour les lecteurs d'écran, qui n'ont rien à faire d'une suite de glyphes."""
    return (f'<span class="avis-note" role="img" aria-label="{n} étoiles sur 5">'
            + '<span aria-hidden="true">' + "★" * n + "☆" * (5 - n) + "</span></span>")


def carte(a):
    date = ""
    if a["date"]:
        an, mois, jour = a["date"].split("-")
        noms = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
                "août", "septembre", "octobre", "novembre", "décembre"]
        date = (f'<time class="avis-date" datetime="{a["date"]}">'
                f'Intervention du {int(jour)} {noms[int(mois)]} {an}</time>')
    return f"""      <figure class="avis-carte">
        {etoiles(a['note'])}
        <blockquote><p>{html.escape(a['texte'])}</p></blockquote>
        <figcaption>
          <span class="avis-auteur">{html.escape(a['nom'])}</span>
          <span class="avis-lieu">{html.escape(a['ville'])} ({a['dep']})</span>
          {date}
        </figcaption>
      </figure>"""


PROVENANCE = """      <p class="avis-provenance">
        Ces témoignages nous ont été adressés par des clients après intervention et sont
        reproduits sans modification. Ils ne font l'objet d'aucune vérification par un tiers
        indépendant : ce sont des avis recueillis et publiés par l'entreprise elle-même, et nous
        préférons l'écrire plutôt que de le laisser supposer.
        <a href="/avis">Voir tous les avis</a>.
      </p>"""


def bloc(avis, titre, intro, provenance=True, niveau="h2"):
    if not avis:
        return ""
    cartes = "\n\n".join(carte(a) for a in avis)
    return f"""<div class="avis-bloc">
  <div class="avis-entete">
    <{niveau}>{titre}</{niveau}>
    <p>{intro}</p>
  </div>
  <div class="avis">
{cartes}
  </div>
{PROVENANCE if provenance else ""}
</div>"""


def schema(avis):
    """Décrit les avis de la page qui leur est consacrée. Pas de note globale,
    pas d'émission sur les autres pages : voir l'en-tête du fichier."""
    noeuds = ",\n".join(
        f"""    {{
      "@type": "Review",
      "author": {{ "@type": "Person", "name": "{a['nom']}" }},
      "reviewBody": "{a['texte'].replace(chr(34), chr(39))}",
      "reviewRating": {{ "@type": "Rating", "ratingValue": {a['note']}, "bestRating": 5, "worstRating": 1 }},
      "itemReviewed": {{ "@id": "{{{{BASE_URL}}}}/#entreprise" }}{(chr(44) + chr(10) + '      "datePublished": "' + a['date'] + '"') if a['date'] else ''}
    }}"""
        for a in avis
    )
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "@id": "{{{{BASE_URL}}}}/avis#liste",
  "name": "Avis de clients de {{{{NOM_COMMERCIAL}}}}",
  "numberOfItems": {len(avis)},
  "itemListElement": [
{noeuds}
  ]
}}
</script>"""


def main():
    if not SOURCE.exists():
        print(f"  ! {SOURCE.relative_to(RACINE)} absent : aucun avis généré")
        return 0

    avis, sans_date = lire()
    if not avis:
        print("  ! aucun avis lisible dans src/avis.txt")
        return 0

    if SORTIE.exists():
        shutil.rmtree(SORTIE)
    SORTIE.mkdir(parents=True)

    ecrits = {}

    def ecrire(nom, contenu):
        if contenu:
            (SORTIE / f"{nom}.html").write_text(contenu)
            ecrits[nom] = contenu

    # --- Tous les avis, pour la page dédiée ---------------------------------
    ecrire("tous", bloc(
        avis,
        "Ce que nos clients ont écrit",
        f"{len(avis)} témoignages reçus après intervention, en Bretagne et dans le Grand Ouest.",
    ))
    ecrire("schema", schema(avis))

    # --- Accueil : un avis par département breton ---------------------------
    # Montrer les seize sur l'accueil noierait le message ; un par département
    # dit l'essentiel — l'entreprise intervient bien partout où elle l'annonce.
    selection = []
    for d in ("35", "29", "56", "22"):
        pour_dep = [a for a in avis if a["dep"] == d]
        if pour_dep:
            selection.append(pour_dep[0])
    ecrire("accueil", bloc(
        selection,
        "Ce que nos clients disent",
        "Quatre témoignages reçus après intervention, un par département breton.",
    ))

    # --- Par département ----------------------------------------------------
    for d, nom_dep in DEPARTEMENTS.items():
        pour_dep = [a for a in avis if a["dep"] == d]
        ecrire(f"dep-{d}", bloc(
            pour_dep,
            f"Nos clients en {nom_dep}",
            f"{len(pour_dep)} témoignage{'s' if len(pour_dep) > 1 else ''} "
            f"reçu{'s' if len(pour_dep) > 1 else ''} après intervention dans le département.",
        ))

    # --- Par ville ----------------------------------------------------------
    villes = {}
    for a in avis:
        villes.setdefault(slug(a["ville"]), []).append(a)
    for s, lot in villes.items():
        ecrire(f"ville-{s}", bloc(
            lot,
            f"Nos clients à {lot[0]['ville']}",
            f"{len(lot)} témoignage{'s' if len(lot) > 1 else ''} reçu{'s' if len(lot) > 1 else ''} "
            f"après intervention sur la commune.",
        ))

    # --- Par sujet, pour les pages de prestation ----------------------------
    sujets = {}
    for a in avis:
        sujets.setdefault(a["sujet"], []).append(a)
    for s, lot in sujets.items():
        ecrire(f"sujet-{s}", bloc(
            lot,
            "Ce que nos clients en disent",
            f"{len(lot)} témoignage{'s' if len(lot) > 1 else ''} portant sur ce type d'intervention.",
        ))

    print(f"  ✓ avis : {len(avis)} témoignage(s) → {len(ecrits)} bloc(s) "
          f"({len(villes)} ville(s), {len(sujets)} sujet(s))")
    if sans_date:
        print(f"  ! {len(sans_date)} avis sans date dans src/avis.txt (ids {', '.join(sans_date)}).")
        print("    L'article L111-7-2 du code de la consommation impose d'afficher la date.")
        print("    Renseignez la colonne « date » (AAAA-MM-JJ) : elle s'affichera aussitôt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
