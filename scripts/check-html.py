#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Contrôle structurel du HTML produit.
#
#   python3 scripts/check-html.py
#
# Complète scripts/check-seo.sh, qui vérifie le contenu et le référencement.
# Ici on vérifie que le document tient debout : balises fermées, hiérarchie
# des titres, identifiants uniques, ancres internes qui pointent quelque part,
# attributs d'accessibilité.
#
# Script FACULTATIF, réservé au développement : il n'est pas appelé par le
# build, qui doit rester exécutable avec bash seul. Nécessite Python 3.
# ---------------------------------------------------------------------------

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PUBLIC = RACINE / "public"

# Éléments sans balise fermante : ils ne comptent pas dans l'équilibrage.
ORPHELINS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


class Structure(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pile = []
        self.erreurs = []
        self.ids = {}
        self.ancres = []
        self.titres = []
        self.champs_sans_label = []
        self.labels_for = set()
        # Un champ écrit <label>… <input> …</label> est correctement étiqueté
        # sans attribut « for » : c'est l'étiquetage implicite du HTML.
        self.profondeur_label = 0
        self.langue = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)

        if tag == "html":
            self.langue = a.get("lang")

        if "id" in a:
            self.ids[a["id"]] = self.ids.get(a["id"], 0) + 1

        href = a.get("href", "")
        if href.startswith("#") and len(href) > 1:
            self.ancres.append(href[1:])

        if re.fullmatch(r"h[1-6]", tag):
            self.titres.append(int(tag[1]))

        if tag == "label":
            self.profondeur_label += 1
            if "for" in a:
                self.labels_for.add(a["for"])

        if tag in ("input", "select", "textarea"):
            type_champ = a.get("type", "text")
            if type_champ not in ("hidden", "submit", "button", "reset"):
                if self.profondeur_label == 0:
                    self.champs_sans_label.append((a.get("id"), a.get("aria-label")))

        if tag in ORPHELINS:
            return
        self.pile.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag == "label" and self.profondeur_label > 0:
            self.profondeur_label -= 1
        if tag in ORPHELINS:
            return
        if not self.pile:
            self.erreurs.append(f"ligne {self.getpos()[0]} : </{tag}> sans ouverture")
            return
        if self.pile[-1][0] == tag:
            self.pile.pop()
            return
        # Recherche d'une ouverture correspondante plus haut dans la pile.
        for i in range(len(self.pile) - 1, -1, -1):
            if self.pile[i][0] == tag:
                non_fermees = [t for t, _ in self.pile[i + 1:]]
                self.erreurs.append(
                    f"ligne {self.getpos()[0]} : </{tag}> ferme alors que "
                    f"{', '.join('<' + t + '>' for t in non_fermees)} reste ouvert"
                )
                del self.pile[i:]
                return
        self.erreurs.append(f"ligne {self.getpos()[0]} : </{tag}> sans ouverture correspondante")


def controler(chemin: Path):
    html = chemin.read_text(encoding="utf-8")
    p = Structure()
    p.feed(html)
    p.close()

    problemes = list(p.erreurs)

    for tag, ligne in p.pile:
        problemes.append(f"ligne {ligne} : <{tag}> jamais fermé")

    for identifiant, n in p.ids.items():
        if n > 1:
            problemes.append(f'id="{identifiant}" présent {n} fois')

    for ancre in p.ancres:
        if ancre not in p.ids:
            problemes.append(f'lien vers #{ancre} : aucun élément ne porte cet id')

    if p.langue != "fr":
        problemes.append(f'attribut lang de <html> : "{p.langue}" au lieu de "fr"')

    # Hiérarchie des titres : un saut de niveau (h2 -> h4) casse la navigation
    # au lecteur d'écran et brouille la structure lue par Google.
    if p.titres:
        if p.titres[0] != 1:
            problemes.append(f"le premier titre est un h{p.titres[0]}, il devrait être h1")
        precedent = p.titres[0]
        for niveau in p.titres[1:]:
            if niveau > precedent + 1:
                problemes.append(f"saut de niveau : h{precedent} suivi de h{niveau}")
            precedent = niveau

    for identifiant, aria in p.champs_sans_label:
        if aria:
            continue
        if identifiant is None:
            problemes.append("champ de formulaire sans id ni aria-label")
        elif identifiant not in p.labels_for:
            problemes.append(f'champ #{identifiant} : aucun <label for="{identifiant}">')

    return problemes


def main():
    if not PUBLIC.is_dir():
        sys.exit("public/ absent — lancez d'abord : bash scripts/build.sh")

    pages = sorted(PUBLIC.rglob("*.html"))
    total = 0

    for page in pages:
        problemes = controler(page)
        if problemes:
            total += len(problemes)
            print(f"\n{page.relative_to(PUBLIC)}")
            for p in problemes:
                print(f"  x {p}")

    print()
    if total == 0:
        print(f"HTML : {len(pages)} pages, aucun défaut de structure.")
        return 0
    print(f"HTML : {total} défaut(s) sur {len(pages)} pages.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
