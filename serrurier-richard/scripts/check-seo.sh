#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Contrôle SEO et pré-vol de mise en ligne.
# À lancer après scripts/build.sh, et à rejouer après chaque modification.
#
#   bash scripts/check-seo.sh
#
# Sortie 1 si au moins une erreur bloquante est détectée.
# Les compteurs transitent par un fichier : les boucles derrière un pipe
# s'exécutent dans des sous-shells et perdraient des variables ordinaires.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source src/config.sh

[ -d public ] || { echo "public/ absent — lancez d'abord : bash scripts/build.sh"; exit 1; }

COMPTEURS="$(mktemp)"
trap 'rm -f "$COMPTEURS"' EXIT

ROUGE=$'\033[31m'; JAUNE=$'\033[33m'; VERT=$'\033[32m'; GRAS=$'\033[1m'; FIN=$'\033[0m'

erreur() { echo "  ${ROUGE}x${FIN} $1"; echo E >> "$COMPTEURS"; }
avert()  { echo "  ${JAUNE}!${FIN} $1"; echo A >> "$COMPTEURS"; }
ok()     { echo "  ${VERT}v${FIN} $1"; }
titre()  { echo; echo "${GRAS}$1${FIN}"; }

PAGES=$(find public -name '*.html' | sort)
NB_PAGES=$(echo "$PAGES" | wc -l)

lire_title() { sed -n 's/.*<title>\(.*\)<\/title>.*/\1/p' "$1" | head -1; }
lire_desc()  { sed -n 's/.*<meta name="description" content="\([^"]*\)".*/\1/p' "$1" | head -1; }

# --- 1. Balises title ------------------------------------------------------
titre "1. Balises title"
while IFS= read -r f; do
  t=$(lire_title "$f"); n=${#t}
  if   [ -z "$t" ];      then erreur "${f#public/} : title absent"
  elif [ "$n" -gt 65 ];  then avert  "${f#public/} : title de $n caracteres (tronque au-dela de ~60)"
  elif [ "$n" -lt 25 ];  then avert  "${f#public/} : title de $n caracteres, trop court"
  fi
done <<< "$PAGES"

DOUBLONS=""
while IFS= read -r f; do DOUBLONS+="$(lire_title "$f")"$'\n'; done <<< "$PAGES"
DOUBLONS=$(echo "$DOUBLONS" | sort | uniq -d | grep -v '^$' || true)
if [ -n "$DOUBLONS" ]; then
  while IFS= read -r d; do erreur "title duplique : $d"; done <<< "$DOUBLONS"
else
  ok "Titles tous uniques ($NB_PAGES pages)"
fi

# --- 2. Meta descriptions --------------------------------------------------
titre "2. Meta descriptions"
while IFS= read -r f; do
  d=$(lire_desc "$f"); n=${#d}
  if   [ -z "$d" ];       then erreur "${f#public/} : description absente"
  elif [ "$n" -gt 165 ];  then avert  "${f#public/} : description de $n caracteres (tronquee au-dela de ~160)"
  elif [ "$n" -lt 70 ];   then avert  "${f#public/} : description de $n caracteres, trop courte"
  fi
done <<< "$PAGES"

DOUBLONS=""
while IFS= read -r f; do DOUBLONS+="$(lire_desc "$f")"$'\n'; done <<< "$PAGES"
DOUBLONS=$(echo "$DOUBLONS" | sort | uniq -d | grep -v '^$' || true)
if [ -n "$DOUBLONS" ]; then
  while IFS= read -r d; do erreur "description dupliquee : ${d:0:70}..."; done <<< "$DOUBLONS"
else
  ok "Descriptions toutes uniques"
fi

# --- 3. Titres H1 ----------------------------------------------------------
titre "3. Titres H1"
PB=0
while IFS= read -r f; do
  n=$(grep -o '<h1[ >]' "$f" | wc -l)
  if [ "$n" -ne 1 ]; then erreur "${f#public/} : $n balise(s) H1, il en faut exactement une"; PB=1; fi
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Une seule H1 par page"

# --- 4. Attributs alt ------------------------------------------------------
titre "4. Accessibilite des images"
PB=0
while IFS= read -r f; do
  while IFS= read -r img; do
    [ -z "$img" ] && continue
    case "$img" in
      *alt=*) : ;;
      *) erreur "${f#public/} : <img> sans alt -> ${img:0:70}"; PB=1 ;;
    esac
  done <<< "$(grep -o '<img [^>]*>' "$f" || true)"
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Toutes les images portent un attribut alt"

