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

# Retire les commentaires HTML de la page produite.
#
# Ils servent aux personnes qui maintiennent les sources ; ils n'ont rien à
# faire chez le visiteur. Ils pèsent une vingtaine de kilo-octets sur
# l'ensemble du site, et publier ses notes internes n'est jamais souhaitable.
#
# Ils causaient de surcroît un défaut réel : un partiel qui documentait le
# jeton par lequel il est injecté — « injecté par {{X}} » — voyait ce jeton
# substitué à son tour, puisqu'il fait partie de la valeur exportée.
#
# Le motif est non gourmand et traverse les sauts de ligne. Aucun « <!-- »
# n'apparaît ailleurs que dans un commentaire : vérifié sur les 43 pages.
nettoyer_html() {
  perl -0pe 's/<!--.*?-->\n?//gs'
}

# Échappe une valeur destinée à un littéral JSON (données structurées).
json_escape() {
  printf '%s' "$1" | perl -pe 's/\\/\\\\/g; s/"/\\"/g; s/\n/ /g'
}

# Réduit un libellé à un identifiant sûr : minuscules, sans accent, sans
# espace. Utilisé pour les familles de la galerie, qui viennent d'un fichier
# de configuration rédigé en français.
ardoise() {
  printf '%s' "$1" | perl -CSD -MUnicode::Normalize -pe '
    $_ = NFD($_); s/\p{NonspacingMark}//g; $_ = lc;
    s/[^a-z0-9]+/-/g; s/^-|-$//g;'
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

# --- Catalogue d'images ----------------------------------------------------
# Chaque entrée de src/images.conf produit deux variables :
#   {{IMG_ID}}     le <img> complet, prêt à poser dans une page
#   {{IMGSRC_ID}}  l'URL seule, pour og:image et les données structurées
#
# Le fichier réellement servi est choisi ici, à la construction : une vraie
# photo déposée dans static/assets/images/ prend automatiquement la place de
# l'illustration vectorielle, sans qu'aucune page n'ait à être modifiée.

IMAGES_SITEMAP=""   # alimente le sitemap images

# Renvoie le chemin web de la meilleure image disponible pour un identifiant.
# L'ordre reflète la qualité perçue : une photographie prime sur une
# illustration, un format moderne prime sur un format ancien.
resoudre_image() {
  local base="$1" ext
  for ext in avif webp jpg jpeg png svg; do
    if [ -f "static/assets/images/${base}.${ext}" ]; then
      printf '/assets/images/%s.%s' "$base" "$ext"
      return 0
    fi
  done
  return 1
}

# Construit un srcset si des variantes -800 / -1200 / -1600 existent.
#
# Le fichier principal est TOUJOURS ajouté à la liste, avec sa largeur réelle.
# Sans lui, un srcset ne contenant que « -800 800w » ne laisse au navigateur
# aucun autre candidat : un écran large afficherait la version 800 px étirée,
# c'est-à-dire moins bien qu'avant l'ajout des variantes.
construire_srcset() {
  local base="$1" ext="$2" largeur_reelle="$3" srcset="" largeur
  # Ces paliers doivent rester alignés sur VARIANTES dans
  # scripts/preparer-photos.py : une variante produite mais absente d'ici est
  # un fichier écrit sur le disque que le site ne sert jamais.
  for largeur in 600 800 1000 1200 1600; do
    if [ "$largeur" -lt "$largeur_reelle" ] \
       && [ -f "static/assets/images/${base}-${largeur}.${ext}" ]; then
      [ -n "$srcset" ] && srcset="${srcset}, "
      srcset="${srcset}/assets/images/${base}-${largeur}.${ext} ${largeur}w"
    fi
  done
  # Une liste réduite au seul fichier principal n'apporte rien : on la laisse
  # vide, et la balise garde son simple « src ».
  if [ -n "$srcset" ]; then
    srcset="${srcset}, /assets/images/${base}.${ext} ${largeur_reelle}w"
  fi
  printf '%s' "$srcset"
}

CATALOGUE_MANQUANT=0
PHOTOS_REELLES=0
PHOTOS_ATTENDUES=0
VISUELS_TOTAL=0

while IFS='|' read -r id photo repli largeur hauteur alt_photo alt_repli; do
  case "$id" in ''|\#*) continue ;; esac

  # Une photographie réelle est attendue à cet emplacement dès lors que la
  # deuxième colonne est renseignée, qu'elle ait été livrée ou non.
  [ -n "$photo" ] && PHOTOS_ATTENDUES=$((PHOTOS_ATTENDUES + 1))

  # La photographie prime toujours sur l'illustration. C'est le seul endroit
  # du site où cet arbitrage est fait.
  base=""; alt=""; nature="illustration"
  if [ -n "$photo" ] && chemin="$(resoudre_image "$photo")"; then
    base="$photo"; alt="$alt_photo"; nature="photo"
    PHOTOS_REELLES=$((PHOTOS_REELLES + 1))
  elif chemin="$(resoudre_image "$repli")"; then
    base="$repli"; alt="$alt_repli"
  else
    echo "  ! aucun visuel pour $id : ni static/assets/images/${photo:-–}.* ni static/assets/images/${repli}.*"
    CATALOGUE_MANQUANT=$((CATALOGUE_MANQUANT + 1))
    continue
  fi

  if [ -z "$alt" ]; then
    echo "  ! texte alternatif absent pour $id (colonne « alt » vide)"
    CATALOGUE_MANQUANT=$((CATALOGUE_MANQUANT + 1))
    continue
  fi

  VISUELS_TOTAL=$((VISUELS_TOTAL + 1))

  ext="${chemin##*.}"
  srcset="$(construire_srcset "$base" "$ext" "$largeur")"
  attr_srcset=""
  [ -n "$srcset" ] && attr_srcset=" srcset=\"${srcset}\" sizes=\"(max-width: 900px) 100vw, 600px\""

  # width et hauteur sont toujours écrits : c'est ce qui réserve la place et
  # évite que la page ne saute pendant le chargement (décalage cumulé).
  export "IMG_${id}=<img src=\"${chemin}\"${attr_srcset} width=\"${largeur}\" height=\"${hauteur}\" alt=\"${alt}\" loading=\"lazy\" decoding=\"async\" data-visuel=\"${nature}\">"
  export "IMGSRC_${id}=${chemin}"
  export "IMGNATURE_${id}=${nature}"

  # Vignette sociale correspondante, produite par scripts/generer-og.mjs à
  # partir du MÊME fichier que la page affiche. Une page écrit « image: og:HERO »
  # dans ses métadonnées : l'aperçu partagé suit alors automatiquement le
  # visuel réel, y compris quand une photographie remplace une illustration.
  og_nom="$(basename "$base")"
  if [ -f "static/assets/images/og/${og_nom}.jpg" ]; then
    export "OGIMG_${id}=/assets/images/og/${og_nom}.jpg"
  fi

  IMAGES_SITEMAP="${IMAGES_SITEMAP}${id}|${chemin}|${alt}"$'\n'
done < src/images.conf
export IMAGES_SITEMAP

# --- Ce que le site a le droit de dire de ses propres visuels ---------------
# La phrase affichée sous la galerie n'est pas écrite en dur : elle décrit ce
# que le build a réellement trouvé sur le disque. Le site ne peut donc pas
# présenter une illustration comme un chantier réel, ni continuer à s'excuser
# de n'avoir que des illustrations une fois les photos livrées.
if [ "$PHOTOS_REELLES" -eq 0 ]; then
  export MENTION_VISUELS="Ces visuels sont des <strong>illustrations</strong> : ils expliquent le geste technique, ils ne représentent pas un chantier particulier."
elif [ "$PHOTOS_REELLES" -lt "$VISUELS_TOTAL" ]; then
  export MENTION_VISUELS="Les photographies sont prises sur nos interventions, avec l'accord des clients concernés. Les visuels restants sont des <strong>illustrations</strong>, signalées comme telles sur chaque vignette."
else
  export MENTION_VISUELS="Photographies prises sur nos interventions, avec l'accord des clients concernés."
fi
export PHOTOS_REELLES PHOTOS_ATTENDUES VISUELS_TOTAL

# --- Carte des zones d'intervention ----------------------------------------
# Le tracé SVG est produit hors build par scripts/generer-carte.py, à partir
# de src/zones.conf et des contours de src/geo/. Il est versionné : le build
# reste sans dépendance Python et fonctionne hors ligne.
#
# La liste des départements, elle, est régénérée ici à chaque construction, à
# partir de la même src/zones.conf. Carte et liste ne peuvent donc pas diverger.

export CARTE_SVG=""
export CARTE_LISTE=""
export CARTE_ZONES=""

if [ -f src/partials/carte-zones.svg ]; then
  CARTE_SVG="$(cat src/partials/carte-zones.svg)"

  liste=""
  while IFS='|' read -r code nom url reste; do
    case "$code" in ''|\#*|VILLE) continue ;; esac
    villes="$(awk -F'|' -v d="$code" '$1=="VILLE" && $5==d { printf "%s%s", (n++ ? ", " : ""), $2 } END { print "" }' src/zones.conf)"
    liste="${liste}      <li>
        <a href=\"${url}\" data-zone=\"${code}\">
          <strong>${nom} <span>(${code})</span></strong>
          <span class=\"carte-villes\">${villes}</span>
        </a>
      </li>
"
  done < src/zones.conf

  CARTE_LISTE="$liste"
  export CARTE_SVG CARTE_LISTE
  # Le partiel contient lui-même {{CARTE_SVG}} et {{CARTE_LISTE}} : une passe
  # de substitution suffit, elle est faite ici pour que le jeton
  # {{CARTE_ZONES}} livre un bloc déjà complet aux pages.
  CARTE_ZONES="$(nettoyer_html < src/partials/carte-zones.html | substituer)"
  export CARTE_ZONES
else
  echo "  ! src/partials/carte-zones.svg absent : lancez python3 scripts/generer-carte.py"
fi

# --- Galerie « Nos interventions » -----------------------------------------
# Entièrement construite depuis src/galerie.conf : ajouter une vignette est
# une ligne de configuration, jamais une modification de page.

export GALERIE=""
export GALERIE_FILTRES=""

if [ -f src/galerie.conf ]; then
  familles=""
  vignettes=""
  while IFS='|' read -r id famille titre legende; do
    case "$id" in ''|\#*) continue ;; esac

    balise="$(printf '%s' "$(eval "printf '%s' \"\${IMG_${id}:-}\"")")"
    if [ -z "$balise" ]; then
      echo "  ! galerie : identifiant d'image inconnu — $id"
      CATALOGUE_MANQUANT=$((CATALOGUE_MANQUANT + 1))
      continue
    fi

    # La famille alimente le filtre ; l'ordre de première apparition dans le
    # fichier décide de l'ordre des boutons.
    case "|${familles}|" in
      *"|${famille}|"*) : ;;
      *) familles="${familles}${familles:+|}${famille}" ;;
    esac

    cle="$(ardoise "$famille")"

    vignettes="${vignettes}      <figure class=\"apparait\" data-famille=\"${cle}\">
        ${balise}
        <figcaption><strong>${titre}</strong>${legende}</figcaption>
      </figure>
