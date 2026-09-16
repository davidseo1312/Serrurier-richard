#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Lisibilité du site par les moteurs de réponse génératifs.
#
#   python3 scripts/check-ia.py
#
# CE QUE CE CONTRÔLE VÉRIFIE, ET CE QU'IL NE PROMET PAS
#
# Il ne mesure PAS si une IA cite le site : personne ne peut le mesurer depuis
# un dépôt, et aucun moteur ne publie ses critères. Prétendre le contraire
# serait inventer un chiffre.
#
# Il vérifie les conditions matérielles SANS lesquelles une citation est
# impossible, et elles sont vérifiables :
#
#   1. chaque page porte l'identité complète de l'entreprise — un moteur ne
#      récupère qu'une URL et doit pouvoir répondre « qui, quoi, où » sans en
#      visiter d'autre ;
#   2. chaque page indexable expose un passage autosuffisant, nommant
#      l'entreprise, le territoire et un moyen de contact, cité tel quel ;
#   3. ce passage est bien celui que « speakable » désigne ;
#   4. robots.txt autorise nommément les robots des moteurs de réponse ;
#   5. llms.txt existe et décrit exactement les pages du sitemap — ni plus,
#      ni moins ;
#   6. le balisage ne déclare qu'UNE entreprise. Un « Locksmith » par ville
#      reviendrait à annoncer des agences qui n'existent pas.
#
# Sortie : code 1 si l'une de ces conditions n'est pas remplie.
# ---------------------------------------------------------------------------

import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PUBLIC = RACINE / "public"
V, X, G, R = "\033[32mv\033[0m", "\033[31mx\033[0m", "\033[1m", "\033[0m"

# Robots des moteurs de réponse qui doivent être nommés dans robots.txt.
ROBOTS_IA = [
    "GPTBot", "OAI-SearchBot", "ChatGPT-User",
    "ClaudeBot", "Claude-SearchBot", "Claude-User",
    "PerplexityBot", "Perplexity-User",
    "Google-Extended", "Applebot-Extended",
    "DuckAssistBot", "MistralAI-User", "CCBot",
]

# Un passage cité hors contexte doit rester vrai et utile : il nomme
# l'entreprise, dit où elle intervient, et dit comment la joindre.
REPONSE_MIN = 180


def pages_html():
    return sorted(p for p in PUBLIC.rglob("*.html"))


def blocs_jsonld(html):
    out = []
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            out.append(json.loads(m))
        except json.JSONDecodeError as e:
            out.append({"__erreur__": str(e)})
    return out


def noeuds(blocs):
    for b in blocs:
        if isinstance(b, dict) and "@graph" in b:
            yield from b["@graph"]
        elif isinstance(b, dict):
            yield b


