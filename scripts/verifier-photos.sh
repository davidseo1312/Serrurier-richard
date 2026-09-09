#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# État des photographies réelles du site.
#
#   bash scripts/verifier-photos.sh
#
# Lit src/images.conf et dit, pour chaque emplacement, si la photographie
# attendue a été déposée ou si le site affiche encore l'illustration de repli.
# Ne modifie rien : c'est un état des lieux, à lancer avant et après un dépôt.
# ---------------------------------------------------------------------------
set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

EXTENSIONS="avif webp jpg jpeg png svg"

trouver() {
  local base="$1" ext
  for ext in $EXTENSIONS; do
    [ -f "static/assets/images/${base}.${ext}" ] && { printf '%s' "static/assets/images/${base}.${ext}"; return 0; }
  done
  return 1
}

attendues=0; livrees=0; manquantes=""

printf '\n%s\n' "Photographies attendues par src/images.conf"
printf '%s\n' "-------------------------------------------"

while IFS='|' read -r id photo repli largeur hauteur alt_photo alt_repli; do
  case "$id" in ''|\#*) continue ;; esac
  [ -n "$photo" ] || continue
  attendues=$((attendues + 1))

  if fichier="$(trouver "$photo")"; then
    livrees=$((livrees + 1))
    poids="$(( $(wc -c < "$fichier") / 1024 ))"
    printf '  ✓ %-20s %s (%s Ko)\n' "$id" "$fichier" "$poids"
    if [ "$poids" -gt 250 ]; then
      printf '      ⚠ au-delà de 250 Ko : convertissez en WebP ou réduisez la définition.\n'
    fi
  else
    manquantes="${manquantes}${id}|${photo}|${largeur}x${hauteur}|${alt_photo}"$'\n'
    printf '  · %-20s attendue : static/assets/images/%s.webp\n' "$id" "$photo"
  fi
done < src/images.conf

printf '\n%s\n' "-------------------------------------------"
printf '  %d photographie(s) livrée(s) sur %d attendue(s).\n' "$livrees" "$attendues"

if [ -n "$manquantes" ]; then
  cat <<'AIDE'

Pour livrer une photographie manquante :

  1. Recadrez-la au format indiqué (une définition supérieure convient, le
     rapport doit être respecté pour éviter un recadrage automatique).
  2. Convertissez-la en WebP, qualité 80 environ, sous les 250 Ko.
  3. Déposez-la sous le nom EXACT indiqué ci-dessus, extension .webp.
  4. Relancez « bash scripts/build.sh ».

Le site adopte alors la photographie partout où l'emplacement est utilisé, y
compris dans l'aperçu social et le sitemap images. Le texte alternatif est
déjà écrit dans src/images.conf : relisez-le, il doit décrire la photo
réellement déposée.

Ne déposez que des clichés pris par l'entreprise, avec l'accord des clients
concernés. Une photo de banque d'images présentée comme une intervention
réelle est une pratique commerciale trompeuse.
AIDE
fi

printf '\n'