"
  done < src/galerie.conf

  GALERIE="$vignettes"

  filtres="        <button type=\"button\" class=\"filtre actif\" data-filtre=\"tout\" aria-pressed=\"true\">Tout voir</button>
"
  ancien_ifs="$IFS"; IFS='|'
  for famille in $familles; do
    cle="$(ardoise "$famille")"
    filtres="${filtres}        <button type=\"button\" class=\"filtre\" data-filtre=\"${cle}\" aria-pressed=\"false\">${famille}</button>
"
  done
  IFS="$ancien_ifs"
  GALERIE_FILTRES="$filtres"

  export GALERIE GALERIE_FILTRES
fi

# --- Schémas explicatifs ---------------------------------------------------
# Voir src/schemas.conf. Un schéma est affiché à ses proportions natives, dans
# une figure autonome, avec une légende qui dit ce qu'il est. Il ne passe ni
# par le catalogue d'images ni par la galerie : ce n'est pas une photographie
# d'intervention et il ne doit jamais être présenté comme telle.
if [ -f src/schemas.conf ]; then
  while IFS='|' read -r id base largeur hauteur alt legende; do
    case "$id" in ''|\#*) continue ;; esac

    chemin="$(resoudre_image "$base" || true)"
    if [ -z "$chemin" ]; then
      echo "  ! schéma introuvable : static/assets/images/${base}.*"
      CATALOGUE_MANQUANT=$((CATALOGUE_MANQUANT + 1))
      continue
    fi

    ext="${chemin##*.}"
    srcset=""
    for l in 600 900; do
      if [ "$l" -lt "$largeur" ] && [ -f "static/assets/images/${base}-${l}.${ext}" ]; then
        srcset="${srcset}${srcset:+, }/assets/images/${base}-${l}.${ext} ${l}w"
      fi
    done
    [ -n "$srcset" ] && srcset="${srcset}, ${chemin} ${largeur}w"
    attr_srcset=""
    [ -n "$srcset" ] && attr_srcset=" srcset=\"${srcset}\" sizes=\"(max-width: 780px) 100vw, 720px\""

    export "SCHEMA_${id}=<figure class=\"schema\"><img src=\"${chemin}\"${attr_srcset} width=\"${largeur}\" height=\"${hauteur}\" alt=\"${alt}\" loading=\"lazy\" decoding=\"async\"><figcaption>${legende}</figcaption></figure>"
  done < src/schemas.conf
