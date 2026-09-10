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
# Distinct d'une erreur : le code est correct, il manque une information que
# seul l'exploitant peut fournir (assurance, médiateur, adresse). Compté à
# part pour ne pas masquer un vrai défaut technique dans le bilan.
adonner() { echo "  ${JAUNE}#${FIN} $1"; echo D >> "$COMPTEURS"; }
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
titre "8. Donnees d'entreprise a fournir (bloquant avant mise en ligne)"
MOTIF='\[(RAISON SOCIALE|SIRET|ADRESSE|FORME|CAPITAL|RCS|N. TVA|ASSUREUR|N. DE POLICE|NOM DU M|URL DU M|.TABLISSEMENT)[^]]*\]'
PLACEHOLDERS=$(grep -rlE "$MOTIF" public/ 2>/dev/null | sed 's|^public/||' | sort || true)
if [ -n "$PLACEHOLDERS" ]; then
  NB_PAGES_PH=$(echo "$PLACEHOLDERS" | grep -c .)
  adonner "Champs a renseigner dans src/config.sh, presents sur $NB_PAGES_PH page(s) :"
  grep -rhoE "$MOTIF" public/ 2>/dev/null | sort -u | sed 's/^/        /'
  echo "        -> ces valeurs sont des obligations legales : elles ne peuvent"
  echo "           pas etre inventees. Voir la section « Avant la mise en ligne »"
  echo "           du README."
else
  ok "Donnees d'entreprise renseignees"
fi
grep -qE '02 99 00 00 00' src/config.sh \
  && erreur "Le numero de telephone est encore le numero fictif (src/config.sh)" \
  || ok "Numero de telephone renseigne"

# --- 9. Fichiers requis ----------------------------------------------------
titre "9. Fichiers requis"
# La CSS et le JS portent l'empreinte de leur contenu dans leur nom : leur
# adresse change à chaque modification, sans quoi le cache d'un an fixé par le
# .htaccess servirait indéfiniment l'ancienne version. On vérifie donc qu'il
# existe exactement un fichier de chaque, pas un nom précis.
for motif in "public/assets/css/style.*.css" "public/assets/js/site.*.js"; do
  n=$(ls $motif 2>/dev/null | wc -l)
  case "$n" in
    1) ok "$(ls $motif | sed 's|public/||')" ;;
    0) erreur "${motif#public/} : aucun fichier" ;;
    *) erreur "${motif#public/} : $n fichiers, il ne doit en rester qu'un" ;;
  esac
done

for f in public/robots.txt public/sitemap.xml public/.htaccess public/404.html \
         public/manifest.webmanifest public/envoi-devis.php \
         public/assets/img/favicon.svg public/assets/img/favicon.ico \
         public/assets/img/apple-touch-icon.png public/assets/img/og-default.jpg \
         public/assets/img/icone-192.png public/assets/img/icone-512.png \
         public/assets/img/icone-512-maskable.png; do
  [ -f "$f" ] && ok "${f#public/}" || erreur "${f#public/} manquant"
done

# --- 10. Ressources referencees par les pages ------------------------------
titre "10. Ressources referencees (images, feuilles, scripts)"
PB=0
REFS=$( { grep -rhoE 'src="/[^"]+"'  public --include='*.html'
          grep -rhoE 'href="/assets/[^"]+"' public --include='*.html'
          grep -rhoE 'href="/manifest[^"]*"' public --include='*.html'
        } | sed 's/^[a-z]*="//;s/"$//' | sort -u )
while IFS= read -r ref; do
  [ -z "$ref" ] && continue
  if [ ! -f "public$ref" ]; then
    erreur "ressource absente : $ref"
    PB=1
  fi
done <<< "$REFS"
[ "$PB" -eq 0 ] && ok "Toutes les ressources referencees existent ($(echo "$REFS" | grep -c .) fichiers)"

# Illustrations encore vectorielles : le site est complet et deployable en
# l'etat, mais des photos reelles convertissent nettement mieux sur ce metier.
NB_SVG=$(grep -rhoE 'src="/assets/img/[a-z0-9-]+\.svg"' public --include='*.html' | sort -u | grep -c . || true)
[ "${NB_SVG:-0}" -gt 0 ] && avert "$NB_SVG illustration(s) encore vectorielle(s) - voir static/assets/img/README.md pour deposer de vraies photos"

# --- 11. Redirections des anciennes URL ------------------------------------
titre "11. Redirections 301"
PB=0
for ancienne in \
  "services/ouverture-de-porte" "services/changement-de-serrure" \
  "services/porte-blindee" "services/apres-effraction" \
  "services/rideau-metallique" "services/coffre-fort" \
  "politique-de-confidentialite"; do
  # L'ancienne URL ne doit plus exister en dur ET doit etre redirigee.
  if [ -f "public/${ancienne}.html" ]; then
    erreur "$ancienne existe encore en page : conflit avec la redirection"
    PB=1
  elif ! grep -qF "^${ancienne}/?\$" public/.htaccess; then
    erreur "aucune redirection 301 pour /$ancienne dans .htaccess"
    PB=1
  fi
