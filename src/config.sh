# ---------------------------------------------------------------------------
# Configuration centrale du site.
# Toute valeur modifiée ici est répercutée sur l'ensemble des pages au build.
# ---------------------------------------------------------------------------

# --- Identité ---------------------------------------------------------------
NOM_COMMERCIAL="Serrurier Richard"
BASELINE="Dépannage serrurerie 24h/24 dans le Grand Ouest"
DOMAINE="serrurier-richard.fr"
BASE_URL="https://serrurier-richard.fr"

# --- Contact ----------------------------------------------------------------
TELEPHONE="02 20 06 00 75"
TELEPHONE_E164="+33220060075"
EMAIL="contact@serrurier-richard.fr"

# --- Identité légale --------------------------------------------------------
# Données vérifiées le 08/09/2026 auprès du registre national des entreprises
# (recherche-entreprises.api.gouv.fr, SIREN 901133041).
RAISON_SOCIALE="Bilal Assoul"
FORME_JURIDIQUE="Entrepreneur individuel"
CAPITAL=""                       # Sans objet pour une entreprise individuelle
SIRET="901 133 041 00011"
SIREN="901 133 041"
RCS="Immatriculée au Registre National des Entreprises (RNE) sous le numéro 901 133 041"
DATE_CREATION="6 juillet 2021"

# Aucun numéro de TVA intracommunautaire actif au 08/09/2026 (vérifié VIES).
# Cohérent avec la franchise en base de TVA. Si l'entreprise devient
# assujettie, renseigner TVA_NUMERO et basculer MENTION_TVA.
TVA_NUMERO=""
MENTION_TVA="TVA non applicable, article 293 B du code général des impôts"
UNITE_PRIX="€"                   # Mettre "€ TTC" si assujetti à la TVA

# --- Adresse du siège (mentions légales) ------------------------------------
# ⚠ ATTENTION : le siège déclaré est à Courbevoie (92), alors que le site
# revendique une implantation à Rennes et une couverture bretonne. Tant que
# cet écart n'est pas résolu, le site ne doit pas être publié : voir la
# section « Cohérence géographique » du README.
SIEGE_RUE="1 rue Albert Simonin"
SIEGE_CP="92400"
SIEGE_VILLE="Courbevoie"

# --- Base opérationnelle (balisage LocalBusiness, délais annoncés) ----------
# ⚠ À N'UTILISER que si un établissement réel existe à cette adresse.
ADRESSE_RUE="[ÉTABLISSEMENT BRETON À CRÉER OU GÉOGRAPHIE DU SITE À CORRIGER]"
ADRESSE_CP="35000"
ADRESSE_VILLE="Rennes"
LATITUDE="48.117266"
LONGITUDE="-1.677793"

# --- Activité déclarée ------------------------------------------------------
# ⚠ APE au registre : 81.29A (désinfection, désinsectisation, dératisation).
# Le dépannage en serrurerie relève du 43.32B. À faire corriger auprès de
# l'INSEE, et vérifier que la RC Pro couvre bien la serrurerie.
CODE_APE="81.29A"

# --- Assurances et médiation (obligatoires) ---------------------------------
ASSUREUR_RCPRO="[ASSUREUR RC PRO]"
POLICE_RCPRO="[N° DE POLICE]"
ASSUREUR_DECENNALE="[ASSUREUR DÉCENNALE]"
MEDIATEUR_NOM="[NOM DU MÉDIATEUR DE LA CONSOMMATION]"
MEDIATEUR_URL="[URL DU MÉDIATEUR]"

# --- Tarifs affichés (arrêté du 24 janvier 2017) ----------------------------
# ⚠ Ces montants DOIVENT correspondre aux tarifs réellement pratiqués.
TAUX_HORAIRE="65"
FRAIS_DEPLACEMENT="35"
MAJORATION_NUIT="50"
FORFAIT_OUVERTURE_SIMPLE="129"
FORFAIT_OUVERTURE_BLINDEE="249"
FORFAIT_CHANGEMENT_CYLINDRE="159"
FORFAIT_OUVERTURE_VERROUILLEE="179"
FORFAIT_EXTRACTION_CLE="99"

