#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Couverture sémantique, ancrage géographique et appel à l'action des articles.
#
#   python3 scripts/check-blog-seo.py
#
# CE QUE CE CONTRÔLE EST, ET CE QU'IL N'EST PAS
#
# Ce n'est PAS 1.fr. 1.fr est un service en ligne payant : il compare un texte
# au champ lexical que les pages déjà bien classées emploient sur une requête,
# et il n'est pas interrogeable depuis ce dépôt. Personne ici ne peut afficher
# un score 1.fr, et prétendre le contraire serait inventer un chiffre.
#
# Ce contrôle applique la même MÉTHODE, avec un champ lexical écrit à la main
# pour chaque article : les termes qu'un texte réellement complet sur le sujet
# emploie forcément. Un article qui couvre 90 % de cette liste couvre le sujet.
# C'est reproductible, c'est vérifiable, et ça ne dépend d'aucun abonnement.
#
# Il vérifie aussi ce que 1.fr ne regarde pas :
#   · l'ancrage breton — région, quatre départements avec leur numéro, villes,
#     et les deux départements ligériens réellement couverts ;
#   · un appel à l'action final avec le numéro de téléphone ;
#   · assez de longueur et de maillage interne pour exister sur la requête ;
#   · l'absence de bourrage : un mot qui dépasse 3 % du texte est un signal
#     de sur-optimisation, que Google traite comme un défaut, pas un atout.
#
# Sortie : code 1 si un article passe sous 90 % ou rate un des garde-fous.
# ---------------------------------------------------------------------------

import re
import sys
import unicodedata
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PUBLIC = RACINE / "public" / "blog"
V, X, A, G, R = "\033[32mv\033[0m", "\033[31mx\033[0m", "\033[33m!\033[0m", "\033[1m", "\033[0m"

SEUIL = 0.90
LONGUEUR_MIN = 1200
MAILLAGE_MIN = 4
DENSITE_MAX = 0.03

# --- Ancrage géographique ---------------------------------------------------
# Les zones réellement couvertes par le site, et elles seules. En inventer une
# serait mentir au visiteur autant qu'à Google.
DEPARTEMENTS = [
    ("Ille-et-Vilaine", "35"),
    ("Morbihan", "56"),
    ("Finistère", "29"),
    ("Côtes-d'Armor", "22"),
    ("Loire-Atlantique", "44"),
    ("Maine-et-Loire", "49"),
]
VILLES = [
    "Rennes", "Nantes", "Vannes", "Brest", "Quimper", "Lorient",
    "Saint-Brieuc", "Saint-Malo", "Lannion", "Angers", "Fougères", "Redon",
    "Concarneau", "Auray", "Dinan", "Morlaix",
]
VILLES_MIN = 5