fi

# --- Blocs réutilisés par les landing pages locales ------------------------
# Ces trois blocs décrivent des règles de fonctionnement identiques partout :
# les mêmes problèmes traités, le même déroulé, les mêmes facteurs de prix.
# Les recopier dans chaque page les ferait diverger à la première correction.
# Le contenu proprement local, lui, est écrit page par page — il n'y a aucune
# page de zone clonée.
export GRILLE_PROBLEMES="$(nettoyer_html < src/partials/grille-problemes.html | substituer)"
export DEROULE="$(nettoyer_html < src/partials/deroule-intervention.html | substituer)"
export FACTEURS_PRIX="$(nettoyer_html < src/partials/facteurs-prix.html | substituer)"
export PRESTATIONS="$(nettoyer_html < src/partials/prestations-completes.html | substituer)"

# --- Avis clients -----------------------------------------------------------
# Aucun avis n'est écrit dans le code du site : le bloc affiché dépend
# uniquement de l'existence d'une fiche Google Business Profile renseignée
# dans src/config.sh. Tant qu'il n'y en a pas, le site le dit, et n'invente
# ni note, ni étoile, ni témoignage.
if [ -n "${URL_GOOGLE_BUSINESS:-}" ]; then
  export AVIS_GOOGLE="$(nettoyer_html < src/partials/avis-fiche.html | substituer)"
  export AVIS_CHAPEAU="Ils sont hébergés par Google, pas par nous : nous ne pouvons ni les choisir, ni les réécrire."