def main():
    defauts = []
    indexables = 0
    avec_reponse = 0

    for p in pages_html():
        rel = p.relative_to(PUBLIC).as_posix()
        html = p.read_text()

        # --- 1. JSON-LD valide et identité présente ------------------------
        blocs = blocs_jsonld(html)
        for b in blocs:
            if isinstance(b, dict) and "__erreur__" in b:
                defauts.append(f"{rel} : JSON-LD illisible — {b['__erreur__']}")

        ns = list(noeuds(blocs))
        entreprises = [n for n in ns if n.get("@id", "").endswith("/#entreprise")]
        if not entreprises:
            defauts.append(f"{rel} : aucune identité d'entreprise (#entreprise absent)")
        else:
            complet = [n for n in entreprises if n.get("telephone") and n.get("areaServed")]
            if not complet:
                defauts.append(f"{rel} : #entreprise présent mais sans téléphone ni zone")

        # --- 6. une seule entreprise déclarée ------------------------------
        locksmiths = [n for n in ns if n.get("@type") == "Locksmith"]
        ids = {n.get("@id") for n in locksmiths}
        if len(ids - {None}) > 1 or any(n.get("@id") is None for n in locksmiths):
            defauts.append(
                f"{rel} : {len(locksmiths)} entreprises déclarées ({sorted(str(i) for i in ids)}) — "
                "un Locksmith par zone revient à annoncer des agences inexistantes"
            )

        pages_ld = [n for n in ns if n.get("@type") == "WebPage"]
        if not pages_ld:
            defauts.append(f"{rel} : aucun nœud WebPage")

        # --- pages hors index : rien d'autre n'est exigé --------------------
        if re.search(r'<meta name="robots" content="noindex', html):
            continue
        indexables += 1

        # --- 2. réponse directe autosuffisante ------------------------------
        m = re.search(r'<div class="reponse-ia"><p>(.*?)</p></div>', html, re.S)
        if not m:
            defauts.append(f"{rel} : pas de bloc de réponse directe")
            continue
        avec_reponse += 1
        texte = re.sub(r"<[^>]*>", "", m.group(1))

        if len(texte) < REPONSE_MIN:
            defauts.append(f"{rel} : réponse trop courte ({len(texte)} car., minimum {REPONSE_MIN})")
        if "Serrurier Richard" not in texte:
            defauts.append(f"{rel} : la réponse ne nomme pas l'entreprise")
        if not re.search(r"0\d(?: \d\d){4}", texte):
            defauts.append(f"{rel} : la réponse ne donne aucun numéro de téléphone")
        geo = ("Bretagne", "Grand Ouest", "Ille-et-Vilaine", "Morbihan", "Finistère",
               "Côtes-d'Armor", "Loire-Atlantique", "Maine-et-Loire", "Rennes", "Nantes",
               "Brest", "Quimper", "Lorient", "Vannes", "Saint-Brieuc", "Saint-Malo",
               "Lannion", "Angers")
        if not any(g in texte for g in geo):
            defauts.append(f"{rel} : la réponse ne situe aucun territoire")

        # --- réponse placée juste après le titre ---------------------------
        if not re.search(r'</h1>\s*<div class="reponse-ia">', html):
            defauts.append(f"{rel} : la réponse n'est pas placée immédiatement après le <h1>")

        # --- 3. speakable pointe sur un élément réel ------------------------
        sel = []
        for n in pages_ld:
            sp = n.get("speakable") or {}
            sel += sp.get("cssSelector", [])
        if ".reponse-ia" not in sel:
            defauts.append(f"{rel} : speakable ne désigne pas le bloc de réponse")

    # --- 4. robots.txt ------------------------------------------------------
    robots = (PUBLIC / "robots.txt")
    if not robots.exists():
        defauts.append("robots.txt absent")
    else:
        txt = robots.read_text()
        manquants = [r for r in ROBOTS_IA if not re.search(rf"^User-agent:\s*{re.escape(r)}\s*$", txt, re.M | re.I)]
        if manquants:
            defauts.append("robots.txt n'autorise pas nommément : " + ", ".join(manquants))
        # Un « Disallow: / » n'appartient qu'au bloc qui le précède : on découpe
        # sur les lignes vides avant de chercher, sinon la recherche traverse
        # les blocs voisins et accuse le mauvais robot.
        for bloc in re.split(r"\n\s*\n", txt):
            agents = re.findall(r"^User-agent:\s*(\S+)\s*$", bloc, re.M)
            if agents and re.search(r"^Disallow:\s*/\s*$", bloc, re.M):
                defauts.append("robots.txt interdit tout le site à " + ", ".join(agents))

    # --- 5. llms.txt cohérent avec le sitemap -------------------------------
    llms = PUBLIC / "llms.txt"
    sitemap = PUBLIC / "sitemap.xml"
    if not llms.exists():
        defauts.append("llms.txt absent")
    elif sitemap.exists():
        urls_site = set(re.findall(r"<loc>([^<]+)</loc>", sitemap.read_text()))
        urls_llms = set(re.findall(r"\]\((https?://[^)]+)\)", llms.read_text()))
        oubliees = urls_site - urls_llms
        fantomes = urls_llms - urls_site
        if oubliees:
            defauts.append(f"llms.txt oublie {len(oubliees)} page(s) du sitemap : {sorted(oubliees)[:3]}")
        if fantomes:
            defauts.append(f"llms.txt cite {len(fantomes)} page(s) hors sitemap : {sorted(fantomes)[:3]}")

    # --- rapport ------------------------------------------------------------
    print(f"\n{G}Lisibilité par les moteurs de réponse{R}")
    print(f"  {len(pages_html())} pages analysées · {indexables} indexables · "
          f"{avec_reponse} avec réponse directe")
    if llms.exists():
        print(f"  llms.txt : {llms.read_text().count(chr(10) + '- [')} page(s) inventoriée(s)")

    if defauts:
        print()
        for d in defauts:
            print(f"  {X} {d}")
        print(f"\n  {len(defauts)} défaut(s).")
        return 1

    print(f"  {V} identité complète sur chaque page, une seule entreprise déclarée")
    print(f"  {V} passage citable et « speakable » sur chaque page indexable")
    print(f"  {V} robots.txt autorise nommément les robots des moteurs de réponse")
    print(f"  {V} llms.txt décrit exactement les pages du sitemap")
    return 0


if __name__ == "__main__":
    sys.exit(main())
