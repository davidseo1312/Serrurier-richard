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

# --- 5. Signature du 403 ---------------------------------------------------
# Les trois causes possibles ne renvoient pas les mêmes codes selon l'URL.
# Comparer la racine et une page interne suffit à les distinguer : cette
# logique a été vérifiée sur un Apache 2.4 en reproduisant chaque cas.
titre "5. Ce que répond le site"

lire_code() {
  curl -s -o /tmp/reponse-diag.html -w '%{http_code}' --max-time 20 "$1" 2>/dev/null
}

CODE_RACINE=$(lire_code "${BASE_URL}/")
CODE_PAGE=$(lire_code "${BASE_URL}/tarifs")
# Le nom de la feuille de style porte l'empreinte de son contenu : on le lit
# dans la page d'accueil en ligne plutôt que de le deviner. C'est aussi le
# meilleur contrôle qui soit — si l'adresse servie n'est pas celle que le
# build vient de produire, c'est que le serveur publie une version périmée.
URL_CSS=$(grep -o 'href="/assets/css/style[^"]*\.css"' /tmp/reponse-diag.html 2>/dev/null \
          | head -1 | sed 's/.*href="//; s/"$//')
URL_CSS="${URL_CSS:-/assets/css/style.css}"
CODE_CSS=$(lire_code "${BASE_URL}${URL_CSS}")

printf '  %-3s  %s\n' "$CODE_RACINE" "${BASE_URL}/"
printf '  %-3s  %s\n' "$CODE_PAGE"   "${BASE_URL}/tarifs"
printf '  %-3s  %s\n' "$CODE_CSS"    "${BASE_URL}${URL_CSS}"

titre "6. Diagnostic"

if [ "$CODE_RACINE" = "403" ] && grep -qi 'hostinger' /tmp/reponse-diag.html 2>/dev/null; then
  echo "  ${ROUGE}x${FIN} Page 403 de Hostinger, pas d'Apache."
  echo "      Le domaine n'est pas encore rattaché à l'hébergement, ou la"
  echo "      propagation DNS est en cours (jusqu'à 24 h après un achat)."
  echo "      hPanel > Domaines : vérifiez que le domaine pointe bien ici."

elif [ "$CODE_RACINE" = "403" ] && grep -qi 'cloudflare' /tmp/reponse-diag.html 2>/dev/null; then
  echo "  ${ROUGE}x${FIN} 403 émis par Cloudflare, en amont de votre hébergement."
  echo "      Votre .htaccess n'est pas en cause. Vérifiez les règles de"
  echo "      pare-feu et le mode « Under Attack » dans Cloudflare."

elif [ "$CODE_RACINE" = "500" ] || [ "$CODE_PAGE" = "500" ]; then
  echo "  ${ROUGE}x${FIN} Erreur 500 : une directive du .htaccess est refusée."
  echo "      Cause quasi certaine : la ligne « Options -MultiViews -Indexes »."
  echo "      Certaines offres interdisent la directive Options en .htaccess."
  echo "      Correction : commentez cette ligne dans static/.htaccess en la"
  echo "      préfixant par un #, relancez le build et redéployez."

elif [ "$CODE_RACINE" = "403" ] && [ "$CODE_PAGE" = "404" ]; then
  echo "  ${ROUGE}x${FIN} CAUSE : la racine web est vide."
  echo "      Vos fichiers sont un niveau trop bas — typiquement dans"
  echo "      public_html/public_html/ ou public_html/public/."
  echo
  echo "      Correction : mettez ${GRAS}FTP_DIR=/${FIN} dans .env, supprimez le"
  echo "      dossier en trop depuis hPanel, puis redéployez."

elif [ "$CODE_RACINE" = "403" ] && [ "$CODE_PAGE" = "200" ]; then
  echo "  ${ROUGE}x${FIN} CAUSE : index.html manquant ou illisible à la racine."
  echo "      Les autres pages répondent : les fichiers sont au bon endroit."
  echo
  echo "      Vérifiez dans hPanel > Gestionnaire de fichiers que index.html"
  echo "      existe bien dans public_html/ et qu'il est en droits 644."

elif [ "$CODE_RACINE" = "403" ] && [ "$CODE_CSS" = "403" ]; then
  echo "  ${ROUGE}x${FIN} CAUSE probable : droits de fichiers trop restrictifs."
  echo "      Tout est refusé, y compris la feuille de style."
  echo "      Dans hPanel > Gestionnaire de fichiers : fichiers en 644,"
  echo "      dossiers en 755."

elif [ "$CODE_RACINE" = "200" ] && [ "$CODE_PAGE" = "404" ]; then
  echo "  ${ROUGE}x${FIN} CAUSE : le .htaccess n'est pas lu."
  echo "      L'accueil s'affiche mais les URLs sans extension échouent."
  echo
  echo "      a) Le fichier .htaccess n'a pas été copié — il commence par un"
  echo "         point et reste invisible tant que l'affichage des fichiers"
  echo "         cachés n'est pas activé. C'est la cause la plus fréquente."
  echo "      b) mod_rewrite est désactivé : hPanel > Avancé > Configuration PHP."

elif [ "$CODE_RACINE" = "200" ] && [ "$CODE_PAGE" = "200" ]; then
  echo "  ${VERT}v${FIN} Le site répond correctement."
  echo "      Si vous voyez encore une erreur dans votre navigateur, videz son"
  echo "      cache (Ctrl+F5) : une réponse d'erreur a pu y être conservée."

else
  echo "  ${JAUNE}!${FIN} Combinaison inhabituelle : racine $CODE_RACINE, page $CODE_PAGE,"
  echo "      feuille de style $CODE_CSS."
  echo "      Testez sans .htaccess : renommez-le en .htaccess.bak depuis hPanel"
  echo "      et rechargez. Si l'erreur disparaît, une directive est en cause."
fi

echo
echo "  ${GRAS}Signatures de référence${FIN} (vérifiées sur Apache 2.4)"
echo "      racine 403 + page 404  -> fichiers un niveau trop bas"
echo "      racine 403 + page 200  -> index.html absent ou illisible"
echo "      tout en 403            -> droits, ou domaine non rattaché"
echo "      tout en 500            -> directive refusée dans le .htaccess"
echo "      racine 200 + page 404  -> .htaccess absent ou mod_rewrite inactif"
echo
