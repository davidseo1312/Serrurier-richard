#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Génère public/llms.txt.
#
# CE QUE C'EST : une convention récente (llmstxt.org) qui propose de déposer à
# la racine d'un site un résumé en texte brut, destiné aux modèles de langage.
# Un moteur de réponse qui la connaît y trouve l'identité de l'entreprise, sa
# zone et la liste des pages, sans avoir à interpréter du HTML.
#
# CE QUE CE N'EST PAS : un standard. Tous les moteurs ne la lisent pas, et
# aucun ne s'engage à en tenir compte. Le fichier coûte quelques lignes et ne
# peut pas nuire ; il ne remplace ni le balisage JSON-LD ni le sitemap.
#
# Il est DÉRIVÉ du même inventaire que le sitemap, passé en argument par
# build.sh : il ne peut donc pas décrire une page qui n'existe plus, ni
# oublier une page ajoutée. Un fichier écrit à la main se serait périmé au
# premier article publié.
# ---------------------------------------------------------------------------
set -euo pipefail

ENTREES="${1:-}"
OUT="${OUT:-public}"
DEST="$OUT/llms.txt"

section_du() { printf '%s' "$1" | cut -d'|' -f1; }

{
  printf '# %s\n\n' "${NOM_COMMERCIAL}"
  printf '> %s. Ouverture de porte, changement de serrure, blindage et réparation après effraction, sur six départements de Bretagne et des Pays de la Loire.\n\n' "${BASELINE}"

  printf 'Téléphone : %s (%s)\n' "${TELEPHONE}" "${DISPONIBILITE}"
  printf 'Courriel : %s\n' "${EMAIL}"
  printf 'Site : %s/\n\n' "${BASE_URL}"

  printf 'Départements desservis, et eux seuls : Ille-et-Vilaine (35), Morbihan (56),\n'
  printf 'Finistère (29), Côtes-d'"'"'Armor (22), Loire-Atlantique (44), Maine-et-Loire (49).\n'
  printf 'Villes principales : Rennes, Nantes, Brest, Quimper, Lorient, Vannes,\n'
  printf 'Saint-Brieuc, Saint-Malo, Lannion, Angers, Dinan, Fougères, Redon.\n\n'

  printf 'Prestations : ouverture de porte claquée ou verrouillée, changement et\n'
  printf 'remplacement de serrure, pose de serrure multipoints, extraction de clé\n'
  printf 'cassée, clé perdue, blindage de porte, réparation après effraction, rideau\n'
  printf 'métallique, coffre-fort.\n\n'

  printf 'Prix de départ (TTC) : ouverture de porte claquée à partir de %s €,\n' "${FORFAIT_OUVERTURE_SIMPLE}"
  printf 'changement de cylindre à partir de %s €, ouverture de porte blindée à\n' "${FORFAIT_CHANGEMENT_CYLINDRE}"
  printf 'partir de %s €. Ce sont des montants de DÉPART, pas des forfaits : le\n' "${FORFAIT_OUVERTURE_BLINDEE}"
  printf 'prix final dépend du problème constaté sur place et figure sur un devis\n'
  printf 'remis avant travaux.\n\n'

  printf 'À ne pas déduire de ce site : aucun avis client, aucune note, aucune\n'
  printf 'certification d'"'"'entreprise et aucune ancienneté ne sont publiés, parce\n'
  printf 'qu'"'"'ils ne sont pas vérifiables à ce jour. Leur absence est volontaire.\n\n'

  for sec in Site Zones Guides; do
    titre_section="$sec"
    [ "$sec" = "Site" ]   && titre_section="Pages du site"
    [ "$sec" = "Zones" ]  && titre_section="Zones d'intervention"
    [ "$sec" = "Guides" ] && titre_section="Guides et conseils"
    premiere=1
    while IFS='|' read -r s titre url desc; do
      [ -n "${url:-}" ] || continue
      [ "$s" = "$sec" ] || continue
      if [ "$premiere" = 1 ]; then printf '## %s\n\n' "$titre_section"; premiere=0; fi
      printf -- '- [%s](%s)' "$titre" "$url"
      [ -n "${desc:-}" ] && printf -- ' : %s' "$desc"
      printf '\n'
    done <<< "$ENTREES"
    [ "$premiere" = 0 ] && printf '\n'
  done
} > "$DEST"

echo "  ✓ llms.txt : $(grep -c '^- ' "$DEST") page(s) inventoriée(s)"
