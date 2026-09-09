#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Génère public/sitemap.xml et public/robots.txt à partir des pages réellement
# construites. Appelé automatiquement par scripts/build.sh.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source src/config.sh

ENTRIES="${1:-}"
TODAY="$(date +%Y-%m-%d)"

{
  echo '<?xml version="1.0" encoding="UTF-8"?>'
  echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
  while IFS='|' read -r url priority lastmod; do
    [ -n "$url" ] || continue
    [ -n "$lastmod" ] || lastmod="$TODAY"
    printf '  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n    <priority>%s</priority>\n  </url>\n' \
      "$url" "$lastmod" "$priority"
  done <<< "$ENTRIES"
  echo '</urlset>'
} > public/sitemap.xml

if [ "$ROBOTS_POLICY" = "index" ]; then
  cat > public/robots.txt <<ROBOTS
User-agent: *
Allow: /

Sitemap: ${BASE_URL}/sitemap.xml
ROBOTS
else
  # Site non prêt : on bloque toute exploration.
  cat > public/robots.txt <<ROBOTS
User-agent: *
Disallow: /
ROBOTS
fi

echo "✓ sitemap.xml ($(grep -c '<loc>' public/sitemap.xml) URLs) et robots.txt générés"
