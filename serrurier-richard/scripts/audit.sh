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
titre "1/5  Construction"
if bash scripts/build.sh; then
  etape "BUILD" "OK"
else
  etape "BUILD" "ECHEC"; ECHEC=1
  echo "${ROUGE}Le build a échoué : les étapes suivantes n'ont pas de sens.${FIN}"
  exit 1
fi

# --- 2. SEO, liens, ressources ---------------------------------------------
titre "2/5  Contrôle SEO, liens internes et ressources"
if bash scripts/check-seo.sh; then
  etape "SEO / LIENS" "OK"
else
  etape "SEO / LIENS" "ECHEC"; ECHEC=1
fi

# --- 3. Structure HTML ------------------------------------------------------
titre "3/5  Structure HTML"
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
titre "4/5  Données structurées"
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
titre "5/5  Parcours navigateur (mobile, tablette, ordinateur)"
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
  printf '  %-25s %s%s%s\n' "$libelle" "$couleur" "$statut" "$FIN"
done <<< "$RESULTATS"

# Le déploiement dépend uniquement des étapes techniques.
if [ "$ECHEC" -eq 0 ]; then
  printf '  %-25s %s%s%s\n' "DÉPLOIEMENT HOSTINGER" "$VERT" "PRÊT" "$FIN"
  echo
  echo "  Le dossier public/ ($(find public -type f | wc -l | tr -d ' ') fichiers,"
  echo "  $(du -sh public | cut -f1)) peut être déposé tel quel dans public_html/."
  echo
  echo "  Rappel : renseignez les informations manquantes listées ci-dessus"
  echo "  (assureur, médiateur) avant l'ouverture au public, et lisez la section"
  echo "  « Cohérence géographique » du README avant de passer le site en index."
else
  printf '  %-25s %s%s%s\n' "DÉPLOIEMENT HOSTINGER" "$ROUGE" "BLOQUÉ" "$FIN"
  echo
  echo "  Corrigez les étapes en échec ci-dessus, puis relancez cet audit."
fi
echo
echo "${GRAS}====================================================${FIN}"
echo

exit "$ECHEC"