done
[ "$PB" -eq 0 ] && ok "Anciennes URL toutes redirigees en 301"

# --- 12. Questions FAQ dupliquees ------------------------------------------
# Deux pages portant la meme question se concurrencent dans les resultats
# enrichis de Google : aucune des deux ne ressort.
titre "12. Donnees structurees FAQ"
DOUBLES=$(grep -rhoE '"name": "[^"]+\?"' public --include='*.html' | sort | uniq -d || true)
if [ -n "$DOUBLES" ]; then
  while IFS= read -r q; do avert "question FAQ presente sur plusieurs pages : ${q:10:70}"; done <<< "$DOUBLES"
else
  NB_FAQ=$(grep -rl '"@type": "FAQPage"' public --include='*.html' | grep -c . || true)
  ok "FAQPage sur ${NB_FAQ:-0} page(s), aucune question dupliquee"
fi

# --- 13. Indexation --------------------------------------------------------
titre "13. Parametres d'indexation"
if [ "$ROBOTS_POLICY" = "index" ]; then
  ok "Site en index"
  grep -q "Sitemap: ${BASE_URL}/sitemap.xml" public/robots.txt \
    && ok "robots.txt declare le sitemap" \
    || erreur "robots.txt ne declare pas le sitemap"
else
  adonner "Site en '$ROBOTS_POLICY' : il ne sera PAS reference tant que"
  echo "        ROBOTS_POLICY n'est pas passe a \"index\" dans src/config.sh."
  echo "        Voir « Coherence geographique » dans le README avant de le faire."
fi
ok "sitemap.xml : $(grep -c '^    <loc>' public/sitemap.xml) URLs"
# Pages mises en noindex individuellement (404, remerciement). Le compte n'a
# de sens que si le site est globalement indexable.
if [ "$ROBOTS_POLICY" = "index" ]; then
  NB_NOINDEX=$(grep -rl 'name="robots" content="noindex' public --include='*.html' | grep -c . || true)
  ok "${NB_NOINDEX:-0} page(s) volontairement en noindex (404, remerciement)"
fi

# --- 14. Poids -------------------------------------------------------------
titre "14. Poids des fichiers"
PB=0
while IFS= read -r l; do
  [ -n "$l" ] && { avert "${l#public/} depasse 100 Ko"; PB=1; }
done <<< "$(find public -name '*.html' -size +100k)"
while IFS= read -r g; do
  [ -n "$g" ] && { avert "${g#public/} depasse 250 Ko"; PB=1; }
done <<< "$(find public/assets -type f -size +250k 2>/dev/null)"
[ "$PB" -eq 0 ] && ok "Aucun fichier trop lourd"
ok "CSS $(du -k public/assets/css/style.*.css | cut -f1) Ko, JS $(du -k public/assets/js/site.*.js | cut -f1) Ko, total site $(du -sk public | cut -f1) Ko"

# --- Bilan -----------------------------------------------------------------
NB_ERR=$(grep -c '^E$' "$COMPTEURS" 2>/dev/null || true)
NB_AVERT=$(grep -c '^A$' "$COMPTEURS" 2>/dev/null || true)
NB_DONN=$(grep -c '^D$' "$COMPTEURS" 2>/dev/null || true)
NB_ERR=${NB_ERR:-0}; NB_AVERT=${NB_AVERT:-0}; NB_DONN=${NB_DONN:-0}

echo
echo "${GRAS}Bilan${FIN}"
echo "  $NB_PAGES pages analysees"
echo "  ${ROUGE}$NB_ERR defaut(s) technique(s)${FIN}     - a corriger dans le code"
echo "  ${JAUNE}$NB_DONN information(s) a fournir${FIN} - a renseigner dans src/config.sh"
echo "  ${JAUNE}$NB_AVERT avertissement(s)${FIN}"
echo

if [ "$NB_ERR" -eq 0 ] && [ "$NB_DONN" -eq 0 ]; then
  echo "  ${VERT}Le site est pret a etre mis en ligne.${FIN}"
elif [ "$NB_ERR" -eq 0 ]; then
  echo "  ${VERT}Aucun defaut technique.${FIN} Le site se construit et se deploie."
  echo "  Completez les informations ci-dessus avant la mise en ligne : ce sont"
  echo "  des mentions legalement obligatoires, elles ne peuvent pas etre devinees."
fi
echo

# Le code de sortie ne signale que les defauts techniques : les informations
# manquantes relevent de l'exploitant, pas d'un echec de construction.
[ "$NB_ERR" -eq 0 ]
