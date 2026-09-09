#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Aperçu local du site, avec les mêmes URLs qu'en production.
#
#   bash scripts/apercu.sh            # http://localhost:8080
#   bash scripts/apercu.sh 3000       # sur un autre port
#
# Le serveur intégré de PHP est utilisé pour deux raisons : il reproduit les
# URLs sans extension via scripts/routeur-local.php, et il permet de tester
# réellement le formulaire de devis, qui est en PHP.
#
# Sur Hostinger, ces mêmes URLs sont produites par le .htaccess : il n'y a
# aucune configuration à refaire au déploiement.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT="${1:-8080}"

command -v php >/dev/null || {
  echo "PHP n'est pas installé sur ce poste."
  echo "Sans lui, ouvrez directement public/index.html : la mise en page sera"
  echo "fidèle, mais les URLs sans extension et le formulaire ne fonctionneront pas."
  exit 1
}

[ -d public ] || bash scripts/build.sh

echo
echo "  Aperçu du site : http://localhost:${PORT}"
echo "  Ctrl+C pour arrêter."
echo
echo "  Note : l'envoi réel d'un e-mail par le formulaire ne fonctionne pas en"
echo "  local (aucun serveur de messagerie). La validation, elle, est testable."
echo

exec php -S "localhost:${PORT}" -t public scripts/routeur-local.php
