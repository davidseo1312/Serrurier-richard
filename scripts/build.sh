#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Assemble les pages statiques du site.
#
#   src/pages/**/*.html  (contenu + métadonnées)
# + src/partials/*.html  (head, header, footer, JSON-LD)
# + src/config.sh        (valeurs globales)
# ->  public/**/*.html   (site déployable tel quel)
#
# Usage : bash scripts/build.sh
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Charge la configuration et exporte chaque variable pour la substitution.
source src/config.sh
while IFS= read -r var; do
  export "$var"
done < <(grep -oE '^[A-Z][A-Z0-9_]*=' src/config.sh | tr -d '=')

ROBOTS_POLICY_GLOBAL="$ROBOTS_POLICY"

OUT="public"
rm -rf "$OUT"
mkdir -p "$OUT"

# Les fichiers statiques (CSS, JS, images, .htaccess…) sont copiés tels quels.
# Les notes de travail en Markdown restent dans le dépôt et ne sont pas
# publiées : elles n'ont rien à faire sur le serveur.
cp -r static/. "$OUT"/
find "$OUT" -name '*.md' -delete

# Remplace {{VARIABLE}} par la valeur de l'environnement.
# Deux passes : un titre de page peut lui-même contenir {{NOM_COMMERCIAL}}.
# Un token inconnu est laissé intact pour être repéré par scripts/check-seo.sh.
substituer() {
  perl -pe 's/\{\{(\w+)\}\}/exists $ENV{$1} ? $ENV{$1} : "{{$1}}"/ge' \
    | perl -pe 's/\{\{(\w+)\}\}/exists $ENV{$1} ? $ENV{$1} : "{{$1}}"/ge'
}

# Échappe une valeur destinée à un littéral JSON (données structurées).
json_escape() {
  printf '%s' "$1" | perl -pe 's/\\/\\\\/g; s/"/\\"/g; s/\n/ /g'
}

# Lit une clé du bloc de métadonnées en tête de page.
meta_get() {
  sed -n '/^<!--meta$/,/^-->$/p' "$1" | sed -n "s/^$2:[[:space:]]*//p" | head -1
}

# --- Blocs optionnels injectés dans <head> ---------------------------------
# Rien n'est écrit tant que l'identifiant correspondant est vide : pas de
# balise creuse, pas de requête réseau inutile.

export BLOC_VERIFICATION=""
if [ -n "${GSC_CODE:-}" ]; then
  BLOC_VERIFICATION="<meta name=\"google-site-verification\" content=\"${GSC_CODE}\">"
fi

export BLOC_GTM=""
export BLOC_GTM_BODY=""
if [ -n "${GTM_ID:-}" ]; then
  # Google Tag Manager n'est PAS chargé ici : le conteneur ne démarre qu'après
  # acceptation du bandeau de consentement (voir static/assets/js/site.js).
  # Seul l'identifiant est transmis au JavaScript, via un attribut de <html>.
  BLOC_GTM="<!-- Conteneur GTM ${GTM_ID} : chargé après consentement, voir assets/js/site.js -->"
fi

# --- Formulaire de devis ---------------------------------------------------
# Le formulaire n'existe qu'en un seul exemplaire, dans src/partials/. Les
# pages qui l'affichent écrivent simplement {{FORMULAIRE_DEVIS}} : une
# correction sur le partiel se répercute partout au build suivant.
export FORMULAIRE_DEVIS="$(cat src/partials/formulaire-devis.html)"

# --- Génération d'un fil d'Ariane BreadcrumbList ---------------------------
# Google exige que le fil d'Ariane balisé corresponde à celui affiché.
# Les pages composent le leur avec <nav class="fil"> ; ce bloc produit le
# JSON-LD équivalent à partir des métadonnées « breadcrumb » et « parent ».
schema_breadcrumb() {
  local nom_page="$1" url_page="$2" nom_parent="$3" url_parent="$4"
  local position=2 items

  items="    { \"@type\": \"ListItem\", \"position\": 1, \"name\": \"Accueil\", \"item\": \"${BASE_URL}/\" }"

  if [ -n "$nom_parent" ] && [ -n "$url_parent" ]; then
    items="${items},
    { \"@type\": \"ListItem\", \"position\": 2, \"name\": \"$(json_escape "$nom_parent")\", \"item\": \"${BASE_URL}${url_parent}\" }"
    position=3
  fi

  items="${items},
    { \"@type\": \"ListItem\", \"position\": ${position}, \"name\": \"$(json_escape "$nom_page")\", \"item\": \"${url_page}\" }"

  cat <<LD
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
${items}
  ]
}
</script>
LD
}

PAGE_COUNT=0
SITEMAP_ENTRIES=""

