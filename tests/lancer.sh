#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Lance les tests de navigateur sur un aperçu local.
#
#   bash tests/lancer.sh
#
# Le script construit le site, démarre le serveur d'aperçu, exécute
# tests/navigateur.mjs, puis arrête le serveur.
#
# Prérequis : PHP (pour l'aperçu) et Playwright (pour le navigateur).
#   npm install playwright && npx playwright install chromium
#
# Ces tests sont FACULTATIFS : ils ne conditionnent ni le build ni le
# déploiement. Ils servent à vérifier, avant une mise en ligne, que les
# parcours réels fonctionnent encore.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT="${PORT:-8099}"

command -v php >/dev/null || { echo "PHP est requis pour l'aperçu local."; exit 1; }
command -v node >/dev/null || { echo "Node.js est requis pour les tests."; exit 1; }

if ! node -e "require.resolve('playwright')" 2>/dev/null; then
  echo
  echo "Playwright n'est pas installé. Pour l'ajouter :"
  echo "    npm install playwright && npx playwright install chromium"
  echo
  echo "Les tests de navigateur sont facultatifs : le site se construit et se"
  echo "déploie sans eux. Lancez au minimum :"
  echo "    bash scripts/build.sh && bash scripts/check-seo.sh"
  exit 1
fi

echo "Construction du site..."
bash scripts/build.sh > /dev/null || { echo "Le build a échoué."; exit 1; }

php -S "localhost:${PORT}" -t public scripts/routeur-local.php > /dev/null 2>&1 &
SERVEUR=$!
# Le serveur est arrêté quoi qu'il arrive, y compris en cas d'interruption.
trap 'kill "$SERVEUR" 2>/dev/null' EXIT INT TERM

# Attente active plutôt qu'un sleep fixe : plus rapide et plus fiable.
for _ in $(seq 1 40); do
  curl -sf -o /dev/null "http://localhost:${PORT}/" && break
  sleep 0.25
done

BASE_URL="http://localhost:${PORT}" node tests/navigateur.mjs
CODE=$?

# Contrôle visuel : mise en page sur onze largeurs, cibles tactiles, formats
# d'image et contraste. Séparé de navigateur.mjs parce qu'il balaie TOUTES les
# pages du sitemap, et non un échantillon de parcours.
BASE_URL="http://localhost:${PORT}" node tests/visuels.mjs || CODE=1

exit "$CODE"
