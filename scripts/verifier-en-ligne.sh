#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Ce que le site EN LIGNE répond vraiment.
#
#   bash scripts/verifier-en-ligne.sh
#
# Aucun identifiant, aucune dépendance : curl suffit. À lancer depuis votre
# poste — un environnement de développement n'a pas toujours accès au domaine.
#
# Il répond à la seule question qui bloque tout quand « ça ne marche pas » :
# le serveur sert-il la version que l'on vient de publier, ou une ancienne ?
# Tant qu'on ne l'a pas tranchée, on corrige à l'aveugle des fichiers que
# personne ne lit.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

GRAS=$'\033[1m'; VERT=$'\033[32m'; ROUGE=$'\033[31m'; JAUNE=$'\033[33m'; FIN=$'\033[0m'
V="${VERT}v${FIN}"; X="${ROUGE}x${FIN}"; ATTENTION="${JAUNE}!${FIN}"

BASE_URL="${1:-$(grep -m1 '^BASE_URL=' src/config.sh | cut -d'"' -f2)}"
BASE_URL="${BASE_URL%/}"
DEFAUTS=0
defaut() { DEFAUTS=$((DEFAUTS + 1)); }

command -v curl > /dev/null || { echo "curl est requis."; exit 1; }

echo
echo "${GRAS}Vérification de ${BASE_URL}${FIN}"

recuperer() {  # $1 = chemin ; remplit CODE, TYPE, CORPS
  CORPS="$(mktemp)"
  CODE="$(curl -sL -o "$CORPS" -w '%{http_code}' --max-time 25 "${BASE_URL}$1" 2>/dev/null)"
  TYPE="$(curl -sL -o /dev/null -w '%{content_type}' --max-time 25 "${BASE_URL}$1" 2>/dev/null)"
}

# --- 1. Le site répond-il ? -------------------------------------------------
echo
echo "${GRAS}1. Le site répond${FIN}"
recuperer "/"
if [ "$CODE" = "000" ]; then
  echo "  $X aucune réponse. Domaine non résolu, serveur injoignable, ou"
  echo "      accès réseau bloqué depuis cette machine."
  defaut
elif [ "$CODE" != "200" ]; then
  echo "  $X l'accueil répond $CODE."
  defaut
else
  echo "  $V l'accueil répond 200."
fi
rm -f "$CORPS"

# --- 2. Quelle version le serveur sert-il ? ---------------------------------
echo
echo "${GRAS}2. Version servie${FIN}"
recuperer "/version.txt"
LOCAL_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo inconnu)"
if [ "$CODE" != "200" ]; then
  echo "  $ATTENTION /version.txt répond $CODE."
  echo "      Soit le serveur sert une version antérieure à l'ajout de ce"
  echo "      fichier — c'est déjà une réponse — soit il ne déploie pas."
  defaut
else
  EN_LIGNE="$(grep -m1 '^commit' "$CORPS" | awk '{print $2}')"
  echo "  en ligne : $(grep -m1 '^construit' "$CORPS" | cut -d' ' -f2-)"
  echo "  commit   : ${EN_LIGNE:0:12}"
  echo "  local    : ${LOCAL_COMMIT:0:12}"
  if [ "$EN_LIGNE" = "$LOCAL_COMMIT" ]; then
    echo "  $V le serveur sert exactement la version de ce dépôt."
  else
    echo "  $X LE SERVEUR SERT UNE AUTRE VERSION."
    echo "      C'est la cause : tout ce qui a été corrigé depuis n'est pas"
    echo "      en ligne. Voir « Déploiement » dans le README."
    defaut
  fi
fi
rm -f "$CORPS"

# --- 3. Ce que Google lit en premier ---------------------------------------
echo
echo "${GRAS}3. Ce que Google lit en premier${FIN}"
recuperer "/robots.txt"
if [ "$CODE" != "200" ]; then
  echo "  $X /robots.txt répond $CODE."
  defaut
elif grep -qiE '^[[:space:]]*Disallow:[[:space:]]*/[[:space:]]*$' "$CORPS"; then
  echo "  $X robots.txt INTERDIT tout le site (Disallow: /)."
  echo "      C'est l'ancienne version : le dépôt autorise l'exploration."
  defaut
else
  echo "  $V robots.txt autorise l'exploration."
  if grep -qi '^Sitemap:' "$CORPS"; then
    echo "  $V il déclare le sitemap."
  else
    echo "  $X il ne déclare pas le sitemap."
    defaut
  fi
fi
rm -f "$CORPS"

recuperer "/sitemap.xml"
if [ "$CODE" != "200" ]; then
  echo "  $X /sitemap.xml répond $CODE."
  defaut
elif ! grep -q '<urlset' "$CORPS"; then
  echo "  $X /sitemap.xml répond 200 mais ne renvoie pas un sitemap (${TYPE})."
  defaut
else
  echo "  $V /sitemap.xml : ${TYPE}, $(grep -c '<loc>' "$CORPS") URLs."
fi
rm -f "$CORPS"

# --- 4. Les pages sont-elles indexables ? -----------------------------------
echo
echo "${GRAS}4. Un échantillon de pages${FIN}"
for chemin in / /serrurier /tarifs /zones/morbihan-56 /blog/securiser-son-logement; do
  recuperer "$chemin"
  if [ "$CODE" != "200" ]; then
    printf '  %s %-34s %s\n' "$X" "$chemin" "$CODE"
    defaut
  elif grep -qi 'content="noindex' "$CORPS"; then
    printf '  %s %-34s 200 mais NOINDEX\n' "$X" "$chemin"
    defaut
  else
    CANON="$(grep -o '<link rel="canonical" href="[^"]*"' "$CORPS" | head -1 | sed 's/.*href="//; s/"$//')"
    printf '  %s %-34s 200 · indexable · %s\n' "$V" "$chemin" "${CANON:-canonique absente}"
    [ -n "$CANON" ] || defaut
  fi
  rm -f "$CORPS"
done

# --- Bilan ------------------------------------------------------------------
echo
if [ "$DEFAUTS" -eq 0 ]; then
  echo "  ${VERT}Rien ne s'oppose à l'indexation.${FIN}"
  echo
  echo "  Dans la Search Console :"
  echo "    Sitemaps        → taper exactement : sitemap.xml"
  echo "    Inspection URL  → coller une page, puis « Demander une indexation »"
  exit 0
fi
echo "  ${ROUGE}${DEFAUTS} point(s) à corriger.${FIN}"
echo "  Si la version servie n'est pas celle du dépôt, commencez par là :"
echo "  tout le reste en découle."
exit 1
