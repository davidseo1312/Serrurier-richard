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
source src/config.sh

for v in FTP_HOST FTP_USER FTP_PASS; do
  [ -n "${!v:-}" ] || { echo "Variable $v absente de .env"; exit 1; }
done
FTP_DIR="${FTP_DIR:-/public_html}"

[ -d public ] || { echo "public/ absent — lancez d'abord : bash scripts/build.sh"; exit 1; }

# --- Contrôle avant envoi ---------------------------------------------------
echo "Contrôle SEO avant déploiement..."
if ! bash scripts/check-seo.sh > /tmp/check-seo.log 2>&1; then
  echo
  echo "Le contrôle signale des défauts techniques :"
  grep -E '^\s+x' /tmp/check-seo.log | sed 's/\x1b\[[0-9;]*m//g'
  echo
  read -r -p "Déployer quand même ? (o/N) " reponse
  case "$reponse" in [oO]*) ;; *) echo "Déploiement annulé."; exit 1 ;; esac
fi

# --- Envoi ------------------------------------------------------------------
TOTAL=$(find public -type f | wc -l)
PARALLELE="${FTP_PARALLELE:-4}"
case "$PARALLELE" in ''|*[!0-9]*) PARALLELE=4 ;; esac
if [ "$PARALLELE" -lt 1 ]; then PARALLELE=1; fi
if [ "$PARALLELE" -gt 8 ]; then PARALLELE=8; fi

echo
echo "Déploiement de $TOTAL fichiers vers ftp://$FTP_HOST$FTP_DIR/"
if [ "$DRY" -eq 1 ]; then echo "(simulation — aucun fichier ne sera envoyé)"; fi
echo "($PARALLELE envois simultanés)"
echo

ECHECS="$(mktemp)"
trap 'rm -f "$ECHECS"' EXIT

envoyer() {
  rel="${1#public/}"
  if [ "$DRY" -eq 1 ]; then
    printf '  · %s\n' "$rel"
    return 0
  fi
  # --ftp-create-dirs crée l'arborescence manquante côté serveur.
  if curl --silent --show-error --fail --connect-timeout 20 --max-time 180 \
          --ftp-create-dirs \
          --user "${FTP_USER}:${FTP_PASS}" \
          --upload-file "$1" \
          "ftp://${FTP_HOST}${FTP_DIR}/${rel}"; then
    printf '  v %s\n' "$rel"
  else
    printf '  x %s\n' "$rel"
    echo "$rel" >> "$ECHECS"
  fi
}
export -f envoyer
export FTP_HOST FTP_USER FTP_PASS FTP_DIR DRY ECHECS

# Les fichiers cachés (.htaccess) sont inclus : c'est lui qui produit les URLs
# sans extension et les redirections. L'oublier casse tout le site.
find public -type f | sort | xargs -P "$PARALLELE" -I{} bash -c 'envoyer "$@"' _ {}

NB_ECHECS=$(grep -c . "$ECHECS" 2>/dev/null || echo 0)

echo
if [ "$DRY" -eq 1 ]; then
  echo "Simulation terminée : $TOTAL fichiers seraient envoyés."
  exit 0
fi

if [ "${NB_ECHECS:-0}" -gt 0 ]; then
  echo "$NB_ECHECS fichier(s) en échec :"
  sed 's/^/    /' "$ECHECS"
  echo
  echo "Relancez la commande : seuls les fichiers manquants seront réécrits."
  exit 1
fi

echo "Déploiement terminé : $TOTAL fichiers envoyés."
echo
echo "À vérifier maintenant, dans cet ordre :"
echo "  1. https://${DOMAINE}/ répond, et http:// redirige bien vers https://"
echo "  2. Les URLs sans extension fonctionnent : https://${DOMAINE}/tarifs"
echo "     (si elles renvoient 404, le .htaccess n'est pas monté ou mod_rewrite"
echo "      est désactivé : voir la section Hostinger du README)"
echo "  3. Une URL inexistante affiche la page 404 personnalisée"
echo "  4. Les anciennes adresses redirigent : /services/ouverture-de-porte"
echo "  5. https://${DOMAINE}/sitemap.xml et /robots.txt sont accessibles"
echo "  6. Le formulaire : https://${DOMAINE}/devis-serrurerie"
echo "     Envoyez une demande de test et vérifiez la réception sur"
echo "     ${EMAIL_DEVIS}. Si rien n'arrive, la boîte d'envoi"
echo "     ${EMAIL_EXPEDITEUR} n'existe probablement pas encore :"
echo "     créez-la dans hPanel > Emails."