while IFS= read -r src_file; do
  rel="${src_file#src/pages/}"

  export PAGE_TITLE="$(meta_get "$src_file" title)"
  export PAGE_DESC="$(meta_get "$src_file" description)"
  export PAGE_IMAGE="$(meta_get "$src_file" image)"
  export PAGE_DATE="$(meta_get "$src_file" date)"
  export PAGE_BREADCRUMB="$(meta_get "$src_file" breadcrumb)"
  PAGE_SCHEMA="$(meta_get "$src_file" schema)"
  PAGE_PRIORITY="$(meta_get "$src_file" priority)"
  PAGE_SITEMAP="$(meta_get "$src_file" sitemap)"
  PAGE_ROBOTS="$(meta_get "$src_file" robots)"
  PAGE_CONVERSION="$(meta_get "$src_file" conversion)"
  PAGE_FAQ="$(meta_get "$src_file" faq)"
  PAGE_PARENT_NOM="$(meta_get "$src_file" parent_nom)"
  PAGE_PARENT_URL="$(meta_get "$src_file" parent_url)"

  [ -n "$PAGE_PRIORITY" ] || PAGE_PRIORITY="0.6"
  [ -n "$PAGE_IMAGE" ] || PAGE_IMAGE="/assets/img/og-default.jpg"
  [ -n "$PAGE_DATE" ] || PAGE_DATE="$(date +%Y-%m-%d)"

  # Une page peut déclarer une conversion mesurée à son affichage (page de
  # remerciement). L'attribut n'est écrit que si la clé est renseignée.
  if [ -n "$PAGE_CONVERSION" ]; then
    export ATTRIBUT_CONVERSION=" data-conversion=\"$PAGE_CONVERSION\""
  else
    export ATTRIBUT_CONVERSION=""
  fi

  # Une page peut forcer son propre robots (ex : 404 en noindex).
  if [ -n "$PAGE_ROBOTS" ]; then
    export ROBOTS_POLICY="$PAGE_ROBOTS"
  else
    export ROBOTS_POLICY="$ROBOTS_POLICY_GLOBAL"
  fi

  # URL canonique :
  #   index.html        -> /
  #   blog/index.html   -> /blog/     (évite le conflit avec le dossier blog/)
  #   tarifs.html       -> /tarifs    (extension masquée par le .htaccess)
  if [ "$rel" = "index.html" ]; then
    export PAGE_PATH="/"
  elif [ "$(basename "$rel")" = "index.html" ]; then
    export PAGE_PATH="/$(dirname "$rel")/"
  else
    export PAGE_PATH="/${rel%.html}"
  fi
  export PAGE_URL="${BASE_URL}${PAGE_PATH}"

  # Le corps est substitué d'abord : le balisage FAQPage doit contenir les
  # valeurs finales (tarifs, téléphone), pas les tokens.
  CORPS="$(sed '/^<!--meta$/,/^-->$/d' "$src_file" | substituer)"

  # FAQPage dérivé des blocs <details> réellement affichés. « faq: non » dans
  # les métadonnées désactive la génération pour une page donnée.
  FAQ_LD=""
  if [ "$PAGE_FAQ" != "non" ]; then
    FAQ_LD="$(printf '%s\n' "$CORPS" | perl scripts/faq-jsonld.pl)"
  fi

  dest="$OUT/$rel"
  mkdir -p "$(dirname "$dest")"

  {
    cat src/partials/head.html
    if [ -n "$PAGE_SCHEMA" ] && [ -f "src/partials/schema-${PAGE_SCHEMA}.html" ]; then
      cat "src/partials/schema-${PAGE_SCHEMA}.html"
    fi
    # Fil d'Ariane balisé sur toutes les pages sauf l'accueil, qui est la
    # racine du fil et n'a donc rien à décrire.
    if [ "$rel" != "index.html" ]; then
      nom="${PAGE_BREADCRUMB:-$PAGE_TITLE}"
      schema_breadcrumb "$nom" "$PAGE_URL" "$PAGE_PARENT_NOM" "$PAGE_PARENT_URL"
    fi
    [ -n "$FAQ_LD" ] && printf '%s\n' "$FAQ_LD"
    cat src/partials/head-close.html
    cat src/partials/header.html
    printf '%s\n' "$CORPS"
    cat src/partials/footer.html
  } | substituer > "$dest"

  # Les pages marquées "sitemap: non" restent hors du sitemap.
  if [ "$PAGE_SITEMAP" != "non" ]; then
  SITEMAP_ENTRIES="${SITEMAP_ENTRIES}${PAGE_URL}|${PAGE_PRIORITY}|${PAGE_DATE}"$'\n'
  fi
  PAGE_COUNT=$((PAGE_COUNT + 1))
done < <(find src/pages -name '*.html' | sort)

