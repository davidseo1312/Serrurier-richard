#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Génère les pages de liste du blog, paginées.
#
#   python3 scripts/gen-blog-pages.py
#
# POURQUOI GÉNÉRER PLUTÔT QU'ÉCRIRE À LA MAIN
#
# Une liste d'articles écrite à la main se périme au premier article publié :
# on oublie une carte, on laisse un article en page 2 alors qu'il vient de
# paraître, ou l'ordre ne correspond plus aux dates. Ces pages sont donc
# reconstruites à chaque build à partir des articles eux-mêmes — leur date,
# leur titre de carte et leur résumé, lus dans leur propre bloc meta.
#
# Conséquence pratique : pour publier un article, il suffit de le déposer
# dans src/pages/blog/ avec ses métadonnées « date », « carte_titre » et
# « carte ». Il apparaît en tête de la page 1 au build suivant, et les
# articles plus anciens descendent d'eux-mêmes.
#
# URLS : /blog/ reste la page 1 — cette URL existe et ne doit pas changer.
# Les suivantes sont /blog/page/2, /blog/page/3, etc.
#
# Les fichiers produits dans src/pages/blog/page/ sont des artefacts de
# build : ils sont ignorés par git et réécrits à chaque fois.
# ---------------------------------------------------------------------------

import re
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
BLOG = RACINE / "src" / "pages" / "blog"
PAGES = BLOG / "page"

PAR_PAGE = 8


def meta(texte, cle):
    m = re.search(rf'^{cle}: (.*)$', texte, re.M)
    return m.group(1).strip() if m else ""


def articles():
    """Tous les articles, du plus récent au plus ancien."""
    out = []
    for p in sorted(BLOG.glob("*.html")):
        if p.name == "index.html":
            continue
        t = p.read_text()
        bloc = re.match(r'<!--meta\n(.*?)\n-->', t, re.S)
        if not bloc:
            print(f"  ! {p.name} : pas de bloc meta, article ignoré")
            continue
        m = bloc.group(1)
        date = meta(m, "date")
        if not date:
            print(f"  ! {p.name} : pas de date, article ignoré")
            continue
        out.append({
            "slug": p.stem,
            "date": date,
            "titre": meta(m, "carte_titre") or meta(m, "breadcrumb") or meta(m, "title"),
            "resume": meta(m, "carte") or meta(m, "description"),
        })
    # date décroissante ; à date égale, ordre alphabétique pour que deux
    # builds successifs produisent exactement le même fichier.
    out.sort(key=lambda a: (a["date"], a["slug"]), reverse=True)
    return out


def carte(a):
    return f"""      <article class="carte">
        <h2>{a['titre']}</h2>
        <p>{a['resume']}</p>
        <a class="lien-fleche" href="/blog/{a['slug']}">Lire le guide</a>
      </article>"""


def url_page(n):
    # Le slash final n'est pas cosmétique : le build fabrique la canonique
    # d'un index.html avec un slash (/blog/page/2/). Un lien sans slash
    # passerait par une redirection Apache à chaque clic, et ne
    # correspondrait pas à l'URL déclarée canonique.
    return "/blog/" if n == 1 else f"/blog/page/{n}/"


def pagination(n, total):
    """Navigation entre pages. Les liens précédent/suivant sont de vrais
    liens : un robot comme un lecteur doit pouvoir parcourir la série."""
    if total < 2:
        return ""
    liens = []
    if n > 1:
        liens.append(f'<a class="page-prec" href="{url_page(n - 1)}" rel="prev">Page précédente</a>')
    for i in range(1, total + 1):
        if i == n:
            liens.append(f'<span class="page-courante" aria-current="page">{i}</span>')
        else:
            liens.append(f'<a href="{url_page(i)}">{i}</a>')
    if n < total:
        liens.append(f'<a class="page-suiv" href="{url_page(n + 1)}" rel="next">Page suivante</a>')
    dedans = "\n        ".join(liens)
    return f"""
    <nav class="pagination" aria-label="Pages de guides">
      <p class="pagination-etat">Page {n} sur {total}</p>
      <div class="pagination-liens">
        {dedans}
      </div>
    </nav>
"""


# --- Données structurées : la liste elle-même ------------------------------
# Un moteur de réponse qui récupère cette page doit pouvoir savoir quels
# articles elle contient sans interpréter le HTML. ItemList le dit.
def schema_liste(lot, n, total):
    elements = ",\n".join(
        f'      {{ "@type": "ListItem", "position": {i}, '
        f'"url": "{{{{BASE_URL}}}}/blog/{a["slug"]}", "name": "{a["titre"].replace(chr(34), chr(39))}" }}'
        for i, a in enumerate(lot, start=1)
    )
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "@id": "{{{{BASE_URL}}}}{url_page(n)}#liste",
  "name": "Conseils serrurerie — page {n} sur {total}",
  "isPartOf": {{ "@id": "{{{{BASE_URL}}}}/#site" }},
  "mainEntity": {{
    "@type": "ItemList",
    "numberOfItems": {len(lot)},
    "itemListOrder": "https://schema.org/ItemListOrderDescending",
    "itemListElement": [
{elements}
    ]
  }}
}}
</script>"""


INTRO_P1 = """      <p>
        Des guides écrits par des professionnels du dépannage, sans jargon et sans argument de vente
        déguisé. L'objectif est simple : que vous sachiez ce qu'il est raisonnable de payer et ce
        qu'il est raisonnable d'exiger. Chaque guide est écrit depuis notre terrain — l'Ille-et-Vilaine
        (35), le Morbihan (56), le Finistère (29), les Côtes-d'Armor (22), la Loire-Atlantique (44) et
        le Maine-et-Loire (49) — parce que le climat, le bâti et les distances d'ici changent
        réellement les réponses.
      </p>"""


def intro_suite(n, total, lot):
    """Les pages suivantes ne répètent pas l'introduction : elles disent ce
    qu'elles contiennent. Quatre pages avec le même chapeau seraient quatre
    pages qui se ressemblent, ce qui n'aide ni le lecteur ni le référencement."""
    annees = sorted({a["date"][:7] for a in lot})
    periode = annees[0] if len(annees) == 1 else f"{annees[0]} à {annees[-1]}"
    return f"""      <p>
        Suite de nos guides de serrurerie, du plus récent au plus ancien. Cette page {n} regroupe
        {len(lot)} guides publiés antérieurement à ceux de la page précédente ({periode}) : ils
        restent d'actualité et sont relus à mesure que les prix, les règles ou le matériel évoluent.
        Les plus récents se trouvent sur la <a href="/blog/">première page</a>.
      </p>"""


