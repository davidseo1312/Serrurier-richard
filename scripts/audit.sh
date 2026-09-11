#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Audit complet avant mise en ligne.
#
#   bash scripts/audit.sh
#
# Enchaîne tous les contrôles disponibles et affiche un tableau de synthèse.
# Les étapes qui demandent un outil absent (Python, Playwright) sont marquées
# « ignorée » et n'empêchent pas l'audit d'aboutir : seuls le build et le
# contrôle SEO sont indispensables.
#
# Code de sortie 1 si une étape obligatoire échoue.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ROUGE=$'\033[31m'; JAUNE=$'\033[33m'; VERT=$'\033[32m'; GRAS=$'\033[1m'; FIN=$'\033[0m'

RESULTATS=""
ECHEC=0

etape() {
  local libelle="$1" statut="$2"
  RESULTATS="${RESULTATS}${libelle}|${statut}"$'\n'
}

titre() { echo; echo "${GRAS}=== $1 ===${FIN}"; echo; }

# --- 1. Construction --------------------------------------------------------
titre "1/8  Construction"
if bash scripts/build.sh; then
  etape "BUILD" "OK"
else
  etape "BUILD" "ECHEC"; ECHEC=1
  echo "${ROUGE}Le build a échoué : les étapes suivantes n'ont pas de sens.${FIN}"
  exit 1
fi

# --- 2. SEO, liens, ressources ---------------------------------------------
titre "2/8  Contrôle SEO, liens internes et ressources"
if bash scripts/check-seo.sh; then
  etape "SEO / LIENS" "OK"
else
  etape "SEO / LIENS" "ECHEC"; ECHEC=1
fi

# --- 3. Structure HTML ------------------------------------------------------
titre "3/8  Structure HTML"
if command -v python3 > /dev/null; then
  if python3 scripts/check-html.py; then
    etape "HTML" "OK"
  else
    etape "HTML" "ECHEC"; ECHEC=1
  fi
else
  echo "Python 3 absent : contrôle ignoré."
  etape "HTML" "IGNOREE"
fi

# --- 4. Données structurées -------------------------------------------------
titre "4/8  Données structurées"
if command -v python3 > /dev/null; then
  if python3 - <<'PY'
import json, re, glob, sys
invalides, blocs = [], 0
for f in sorted(set(glob.glob('public/**/*.html', recursive=True))):
    html = open(f, encoding='utf-8').read()
    for bloc in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        blocs += 1
        try:
            json.loads(bloc)
        except Exception as e:
            invalides.append(f"{f} : {e}")
print(f"  {blocs} bloc(s) JSON-LD analysé(s)")
for i in invalides:
    print("  x", i)
sys.exit(1 if invalides else 0)
PY
  then
    etape "JSON-LD" "OK"
  else
    etape "JSON-LD" "ECHEC"; ECHEC=1
  fi
else
  echo "Python 3 absent : contrôle ignoré."
  etape "JSON-LD" "IGNOREE"
fi

# --- 5. Parcours navigateur -------------------------------------------------
titre "5/8  Parcours navigateur (mobile, tablette, ordinateur)"
if command -v node > /dev/null && command -v php > /dev/null \
   && node -e "require.resolve('playwright')" 2>/dev/null; then
  if bash tests/lancer.sh; then
    etape "TESTS NAVIGATEUR" "OK"
  else
    etape "TESTS NAVIGATEUR" "ECHEC"; ECHEC=1
  fi
else
  echo "PHP ou Playwright absent : tests ignorés."
  echo "Pour les activer : npm install playwright && npx playwright install chromium"
  etape "TESTS NAVIGATEUR" "IGNOREE"
fi

# --- 6. Simulation du déploiement Hostinger --------------------------------
# Une erreur 403 sur un mutualisé a presque toujours la même origine : le
# dossier servi par Apache ne contient pas de page d'accueil. Cette étape
# reconstitue ce qu'Apache verra et le vérifie, sans avoir besoin d'Apache.
# --- 5 bis. Indexation -----------------------------------------------------
titre "6/8  Indexation"
if command -v python3 > /dev/null; then
  if python3 scripts/audit-indexation.py; then
    etape "INDEXATION" "OK"
  else
    etape "INDEXATION" "ECHEC"; ECHEC=1
  fi
else
  echo "Python 3 absent : audit ignoré."
  etape "INDEXATION" "IGNOREE"
fi

# --- 6. Images -------------------------------------------------------------
titre "7/8  Images et SEO images"
if command -v python3 > /dev/null; then
  if python3 scripts/audit-images.py; then
    etape "IMAGES" "OK"
  else
    etape "IMAGES" "ECHEC"; ECHEC=1
  fi
