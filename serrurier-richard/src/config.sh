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

# --- Analytics --------------------------------------------------------------
# Laisser vide tant que la propriété GA4 n'est pas créée.
GA4_ID=""

# --- Indexation -------------------------------------------------------------
# "noindex" tant que le site n'est pas prêt à être référencé, "index" ensuite.
ROBOTS_POLICY="noindex"
