#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Déploiement du dossier public/ vers Hostinger par FTP.
#
#   bash scripts/deploy-hostinger.sh          # déploiement réel
#   bash scripts/deploy-hostinger.sh --dry    # simulation, aucun envoi
#
# Les identifiants sont lus dans .env, qui est ignoré par Git et ne doit
# JAMAIS être versionné. Créez-le à partir de .env.exemple.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DRY=0
[ "${1:-}" = "--dry" ] && DRY=1

# --- Identifiants -----------------------------------------------------------
if [ ! -f .env ]; then
  cat <<'AIDE'
Fichier .env introuvable.

Créez-le à la racine du projet avec vos identifiants FTP Hostinger
(hPanel > Fichiers > Comptes FTP) :

    FTP_HOST=ftp.votre-domaine.fr
    FTP_USER=u123456789
    FTP_PASS=votre-mot-de-passe
    FTP_DIR=/public_html

Ce fichier est ignoré par Git : vos identifiants ne partiront jamais
sur GitHub.
AIDE
  exit 1
fi

set -a; source .env; set +a

for v in FTP_HOST FTP_USER FTP_PASS; do
  [ -n "${!v:-}" ] || { echo "Variable $v absente de .env"; exit 1; }
done
FTP_DIR="${FTP_DIR:-/public_html}"

[ -d public ] || { echo "public/ absent — lancez d'abord : bash scripts/build.sh"; exit 1; }

# --- Contrôle avant envoi ---------------------------------------------------
echo "Contrôle SEO avant déploiement..."
if ! bash scripts/check-seo.sh > /tmp/check-seo.log 2>&1; then
  echo
  echo "Le contrôle SEO signale des erreurs bloquantes :"
  grep -E '^\s+x' /tmp/check-seo.log | sed 's/\x1b\[[0-9;]*m//g'
  echo
  read -r -p "Déployer quand même ? (o/N) " reponse
  case "$reponse" in [oO]*) ;; *) echo "Déploiement annulé."; exit 1 ;; esac
fi

# --- Envoi ------------------------------------------------------------------
NB=0
TOTAL=$(find public -type f | wc -l)
echo
echo "Déploiement de $TOTAL fichiers vers ftp://$FTP_HOST$FTP_DIR/"
[ "$DRY" -eq 1 ] && echo "(simulation — aucun fichier ne sera envoyé)"
echo

while IFS= read -r fichier; do
  rel="${fichier#public/}"
  cible="ftp://${FTP_HOST}${FTP_DIR}/${rel}"
  NB=$((NB + 1))
  printf '  [%2d/%2d] %s\n' "$NB" "$TOTAL" "$rel"
  if [ "$DRY" -eq 0 ]; then
    curl --silent --show-error --fail \
         --ftp-create-dirs \
         --user "${FTP_USER}:${FTP_PASS}" \
         --upload-file "$fichier" \
         "$cible" \
      || { echo "  ERREUR sur $rel"; exit 1; }
  fi
done < <(find public -type f | sort)

echo
if [ "$DRY" -eq 1 ]; then
  echo "Simulation terminée : $TOTAL fichiers seraient envoyés."
else
  echo "Déploiement terminé : $TOTAL fichiers envoyés."
  echo
  echo "À vérifier maintenant :"
  echo "  1. Le site répond en HTTPS et redirige bien depuis http://"
  echo "  2. Les URLs sans extension fonctionnent (ex: /tarifs)"
  echo "  3. Une URL inexistante affiche bien la page 404"
  echo "  4. Le sitemap est accessible : /sitemap.xml"
fi
