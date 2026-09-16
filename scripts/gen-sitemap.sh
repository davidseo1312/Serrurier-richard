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

# -------------------------------------------------------------------------
# Robots des moteurs de réponse génératifs.
#
# La règle générale ci-dessus les autorise déjà : ces blocs nommés ne
# changent donc rien techniquement. Ils existent pour deux raisons.
# D'abord, plusieurs de ces robots cherchent leur propre nom avant de
# retomber sur la règle générale. Ensuite, une autorisation écrite noir sur
# blanc évite qu'un blocage soit ajouté par erreur un jour — ce qui
# retirerait le site des réponses d'IA sans que personne ne s'en aperçoive.
#
# Google-Extended et Applebot-Extended ne sont pas des robots mais des
# jetons de REFUS : ils ne servent qu'à interdire l'usage du contenu par
# Gemini ou Apple Intelligence. Les mentionner en Allow est sans effet
# technique ; leur présence ici documente qu'aucun refus n'est posé.
# -------------------------------------------------------------------------

User-agent: Googlebot
Allow: /

User-agent: Googlebot-Image
Allow: /

User-agent: bingbot
Allow: /

User-agent: DuckDuckBot
Allow: /

User-agent: Qwantify
Allow: /

User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Perplexity-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: DuckAssistBot
Allow: /

User-agent: MistralAI-User
Allow: /

User-agent: Amazonbot
Allow: /

User-agent: meta-externalagent
Allow: /

User-agent: YouBot
Allow: /

User-agent: cohere-ai
Allow: /

User-agent: CCBot
Allow: /

Sitemap: ${BASE_URL}/sitemap.xml
LLMs: ${BASE_URL}/llms.txt
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