else
  export AVIS_GOOGLE="$(nettoyer_html < src/partials/avis-vide.html | substituer)"
  export AVIS_CHAPEAU="Nous préférons ne rien afficher plutôt que d'afficher des avis que nous n'aurions pas reçus."
fi


# Le visuel du héros est le plus grand élément affiché à l'ouverture : il ne
# doit pas être différé, sans quoi il devient lui-même le frein au rendu.
if [ -n "${IMG_HERO:-}" ]; then
  export IMG_HERO="${IMG_HERO/ loading=\"lazy\" decoding=\"async\"/ fetchpriority=\"high\" decoding=\"async\"}"
fi

# --- Dimensionnement réel des images ---------------------------------------
# Un même identifiant d'image sert dans plusieurs emplacements : le héros, une
# carte de service, une vignette de galerie. Or l'attribut « sizes » ne décrit
# pas le fichier, il décrit la LARGEUR À LAQUELLE LA PAGE VA L'AFFICHER — c'est
# elle qui détermine le fichier choisi dans le srcset. Une valeur unique était
# donc forcément fausse quelque part : elle annonçait 600 px partout, et le
# navigateur téléchargeait le fichier de 600 px pour l'afficher sur 1 198 px.
# Résultat : une image visiblement floue sur ordinateur.
#
# Les valeurs ci-dessous ont été relevées au navigateur sur les onze largeurs
# testées, conteneur par conteneur. Elles sont volontairement légèrement
# supérieures au maximum mesuré : mieux vaut quelques kilo-octets de trop
# qu'une image floue.
#
# La même passe désigne l'image principale de la page — la première d'un
# grand conteneur — et lui retire le chargement différé : c'est elle que le
# navigateur doit demander en premier, pas en dernier.
# --- Intégrité de la feuille de style --------------------------------------
# Une accolade orpheline dans un fichier CSS n'est pas une erreur bruyante :
# le navigateur abandonne silencieusement TOUTES les règles qui suivent. Une
# moitié de site perd sa mise en forme sans qu'aucun outil ne proteste, et le
# défaut ne se voit qu'à l'œil, page par page.
#
# Ce contrôle compte les accolades hors commentaires. Il ne remplace pas un
# analyseur CSS, mais il attrape la faute qui coûte le plus cher.
verifier_css() {
  local fichier="$1"
  local bilan
  bilan="$(perl -0777 -ne '
    s{/\*.*?\*/}{}gs;
    my $o = () = /\{/g;
    my $f = () = /\}/g;
    print "$o $f";
  ' "$fichier")"
  set -- $bilan
  if [ "$1" != "$2" ]; then
    echo "  ! $fichier : $1 accolade(s) ouvrante(s) pour $2 fermante(s)."
    echo "    Le navigateur ignorerait toutes les règles après le déséquilibre."
    return 1
  fi
  return 0
}