# --- Champs lexicaux --------------------------------------------------------
# Une entrée = un concept. Plusieurs graphies acceptées pour un même concept :
# le but est de mesurer la couverture du sujet, pas de compter des chaînes.
CHAMPS = {
    "porte-claquee-que-faire.html": {
        "requete": "porte claquée que faire",
        "termes": [
            ["porte claquée"], ["fermée à clé", "fermee a cle"], ["pêne demi-tour"],
            ["pêne dormant", "pênes dormants"], ["gâche"], ["dormant"], ["ouvrant"],
            ["huisserie"], ["cylindre"], ["barillet"], ["radiographie"],
            ["crochetage", "crocheter"], ["perçage", "percer"], ["serrure"],
            ["serrurier"], ["double de clé", "double des clés", "un double"],
            ["trousseau"], ["tour de clé"], ["verrouill"], ["ouverture de porte"],
            ["sans casse", "sans dégât", "sans dommage"], ["dépannage"],
            ["urgence"], ["intervention"], ["technicien"], ["artisan"],
            ["devis"], ["tarif"], ["frais de déplacement"], ["majoration"],
            ["assurance habitation"], ["assistance"], ["multirisque"],
            ["gardien"], ["syndic"], ["copropriété"], ["locataire"],
            ["propriétaire", "bailleur"], ["pompiers"], ["112", "le 18"],
            ["carte bancaire"], ["tournevis"], ["pied-de-biche"],
            ["boîte à clés", "boite a cles"], ["voisin"], ["immeuble"],
            ["palière", "palier"], ["rez-de-chaussée"], ["appartement"],
            ["maison"], ["courant d'air", "coup de vent", "le vent"],
            ["multipoints", "trois points"], ["facture"],
            ["arrêté du 24 janvier 2017"], ["nuit"], ["week-end", "dimanche"],
        ],
    },
    "prix-ouverture-de-porte.html": {
        "requete": "prix ouverture de porte serrurier",
        "termes": [
            ["prix"], ["tarif"], ["coût", "cout"], ["devis"], ["facture"],
            ["main-d'œuvre", "main d'oeuvre"], ["taux horaire"],
            ["frais de déplacement"], ["fournitures", "pièces"], ["forfait"],
            ["à partir de"], ["majoration"], ["nuit"], ["dimanche"],
            ["jour férié", "jours fériés"], ["ouverture de porte"],
            ["porte claquée"], ["porte blindée"], ["multipoints"],
            ["serrure"], ["serrurier"], ["cylindre"], ["A2P"],
            ["clé cassée", "extraction"], ["changement de cylindre"],
            ["dépannage"], ["urgence"], ["intervention"], ["technicien"],
            ["artisan"], ["plateforme", "intermédiation"],
            ["assurance habitation"], ["garantie assistance"],
            ["franchise"], ["dépôt de plainte"], ["effraction"],
            ["DGCCRF", "SignalConso"], ["médiateur"],
            ["arrêté du 24 janvier 2017"], ["affichage des prix", "prix affichés"],
            ["rétractation"], ["TVA"], ["carte bancaire", "paiement"],
            ["surfactur", "abusive"], ["prix d'appel"], ["estimation"],
            ["téléphone"], ["sur place"], ["diagnostic"],
        ],
    },
    "eviter-arnaques-serrurier.html": {
        "requete": "arnaque serrurier que faire",
        "termes": [
            ["arnaque"], ["escroquerie"], ["faux serrurier", "faux artisan"],
            ["plateforme"], ["intermédiation"], ["annonce", "publicité"],
            ["numéro local"], ["commission"], ["devis"], ["facture"],
            ["surfactur", "abusive"], ["prix d'appel"], ["perçage", "percer"],
            ["cylindre"], ["serrure"], ["serrurier"], ["porte claquée"],
            ["SIRET"], ["raison sociale", "dénomination"], ["assurance"],
            ["responsabilité civile"], ["DGCCRF"], ["SignalConso"],
            ["médiateur"], ["rétractation"], ["code de la consommation"],
            ["pratique commerciale trompeuse", "pratiques commerciales trompeuses"],
            ["abus de faiblesse"], ["lettre recommandée"], ["opposition"],
            ["banque"], ["plainte"], ["association de consommateurs"],
            ["UFC", "CLCV"], ["arrêté du 24 janvier 2017"],
            ["affichage des prix", "prix affichés"], ["urgence"],
            ["dépannage"], ["intervention"], ["technicien"], ["artisan"],
            ["espèces"], ["carte bancaire"], ["photographi"],
            ["immatriculation"], ["annuaire des entreprises"],
            ["avis"], ["signature", "signer"], ["pression"],
        ],
    },
    "choisir-serrure-a2p.html": {
        "requete": "serrure A2P 1 2 3 étoiles",
        "termes": [
            ["A2P"], ["CNPP"], ["certification"], ["étoile"],
            ["résistance"], ["effraction"], ["crochetage"], ["perçage"],
            ["arrachement"], ["bumping"], ["cassage"], ["cylindre"],
            ["barillet"], ["serrure"], ["serrurier"], ["multipoints"],
            ["trois points"], ["cinq points"], ["bloc-porte"],
            ["BP1", "BP3"], ["porte blindée"], ["blindage"],
            ["huisserie"], ["gâche"], ["ouvrant"], ["carte de propriété"],
            ["reproduction", "double de clé"], ["organigramme"],
            ["assurance"], ["contrat"], ["indemnisation"],
            ["conditions particulières"], ["vol"], ["cambriolage"],
            ["dissuasion", "dissuasif"], ["laiton", "acier"],
            ["dimension", "cote"], ["longueur"], ["débord", "dépasse"],
            ["entretien", "lubrifi"], ["graphite", "PTFE"],
            ["humidité"], ["corrosion", "grippe"], ["embruns", "air marin"],
            ["devis"], ["prix"], ["pose"], ["remplacement"],
        ],
    },
    "securiser-son-logement.html": {
        "requete": "sécuriser son logement contre le cambriolage",
        "termes": [
            ["cambriolage"], ["cambrioleur"], ["effraction"], ["intrusion"],
            ["prévention"], ["dissuasion", "dissuasif"], ["mode opératoire"],
            ["pied-de-biche"], ["porte-fenêtre"], ["fenêtre"], ["volet"],
            ["verrou"], ["serrure"], ["serrurier"], ["cylindre"], ["A2P"],
            ["gâche"], ["cornière"], ["multipoints"], ["blindage"],
            ["porte blindée"], ["tour de clé"], ["verrouill"],
            ["clé cachée", "clé sous", "cacher une clé"], ["boîte à clés"],
            ["éclairage"], ["détection", "détecteur"], ["alarme"],
            ["caméra"], ["voisin"], ["voisins vigilants", "voisinage"],
            ["opération tranquillité vacances", "tranquillité vacances"],
            ["gendarmerie", "police"], ["plainte"], ["assurance"],
            ["indemnisation"], ["inoccupation", "inoccupé"],
            ["résidence secondaire"], ["littoral", "côte"], ["longère"],
            ["rez-de-chaussée"], ["appartement"], ["maison"],
            ["étudiant", "colocation"], ["garage"], ["abri de jardin", "outils"],
            ["devis"], ["diagnostic"],
        ],
    },
}


