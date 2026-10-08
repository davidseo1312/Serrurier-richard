#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Blocs « guides locaux » pour les six pages de zone.

Le constat qui justifie ce script : le site comptait soixante articles et les
pages départementales — qui sont les pages les plus fortes sur les requêtes
locales — n'en citaient que deux, toujours les mêmes. Un article qui ne reçoit
aucun lien depuis une page importante du site est un article que Google
explore tard et juge peu.

Le script lit les en-têtes des articles, les range par département d'après le
suffixe du nom de fichier (-22, -29, -35, -44, -49, -56), et écrit un fragment
HTML par département. Aucune donnée n'est inventée : le titre et le résumé
sortent des champs « carte_titre » et « carte » déjà rédigés dans l'article.

Déterministe : à contenu identique, sortie identique. Le build peut donc le
relancer à chaque fois sans produire de diff parasite.
"""

from pathlib import Path
import re
import sys

RACINE = Path(__file__).resolve().parent.parent
ARTICLES = RACINE / "src" / "pages" / "blog"
SORTIE = RACINE / "src" / "partials" / "guides"

# Nom du département et sa préposition : « dans les Côtes-d'Armor » mais
# « en Ille-et-Vilaine ». Une règle automatique se tromperait un département
# sur deux, donc la forme est écrite une fois pour toutes.
DEPARTEMENTS = {
    "22": ("Côtes-d'Armor", "dans les Côtes-d'Armor"),
    "29": ("Finistère", "dans le Finistère"),
    "35": ("Ille-et-Vilaine", "en Ille-et-Vilaine"),
    "44": ("Loire-Atlantique", "en Loire-Atlantique"),
    "49": ("Maine-et-Loire", "en Maine-et-Loire"),
    "56": ("Morbihan", "dans le Morbihan"),
}

# Au-delà de ce nombre, le bloc cesse d'être un maillage utile pour devenir un
# annuaire : on garde les plus récents et on renvoie au blog pour le reste.
MAX_PAR_ZONE = 8


def meta(html: str, cle: str) -> str:
    """Valeur d'un champ de l'en-tête <!--meta ... -->, vide si absent."""
    entete = re.search(r"<!--meta(.*?)-->", html, re.S)
    if not entete:
        return ""
    for ligne in entete.group(1).split("\n"):
        if ligne.strip().startswith(cle + ":"):
            return ligne.split(":", 1)[1].strip()
    return ""


def echapper(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def collecter() -> dict:
    par_dep = {num: [] for num in DEPARTEMENTS}
    for fichier in sorted(ARTICLES.glob("*.html")):
        if fichier.name == "index.html":
            continue
        suffixe = fichier.stem[-2:]
        if suffixe not in DEPARTEMENTS:
            continue  # article générique, sans ancrage départemental
        html = fichier.read_text(encoding="utf-8")
        titre = meta(html, "carte_titre") or meta(html, "breadcrumb")
        resume = meta(html, "carte")
        date = meta(html, "date")
        if not titre or not resume:
            print(f"  ! {fichier.name} : carte_titre ou carte manquant, article ignoré")
            continue
        par_dep[suffixe].append(
            {"url": "/blog/" + fichier.stem, "titre": titre, "resume": resume, "date": date}
        )
    for num in par_dep:
        # Les plus récents d'abord ; le slug départage pour rester déterministe.
        par_dep[num].sort(key=lambda a: (a["date"], a["url"]), reverse=True)
    return par_dep


def ecrire(par_dep: dict) -> int:
    SORTIE.mkdir(parents=True, exist_ok=True)
    total = 0
    for num, (nom, situe) in DEPARTEMENTS.items():
        articles = par_dep[num][:MAX_PAR_ZONE]
        if not articles:
            (SORTIE / f"{num}.html").write_text("", encoding="utf-8")
            continue
        lignes = [
            f'    <h3 style="margin-top:2.5rem">Guides d\'urgence {situe} ({num})</h3>',
            "    <p>Nos conseils rédigés commune par commune, pour savoir quoi dire au",
            "      téléphone et ce que l'heure change au prix.</p>",
            '    <ul class="liens-connexes liens-guides">',
        ]
        for a in articles:
            lignes.append(
                f'      <li><a href="{a["url"]}"><strong>{echapper(a["titre"])}</strong>'
                f'<span>{echapper(a["resume"])}</span></a></li>'
            )
        lignes.append("    </ul>")
        # Le lien doit porter une zone tactile d'au moins 24 px : un lien nu
        # dans un paragraphe fait 20 px de haut et fait échouer le contrôle
        # des cibles tactiles sur les onze largeurs testées.
        lignes.append(
            '    <p><a class="lien-tous-guides" href="/blog/">'
            "Tous nos guides de serrurerie</a></p>"
        )
        (SORTIE / f"{num}.html").write_text("\n".join(lignes) + "\n", encoding="utf-8")
        total += len(articles)
        print(f"  ✓ guides {nom} ({num}) : {len(articles)} article(s) liés")
    return total


def main() -> int:
    par_dep = collecter()
    total = ecrire(par_dep)
    vides = [n for n, a in par_dep.items() if not a]
    if vides:
        print(f"  ! aucun article rattaché aux départements : {', '.join(sorted(vides))}")
    print(f"  ✓ maillage zones → blog : {total} lien(s) générés")
    return 0


if __name__ == "__main__":
    sys.exit(main())