# --- Page courante dans la navigation --------------------------------------
# Un menu de sept entrées sans repère visuel oblige le visiteur à relire le
# titre de la page pour savoir où il est. La marque est posée ici, sur le
# lien dont l'adresse correspond exactement à celle de la page : le HTML
# porte aria-current="page", la CSS s'en sert pour le souligner. Aucune page
# n'a donc à connaître sa propre entrée de menu.
marquer_page_courante() {
  printf '%s' "$1" | PAGE_PATH="$2" perl -0777 -pe '
    my $ici = $ENV{PAGE_PATH};
    # « /blog/ » et « / » se terminent par une barre ; les autres non.
    s{(<nav id="nav-principal".*?</nav>)}{
      my $nav = $1;
      $nav =~ s/<a href="\Q$ici\E"/<a href="$ici" aria-current="page"/;
      $nav;
    }gse;
  '
}

ajuster_visuels() {
  printf '%s' "$1" | perl -0777 -pe '
    my %profil = (
      "hero-media"        => "(max-width: 1150px) 96vw, 600px",
      "media-large"       => "(max-width: 1240px) 96vw, 1200px",
      "hero-local-media"  => "(max-width: 560px) 92vw, (max-width: 900px) 96vw, 560px",
      "intervention-media"=> "(max-width: 560px) 92vw, (max-width: 900px) 96vw, 680px",
      "carte-media"       => "(max-width: 560px) 92vw, 400px",
      "apparait"          => "(max-width: 560px) 92vw, 360px",
      "avant-apres"       => "(max-width: 700px) 92vw, 560px",
    );
    my %grand = map { $_ => 1 } qw(hero-media media-large hero-local-media);
    my $principale = 0;

    s{(.*?)(<img\b[^>]*>)}{
      my ($avant, $img) = ($1, $2);
      my $classe = "";
      $classe = $1 while $avant =~ /class="([^"]*)"/g;
      my ($premiere) = split / /, $classe;
      $premiere = "" unless defined $premiere;

      if (my $s = $profil{$premiere}) {
        $img =~ s/\ssizes="[^"]*"/ sizes="$s"/;
      }
      if (!$principale && $grand{$premiere}) {
        $principale = 1;
        $img =~ s/\sloading="lazy"/ fetchpriority="high"/;
      }
      $avant . $img;
    }gse;
  '
}