def sans_accents(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def texte_visible(html: str) -> str:
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def corps_article(html: str) -> str:
    """Le corps rédigé seul : ni en-tête, ni pied de page, ni bandeau.

    Sans cette découpe, « Bretagne » et « Rennes » seraient comptés parce
    qu'ils figurent dans le pied de page de TOUTES les pages du site. On
    mesurerait alors le gabarit, pas l'article."""
    debut = html.find('<div class="wrap article">')
    fin = html.find('<section class="cta-final">')
    if debut == -1:
        return html
    return html[debut:fin if fin != -1 else len(html)]


def analyser(fichier: Path, regle: dict) -> list:
    html = fichier.read_text(encoding="utf-8")
    corps = corps_article(html)
    texte = texte_visible(corps)
    plat = sans_accents(texte).lower()
    defauts, notes = [], []

    # 1. Couverture du champ lexical.
    manquants = [
        variantes[0] for variantes in regle["termes"]
        if not any(sans_accents(v).lower() in plat for v in variantes)
    ]
    total = len(regle["termes"])
    couverture = (total - len(manquants)) / total
    # Une décimale, et pas zéro : 43/48 s'arrondit à 90 % tout en étant sous le
    # seuil. « couverture 90 % < 90 % » ferait passer un contrôle juste pour un
    # contrôle cassé.
    notes.append(f"couverture sémantique {couverture:.1%} ({total - len(manquants)}/{total})")
    if couverture < SEUIL:
        defauts.append(
            f"couverture {couverture:.1%} < {SEUIL:.0%} — manque : {', '.join(manquants[:10])}"
        )

    # 2. Ancrage géographique réel.
    if "Bretagne" not in texte:
        defauts.append("la Bretagne n'est pas nommée")
    for nom, numero in DEPARTEMENTS:
        if sans_accents(nom).lower() not in plat:
            defauts.append(f"département absent : {nom}")
        elif numero not in texte:
            defauts.append(f"{nom} cité sans son numéro ({numero})")
    citees = [v for v in VILLES if v in texte]
    notes.append(f"{len(citees)} ville(s) citée(s)")
    if len(citees) < VILLES_MIN:
        defauts.append(f"seulement {len(citees)} ville(s) citée(s), minimum {VILLES_MIN}")

    # 3. Appel à l'action final, avec le numéro.
    final = re.search(r'<section class="cta-final">(.*?)</section>', html, re.S)
    if not final:
        defauts.append("aucun appel à l'action final")
    else:
        bloc = final.group(1)
        if 'href="tel:' not in bloc:
            defauts.append("l'appel à l'action final ne propose pas d'appeler")
        if not re.search(r"appel|téléphon|décroch|composez", bloc, re.I):
            defauts.append("l'appel à l'action final n'incite pas explicitement à appeler")

    # 4. Longueur et maillage.
    mots = re.findall(r"[A-Za-zÀ-ÿ'’-]+", texte)
    notes.append(f"{len(mots)} mots")
    if len(mots) < LONGUEUR_MIN:
        defauts.append(f"{len(mots)} mots, minimum {LONGUEUR_MIN}")

    liens = set(re.findall(r'<a [^>]*href="(/[^"#]*)"', corps))
    notes.append(f"{len(liens)} lien(s) interne(s)")
    if len(liens) < MAILLAGE_MIN:
        defauts.append(f"{len(liens)} lien(s) interne(s), minimum {MAILLAGE_MIN}")

    # 5. Garde-fou anti-bourrage.
    frequences = {}
    for mot in mots:
        m = sans_accents(mot).lower()
        if len(m) > 4:
            frequences[m] = frequences.get(m, 0) + 1
    if mots:
        mot, n = max(frequences.items(), key=lambda kv: kv[1], default=("", 0))
        densite = n / len(mots)
        notes.append(f"mot le plus dense « {mot} » {densite:.1%}")
        if densite > DENSITE_MAX:
            defauts.append(f"bourrage probable : « {mot} » représente {densite:.1%} du texte")

    return defauts, notes


def main() -> int:
    if not PUBLIC.is_dir():
        print("public/blog est absent : lancez d'abord bash scripts/build.sh")
        return 1

    print(f"\n{G}Articles : couverture sémantique, ancrage breton, appel à l'action{R}")
    code = 0
    for nom, regle in CHAMPS.items():
        fichier = PUBLIC / nom
        if not fichier.is_file():
            print(f"  {X} {nom} : article introuvable")
            code = 1
            continue
        defauts, notes = analyser(fichier, regle)
        marque = X if defauts else V
        print(f"\n  {marque} {nom}  — requête : « {regle['requete']} »")
        print(f"      {' · '.join(notes)}")
        for d in defauts:
            print(f"      {X} {d}")
            code = 1

    manquants = sorted(
        p.name for p in PUBLIC.glob("*.html")
        if p.name != "index.html" and p.name not in CHAMPS
    )
    if manquants:
        print(f"\n  {A} article(s) sans champ lexical déclaré : {', '.join(manquants)}")
        print("      Ajoutez-les dans CHAMPS, sinon ils ne sont pas contrôlés.")
        code = 1

    print()
    if code == 0:
        print(f"  {V} Tous les articles couvrent leur sujet, nomment les départements")
        print("      desservis et se terminent par une invitation à appeler.")
    return code


if __name__ == "__main__":
    sys.exit(main())
