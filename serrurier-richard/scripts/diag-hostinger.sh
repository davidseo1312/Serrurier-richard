#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Diagnostic d'un déploiement Hostinger qui répond 403.
#
#   bash scripts/diag-hostinger.sh
#
# Ne modifie rien : le script se contente de lire le serveur FTP et le site.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

[ -f .env ] || { echo "Fichier .env introuvable (voir .env.exemple)."; exit 1; }
set -a; source .env; set +a
source src/config.sh

GRAS=$'\033[1m'; VERT=$'\033[32m'; ROUGE=$'\033[31m'; JAUNE=$'\033[33m'; FIN=$'\033[0m'
titre() { echo; echo "${GRAS}$1${FIN}"; }

FTP="ftp://${FTP_HOST}"
AUTH=(--user "${FTP_USER}:${FTP_PASS}" --silent --show-error --max-time 25)

lister() {
  curl "${AUTH[@]}" --list-only "${FTP}$1/" 2>&1
}

# --- 1. Connexion ----------------------------------------------------------
titre "1. Connexion FTP"
RACINE=$(lister "/")
if echo "$RACINE" | grep -qi 'login\|denied\|530'; then
  echo "  ${ROUGE}x${FIN} Connexion refusée. Vérifiez FTP_USER et FTP_PASS dans .env."
  echo "$RACINE" | head -3 | sed 's/^/      /'
  exit 1
fi
echo "  ${VERT}v${FIN} Connecté à $FTP_HOST"

# --- 2. Où se trouve la racine web ? ---------------------------------------
titre "2. Contenu de la racine du compte FTP (/)"
echo "$RACINE" | sed 's/^/      /'

titre "3. Où sont réellement les fichiers du site ?"
TROUVE=""
for chemin in "" "/public_html" "/public_html/public_html" "/public_html/public" \
              "/domains/${DOMAINE}/public_html" "/domains/${DOMAINE}/public_html/public" \
              "/domains" "/htdocs" "/www"; do
  contenu=$(lister "$chemin" 2>/dev/null)
  if echo "$contenu" | grep -qx 'index.html'; then
    echo "  ${VERT}v${FIN} index.html trouvé dans : ${chemin:-/}"
    TROUVE="${chemin:-/}"
  elif [ -n "$contenu" ] && ! echo "$contenu" | grep -qi 'not found\|550'; then
    nb=$(echo "$contenu" | grep -c . )
    echo "  ${JAUNE}·${FIN} ${chemin:-/} existe ($nb entrées) mais sans index.html"
  fi
done

# --- 4. Verdict ------------------------------------------------------------
titre "4. Verdict"
if [ -z "$TROUVE" ]; then
  echo "  ${ROUGE}x${FIN} Aucun index.html trouvé. Les fichiers ne sont pas montés,"
  echo "      ou ils sont dans un dossier que ce script n'a pas exploré."
elif [ "$TROUVE" = "/public_html/public_html" ] || [ "$TROUVE" = "/public_html/public" ]; then
  echo "  ${ROUGE}x${FIN} CAUSE TROUVÉE : les fichiers sont dans $TROUVE,"
  echo "      c'est-à-dire un niveau trop bas. La racine web est vide, d'où le 403."
  echo
  echo "  Correction : dans .env, remplacez la ligne FTP_DIR par :"
  echo "      ${GRAS}FTP_DIR=/${FIN}"
  echo "  Puis supprimez le dossier en trop depuis le gestionnaire de fichiers"
  echo "  hPanel, et relancez : bash scripts/deploy-hostinger.sh"
elif [ "$TROUVE" = "/" ]; then
  echo "  ${VERT}v${FIN} Les fichiers sont à la racine FTP."
  echo "      Si le 403 persiste, votre compte FTP pointe déjà sur public_html :"
  echo "      c'est la bonne configuration, cherchez ailleurs (voir point 5)."
else
  echo "  ${VERT}v${FIN} Les fichiers sont dans $TROUVE, ce qui semble correct."
fi

# --- 5. Réponse HTTP réelle ------------------------------------------------
titre "5. Ce que répond le site"
for url in "${BASE_URL}/" "${BASE_URL}/index.html" "${BASE_URL}/tarifs"; do
  code=$(curl -s -o /tmp/reponse.html -w '%{http_code}' --max-time 20 -L "$url" 2>/dev/null)
  printf '  %-3s  %s\n' "$code" "$url"
  if [ "$code" = "403" ]; then
    # Distinguer un 403 Apache d'un 403 Hostinger ou Cloudflare.
    if grep -qi 'hostinger' /tmp/reponse.html 2>/dev/null; then
      echo "        -> page 403 de Hostinger : domaine pas encore rattaché à l'hébergement"
    elif grep -qi 'cloudflare' /tmp/reponse.html 2>/dev/null; then
      echo "        -> 403 Cloudflare : protection en amont, pas votre .htaccess"
    else
      echo "        -> 403 Apache : dossier sans index.html, ou droits insuffisants"
    fi
  fi
done

titre "6. Si le 403 persiste malgré des fichiers bien placés"
cat <<'FIN_AIDE'
      a) Droits des fichiers. Dans hPanel > Gestionnaire de fichiers, les
         fichiers doivent être en 644 et les dossiers en 755. Un envoi FTP
         peut produire des droits trop restrictifs.

      b) Testez sans .htaccess. Renommez-le en .htaccess.bak depuis hPanel
         et rechargez la page. Si le 403 disparaît, le problème vient d'une
         directive : sur certaines offres, Options +FollowSymLinks est
         interdit et déclenche une erreur.

      c) Domaine non rattaché. Si le domaine vient d'être acheté, la
         propagation DNS prend jusqu'à 24 h et Hostinger sert sa propre
         page d'erreur en attendant.

      d) Domaine additionnel. Sa racine n'est pas /public_html mais
         /domains/votre-domaine.fr/public_html — ajustez FTP_DIR.
FIN_AIDE
echo