# Le navigateur ne découvre l'image d'ouverture qu'après avoir analysé le corps
# de la page. Le préchargement la lui annonce dès l'en-tête : elle part en même
# temps que la feuille de style au lieu d'attendre son tour.
#
# Il est calculé PAR PAGE, à partir de la balise réellement présente dans son
# corps — celle qui porte fetchpriority="high". Un préchargement global ferait
# télécharger le visuel d'accueil sur les 43 pages, y compris celles qui ne
# l'affichent pas : le gain sur une page se paierait par une centaine de
# kilo-octets perdus sur les quarante-deux autres.
#
# imagesrcset et imagesizes reprennent exactement ceux de la balise, sans quoi
# le navigateur téléchargerait deux fichiers différents.
precharger_visuel_principal() {
  printf '%s' "$1" | perl -0ne '
    exit unless /(<img[^>]*fetchpriority="high"[^>]*>)/;
    my $b = $1;
    my ($src)    = $b =~ /\ssrc="([^"]*)"/;
    my ($srcset) = $b =~ /\ssrcset="([^"]*)"/;
    my ($sizes)  = $b =~ /\ssizes="([^"]*)"/;
    exit unless $src;
    my $attrs = $srcset ? qq( imagesrcset="$srcset" imagesizes="$sizes") : "";
    print qq(<link rel="preload" href="$src" as="image"$attrs fetchpriority="high">);
  '
}

# --- Formulaire de devis ---------------------------------------------------
# Le formulaire n'existe qu'en un seul exemplaire, dans src/partials/. Les
# pages qui l'affichent écrivent simplement {{FORMULAIRE_DEVIS}} : une
# correction sur le partiel se répercute partout au build suivant.
export FORMULAIRE_DEVIS="$(nettoyer_html < src/partials/formulaire-devis.html)"

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
  # « image: og:HERO » désigne la vignette sociale de l'entrée HERO du
  # catalogue, quel que soit le fichier réellement retenu pour cette entrée.
  case "$PAGE_IMAGE" in
    og:*)
      cle_og="OGIMG_${PAGE_IMAGE#og:}"
      resolue="$(eval "printf '%s' \"\${${cle_og}:-}\"")"
      if [ -n "$resolue" ]; then
        PAGE_IMAGE="$resolue"
      else
        echo "  ! aperçu social introuvable pour ${PAGE_IMAGE} (page ${rel})"
        PAGE_IMAGE=""
      fi
      ;;
  esac
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
  CORPS="$(ajuster_visuels "$CORPS")"

  export PRECHARGEMENT_HERO="$(precharger_visuel_principal "$CORPS")"

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
    marquer_page_courante "$(cat src/partials/header.html)" "$PAGE_PATH"
    printf '%s\n' "$CORPS"
    cat src/partials/footer.html
  } | substituer | nettoyer_html > "$dest"

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
NB_URLS=$(grep -c '^    <loc>' "$OUT/sitemap.xml" 2>/dev/null || echo 0)
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

if ! verifier_css static/assets/css/style.css; then
  echo
  echo "BUILD ÉCHEC : feuille de style invalide."
  exit 1
fi

echo "BUILD SUCCESS"
echo "  $PAGE_COUNT pages · $NB_URLS URLs au sitemap · $NB_RESSOURCES ressources vérifiées"
echo "  Dossier de production : $OUT/  (à servir comme document root)"
exit 0