# --- Analytics --------------------------------------------------------------
# Laisser vide tant que la propriété GA4 n'est pas créée.
GA4_ID=""

# --- Indexation -------------------------------------------------------------
# "index"  : robots.txt autorise l'exploration et déclare le sitemap, et
#            chaque page porte <meta name="robots" content="index, follow">.
# "noindex": robots.txt bloque tout, et chaque page porte "noindex".
#
# Deux pages gardent "noindex" quoi qu'il arrive, par leurs propres
# métadonnées : /merci (page de confirmation, sans intérêt pour un moteur et
# source de doublons) et la 404.
#
# ⚠ RESTE À RÉGLER AVANT QUE LE RÉFÉRENCEMENT SOIT SAIN — ces points ne
#   bloquent pas l'indexation techniquement, mais ils l'affaibliront :
#   · l'établissement déclaré au registre (SIREN 901133041) est domicilié à
#     Courbevoie avec le code APE 81.29A, qui ne correspond pas à la
#     serrurerie, alors que le site annonce une base dans le Grand Ouest ;
#   · l'assureur RC Pro et le médiateur de la consommation sont encore vides
#     dans les mentions légales, alors qu'ils sont obligatoires ;
#   · aucune fiche Google Business Profile n'est rattachée : sans elle, un
#     serrurier local ne remonte pas sur les requêtes géolocalisées.
ROBOTS_POLICY="index"

# ---------------------------------------------------------------------------
# --- Disponibilité et horaires ---------------------------------------------
# ⚠ N'annoncez que la disponibilité réellement assurée. Une promesse « 24h/24 »
# non tenue est une pratique commerciale trompeuse (art. L121-2 code de la
# consommation) et fait chuter la note Google Business Profile.
# Ces valeurs alimentent aussi le balisage LocalBusiness : elles doivent
# correspondre exactement à ce qui est affiché sur le site.
DISPONIBILITE="24h/24 et 7j/7"
HORAIRES_URGENCE="24 heures sur 24, 7 jours sur 7, jours fériés compris"
HORAIRES_BUREAU="du lundi au vendredi, 8h – 19h"
DELAI_REPONSE="24 à 48 heures ouvrées"

# --- Zone d'intervention (texte affiché) ------------------------------------
ZONE_INTERVENTION="Ille-et-Vilaine (35), Morbihan (56), Finistère (29), Côtes-d'Armor (22), Loire-Atlantique (44) et Maine-et-Loire (49)"
ZONE_COURTE="Bretagne et Pays de la Loire"

# --- Formulaire de devis ----------------------------------------------------
# Adresse qui REÇOIT les demandes de devis.
EMAIL_DEVIS="contact@serrurier-richard.fr"
# Adresse qui ENVOIE le message. Sur un mutualisé Hostinger, elle DOIT
# appartenir au domaine du site, sinon le message part en spam ou est rejeté
# (SPF/DKIM). Créez-la dans hPanel > Emails avant la mise en ligne.
EMAIL_EXPEDITEUR="site@serrurier-richard.fr"
# Poids maximal d'une photo jointe, en mégaoctets.
DEVIS_PHOTO_MAX_MO="5"

# --- Mesure d'audience et vérification Google -------------------------------
# Laisser vide désactive proprement la fonctionnalité : aucun script tiers
# n'est chargé, aucune balise vide n'est écrite dans le HTML.
#
#   GA4_ID    : « G-XXXXXXXXXX »   (Google Analytics 4)
#   GTM_ID    : « GTM-XXXXXXX »    (Google Tag Manager — laisser vide si GA4
#               est utilisé seul ; charger les deux compterait double)
#   GSC_CODE  : contenu de l'attribut « content » de la balise fournie par
#               Google Search Console, méthode « balise HTML ».
#               La vérification par fichier HTML ou par DNS est préférable :
#               elle ne pèse rien sur les pages.
GTM_ID=""
GSC_CODE=""

# --- Réseaux sociaux et fiche Google Business Profile -----------------------
# Renseignez uniquement les profils qui existent réellement : ils alimentent
# le champ « sameAs » des données structurées, que Google recoupe.
URL_GOOGLE_BUSINESS=""
URL_FACEBOOK=""
URL_LINKEDIN=""