else
  echo "Python 3 absent : audit ignoré."
  etape "IMAGES" "IGNOREE"
fi

titre "8/8  Simulation du déploiement Hostinger"

PB403=0
signaler() { echo "  ${ROUGE}x${FIN} $1"; PB403=1; }
valider()  { echo "  ${VERT}v${FIN} $1"; }

# a) Ce que Hostinger servira comme racine web est le contenu de public/.
if [ -f public/index.html ]; then
  valider "index.html présent à la racine du document root"
else
  signaler "index.html ABSENT de la racine — Apache renverrait 403"
fi

# b) Aucune couche intermédiaire.
COUCHE=0
for d in public/public public/dist public/build public/serrurier-richard; do
  if [ -d "$d" ]; then signaler "couche superflue : $d/"; COUCHE=1; fi
done
[ "$COUCHE" -eq 0 ] && valider "aucune couche superflue dans le document root"

# c) Le dépôt lui-même ne doit pas réintroduire d'imbrication.
if [ -d serrurier-richard ]; then
  signaler "dossier serrurier-richard/ à la racine du dépôt : imbrication réintroduite"
else
  valider "racine du dépôt à plat"
fi

# d) Le .htaccess, sans lequel les URLs sans extension tombent en 404.
if [ -f public/.htaccess ]; then
  valider ".htaccess présent dans le document root"
  grep -q 'ErrorDocument 404' public/.htaccess \
    && valider "page 404 personnalisée déclarée" \
    || signaler "ErrorDocument 404 absent du .htaccess"
  grep -q 'RewriteRule \^\\\.git' public/.htaccess \
    && valider "dossier .git bloqué (le déploiement Git en dépose un)" \
    || signaler ".git non bloqué : le code source serait lisible en ligne"
else
  signaler ".htaccess absent : toutes les URLs sans extension renverraient 404"
fi

# e) Le workflow qui alimente la branche servie par Hostinger.
if [ -f .github/workflows/deploy.yml ]; then
  valider "workflow de publication présent"
  grep -q 'HEAD:deploy\|origin deploy' .github/workflows/deploy.yml \
    && valider "il publie bien vers la branche deploy" \
    || signaler "le workflow ne publie pas vers la branche deploy"
else
  signaler "aucun workflow : la branche deploy ne serait jamais alimentée"
fi

# f) Reconstitution du dossier tel qu'il arrivera sur le serveur.
TMP_SIM="$(mktemp -d)"
cp -a public/. "$TMP_SIM"/ 2>/dev/null
if [ -f "$TMP_SIM/index.html" ]; then
  valider "simulation : le clone de la branche deploy expose index.html à sa racine"
else
  signaler "simulation : la racine du clone serait sans index.html"
fi
NB_FICHIERS=$(find "$TMP_SIM" -type f | wc -l | tr -d ' ')
rm -rf "$TMP_SIM"
echo "      ${NB_FICHIERS} fichiers seraient déployés"

if [ "$PB403" -eq 0 ]; then
  etape "403 CHECK" "OK"
else
  etape "403 CHECK" "ECHEC"; ECHEC=1
fi

# --- Synthèse ---------------------------------------------------------------
echo
echo "${GRAS}================ SYNTHÈSE DE L'AUDIT ================${FIN}"
echo
while IFS='|' read -r libelle statut; do
  [ -z "$libelle" ] && continue
  case "$statut" in
    OK)      couleur="$VERT" ;;
    IGNOREE) couleur="$JAUNE" ;;
    *)       couleur="$ROUGE" ;;
  esac
  printf '  %-28s %s%s%s\n' "$libelle" "$couleur" "$statut" "$FIN"
done <<< "$RESULTATS"

# Le déploiement dépend uniquement des étapes techniques.
if [ "$ECHEC" -eq 0 ]; then
  printf '  %-28s %s%s%s\n' "DÉPLOIEMENT HOSTINGER" "$VERT" "PRÊT" "$FIN"
  echo
  echo "  Le dossier public/ ($(find public -type f | wc -l | tr -d ' ') fichiers,"
  echo "  $(du -sh public | cut -f1)) peut être déposé tel quel dans public_html/."
  echo
  echo "  Rappel : renseignez les informations manquantes listées ci-dessus"
  echo "  (assureur, médiateur) avant l'ouverture au public, et lisez la section"
  echo "  « Cohérence géographique » du README avant de passer le site en index."
else
  printf '  %-28s %s%s%s\n' "DÉPLOIEMENT HOSTINGER" "$ROUGE" "BLOQUÉ" "$FIN"
  echo
  echo "  Corrigez les étapes en échec ci-dessus, puis relancez cet audit."
fi
echo
echo "${GRAS}====================================================${FIN}"
echo

exit "$ECHEC"
