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
# Un mot-clé présent une seule fois dans 4 000 mots ne pèse rien. Les outils
# d'optimisation sémantique notent la richesse d'emploi, pas la présence : un
# terme employé trois fois dans des contextes différents compte, une mention
# unique passe pour une coïncidence. D'où ce plancher sur les mots-clés dont
# l'article doit vraiment traiter.
RENFORT_MIN = 3
LONGUEUR_MIN = 1200
MAILLAGE_MIN = 4
DENSITE_MAX = 0.03
# Redondance entre articles. Deux guides qui redisent la même chose se
# cannibalisent : Google en choisit un, l'autre disparaît des résultats.
# Mesurée en passages de cinq mots partagés (indice de Jaccard) : le fond
# commun normal d'un même métier tourne autour de 2 %. Au-delà de 6 %, deux
# articles racontent la même histoire et l'un des deux est de trop.
SEUIL_REDONDANCE = 0.06


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
            # Mots-clés demandés en complément : ils décrivent le vocabulaire
            # que les visiteurs emploient réellement dans leurs recherches.
            ["porte d'entrée"], ["haute sécurité"], ["Vachette"], ["Fichet"],
            ["verrou"], ["verrous"], ["verrouillage"], ["clefs"],
            ["cambriolage"], ["cambrioleurs"], ["serruriers"],
            ["blindée", "blindées"], ["portes blindées"], ["cylindres"],
            ["entreprise de serrurerie", "entreprise serrurerie"],
            ["ouvrir la porte"], ["dépanner"], ["dépannages"],
            ["dépannage serrurerie", "dépannage serrurier"],
            ["dépannage de serrure", "dépannage serrure"],
            ["porte de garage"], ["serrurier professionnel"],
            ["changer la serrure", "changer de serrure", "changer serrure"],
            ["serrure multipoints"], ["artisan serrurier"],
            ["pose de serrure"], ["métalliques"], ["type de serrure"],
            ["installateur"], ["faire appel à un serrurier"],
            ["serrure de porte", "serrure porte"], ["niveau de sécurité"],
            ["pêne"],
        ],
        # Les 36 mots-clés demandés : présence ET emploi répété.
        "renforces": [
            ["porte d'entrée"], ["haute sécurité"], ["Vachette"], ["Fichet"],
            ["verrou"], ["verrous"], ["verrouillage"], ["clefs"],
            ["barillet"], ["cambriolage"], ["cambrioleurs"], ["serruriers"],
            ["blindée", "blindées"], ["portes blindées"], ["cylindres"],
            ["entreprise de serrurerie"], ["ouvrir la porte"],
            ["dépanner"], ["dépannages"], ["dépannage serrurerie"],
            ["dépannage de serrure"], ["porte de garage"],
            ["serrurier professionnel"], ["crochetage"],
            ["changer la serrure", "changer le cylindre"],
            ["serrure multipoints"], ["gâche"], ["artisan serrurier"],
            ["pose de serrure"], ["métalliques"], ["type de serrure"],
            ["pêne"], ["installateur"], ["faire appel à un serrurier"],
            ["serrure de porte"], ["niveau de sécurité"],
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
    "serrurier-rennes-nouvel-arrivant.html": {
        "requete": "emménager à Rennes changer serrure clés",
        "termes": [
            ["Rennes"], ["rennais", "rennaise"], ["Ille-et-Vilaine"],
            ["emménag", "arriv"], ["logement"], ["locataire"],
            ["propriétaire", "bailleur"], ["état des lieux"],
            ["dépôt de garantie"], ["clés"], ["clefs"], ["double", "doubles"],
            ["cylindre"], ["barillet"], ["serrure"], ["serrurier"],
            ["porte palière"], ["immeuble"], ["copropriété"], ["syndic"],
            ["gardien"], ["digicode"], ["interphone"],
            ["contrôle d'accès", "badge"], ["organigramme"],
            ["parties communes"], ["boîte aux lettres"], ["local à vélos"],
            ["colocation"], ["colocataire"], ["étudiant"],
            ["assurance habitation"], ["vol"], ["effraction"],
            ["boîte à clés"], ["devis"], ["prix", "tarif"], ["SIRET"],
            ["annuaire des entreprises"], ["dépannage"],
            ["multipoints"], ["quartier", "quartiers"],
            ["première couronne"], ["maison individuelle", "maison"],
            ["humidité"], ["tour de clé"], ["inoccupation", "absence"],
            ["cotes", "dimensions"],
        ],
    },
    "serrurier-saint-malo-intra-muros.html": {
        "requete": "serrurier Saint-Malo intra-muros accès",
        "termes": [
            ["Saint-Malo"], ["malouin", "malouine"], ["Ille-et-Vilaine"],
            ["intra-muros"], ["remparts", "cité close"],
            ["porte de ville", "portes de ville"], ["Paramé"],
            ["Saint-Servan"], ["Rothéneuf"], ["Sillon"],
            ["stationnement"], ["accès"], ["étage"], ["ascenseur"],
            ["escalier"], ["outillage"], ["technicien"],
            ["délai", "temps"], ["circulation"], ["saison", "saisonnier"],
            ["meublé", "location saisonnière"], ["clés", "clefs"],
            ["boîte à clés"], ["cylindre"], ["serrure"], ["serrurier"],
            ["mandat"], ["granite"], ["scellement", "scellée"],
            ["gâche"], ["arrachement"], ["embruns", "sel"],
            ["lubrifiant", "graphite"], ["corrosion", "grippe"],
            ["porte claquée"], ["vent"], ["humidité"], ["volets"],
            ["secteur protégé", "urbanisme"], ["porte blindée"],
            ["devis"], ["prix", "tarif"], ["dépannage"], ["intervention"],
            ["effraction"], ["assurance"], ["vol"],
        ],
    },
    "serrurier-saint-brieuc-comparer-devis.html": {
        "requete": "comparer devis serrurier Saint-Brieuc",
        "termes": [
            ["Saint-Brieuc"], ["briochin", "briochine"], ["Côtes-d'Armor"],
            ["Plérin"], ["Ploufragan"], ["Langueux"], ["Légué"],
            ["agglomération"], ["quartier", "quartiers"],
            ["devis"], ["comparer", "comparaison"], ["total"],
            ["décompte", "détaillé"], ["prix unitaire"], ["quantité"],
            ["SIRET"], ["dénomination"], ["validité"],
            ["déplacement"], ["main-d'œuvre", "main d'oeuvre"],
            ["taux horaire"], ["forfait"], ["fournitures", "fourniture"],
            ["marque"], ["référence"], ["certification", "certifié"],
            ["A2P"], ["étoiles"], ["haute sécurité"], ["cylindre"],
            ["clés", "clefs"], ["carte de propriété"], ["gâche"],
            ["huisserie"], ["paumelles"], ["organigramme"],
            ["bailleur", "syndic"], ["corrosion", "marine"],
            ["facture"], ["signature", "signer"], ["refuser"],
            ["litige"], ["DGCCRF", "SignalConso"],
            ["lettre recommandée"], ["majoration"], ["urgence"],
            ["serrurier"], ["intervention"], ["dépannage"],
            ["TTC"], ["assurance habitation"], ["garantie vol", "garantie"],
            ["cambriolage"], ["multipoints"], ["barillet"],
        ],
        # Les 36 mots-clés demandés : présence ET emploi répété.
        "renforces": [
            ["serruriers"], ["multipoints"], ["métalliques"],
            ["porte d'entrée"], ["porte de garage"], ["niveau de sécurité"],
            ["cylindres"], ["blindées"], ["barillet"],
            ["portes blindées"], ["Vachette"], ["installateur"],
            ["cambriolage"], ["Fichet"], ["verrou"],
            ["clefs"], ["dépannages"], ["lock"],
            ["serrure multipoints"], ["porte claquée"], ["verrouillage"],
            ["menuiserie"], ["dépanner"], ["contrôle d'accès"],
            ["stores"], ["TTC"], ["verrous"],
            ["rideaux"], ["cambrioleurs"], ["fermetures"],
            ["assurance habitation"], ["ouvrir la porte"], ["coffres"],
            ["coffres-forts"], ["menuiseries"], ["panique"],
        ],
    },
    "serrurier-lannion-entretien-prevention.html": {
        "requete": "entretien serrure Lannion prévention panne",
        "termes": [
            ["Lannion"], ["Trégor", "trégorrois"], ["Côtes-d'Armor"],
            ["Léguer"], ["Perros-Guirec"], ["Trébeurden"],
            ["granit rose", "granit"], ["entretien"], ["prévention"],
            ["signal", "signaux"], ["panne"], ["usure"],
            ["clé"], ["cylindre"], ["barillet"], ["serrure"],
            ["serrurier"], ["pêne"], ["gâche"], ["paumelles"],
            ["poignée"], ["carré"], ["tringlerie"], ["multipoints"],
            ["verrou", "verrous"], ["visserie", "vis"], ["tournevis"],
            ["lubrifiant", "lubrifi"], ["graphite"], ["PTFE"],
            ["huile multi-usage", "aérosol"], ["graisse"],
            ["dégrippant", "dégrippage"], ["corrosion"],
            ["embruns", "sel"], ["humidité"], ["bois"], ["gonfl"],
            ["frotte", "frottement"], ["alignement", "désalign"],
            ["réglage"], ["remplacement"], ["clé cassée"],
            ["extraction"], ["forcer"], ["urgence"], ["dépannage"],
            ["rendez-vous"], ["volets"], ["garage"],
            ["blindée", "blindées"], ["coupe-feu"], ["anti-panique"],
            ["crochetage"], ["cambriolage"], ["installateur"],
        ],
        # Les 36 mots-clés demandés : présence ET emploi répété.
        "renforces": [
            ["porte d'entrée"], ["Vachette"], ["verrou"],
            ["porte de garage"], ["cambriolage"], ["verrouillage"],
            ["serruriers"], ["blindées"], ["portes blindées"],
            ["clefs"], ["cambrioleurs"], ["métalliques"],
            ["fermetures"], ["Fichet"], ["lock"],
            ["niveau de sécurité"], ["panique"], ["anti-panique"],
            ["dormant"], ["pose de serrure"], ["menuiserie"],
            ["intrusion"], ["stores"], ["crochetage"],
            ["porte claquée"], ["cambriolages"], ["coffres"],
            ["ouvrir la porte"], ["rideaux"], ["contrôle d'accès"],
            ["portes de garage"], ["dépanner"], ["installateur"],
            ["certifiées"], ["serrure de sécurité"], ["coupe-feu"],
        ],
    },
    "trouver-serrurier-brest.html": {
        "requete": "serrurier Brest trouver dépannage",
        "termes": [
            ["Brest"], ["brestois", "brestoise"], ["Finistère"],
            ["quartier", "quartiers"], ["Recouvrance"], ["Penfeld"],
            ["pont", "ponts"], ["agglomération"], ["commune", "communes"],
            ["délai", "délais"], ["temps de route", "temps de trajet"],
            ["trajet"], ["circulation"], ["vent"], ["pluie"],
            ["serrurier"], ["serrure"], ["cylindre"], ["gâche"],
            ["porte palière"], ["immeuble"], ["Reconstruction"],
            ["bailleur", "syndic"], ["organigramme"], ["digicode"],
            ["interphone"], ["étage"], ["stationnement"], ["tramway"],
            ["rue piétonne", "rues piétonnes"], ["dépannage"],
            ["urgence"], ["intervention"], ["technicien"], ["artisan"],
            ["plateforme"], ["devis"], ["prix"], ["tarif"], ["SIRET"],
            ["annuaire des entreprises"], ["facture"],
            ["arrêté du 24 janvier 2017", "obligation légale"],
            ["porte claquée"], ["sans casse"], ["huisserie"],
            ["humidité"], ["maison", "maisons"], ["garage"],
        ],
        # Les 36 mots-clés demandés : présence ET emploi répété.
        "renforces": [
            ["A2P"], ["porte d'entrée"], ["haute sécurité"],
            ["multipoints"], ["serrure multipoints"], ["serruriers"],
            ["cylindres"], ["blindées"], ["portes blindées"], ["clefs"],
            ["porte de garage"], ["Vachette"], ["Fichet"], ["verrou"],
            ["verrous"], ["verrouillage"], ["cambriolage"],
            ["cambriolages"], ["cambrioleurs"], ["métalliques"],
            ["barillet"], ["pêne"], ["dormant"], ["crochetage"],
            ["lock"], ["fermetures"], ["dépanner"], ["dépannages"],
            ["ouvrir la porte"], ["niveau de sécurité"],
            ["anti-panique"], ["panique"], ["menuiserie"],
            ["entreprise de serrurerie"], ["certifiée"],
            ["tentative d'effraction"],
        ],
    },
    "trouver-serrurier-quimper.html": {
        "requete": "serrurier Quimper vérifier entreprise",
        "termes": [
            ["Quimper"], ["quimpérois", "quimpéroise"], ["Finistère"],
            ["Cornouaille"], ["Locmaria"], ["Ergué-Armel"], ["Penhars"],
            ["Kerfeunteun"], ["cathédrale"], ["pans de bois"],
            ["quartier", "quartiers"], ["commune", "communes"],
            ["SIRET"], ["annuaire des entreprises"],
            ["mentions légales"], ["dénomination"], ["siège"],
            ["activité déclarée", "activité"], ["vérification", "vérifier"],
            ["assurance"], ["responsabilité civile"], ["attestation"],
            ["avis"], ["note"], ["commentaire", "commentaires"],
            ["devis"], ["facture"], ["prix"], ["tarif"],
            ["arrêté du 24 janvier 2017"], ["affichage"],
            ["serrurier"], ["serrure"], ["cylindre"], ["clé"],
            ["dépannage"], ["intervention"], ["technicien"], ["artisan"],
            ["plateforme"], ["numéro local", "numéro en 02"],
            ["domiciliation"], ["délai"], ["déclaration préalable"],
            ["porte"], ["bois"], ["organigramme"], ["air marin", "sel"],
            ["lubrifiant", "lubrifi"], ["résidence secondaire"],
        ],
        # Les 36 mots-clés demandés : présence ET emploi répété.
        "renforces": [
            ["dépannages"], ["dépanner"], ["dépannage d'urgence"],
            ["intervention rapide"], ["serruriers"], ["installateur"],
            ["métalliques"], ["rideaux"], ["rideaux métalliques"],
            ["fermetures"], ["volets roulants"], ["roulants"],
            ["stores"], ["portails"], ["porte de garage"],
            ["portes de garage"], ["menuiserie"], ["menuiseries"],
            ["clefs"], ["reproduction de clés"], ["toutes les marques"],
            ["A2P"], ["haute sécurité"], ["Vachette"], ["Fichet"],
            ["barillet"], ["multipoints"], ["verrou"],
            ["porte d'entrée"], ["porte claquée"], ["blindées"],
            ["portes blindées"], ["cambriolage"], ["coffres"],
            ["coffres-forts"], ["lock"],
        ],
    },
    "trouver-serrurier-lorient.html": {
        "requete": "serrurier Lorient appeler dépannage",
        "termes": [
            ["Lorient"], ["lorientais", "lorientaise"], ["Morbihan"],
            ["Lanester"], ["Ploemeur"], ["Hennebont"], ["Keryado"],
            ["Kerentrech"], ["Merville"], ["Keroman", "port"],
            ["quartier", "quartiers"], ["agglomération"],
            ["appel"], ["téléphone"], ["information", "informations"],
            ["situation"], ["type de fermeture", "type de serrure"],
            ["adresse"], ["accès"], ["étage"], ["digicode"],
            ["interphone"], ["horaire"], ["majoration"], ["nuit"],
            ["dimanche"], ["jour férié", "jours fériés"],
            ["pêne demi-tour", "demi-tour"], ["multipoints"],
            ["porte blindée"], ["serrure"], ["serrurier"], ["cylindre"],
            ["devis"], ["facture"], ["prix"], ["tarif"],
            ["main-d'œuvre", "main d'oeuvre"], ["déplacement"],
            ["locataire"], ["propriétaire"], ["copropriété"], ["syndic"],
            ["parties communes"], ["organigramme"], ["gâche"],
            ["dépannage"], ["intervention"], ["pompiers"], ["112", "le 18"],
            ["air marin", "sel"],
        ],
        # Les 36 mots-clés demandés : présence ET emploi répété.
        "renforces": [
            ["A2P"], ["certifiée"], ["porte d'entrée"], ["porte claquée"],
            ["haute sécurité"], ["niveau de sécurité"], ["serruriers"],
            ["artisan serrurier"], ["entreprise de serrurerie"],
            ["blindées"], ["portes blindées"], ["serrure multipoints"],
            ["porte de garage"], ["fermetures"], ["stores"],
            ["menuiserie"], ["anti-panique"], ["panique"],
            ["Vachette"], ["Fichet"], ["barillet"], ["dormant"],
            ["verrou"], ["verrous"], ["verrouillage"], ["clefs"],
            ["crochetage"], ["ouvrir la porte"], ["pose de serrure"],
            ["dépanner"], ["dépannages"], ["cambriolage"],
            ["cambriolages"], ["cambrioleurs"], ["intrusion"],
            ["tentative d'effraction"],
        ],
    },
    "trouver-serrurier-vannes.html": {
        "requete": "serrurier Vannes urgence rendez-vous",
        "termes": [
            ["Vannes"], ["vannetais", "vannetaise"], ["Morbihan"],
            ["golfe"], ["presqu'île de Rhuys", "Rhuys"], ["Sarzeau"],
            ["Arzon"], ["Arradon"], ["Séné"], ["Baden"], ["Locmariaquer"],
            ["commune", "communes"], ["agglomération"],
            ["urgence"], ["rendez-vous"], ["devis"], ["délai"],
            ["majoration"], ["nuit"], ["dimanche"],
            ["copropriété"], ["syndic"], ["parties communes"],
            ["porte palière"], ["interphone"], ["contrôle d'accès"],
            ["organigramme"], ["règlement de copropriété"],
            ["locataire"], ["propriétaire"],
            ["résidence secondaire"], ["inoccupation", "inoccupé"],
            ["mandat"], ["assurance"], ["assistance"], ["multirisque"],
            ["garantie vol", "garantie"], ["embruns", "sel"],
            ["grippé", "grippe"], ["graphite", "PTFE"], ["cylindre"],
            ["serrure"], ["serrurier"], ["clé", "clés"],
            ["effraction"], ["cambriolage"], ["pompiers"], ["112", "le 18"],
            ["saison", "saisonnier"], ["circulation"], ["intervention"],
        ],
        # Les 36 mots-clés demandés : présence ET emploi répété.
        "renforces": [
            ["porte d'entrée"], ["porte claquée"], ["serruriers"],
            ["artisan serrurier"], ["entreprise de serrurerie"],
            ["installateur"], ["multipoints"], ["serrure multipoints"],
            ["blindées"], ["portes blindées"], ["haute sécurité"],
            ["certifiée"], ["anti-effraction"], ["clefs"],
            ["toutes les marques"], ["cylindres"], ["barillet"],
            ["pêne"], ["verrou"], ["verrous"], ["verrouillage"],
            ["métalliques"], ["rideaux"], ["fermetures"],
            ["menuiserie"], ["porte de garage"], ["coffres"],
            ["coffres-forts"], ["ouvrir la porte"], ["dépanner"],
            ["dépannages"], ["cambriolages"], ["cambrioleurs"],
            ["panique"], ["Vachette"], ["Fichet"],
        ],
    },
    "changer-serrure-rennes-autorisations.html": {
        "requete": "changer serrure porte Rennes autorisation",
        "termes": [
            ["Rennes"], ["autorisation"], ["déclaration préalable"],
            ["urbanisme"], ["code de l'urbanisme", "urbanisme"],
            ["site patrimonial remarquable"], ["secteur sauvegardé"],
            ["monument historique", "monuments historiques"],
            ["abords"], ["Architecte des Bâtiments de France", "ABF"],
            ["avis"], ["aspect extérieur"], ["façade"], ["porte d'entrée"],
            ["porte palière"], ["vantail", "ouvrant"], ["cylindre"],
            ["serrure"], ["serrurier"], ["verrou"], ["blindage", "blindée"],
            ["bloc-porte"], ["parement", "matériau"], ["teinte"],
            ["quincaillerie"], ["bois"], ["PVC"], ["rideau métallique"],
            ["grille"], ["vitrine"], ["devanture"], ["commerce"],
            ["copropriété"], ["règlement de copropriété"], ["syndic"],
            ["assemblée générale"], ["parties communes"],
            ["partie privative", "parties communes"], ["interphone"],
            ["contrôle d'accès"], ["organigramme"], ["locataire"],
            ["effraction"], ["mise en sécurité"], ["dépôt de plainte"],
            ["assurance", "assureur"], ["délai"], ["instruction"],
            ["Cerfa", "formulaire"], ["mairie"], ["service urbanisme"],
            ["devis"], ["quartier", "quartiers"],
        ],
    },
    "enferme-chez-soi-que-faire.html": {
        "requete": "bloqué chez soi porte ne s'ouvre plus de l'intérieur",
        "termes": [
            ["enfermé", "enferme"], ["bloqué", "bloquée"], ["sortir"],
            ["de l'intérieur", "intérieur"], ["porte"], ["serrure"],
            ["serrurier"], ["cylindre"], ["canon"], ["clé"], ["poignée"],
            ["carré"], ["bouton moleté", "bouton"], ["pêne"], ["gâche"],
            ["dormant"], ["paumelle"], ["multipoints"], ["tringlerie"],
            ["verrou"], ["condamnation"], ["déverrouillage d'urgence"],
            ["salle de bain"], ["WC", "toilettes"], ["enfant"],
            ["personne âgée", "vivant seul", "vit seul"],
            ["pompiers"], ["112", "le 18"], ["secours"], ["danger"],
            ["fumée"], ["gaz"], ["malaise"], ["urgence"],
            ["assurance habitation"], ["assistance"], ["multirisque"],
            ["voisin"], ["gardien"], ["syndic"], ["bailleur"],
            ["double"], ["grippé", "grippe"], ["lubrifi"],
            ["graphite", "PTFE"], ["forcer"], ["perçage", "percer"],
            ["sans casse", "sans dégât"], ["dépannage"], ["diagnostic"],
            ["tarif", "prix"], ["téléphone"],
        ],
        # Les 36 mots-clés demandés : présence ET emploi répété.
        "renforces": [
            ["A2P"], ["porte d'entrée"], ["barillet"], ["serruriers"],
            ["haute sécurité"], ["verrouillage"], ["ouvrir la porte"],
            ["cambriolage"], ["cambriolages"], ["cambrioleurs"],
            ["blindées"], ["portes blindées"], ["Vachette"], ["Fichet"],
            ["crochetage"], ["clefs"], ["changer la serrure"],
            ["nouvelle serrure"], ["pose de serrure"], ["dépanner"],
            ["dépannage serrurier"], ["faire appel à un serrurier"],
            ["faites appel"], ["artisan serrurier"],
            ["serrurier professionnel"], ["entreprise de serrurerie"],
            ["porte de garage"], ["tentative d'effraction"],
            ["demi-tour"], ["pêne demi-tour"], ["verrous"],
            ["serrure de porte"], ["type de serrure"],
            ["types de serrures"], ["métalliques"], ["lock"],
        ],
    },
    "securiser-un-commerce.html": {
        "requete": "sécuriser un commerce local professionnel",
        "termes": [
            ["commerce"], ["local professionnel", "locaux professionnels"],
            ["boutique"], ["atelier"], ["entrepôt"], ["bureau"],
            ["vitrine"], ["devanture"], ["rideau métallique"],
            ["grille"], ["vitrage feuilleté", "feuilleté"],
            ["serrure de sol", "serrures de sol"], ["coulisse"],
            ["tablier"], ["organigramme"], ["passe général"],
            ["plan de fermeture"], ["carte de propriété"],
            ["contrôle d'accès"], ["badge"], ["cylindre"],
            ["clés"], ["trousseau"], ["salarié"], ["personnel"],
            ["saisonnier"], ["prestataire"], ["coffre-fort"],
            ["scellement", "scellé"], ["espèces"], ["caisse"], ["stock"],
            ["issue de secours", "issues de secours"],
            ["barre anti-panique"], ["public", "recevant du public"],
            ["alarme"], ["vidéoprotection"],
            ["assurance", "assureur"],
            ["multirisque professionnelle", "multirisque"],
            ["clause de protection", "moyens de protection"],
            ["indemnisation"], ["perte d'exploitation"],
            ["effraction"], ["intrusion"], ["vol"],
            ["fermeture prolongée", "période de fermeture"],
            ["maintenance", "entretien"], ["dégrippage", "lubrifi"],
            ["embruns", "sel"], ["devis"], ["diagnostic"],
        ],
        # Les 36 mots-clés demandés : présence ET emploi répété.
        "renforces": [
            ["porte de garage"], ["portes de garage"], ["haute sécurité"],
            ["cambriolage"], ["cambriolages"], ["cambrioleurs"],
            ["A2P"], ["verrou"], ["blindées"], ["portes blindées"],
            ["Vachette"], ["Fichet"], ["Point Fort Fichet"],
            ["multipoints"], ["serrure multipoints"], ["fermetures"],
            ["stores"], ["roulants"], ["volets roulants"],
            ["barillet"], ["serruriers"], ["menuiserie"], ["menuiseries"],
            ["alu"], ["clefs"], ["portails"], ["ouvertures"],
            ["crochetage"], ["lock"], ["niveau de sécurité"],
            ["dépanner"], ["dépannages"], ["coffres-forts"],
            ["pêne"], ["tentative d'effraction"], ["gâche"],
        ],
    },
    "serrure-locataire-proprietaire.html": {
        "requete": "serrure qui paie locataire ou propriétaire",
        "termes": [
            ["locataire"], ["propriétaire"], ["bailleur"], ["bail"],
            ["logement"], ["dépôt de garantie"], ["état des lieux"],
            ["vétusté"], ["réparations locatives", "réparation locative"],
            ["décret", "26 août 1987"], ["loi du 6 juillet 1989", "1989"],
            ["entretien courant"], ["menues réparations", "petites pièces"],
            ["serrure"], ["serrurier"], ["cylindre"], ["clés", "clefs"],
            ["clés perdues", "perte de clés", "clefs égarées"],
            ["reproduction", "double"], ["verrou"], ["porte d'entrée"],
            ["porte palière"], ["copropriété"], ["syndic"],
            ["règlement de copropriété"], ["parties communes"],
            ["partie privative", "parties privatives"],
            ["changement de serrure", "changer la serrure"],
            ["remplacement"], ["dépannage"], ["facture"], ["devis"],
            ["assurance habitation"], ["garantie"], ["effraction"],
            ["cambriolage"], ["dépôt de plainte"], ["indemnisation"],
            ["force majeure"], ["vice de construction", "malfaçon"],
            ["restitution", "restituer"], ["colocation"],
            ["logement social", "bailleur social", "parc social"],
            ["meublé", "location saisonnière"],
            ["gestion locative", "agence"], ["litige"],
            ["commission départementale de conciliation", "conciliation"],
            ["grille de vétusté"], ["organigramme"], ["astreinte"],
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

    # 1 bis. Occurrences minimales sur les mots-clés renforcés.
    faibles = []
    for variantes in regle.get("renforces", []):
        n = sum(plat.count(sans_accents(v).lower()) for v in variantes)
        if n < RENFORT_MIN:
            faibles.append(f"{variantes[0]} ({n}×)")
    if regle.get("renforces"):
        renforces = len(regle["renforces"])
        notes.append(f"{renforces - len(faibles)}/{renforces} mots-clés à {RENFORT_MIN}× ou plus")
    if faibles:
        defauts.append(
            f"mots-clés trop peu employés (< {RENFORT_MIN}×) : {', '.join(faibles[:10])}"
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


def empreintes(corps_texte: str, n: int = 5) -> set:
    """Les suites de n mots du texte, pour comparer deux articles."""
    mots = re.findall(r"[a-z0-9\']+", sans_accents(corps_texte).lower())
    return {" ".join(mots[i:i + n]) for i in range(len(mots) - n + 1)}


def controler_redondance(pages: dict) -> int:
    """Compare les articles deux à deux et refuse les doublons de fond."""
    from itertools import combinations

    print(f"\n{G}Redondance entre articles{R}")
    if len(pages) < 2:
        print("  un seul article : rien à comparer")
        return 0

    paires = []
    for a, b in combinations(sorted(pages), 2):
        commun = len(pages[a] & pages[b])
        total = len(pages[a] | pages[b])
        paires.append(((commun / total) if total else 0.0, commun, a, b))
    paires.sort(reverse=True)

    pire, commun, a, b = paires[0]
    print(f"  {len(paires)} paires comparées · maximum {pire:.2%}"
          f" ({commun} passages communs entre {a} et {b})")

    fautives = [p for p in paires if p[0] > SEUIL_REDONDANCE]
    for taux, commun, a, b in fautives:
        print(f"  {X} {a} et {b} partagent {taux:.2%} de leur texte")
    if fautives:
        print(f"\n  Deux articles qui se recouvrent à plus de {SEUIL_REDONDANCE:.0%}")
        print("  se cannibalisent : Google en retient un et ignore l'autre.")
        return 1
    print(f"  {V} Chaque article traite un sujet distinct.")
    return 0


def main() -> int:
    if not PUBLIC.is_dir():
        print("public/blog est absent : lancez d'abord bash scripts/build.sh")
        return 1

    print(f"\n{G}Articles : couverture sémantique, ancrage breton, appel à l'action{R}")
    code = 0
    empreintes_par_article = {}
    for nom, regle in CHAMPS.items():
        fichier = PUBLIC / nom
        if not fichier.is_file():
            print(f"  {X} {nom} : article introuvable")
            code = 1
            continue
        empreintes_par_article[nom] = empreintes(
            texte_visible(corps_article(fichier.read_text(encoding="utf-8")))
        )
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

    code = controler_redondance(empreintes_par_article) or code

    print()
    if code == 0:
        print(f"  {V} Tous les articles couvrent leur sujet, nomment les départements")
        print("      desservis et se terminent par une invitation à appeler.")
    return code


if __name__ == "__main__":
    sys.exit(main())