# --- 5. Liens internes -----------------------------------------------------
titre "5. Liens internes"
PB=0
while IFS= read -r f; do
  while IFS= read -r lien; do
    [ -z "$lien" ] && continue
    case "$lien" in /assets/*) continue ;; esac
    cible="public${lien}"
    if   [ "$lien" = "/" ] && [ -f public/index.html ]; then continue
    elif [ -f "$cible" ];          then continue
    elif [ -f "${cible}.html" ];   then continue
    elif [ -f "${cible}/index.html" ]; then continue
    elif [ -f "${cible%/}.html" ]; then continue
    else erreur "${f#public/} : lien brise vers $lien"; PB=1
    fi
  done <<< "$(grep -o 'href="/[^"#]*"' "$f" | sed 's/href="//;s/"$//' | sort -u)"
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Aucun lien interne brise"

# --- 6. Canoniques et JSON-LD ----------------------------------------------
titre "6. URL canoniques et donnees structurees"
PB=0
while IFS= read -r f; do
  grep -q '<link rel="canonical"' "$f" || { erreur "${f#public/} : canonique absente"; PB=1; }
done <<< "$PAGES"
[ "$PB" -eq 0 ] && ok "Canonique presente sur toutes les pages"
NB_LD=$(grep -l 'application/ld+json' $PAGES 2>/dev/null | wc -l)
ok "JSON-LD present sur $NB_LD page(s)"

# --- 7. Tokens non resolus -------------------------------------------------
titre "7. Tokens de gabarit"
RESTES=$(grep -rho '{{[A-Za-z_]*}}' public/ 2>/dev/null | sort -u || true)
if [ -n "$RESTES" ]; then
  while IFS= read -r t; do erreur "token non resolu : $t"; done <<< "$RESTES"
else
  ok "Aucun token non resolu"
fi

# --- 8. Donnees d'entreprise -----------------------------------------------
titre "8. Donnees d'entreprise (bloquant avant mise en ligne)"
PLACEHOLDERS=$(grep -rlE '\[(RAISON SOCIALE|SIRET|ADRESSE|FORME|CAPITAL|RCS|N. TVA|ASSUREUR|N. DE POLICE|NOM DU M|URL DU M|.TABLISSEMENT)[^]]*\]' public/ 2>/dev/null | sed 's|^public/||' || true)
if [ -n "$PLACEHOLDERS" ]; then
  erreur "Champs a completer dans src/config.sh - pages concernees :"
  echo "$PLACEHOLDERS" | sed 's/^/        /'
else
  ok "Donnees d'entreprise renseignees"
fi
grep -qE '02 99 00 00 00' src/config.sh \
  && erreur "Le numero de telephone est encore le numero fictif (src/config.sh)" \
  || ok "Numero de telephone renseigne"

# --- 9. Fichiers requis ----------------------------------------------------
titre "9. Fichiers requis"
for f in public/robots.txt public/sitemap.xml public/.htaccess public/404.html \
         public/assets/css/style.css public/assets/js/site.js public/assets/img/favicon.svg; do
  [ -f "$f" ] && ok "${f#public/}" || erreur "${f#public/} manquant"
done
# Photos référencées par les pages : voir static/assets/img/README.md
while IFS= read -r img; do
  [ -z "$img" ] && continue
  if [ -f "public$img" ]; then
    ok "${img#/}"
  else
    erreur "${img#/} manquant - voir static/assets/img/README.md"
  fi
done <<< "$(grep -rho '/assets/img/[a-z-]*\.jpg' src/pages/ | sort -u)"

[ -f public/assets/img/og-default.jpg ] \
  && ok "assets/img/og-default.jpg" \
  || erreur "assets/img/og-default.jpg manquant - partage social 1200x630 (voir static/assets/img/README.md)"

# --- 10. Indexation --------------------------------------------------------
titre "10. Parametres d'indexation"
if [ "$ROBOTS_POLICY" = "index" ]; then
  ok "Site en index"
else
  avert "Site en '$ROBOTS_POLICY' : il ne sera PAS reference. Passez ROBOTS_POLICY=index dans src/config.sh."
fi
grep -q "Sitemap: ${BASE_URL}/sitemap.xml" public/robots.txt \
  && ok "robots.txt declare le sitemap" \
  || avert "robots.txt ne declare pas le sitemap"
ok "sitemap.xml : $(grep -c '<loc>' public/sitemap.xml) URLs"

# --- 11. Poids -------------------------------------------------------------
titre "11. Poids des fichiers"
PB=0
while IFS= read -r l; do
  [ -n "$l" ] && { avert "${l#public/} depasse 100 Ko"; PB=1; }
done <<< "$(find public -name '*.html' -size +100k)"
while IFS= read -r g; do
  [ -n "$g" ] && { avert "${g#public/} depasse 250 Ko"; PB=1; }
done <<< "$(find public/assets -type f -size +250k 2>/dev/null)"
[ "$PB" -eq 0 ] && ok "Aucun fichier trop lourd"

# --- Bilan -----------------------------------------------------------------
NB_ERR=$(grep -c '^E$' "$COMPTEURS" 2>/dev/null || true)
NB_AVERT=$(grep -c '^A$' "$COMPTEURS" 2>/dev/null || true)
NB_ERR=${NB_ERR:-0}; NB_AVERT=${NB_AVERT:-0}

echo
echo "${GRAS}Bilan${FIN}"
echo "  $NB_PAGES pages analysees"
echo "  ${ROUGE}$NB_ERR erreur(s) bloquante(s)${FIN}"
echo "  ${JAUNE}$NB_AVERT avertissement(s)${FIN}"
echo

[ "$NB_ERR" -eq 0 ]