# --- Scripts PHP -----------------------------------------------------------
# Le traitement du formulaire de devis a besoin des mêmes valeurs que les
# pages (adresse de réception, nom commercial…). Les fichiers .php passent
# donc par la même substitution que le HTML.
PHP_COUNT=0
while IFS= read -r php_file; do
  [ -n "$php_file" ] || continue
  rel="${php_file#static/}"
  substituer < "$php_file" > "$OUT/$rel"
  PHP_COUNT=$((PHP_COUNT + 1))
done < <(find static -name '*.php' 2>/dev/null | sort)

# --- Manifeste d'application ------------------------------------------------
[ -f static/manifest.webmanifest ] && substituer < static/manifest.webmanifest > "$OUT/manifest.webmanifest"

bash scripts/gen-sitemap.sh "$SITEMAP_ENTRIES"

echo "✓ $PAGE_COUNT pages générées dans public/"
[ "$PHP_COUNT" -gt 0 ] && echo "✓ $PHP_COUNT script(s) PHP traité(s)"

# ---------------------------------------------------------------------------
# Vérification du résultat.
#
# Un build « qui n'a pas planté » n'est pas un build valide : c'est exactement
# ce qui a produit un déploiement en 403, un dossier sans index.html à
# l'endroit servi par Apache. Le script refuse donc de rendre la main tant
# que le dossier de production n'est pas réellement exploitable.
# ---------------------------------------------------------------------------

MANQUES=0
manque() { echo "  ✗ $1"; MANQUES=$((MANQUES + 1)); }

echo
echo "Vérification du dossier de production…"

# 1. La page d'accueil, à la RACINE de public/ et nulle part ailleurs.
if [ -f "$OUT/index.html" ]; then
  echo "  ✓ index.html présent à la racine de $OUT/"
else
  manque "index.html ABSENT de la racine de $OUT/ — Apache renverrait 403"
fi

# 2. Aucune couche superflue : public/public/, public/serrurier-richard/…
for indesirable in "$OUT/public" "$OUT/dist" "$OUT/build" "$OUT/serrurier-richard"; do
  [ -d "$indesirable" ] && manque "couche superflue détectée : $indesirable/"
done

# 3. Les fichiers indispensables au fonctionnement et au référencement.
for requis in \
  "$OUT/.htaccess" \
  "$OUT/404.html" \
  "$OUT/robots.txt" \
  "$OUT/sitemap.xml" \
  "$OUT/manifest.webmanifest" \
  "$OUT/assets/css/style.css" \
  "$OUT/assets/js/site.js" \
  "$OUT/assets/img/favicon.svg" \
  "$OUT/assets/img/og-default.jpg"; do
  [ -f "$requis" ] || manque "fichier requis absent : ${requis#$OUT/}"
done

# 4. Toutes les ressources référencées par les pages existent réellement.
#    C'est ce contrôle qui attrape un CSS ou une image manquante avant la
#    mise en ligne, plutôt qu'après.
RESSOURCES=$( { grep -rhoE 'src="/[^"]+"' "$OUT" --include='*.html'
                grep -rhoE 'href="/assets/[^"]+"' "$OUT" --include='*.html'
                grep -rhoE 'href="/manifest[^"]*"' "$OUT" --include='*.html'
              } 2>/dev/null | sed 's/^[a-z]*="//;s/"$//' | sort -u )
NB_RESSOURCES=0
while IFS= read -r ref; do
  [ -n "$ref" ] || continue
  NB_RESSOURCES=$((NB_RESSOURCES + 1))
  [ -f "$OUT$ref" ] || manque "ressource référencée mais absente : $ref"
done <<< "$RESSOURCES"

# 5. Le sitemap doit contenir des URLs, pas seulement son enveloppe XML.
NB_URLS=$(grep -c '<loc>' "$OUT/sitemap.xml" 2>/dev/null || echo 0)
if [ "${NB_URLS:-0}" -lt 1 ]; then
  manque "sitemap.xml ne contient aucune URL"
fi

# 6. Aucun token de gabarit non résolu.
if grep -rqo '{{[A-Za-z_]*}}' "$OUT" 2>/dev/null; then
  manque "tokens {{...}} non résolus : $(grep -rho '{{[A-Za-z_]*}}' "$OUT" | sort -u | tr '\n' ' ')"
fi

echo

if [ "$MANQUES" -gt 0 ]; then
  echo "BUILD FAILED — $MANQUES problème(s). Le dossier $OUT/ n'est pas déployable."
  exit 1
fi

echo "BUILD SUCCESS"
echo "  $PAGE_COUNT pages · $NB_URLS URLs au sitemap · $NB_RESSOURCES ressources vérifiées"
echo "  Dossier de production : $OUT/  (à servir comme document root)"
exit 0
