#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Génère public/sitemap.xml et public/robots.txt à partir des pages réellement
# construites. Appelé automatiquement par scripts/build.sh.
#
# Le sitemap déclare aussi les IMAGES de chaque page, via l'extension
# sitemap-image de Google. C'est le moyen le plus direct de faire découvrir
# les visuels du site par Google Images : les images posées en HTML sont
# explorées, celles qui ne vivent qu'en CSS ne le sont pas.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source src/config.sh

ENTRIES="${1:-}"
TODAY="$(date +%Y-%m-%d)"

# Échappe les caractères que XML n'accepte pas dans un attribut ou un texte.
xml_echappe() {
  printf '%s' "$1" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g'
}

# Retrouve le fichier HTML correspondant à une URL, pour y relever les images.
fichier_de_url() {
  local chemin="${1#$BASE_URL}"
  case "$chemin" in
    /)   echo "public/index.html" ;;
    */)  echo "public${chemin}index.html" ;;
    *)   echo "public${chemin}.html" ;;
  esac
}

{
  echo '<?xml version="1.0" encoding="UTF-8"?>'
  echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
  echo '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'

  while IFS='|' read -r url priority lastmod; do
    [ -n "$url" ] || continue
    [ -n "$lastmod" ] || lastmod="$TODAY"

    printf '  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n    <priority>%s</priority>\n' \
      "$url" "$lastmod" "$priority"

    # Images de la page, dédoublonnées, avec leur texte alternatif comme
    # légende : c'est ce que Google Images affiche et indexe.
    fichier="$(fichier_de_url "$url")"
    if [ -f "$fichier" ]; then
      { grep -o '<img [^>]*>' "$fichier" 2>/dev/null || true; } | while IFS= read -r balise; do
        src=$(printf '%s' "$balise" | sed -n 's/.*src="\([^"]*\)".*/\1/p')
        alt=$(printf '%s' "$balise" | sed -n 's/.*alt="\([^"]*\)".*/\1/p')
        case "$src" in /assets/*) ;; *) continue ;; esac
        printf '    <image:image>\n      <image:loc>%s%s</image:loc>\n' "$BASE_URL" "$src"
        [ -n "$alt" ] && printf '      <image:title>%s</image:title>\n' "$(xml_echappe "$alt")"
        printf '    </image:image>\n'
      done | awk '!vu[$0]++'
    fi

    printf '  </url>\n'
  done <<< "$ENTRIES"

  echo '</urlset>'
} > public/sitemap.xml

if [ "$ROBOTS_POLICY" = "index" ]; then
  cat > public/robots.txt <<ROBOTS
User-agent: *
Allow: /

# Les images doivent rester explorables : sans cela elles n'apparaissent pas
# dans Google Images, quelle que soit la qualité du balisage.
Allow: /assets/images/
Allow: /assets/img/

Sitemap: ${BASE_URL}/sitemap.xml
ROBOTS
else
  # Site non prêt : on bloque toute exploration.
  cat > public/robots.txt <<ROBOTS
User-agent: *
Disallow: /
ROBOTS
fi

NB_IMG=$(grep -c '<image:loc>' public/sitemap.xml || true)
NB_URL=$(grep -c '^    <loc>' public/sitemap.xml || true)
echo "✓ sitemap.xml (${NB_URL:-0} URLs, ${NB_IMG:-0} images) et robots.txt générés"