def page(lot, n, total):
    cartes = "\n\n".join(carte(a) for a in lot)
    if n == 1:
        titre = "Conseils serrurerie : guides pratiques et prévention"
        desc = ("Guides de serrurerie pour la Bretagne et le Grand Ouest : porte claquée, prix d'une "
                "ouverture, arnaques, serrure A2P, cambriolage, locataire ou propriétaire.")
        reponse = ("Les guides de {{NOM_COMMERCIAL}} traitent trois familles de sujets : que faire dans "
                   "l'urgence (porte claquée, clé cassée, clé qui tourne dans le vide), comment ne pas "
                   "se faire avoir (prix d'une ouverture, comparer deux devis, éviter les arnaques), et "
                   "comment choisir son matériel (certification A2P, serrure multipoints, blindage). "
                   "S'y ajoutent des guides par département — Ille-et-Vilaine (35), Finistère (29), "
                   "Morbihan (56), Côtes-d'Armor (22) — et par ville : Rennes, Saint-Malo, Saint-Brieuc, "
                   f"Lannion, Brest, Quimper, Lorient et Vannes. Les {total} pages sont "
                   "classées du plus récent au plus ancien. Aucun ne remplace un diagnostic sur place : "
                   "pour un cas précis, appelez le {{TELEPHONE}}.")
        h1 = "Conseils serrurerie"
        intro = INTRO_P1
        fil = "<li>Conseils</li>"
        parent = ""
    else:
        titre = f"Conseils serrurerie — page {n} sur {total}"
        desc = (f"Page {n} de nos guides de serrurerie en Bretagne et dans le Grand Ouest : "
                f"{lot[0]['titre'][:60]}… et {len(lot) - 1} autres guides.")
        reponse = ("{{NOM_COMMERCIAL}} publie ses guides de serrurerie du plus récent au plus ancien, "
                   f"sur {total} pages. Cette page {n} rassemble {len(lot)} guides antérieurs, toujours "
                   "d'actualité : urgences, prix, matériel, et cas particuliers par département de "
                   "Bretagne et du Grand Ouest. Pour une situation précise, un technicien répond au "
                   "{{TELEPHONE}}, {{DISPONIBILITE}}.")
        h1 = f"Conseils serrurerie — page {n}"
        intro = intro_suite(n, total, lot)
        fil = '<li><a href="/blog/">Conseils</a></li>\n      <li>Page ' + str(n) + "</li>"
        parent = "parent_nom: Conseils serrurerie\nparent_url: /blog/\n"

    nav = pagination(n, total)

    return f"""<!--meta
title: {titre}
description: {desc}
priority: {'0.7' if n == 1 else '0.5'}
{parent}reponse: {reponse}
-->

{schema_liste(lot, n, total)}

<div class="wrap fil">
  <nav aria-label="Fil d'Ariane">
    <ol>
      <li><a href="/">Accueil</a></li>
      {fil}
    </ol>
  </nav>
</div>

<section>
  <div class="wrap">
    <div class="section-titre">
      <h1>{h1}</h1>
{intro}
    </div>

    <div class="grille grille-2">
{cartes}
    </div>
{nav}  </div>
</section>

<section class="cta-final">
  <div class="wrap">
    <h2>Une question sur votre porte ?</h2>
    <p>
      Ces guides répondent au cas général. Le vôtre a ses particularités : décrivez-nous la situation
      au téléphone, un technicien décroche et vous répond directement, sans engagement.
    </p>
    <p style="margin-top:1.5rem">
      <a class="btn btn-call" href="tel:{{{{TELEPHONE_E164}}}}" data-track="appel" data-track-zone="cta-final-blog">{{{{TELEPHONE}}}}</a>
    </p>
  </div>
</section>
"""


def main():
    arts = articles()
    if not arts:
        print("  ! aucun article de blog trouvé")
        return 1
    lots = [arts[i:i + PAR_PAGE] for i in range(0, len(arts), PAR_PAGE)]
    total = len(lots)

    # Le dossier des pages 2+ est entièrement reconstruit : une page qui n'a
    # plus lieu d'être (articles supprimés) ne doit pas survivre au build.
    if PAGES.exists():
        shutil.rmtree(PAGES)

    (BLOG / "index.html").write_text(page(lots[0], 1, total))
    for n, lot in enumerate(lots[1:], start=2):
        d = PAGES / str(n)
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page(lot, n, total))

    print(f"  ✓ blog paginé : {len(arts)} articles, {total} page(s) de {PAR_PAGE} maximum")
    for n, lot in enumerate(lots, start=1):
        print(f"      page {n} ({url_page(n)}) : {len(lot)} article(s), "
              f"{lot[0]['date']} → {lot[-1]['date']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
