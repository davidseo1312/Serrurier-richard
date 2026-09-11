# Serrurier Richard

Site vitrine, pages de services, pages locales et blog SEO pour une entreprise
de dépannage en serrurerie intervenant sur six départements du Grand Ouest :
Ille-et-Vilaine (35), Morbihan (56), Finistère (29), Côtes-d'Armor (22),
Loire-Atlantique (44) et Maine-et-Loire (49).

**43 pages en HTML statique**, sans framework et sans dépendance. Une feuille
de style, un fichier JavaScript, aucune requête réseau externe au chargement.
Un seul fichier PHP, pour le formulaire de devis.

Conçu pour un hébergement mutualisé Hostinger : on dépose le contenu de
`public/` dans `public_html/`, et le site fonctionne.

---

## Sommaire

- [Démarrage rapide](#démarrage-rapide)
- [Comment le site est construit](#comment-le-site-est-construit)
- [Organisation des fichiers](#organisation-des-fichiers)
- [Modifier le site](#modifier-le-site)
  - [Téléphone, adresse, horaires, tarifs](#téléphone-adresse-horaires-tarifs)
  - [Ajouter une page de service](#ajouter-une-page-de-service)
  - [Ajouter une page locale par ville](#ajouter-une-page-locale-par-ville)
  - [Ajouter un article de blog](#ajouter-un-article-de-blog)
  - [Modifier le menu et le pied de page](#modifier-le-menu-et-le-pied-de-page)
  - [Ajouter une photo — sans écrire une ligne de code](#ajouter-une-photo--sans-écrire-une-ligne-de-code)
  - [La galerie « Nos interventions »](#la-galerie--nos-interventions-)
  - [La carte des zones d'intervention](#la-carte-des-zones-dintervention)
  - [Les avis clients](#les-avis-clients)
  - [Les landing pages de zones](#les-landing-pages-de-zones)
  - [Les CTA](#les-cta)
- [Le formulaire de devis](#le-formulaire-de-devis)
- [Google Analytics, Tag Manager, Search Console](#google-analytics-tag-manager-search-console)
- [Contrôles avant mise en ligne](#contrôles-avant-mise-en-ligne)
- [DEPLOYMENT HOSTINGER](#deployment-hostinger)
- [Cohérence géographique — à trancher avant publication](#cohérence-géographique--à-trancher-avant-publication)
- [Avant la mise en ligne : informations à fournir](#avant-la-mise-en-ligne--informations-à-fournir)

---

## Démarrage rapide

```bash
bash scripts/build.sh        # génère public/
bash scripts/check-seo.sh    # contrôle SEO et pré-vol de mise en ligne
bash scripts/apercu.sh       # aperçu sur http://localhost:8080
```

Rien à installer : `bash`, `perl` et `find` suffisent au build. `php` n'est
nécessaire que pour l'aperçu local et le formulaire.

Vous pouvez aussi ouvrir directement `public/index.html` dans un navigateur.
Les URLs sans extension ne fonctionneront pas ainsi (elles dépendent du
`.htaccess`), mais la mise en page et le contenu sont fidèles.

---

## Comment le site est construit

`scripts/build.sh` assemble chaque page à partir de trois sources :

```
src/pages/**.html      contenu de la page + bloc de métadonnées
src/partials/*.html    en-tête, pied de page, formulaire, JSON-LD
src/config.sh          valeurs partagées : téléphone, tarifs, horaires…
        |
        v
public/**.html         site complet, déployable tel quel
```

Les pages écrivent `{{NOM_DE_LA_VARIABLE}}` là où une valeur de `config.sh`
doit apparaître. Le build les remplace, et `check-seo.sh` signale tout token
qui n'aurait pas été résolu.

Le build produit également, sans intervention :

- l'**URL canonique** de chaque page, déduite du chemin du fichier ;
- le **fil d'Ariane** en données structurées `BreadcrumbList` ;
- le balisage **`FAQPage`** de chaque page, dérivé de ses blocs `<details>`
  réellement affichés — Google exige que le balisage corresponde au texte
  visible, et le dériver supprime tout risque d'écart ;
- `sitemap.xml` et `robots.txt`.

L'URL découle du nom de fichier :

| Fichier source | URL publiée |
|---|---|
| `src/pages/index.html` | `/` |
| `src/pages/ouverture-porte.html` | `/ouverture-porte` |
| `src/pages/zones/morbihan-56.html` | `/zones/morbihan-56` |
| `src/pages/blog/index.html` | `/blog/` |

---

## Organisation des fichiers

```
src/
  config.sh                    Toutes les valeurs partagées du site
  partials/
    head.html, head-close.html En-tête HTML, métadonnées, Open Graph
    header.html, footer.html   Navigation, pied de page, barre d'appel mobile
    formulaire-devis.html      Le formulaire, en un seul exemplaire
    schema-*.html              Données structurées par type de page
  pages/                       Une page = un fichier
static/                        Copié tel quel dans public/
  .htaccess                    URLs propres, redirections, cache, sécurité
  envoi-devis.php              Traitement du formulaire
  manifest.webmanifest
  assets/css/style.css         Feuille de style unique
  assets/js/site.js            Menu, consentement, suivi des conversions
  assets/img/                  Illustrations, icônes, vignette sociale
public/                        Généré par le build — ne jamais éditer à la main
scripts/
  build.sh                     Assemble le site
  gen-sitemap.sh               sitemap.xml et robots.txt
  faq-jsonld.pl                Balisage FAQPage dérivé des <details>
  audit.sh                     Enchaîne tous les contrôles
  check-seo.sh                 Contrôle SEO et pré-vol
  check-html.py                Contrôle structurel du HTML (facultatif)
  apercu.sh                    Aperçu local avec les URLs de production
  routeur-local.php            Reproduit le .htaccess pour l'aperçu
  generer-images.py            Vignette sociale et icônes (facultatif)
  deploy-hostinger.sh          Envoi FTP
  diag-hostinger.sh            Diagnostic en cas de 403
tests/
  navigateur.mjs               Parcours réels, mobile et ordinateur
  lancer.sh                    Lance ces tests
docs/
  modele-page-ville.html       Modèle commenté pour une nouvelle page locale
  deploiement-hostinger.md     Marche à suivre détaillée
  configuration.md             Référence de toutes les variables
.github/workflows/
  deploy.yml                   Build et publication vers la branche deploy
```

`public/` **est versionné** : il permet de récupérer le dossier prêt à
déployer directement depuis GitHub, sans relancer le build. Il est
intégralement régénéré à chaque `build.sh` — n'y modifiez jamais un fichier à
la main, il serait écrasé.

---

## Modifier le site

### Téléphone, adresse, horaires, tarifs

**Tout est dans `src/config.sh`**, puis `bash scripts/build.sh`.

| Vous voulez changer… | Variable |
|---|---|
| Le numéro de téléphone | `TELEPHONE` **et** `TELEPHONE_E164` |
| L'adresse affichée dans les mentions légales | `SIEGE_RUE`, `SIEGE_CP`, `SIEGE_VILLE` |
| L'adresse d'exploitation (balisage local) | `ADRESSE_RUE`, `ADRESSE_CP`, `ADRESSE_VILLE`, `LATITUDE`, `LONGITUDE` |
| Les horaires annoncés | `DISPONIBILITE`, `HORAIRES_URGENCE`, `HORAIRES_BUREAU` |
| Le délai de réponse aux devis | `DELAI_REPONSE` |
| La zone d'intervention affichée | `ZONE_INTERVENTION`, `ZONE_COURTE` |
| Les tarifs | `TAUX_HORAIRE`, `FRAIS_DEPLACEMENT`, `MAJORATION_NUIT`, `FORFAIT_*` |
| L'adresse qui reçoit les devis | `EMAIL_DEVIS` |
| Le nom commercial, la baseline | `NOM_COMMERCIAL`, `BASELINE` |
| Le domaine | `DOMAINE`, `BASE_URL` |

> **`TELEPHONE_E164`** est le format international, sans espaces :
> `02 20 06 00 75` s'écrit `+33220060075`. C'est lui qui fait fonctionner les
> liens `tel:` sur mobile. Les deux doivent être modifiés ensemble.

> **Les tarifs affichés doivent être ceux réellement pratiqués.** L'arrêté du
> 24 janvier 2017 l'impose pour le dépannage à domicile.

> **N'annoncez que la disponibilité réellement assurée.** Une promesse
> « 24h/24 » non tenue est une pratique commerciale trompeuse (art. L121-2 du
> code de la consommation) et fait chuter la note Google Business Profile.

Après un changement de `NOM_COMMERCIAL` ou de `BASELINE`, régénérez aussi la
vignette de partage social :

```bash
python3 scripts/generer-images.py     # nécessite Pillow
```

### Ajouter une page de service

1. Créer `src/pages/mon-service.html` — l'URL sera `/mon-service`.
2. Commencer par un bloc de métadonnées :

```html
<!--meta
title: Titre de moins de 60 caractères
description: Description de 120 à 158 caractères.
schema: service
breadcrumb: Nom court
parent_nom: Nos prestations
parent_url: /serrurier
priority: 0.8
-->
```

3. Ajouter la carte correspondante dans `src/pages/serrurier.html` et le lien
   dans `src/partials/footer.html`.
4. `bash scripts/build.sh && bash scripts/check-seo.sh`

Les blocs `<details>` d'une section `.faq` produisent automatiquement le
balisage `FAQPage` : ne l'écrivez pas à la main. Vérifiez simplement que vos
questions ne figurent pas déjà sur une autre page — `check-seo.sh` le signale,
car deux pages portant la même question se concurrencent dans les résultats
enrichis.

### Ajouter une page locale par ville

```bash
cp docs/modele-page-ville.html src/pages/serrurier-quimper.html
```

Le modèle est intégralement commenté. **Lisez-le avant d'écrire** : une page
locale qui reprend le texte d'une autre en changeant le nom de la ville est du
contenu dupliqué, et en produire vingt dégrade le référencement de tout le
site, y compris des pages qui fonctionnaient.

Ajoutez ensuite le lien dans `src/pages/zones-d-intervention.html` et dans la
page départementale correspondante.

Exemples à suivre : `src/pages/serrurier-rennes.html`,
`serrurier-vannes.html`, `serrurier-nantes.html` — trois contextes différents,
aucune n'est la copie d'une autre.

### Ajouter un article de blog

1. Créer `src/pages/blog/mon-article.html`
2. Bloc de métadonnées :

```html
<!--meta
title: Titre de moins de 60 caractères
description: Description de 120 à 158 caractères.
schema: article
breadcrumb: Titre affiché dans les données structurées
parent_nom: Conseils serrurerie
parent_url: /blog/
date: 2026-09-15
priority: 0.7
-->
```

3. Ajouter la carte dans `src/pages/blog/index.html`
4. `bash scripts/build.sh && bash scripts/check-seo.sh`

### Modifier le menu et le pied de page

- Menu principal : `src/partials/header.html`
- Pied de page : `src/partials/footer.html`
- Barre d'appel fixe sur mobile : fin de `src/partials/footer.html`

Ces trois éléments sont partagés par toutes les pages : une modification s'y
répercute partout au build suivant.

### Ajouter une photo — sans écrire une ligne de code

C'est le point le plus important du système visuel. **Déposer un fichier
suffit** : le build préfère automatiquement une vraie photo à l'illustration
vectorielle livrée.

**Commencez toujours par l'état des lieux :**

```bash
bash scripts/verifier-photos.sh
```

Il liste les emplacements qui attendent une photographie, avec le **nom de
fichier exact** et le format à respecter, et signale les fichiers trop lourds.

```
static/assets/images/
├── serrurerie/        ouverture-porte/      porte-bloquee/
├── cle-cassee/        cle-perdue/           serrure/
├── serrure-3-points/  serrure-5-points/     porte-blindee/
├── blindage/          effraction/           coffre-fort/
├── rideau-metallique/ installation/         interventions/
└── og/                vignettes de partage social, générées
```

**La marche à suivre**

1. `bash scripts/verifier-photos.sh` — repérez la ligne de l'emplacement
   voulu. Elle donne le chemin, le nom de fichier exact et les dimensions.
2. Préparez la photo à ces dimensions, en **WEBP** de préférence
   (<https://squoosh.app> suffit, rien à installer), sous 250 Ko.
3. Déposez-la **sous le nom exact** indiqué, avec l'extension `.webp`.
4. `bash scripts/build.sh`
5. Relisez le texte alternatif dans `src/images.conf` : il est déjà écrit,
   mais il doit décrire le cliché **réellement** déposé.

L'illustration est remplacée **partout** : dans la page, dans la galerie de
l'accueil, dans le sitemap images et dans la vignette de partage social.

**Deux candidats par emplacement.** Chaque ligne de `src/images.conf` déclare
la photographie attendue *et* l'illustration de repli, avec un texte
alternatif pour chacune — une photo et un dessin ne montrent pas la même
chose, et l'`alt` doit décrire ce qui est réellement affiché :

```
ID | photo | repli | largeur | hauteur | alt de la photo | alt du repli
```

**Ordre de préférence du build** : `.avif` → `.webp` → `.jpg` → `.jpeg` →
`.png` → `.svg`. L'illustration vectorielle arrive en dernier : elle ne
reprend la main que si aucune photo n'existe.

**Variantes responsives** : déposez en plus `nom-800.webp`, `nom-1200.webp`
ou `nom-1600.webp` et le `srcset` se construit tout seul.

> **Le site dit lui-même ce qu'il affiche.** Chaque vignette de la galerie
> porte la mention « Illustration » tant qu'elle en est une, et la phrase
> d'introduction de la section « Nos interventions » change selon ce que le
> build a réellement trouvé sur le disque. Une illustration ne peut donc pas
> être présentée comme un chantier réel, même par inadvertance — et le site
> cesse de s'en excuser dès que les photos arrivent.

> **Une règle à ne pas enfreindre.** N'utilisez ni image trouvée dans Google
> Images, ni photo de concurrent, ni lien direct vers un fichier hébergé
> ailleurs. Ne publiez pas la porte d'un client sans son accord, et retirez
> les données GPS des fichiers (`exiftool -all= photo.jpg`).

**Marche à suivre complète, cas particuliers compris :** [`docs/photos.md`](docs/photos.md).

### Schémas explicatifs

Une planche pédagogique — texte, repères, vue éclatée — passe par
**`src/schemas.conf`**, pas par `src/images.conf`. Elle est affichée à ses
proportions natives, avec sa légende, via le jeton `{{SCHEMA_ID}}`. La
recadrer au format d'une carte couperait ses légendes.

> **Une planche « avant / après » ne documente pas un chantier**, elle illustre
> une prestation. La légende affichée le dit explicitement.

### Aucun pictogramme inventé

Le site n'embarque **aucune icône vectorielle décorative** : ni logo de marque,
ni combiné téléphonique, ni bouclier, ni horloge. Chacun a été remplacé par ce
qu'il prétendait représenter — le numéro en toutes lettres sur les boutons
d'appel, quatre photographies sur la réassurance, de la typographie ailleurs.
L'icône d'onglet porte les initiales composées.

Le seul SVG restant est le tracé réel des six départements : une donnée, pas
une décoration. **N'y remettez pas d'icône de banque** en ajoutant un
composant.

### La galerie « Nos interventions »

Elle est pilotée par **`src/galerie.conf`**. Une ligne = une vignette :

```
ID D'IMAGE | FAMILLE | TITRE | LÉGENDE
```

L'ordre du fichier est l'ordre d'affichage. La `FAMILLE` alimente les boutons
de filtre affichés au-dessus de la galerie : ils sont déduits du fichier, dans
l'ordre de première apparition. Ajouter une famille ne demande donc ni CSS ni
JavaScript. Sans JavaScript, les boutons restent inertes et la galerie affiche
l'ensemble des vignettes — le comportement utile par défaut.

### Les landing pages de zones

Les six pages de `src/pages/zones/` ne sont pas des pages SEO : ce sont des
**pages commerciales complètes**, d'environ 2 200 mots chacune, conçues pour
qu'un visiteur arrivé de Google y trouve tout sans avoir à naviguer ailleurs.

Chacune suit la même architecture :

| Section | Rôle |
|---|---|
| Héros local | H1, promesse, deux CTA, photo, communes couvertes en pastilles |
| Besoin d'un serrurier ? | Grille des neuf situations, chacune liée à sa page service |
| Prestations locales | Six cartes avec photo, contexte local et lien |
| Le terrain | Description longue, réellement propre au département |
| Nos interventions | Trois cas types : problème, diagnostic, intervention, résultat |
| Avis | Composant piloté par la configuration, sans témoignage fabriqué |
| Déroulé | Les quatre étapes, en frise |
| Tarifs | Chiffres réels de `src/config.sh` et facteurs de variation |
| Les réponses en une phrase | Six réponses courtes, lisibles par un moteur comme par un humain |
| FAQ locale | Six questions **spécifiques au département** |
| Communes | Grille des villes et maillage interne |
| CTA final | Appel et devis |

**Ce qui est mutualisé, et pourquoi.** Trois blocs sont des partiels communs —
la grille des problèmes (`{{GRILLE_PROBLEMES}}`), le déroulé (`{{DEROULE}}`) et
les facteurs de prix (`{{FACTEURS_PRIX}}`). Ce sont des règles de
fonctionnement identiques partout : les recopier dans six pages les ferait
diverger à la première correction. Tout le reste est écrit page par page.

**Mesure de duplication.** Similarité maximale entre deux pages de zone :
**13 %** — soit exactement les trois blocs mutualisés. Les 87 % restants sont
propres à chaque département. Aucune page n'est clonée.

> **Pour ajouter un département**, ajoutez-le à `src/zones.conf`, lancez
> `python3 scripts/telecharger-contours.py` puis `python3 scripts/generer-carte.py`,
> et écrivez la page en reprenant la structure d'une page existante. **N'en
> faites pas une copie avec les noms de communes remplacés** : une page de zone
> sans contenu propre ne sert ni le visiteur ni le référencement.

### Les CTA

Chaque landing page de zone porte **huit liens d'appel et neuf liens de devis**,
répartis aux endroits où la décision se prend : héros, après les prestations,
après les interventions, après la FAQ, et en pied de page. Les pages services
en portent au moins trois, dont une bande intermédiaire posée juste avant la
FAQ.

Tous les liens d'appel portent `data-track="appel"` et un `data-track-zone`
identifiant l'emplacement : c'est ce qui permettra de savoir quel CTA convertit
réellement une fois la mesure d'audience activée.

### La carte des zones d'intervention

Elle vit dans **`src/zones.conf`**, source unique des départements et des
villes affichés. Le tracé lui-même est produit par :

```bash
python3 scripts/generer-carte.py
```

qui écrit `src/partials/carte-zones.svg` à partir de `src/zones.conf` et des
contours de `src/geo/` (données IGN Admin Express, Licence ouverte Etalab).
Le SVG est versionné : le build n'a donc besoin ni de Python ni du réseau.
La **liste** des départements affichée à côté de la carte, elle, est
régénérée à chaque construction depuis le même `src/zones.conf` — carte et
liste ne peuvent pas diverger.

Le jeton `{{CARTE_ZONES}}` pose le bloc complet dans une page. Il est
actuellement utilisé sur l'accueil et sur `/zones-d-intervention`.

> **N'ajoutez jamais dans `src/zones.conf` un département ou une ville où
> l'entreprise n'intervient pas réellement.** La carte doit refléter
> exactement les zones annoncées dans les pages.

**Deux niveaux, et c'est délibéré.** La carte affichée par défaut est un SVG
servi par le site : affichage instantané, aucune requête vers un tiers, aucune
adresse IP transmise, donc aucun consentement à demander, et elle fonctionne
sans JavaScript. La carte détaillée à tuiles (Leaflet + OpenStreetMap,
`static/assets/vendor/leaflet/`, hébergée par le site) n'est chargée
**qu'après un clic explicite** du visiteur, qui est prévenu que le service est
extérieur. C'est aussi pour elle que la CSP autorise
`tile.openstreetmap.org` : si vous retirez la carte détaillée, retirez ce
domaine de `static/.htaccess`.

### Les avis clients

Le site n'affiche **aucun avis écrit en dur**, et n'en affichera jamais : le
bloc dépend uniquement de `URL_GOOGLE_BUSINESS` dans `src/config.sh`.

| `URL_GOOGLE_BUSINESS` | Ce qui s'affiche |
|---|---|
| vide (cas actuel) | un encadré qui annonce l'emplacement réservé aux avis vérifiés, sans note ni témoignage |
| renseignée | un renvoi vers la fiche, où le visiteur lit les avis réels et à jour |

Ni note, ni nombre d'étoiles, ni compteur ne sont écrits dans le site : ces
valeurs changent en permanence, un chiffre figé dans le code serait faux le
lendemain. Aucun balisage `AggregateRating` n'est émis non plus — un site qui
se note lui-même relève des « avis auto-attribués », que Google ignore et qui
exposent à une action manuelle.

> **Ne fabriquez jamais un avis, une note, une étoile ou un témoignage.**
> C'est une pratique commerciale trompeuse (art. L121-2 du code de la
> consommation), et cela se repère.

### Contrôler les images

```bash
python3 scripts/audit-images.py
```

Détecte : image référencée mais absente, texte alternatif manquant ou trop
court, `width`/`height` absents, fichier trop lourd, nom de fichier sans
signification, image livrée mais utilisée nulle part, vignette de partage
au format SVG — que les réseaux sociaux ignorent — et **le même visuel affiché
deux fois sur une même page**, qui est une erreur bloquante.

### Une image, un seul emplacement

La règle est absolue et vérifiée par les tests : **un fichier image n'est
affiché qu'à un seul endroit du site.** 17 visuels, 17 emplacements. Elle a
trois conséquences assumées :

- une page affiche **au plus une image**, celle de son sujet ;
- les pages sans image pertinente n'en ont pas : cartes de prestations,
  landing pages de zones, articles de blog, pages de ville. Elles portent du
  texte, ce qui vaut mieux que la quatrième apparition de la même serrure ;
- **la galerie « Nos interventions » a quitté l'accueil.** Elle réunissait sur
  un écran les photographies déjà présentes sur les pages de service : c'était
  la répétition à supprimer. Son mécanisme est intact (`src/galerie.conf`, les
  filtres, la visionneuse, la CSS marquée « en sommeil ») ; il suffit de
  remettre la section dans `src/pages/index.html` pour la rallumer, le jour où
  des photographies existeront qui n'ont pas déjà leur place ailleurs.

Pour voir la répartition réelle après un build :

```bash
grep -ro 'src="/assets/images/[^"]*"' public --include='*.html' \
  | cut -d/ -f5- | sort | uniq -c | sort -rn | head
```

Aucun fichier ne doit dominer la liste. `docs/photos.md` détaille les rapports
d'affichage imposés par chaque conteneur et la façon dont le build calcule
`sizes` et `fetchpriority`.

### Régénérer les visuels

```bash
python3 scripts/generer-illustrations.py   # les 16 illustrations
node    scripts/generer-og.mjs             # les vignettes de partage
python3 scripts/generer-polices.py         # les polices, en WOFF2
python3 scripts/generer-images.py          # favicons et icônes
```

Tous ces scripts sont **facultatifs** : leurs résultats sont versionnés. À
relancer seulement après un changement de charte.

### Modifier la charte graphique

Tout est en jetons CSS, en tête de `static/assets/css/style.css`. Modifier une
valeur y repeint le site entier.

| Jeton | Rôle | Valeur |
|---|---|---|
| `--color-primary` | ardoise, texte secondaire et icônes (7,07:1) | `#475569` |
| `--color-primary-light` | traits marqués (4,76:1) | `#64748B` |
| `--color-primary-lighter` | traits fins — **jamais du texte** | `#94A3B8` |
| `--color-primary-dark` | titres et contours de composant (10,41:1) | `#334155` |
| `--color-primary-deep` | **texte, liens, fonds de bouton** (14,6:1) | `#1E293B` |
| `--color-primary-soft` / `-tint` | aplats de section, pastilles | `#E9EDF2` / `#F5F7F9` |
| `--color-secondary` | orange, **appeler uniquement** | `#F97316` |
| `--color-dark` | encre des titres et de la barre de service | `#0F172A` |
| `--color-text` | texte courant (10,41:1) | `#334155` |
| `--color-background` / `-2` | blanc cassé, surfaces alternées | `#FAFAF9` / `#F4F4F2` |
| `--color-muted` | texte discret — **valable sur blanc pur seulement** (4,76:1) | `#64748B` |
| `--font-title` / `--font-body` | Inter, pour tout le site | — |
| `--radius-*` | **tous à zéro** : le site n'a aucun coin arrondi | `0` |

**Le site est ardoise sur blanc cassé.** Pas de bleu, pas de dégradé coloré :
la couleur ne sert plus à décorer, seulement à hiérarchiser. La seule surface
sombre est la barre de service en haut de page ; la classe `section.sombre` a
gardé son nom — elle est employée dans les pages — mais désigne un aplat
ardoise très clair entre deux sections blanches.

**L'orange ne veut dire qu'une chose : appeler.** Bouton d'appel de l'en-tête,
du héros, du bandeau d'urgence, et barre fixe du mobile. Partout ailleurs il
est interdit : le badge du héros est neutre, et le bouton d'appel des cartes
de service est en contour, parce que six aplats orange dans un même écran ne
se lisent plus comme un signal mais comme un motif.

> **Quatre règles de contraste à ne pas enfreindre.** Elles sont vérifiées
> nœud par nœud sur les 41 pages du sitemap par `tests/visuels.mjs` ; tout
> écart fait échouer les tests.
> - L'ardoise a **cinq niveaux** et le contraste décide de l'usage de chacun.
>   `--color-primary-lighter` ne doit jamais porter de texte : 2,6:1 sur blanc.
> - `--color-muted` n'est valable que sur **blanc pur**. Sur un aplat il tombe
>   sous le seuil : employez `--color-dark-3`.
> - Sur la barre de service, fond `--color-dark`, le texte doit être clair —
>   `#CBD5E1` ou `#94A3B8` pour les filets. `--color-dark-3` y donne 1,7:1,
>   c'est-à-dire rien du tout.
> - Le texte du bouton d'appel est **brun très sombre**, pas blanc : blanc sur
>   `#F97316` ne donne que 2,80:1. Même raison pour l'astérisque de champ
>   obligatoire, qui utilise `--color-secondary-dark`.

### La police

**Inter, et elle seule.** Un seul fichier variable de 34 Ko couvre les
graisses 100 à 900 — les quatre fichiers précédents (Outfit 400/700, Work
Sans 400/700) en pesaient 55 à eux quatre, pour deux graisses chacun.

Inter est dessinée pour les écrans, et c'est ce qui la rend lisible ici :
hauteur d'x généreuse, formes ouvertes, et des lettres qu'on ne confond pas —
le `I` majuscule, le `l` minuscule et le chiffre `1` sont trois dessins
distincts, ce qui n'est pas le cas de toutes les grotesques. Sur un site où
l'on lit un numéro de téléphone et des prix, cela compte davantage que le
caractère.

La distinction titre/texte se fait par la **graisse et l'interlettrage**, pas
par un changement de dessin : 700 et `-0.03em` pour un H1, 400 pour le texte.
Deux polices mal accordées se remarquent ; une seule bien réglée ne se
remarque pas. Les deux jetons `--font-title` et `--font-body` sont conservés —
une centaine de règles s'y réfèrent — mais pointent vers la même famille.

Deux réglages qui se voient à l'usage :

- **`strong` en 600, pas 700.** Dans une phrase, le 700 d'Inter fait une tache
  noire qui attire l'œil hors de la ligne. Les titres, eux, restent en 700.
- **Chiffres tabulaires** sur les prix, le numéro de téléphone et la barre
  d'appel. Toutes les figures ont alors la même largeur : les prix s'alignent
  verticalement dans la colonne, et un « 1 » étroit ne décale plus la ligne.

La police est auto-hébergée (aucune requête vers un domaine tiers, CSP stricte
conservée), préchargée depuis l'en-tête, et sous licence OFL — le fichier de
licence est publié à côté, comme l'exige cette licence. Les sources sont
versionnées dans `src/polices/`, hors production : `scripts/generer-polices.py`
tourne donc sans réseau, sur n'importe quelle machine.

**Angles vifs, partout.** Les cinq jetons `--radius-*` valent zéro : boutons,
cartes, champs, pastilles, images, panneau de menu. Les jetons gardent leur
nom parce qu'une centaine de règles s'y réfèrent — pour revenir à des angles
adoucis, il suffit de leur redonner une valeur. Les ombres portées des boutons
sont franches et neutres (`0 3px 0`) : un halo de couleur flou ramollirait
l'arête qu'on vient de créer. `tests/visuels.mjs` refuse qu'un seul élément
des 41 pages retrouve un rayon supérieur à 0,5 px.

Deux exceptions qui n'en sont pas : les **boutons radio** sont dessinés ronds
par le système, et un radio qui ne ressemble pas à un radio cesse d'être
compris ; et les **illustrations vectorielles** contiennent des formes
arrondies parce qu'elles dessinent des objets — une porte, un coffre, une clé.
Leur cadre, lui, est carré.

> **Une accolade orpheline dans la CSS n'est pas une erreur bruyante.** Le
> navigateur abandonne silencieusement toutes les règles qui suivent : la
> moitié du site perd sa mise en forme sans qu'aucun outil ne proteste. Le
> build compte donc les accolades hors commentaires et refuse de publier une
> feuille déséquilibrée.

Après un changement de charte, régénérez les visuels qui la reprennent :

```bash
python3 scripts/generer-illustrations.py   # les 16 illustrations de repli
node scripts/generer-og.mjs                # les vignettes de partage social
bash scripts/build.sh
```

### L'en-tête

`src/partials/header.html` décrit **une seule ligne** : un rail à trois
colonnes — nom, navigation, actions — dont la colonne centrale est réellement
centrée (`1fr auto 1fr`). Il reste collé en haut et se resserre au défilement.

La barre de service sombre qui coiffait la page a été supprimée : elle
répétait le téléphone et le devis déjà présents dans le rail, elle poussait le
contenu vers le bas, et c'était le premier bloc que voyait le visiteur. Ce
qu'elle portait d'utile est remonté — le téléphone et le devis à droite du
rail, les trois métiers en baseline sous le nom, où ils ne coûtent aucune
hauteur.

Dans la colonne d'actions, **le devis est un lien, pas un bouton** : deux
boutons côte à côte se concurrencent, et c'est l'appel qui doit gagner. Sous
1 080 px la ligne se réduit à *logo · appeler · menu*.

### Le logo

Le fichier livré est un « lockup » complet : la marque (cadenas, bouclier,
hermines), le mot-symbole sur trois lignes, et une bande de services en bas.
Tel quel il est inutilisable dans un en-tête — la bande serait illisible, et
le fond blanc opaque interdirait tout autre fond derrière.

`scripts/preparer-logo.py` en tire deux fichiers, en trois définitions :

| Fichier | Affiché |
|---|---|
| `logo-serrurier-richard.webp` | au-dessus de 560 px — 56 px de haut, 44 px une fois la page défilée |
| `logo-marque.webp` | en dessous de 560 px — le mot-symbole y descendrait sous 9 px de haut |

La bascule est faite par `<picture>` et non par la CSS : **le navigateur ne
télécharge que le fichier qui correspond**, et il n'y a qu'une balise `<img>`,
donc un seul texte alternatif, toujours juste. Deux images masquées l'une
après l'autre auraient fait télécharger les deux partout, et posé la question
insoluble de savoir laquelle porte l'`alt`.

Le détourage se fait **par propagation depuis les bords** : seuls les pixels
blancs atteignables depuis l'extérieur deviennent transparents. Un simple
« tout le blanc devient transparent » aurait percé le trou de serrure au
centre du bouclier, qui est du blanc enfermé.

Le fichier d'origine est conservé dans `src/marque/`, hors production. Pour
remplacer le logo : déposez la nouvelle version sous le même nom et relancez
le script. Un logo **vectoriel** serait préférable — net à toutes les tailles,
quelques kilo-octets, aucun détourage à deviner.

La **page courante est marquée** : le build pose `aria-current="page"` sur
l'entrée de menu dont l'adresse correspond à celle de la page, et la CSS la
souligne en orange. Aucune page n'a donc à connaître sa propre entrée. C'est
la fonction `marquer_page_courante()` de `scripts/build.sh`.

Le fond du rail est **blanc plein, pas translucide** : un en-tête collant qui
laisse transparaître la page qui défile dessous est joli une seconde et
illisible ensuite.

### Les adresses de la CSS et du JS portent une empreinte

Le `.htaccess` sert la feuille de style et le script avec
`Cache-Control: public, max-age=31536000, immutable` — un an, sans
revalidation. C'est le bon réglage, à une condition qui n'était pas remplie :
**que l'adresse change quand le fichier change.**

Sans cela, un visiteur déjà venu gardait l'ancienne feuille pendant un an. Le
site lui apparaissait avec le HTML du jour et la charte de l'an dernier, et ni
un rechargement ni une republication n'y changeaient rien — `immutable`
interdit au navigateur de redemander le fichier. C'est exactement ce qui s'est
produit après le passage à la charte ardoise.

Le build calcule donc une empreinte du contenu et la place dans le nom :

```
/assets/css/style.6726b49fb1.css
/assets/js/site.7ef1ebde59.js
```

Les pages y renvoient par les jetons `CSS_URL` et `JS_URL`. Une couleur
modifiée produit une nouvelle adresse, que le cache n'a jamais vue : la mise
à jour est immédiate pour tout le monde, et le cache d'un an reste acquis
pour les visiteurs qui n'ont rien à retélécharger. Rien à purger, jamais.

Toute l'animation est en CSS. Le JavaScript ne fait qu'une chose : poser la
classe `defile` sur `<body>` au-delà de 60 px de défilement, dans un
`requestAnimationFrame`. Sans JavaScript, l'en-tête reste simplement à sa
taille pleine — rien n'est cassé.

Sur mobile (≤ 760 px) l'en-tête se réduit à **nom · appeler · menu** : le
bouton d'appel reste visible en permanence, ce qui est le geste attendu sur un
site de dépannage. Les séparateurs de la barre supérieure sont en `#94A3B8` :
sur fond sombre, `--color-dark-3` tombait à 1,7:1, c'est-à-dire invisible.

### Clés de métadonnées disponibles

| Clé | Rôle |
|---|---|
| `title` | Balise `<title>` — viser moins de 60 caractères |
| `description` | Meta description — viser 120 à 158 caractères |
| `schema` | `home`, `service`, `zone` ou `article` — injecte le JSON-LD |
| `breadcrumb` | Nom court utilisé dans le fil d'Ariane balisé |
| `parent_nom` / `parent_url` | Niveau intermédiaire du fil d'Ariane |
| `image` | Image Open Graph propre à la page |
| `date` | Date de publication (articles) |
| `priority` | Priorité dans le sitemap (0.1 à 1.0) |
| `robots` | Surcharge locale, ex. `noindex` |
| `sitemap` | `non` pour exclure la page du sitemap |
| `conversion` | Nom de l'événement mesuré à l'affichage (page de remerciement) |
| `faq` | `non` pour ne pas générer de balisage `FAQPage` |

---

## Le formulaire de devis

`/devis-serrurerie` envoie vers `static/envoi-devis.php`, seul élément
dynamique du site. Il fonctionne sur un mutualisé Hostinger standard : PHP 7.4
ou supérieur, fonction `mail()` activée par défaut, aucune extension
particulière, aucune base de données.

**Une seule chose à faire avant la mise en ligne :** créer la boîte
`EMAIL_EXPEDITEUR` dans *hPanel > Emails*. Sur un mutualisé, un message expédié
depuis une adresse extérieure au domaine est rejeté ou classé en indésirable
(SPF/DKIM). Par défaut :

```
EMAIL_DEVIS="contact@serrurier-richard.fr"       # reçoit les demandes
EMAIL_EXPEDITEUR="site@serrurier-richard.fr"     # expédie — à créer
```

Ce que fait le script, dans l'ordre :

1. refuse tout ce qui n'est pas une requête POST ;
2. limite à cinq **envois réussis** par heure et par adresse IP — une saisie
   erronée ne consomme pas ce quota, pour ne pas bloquer un visiteur maladroit ;
3. piège à robots invisible et délai minimal de trois secondes ;
4. valide chaque champ : téléphone français, e-mail, code postal, listes
   fermées pour le type d'intervention et l'urgence ;
5. contrôle la photo jointe par son **type MIME réel**, jamais par son
   extension, et vérifie qu'elle est décodable comme image ;
6. neutralise l'injection d'en-têtes en supprimant les retours à la ligne de
   toutes les valeurs reprises dans le courriel ;
7. redirige en 303 vers `/merci`, ce qui empêche un double envoi si le
   visiteur actualise la page.

En cas d'erreur, une page autonome liste ce qui doit être corrigé et propose
de revenir en arrière : le navigateur restaure alors les valeurs saisies. Le
numéro de téléphone y est toujours rappelé — une demande qui échoue ne doit
jamais être une impasse.

Le formulaire vit dans `src/partials/formulaire-devis.html`, en un seul
exemplaire. Les pages qui l'affichent écrivent `{{FORMULAIRE_DEVIS}}`.

**Pour tester après déploiement :** envoyez une demande depuis le site en
ligne et vérifiez la réception. Si rien n'arrive, la cause est presque toujours
la boîte d'expédition non créée.

---

## Google Analytics, Tag Manager, Search Console

Tout se règle dans `src/config.sh`. **Laissées vides, ces variables
désactivent proprement la fonctionnalité** : aucun script tiers n'est chargé,
aucune balise vide n'est écrite, aucun bandeau de consentement n'apparaît.

| Variable | Valeur attendue |
|---|---|
| `GA4_ID` | `G-XXXXXXXXXX` |
| `GTM_ID` | `GTM-XXXXXXX` — laisser vide si GA4 est utilisé seul |
| `GSC_CODE` | Le contenu de l'attribut `content` de la balise fournie par Search Console |

Puis `bash scripts/build.sh`.

**Mesure active : `G-4MD9C1NX66`.**

**Le tag n'est pas collé en dur dans les pages, et c'est volontaire.** Le bloc
fourni par Google (`<script async src="…/gtag/js?id=…">`) dépose ses cookies
dès l'ouverture de la page, donc avant tout consentement — ce que la CNIL
interdit. Ici l'identifiant est posé sur la balise `<html>`
(`data-ga="G-…"`), et `assets/js/site.js` charge le tag uniquement après un
clic sur « Accepter ». Le résultat mesuré est identique ; le risque juridique,
non. Pour changer d'identifiant, modifiez `GA4_ID` et reconstruisez : il n'y a
rien à toucher dans les pages.

**Vérifier que ça remonte vraiment.** Les tests prouvent le comportement du
site, pas la réception chez Google, qui ne se voit que depuis GA4 :

1. ouvrez le site, **acceptez** le bandeau ;
2. dans Google Analytics : *Rapports → Temps réel* ;
3. vous devez apparaître en utilisateur actif dans la minute ;
4. cliquez sur le numéro de téléphone : l'événement `appel` apparaît dans la
   liste des événements, avec son paramètre `zone`.

Rien ne remonte ? Dans l'ordre : le bandeau a-t-il été accepté (le refus est
mémorisé — videz les données du site pour le revoir) ; un bloqueur de
publicité est-il actif ; la console du navigateur signale-t-elle un blocage
`Content-Security-Policy` (voir la section CSP du `.htaccess`).

**Search Console.** La vérification par fichier HTML ou par enregistrement DNS
est préférable : elle ne pèse rien sur les pages. Si vous choisissez la méthode
« balise HTML », copiez uniquement la valeur de `content=` dans `GSC_CODE`.
Depuis que GA4 est en place, une troisième méthode est disponible et ne coûte
rien non plus : *Google Analytics*, qui s'appuie sur le tag déjà présent —
à condition d'utiliser le même compte Google que la propriété GA4.

**Consentement.** Aucun script de mesure n'est chargé avant acceptation
explicite du bandeau, conformément aux exigences de la CNIL. Un refus est
mémorisé et respecté : les événements survenus avant la réponse sont mis en
attente, puis transmis en cas d'acceptation, ou effacés en cas de refus.

**Conversions suivies.** Elles remontent automatiquement, sans code par page :

| Événement | Déclenchement |
|---|---|
| `appel` | Clic sur un numéro de téléphone, avec la zone d'origine (`hero`, `barre-mobile`, `entete`…) |
| `clic_devis` | Clic vers le formulaire de devis |
| `clic_urgence` | Clic vers la page urgence depuis le bandeau rouge |
| `clic_email` | Clic sur une adresse e-mail |
| `devis_envoye` | Affichage de `/merci`, donc uniquement après un envoi réellement accepté par le serveur |

Le paramètre `zone` indique **quel** appel à l'action a converti : c'est
l'information qui permet d'arbitrer la mise en page.

Pour suivre un nouvel élément, ajoutez-lui simplement
`data-track="nom_evenement" data-track-zone="emplacement"`.

**Google Business Profile.** Renseignez `URL_GOOGLE_BUSINESS` une fois la
fiche créée : elle alimente le champ `sameAs` des données structurées, que
Google recoupe. Ne renseignez que des profils réellement existants.

---

## Contrôles avant mise en ligne

Une seule commande enchaîne tous les contrôles disponibles et affiche une
synthèse :

```bash
bash scripts/audit.sh
```

```
  BUILD                     OK
  SEO / LIENS               OK
  HTML                      OK
  JSON-LD                   OK
  TESTS NAVIGATEUR          OK
  DÉPLOIEMENT HOSTINGER     PRÊT
```

Les étapes qui demandent un outil absent (Python, Playwright) sont marquées
« IGNORÉE » et n'empêchent pas l'audit d'aboutir. Chaque contrôle reste
lançable séparément :

```bash
bash scripts/build.sh          # construction
bash scripts/check-seo.sh      # SEO, liens, ressources, redirections
python3 scripts/check-html.py  # structure HTML (facultatif)
bash tests/lancer.sh           # parcours navigateur (facultatif)
```

`check-seo.sh` distingue deux catégories, et c'est important :

- les **défauts techniques** — à corriger dans le code. Le script sort en
  erreur tant qu'il en reste un.
- les **informations à fournir** — assurance, médiateur, adresse. Ce ne sont
  pas des bogues : ce sont des données que seul l'exploitant possède.

Il vérifie notamment : titres et descriptions uniques et de bonne longueur, une
seule `<h1>` par page, `alt` sur toutes les images, aucun lien interne brisé,
canonique partout, aucun token non résolu, toutes les ressources référencées
présentes, les anciennes URL bien redirigées, aucune question de FAQ dupliquée
entre deux pages, et le poids des fichiers.

Les tests de navigateur (`tests/lancer.sh`) exécutent 32 vérifications sur
iPhone, Android et ordinateur : chargement des pages sans erreur, absence de
débordement horizontal, menu, FAQ, barre d'appel fixe, taille des cibles
tactiles, validation du formulaire, absence de cookie sans consentement,
fonctionnement sans JavaScript et navigation au clavier. Ils demandent
Playwright :

```bash
npm install playwright && npx playwright install chromium
```

---

## DEPLOYMENT HOSTINGER

### En une ligne

| | |
|---|---|
| **Dépôt GitHub** | `https://github.com/davidseo1312/serrurier-richard` |
| **Branche à déployer** | **`deploy`** — surtout pas `main` |
| **Commande de build** | aucune côté Hostinger : GitHub construit en amont |
| **Dossier de sortie du build** | `public/` (sur `main`) |
| **Répertoire racine Hostinger** | `public_html` |
| **Document root servi** | `public_html`, qui contient directement `index.html` |

> **Le point décisif : la branche est `deploy`, pas `main`.**
> Pointer Hostinger sur `main` reproduit exactement l'erreur 403 : la racine
> web se retrouve sans `index.html`. La section « Pourquoi une branche
> `deploy` » ci-dessous explique pourquoi.

### Pourquoi une branche `deploy`

Le déploiement Git de Hostinger, sur une offre mutualisée, **clone le dépôt et
s'arrête là**. Il n'exécute aucun build : ni `npm`, ni script shell, ni
`post-receive`. Ce que contient la branche est exactement ce qu'Apache servira.

Or `main` contient les sources *et* le résultat du build, avec la page
d'accueil dans `public/index.html`. Cloner `main` dans `public_html` donne
donc une racine web sans page d'accueil, et Apache répond :

```
AH01276: Cannot serve directory /public_html/: No matching DirectoryIndex
found, and server-generated directory index forbidden by Options directive
```

C'est-à-dire **403 Forbidden**.

Le workflow `.github/workflows/deploy.yml` résout cela en déplaçant le build
en amont : à chaque poussée sur `main`, GitHub construit le site, contrôle le
résultat, et publie le **contenu** de `public/` à la **racine** de la branche
`deploy`.

```
main    →  sources + scripts + public/   (le dépôt de travail)
   │
   │  GitHub Actions : build + vérifications
   ▼
deploy  →  index.html, assets/, blog/…   (uniquement le site)
   │
   │  Hostinger : git clone / git pull
   ▼
public_html/index.html                   →  le site répond
```

La branche `deploy` ne contient ni sources, ni scripts, ni documentation :
rien de ce qui n'a pas à être publié.

### Configuration dans hPanel

*hPanel > Avancé > Git*

| Champ | Valeur |
|---|---|
| Repository | `https://github.com/davidseo1312/serrurier-richard.git` |
| Branch | `deploy` |
| Directory | *laisser vide* (ou `public_html`) |

Puis **Create**. Hostinger clone la branche dans la racine web.

Pour les mises à jour, deux possibilités :

- **Manuelle** : bouton *Deploy* dans hPanel après chaque poussée sur `main`.
- **Automatique** : copiez l'URL du *webhook* affichée par hPanel et
  collez-la dans GitHub, sous *Settings > Webhooks > Add webhook*, en
  déclencheur `push`. Chaque publication sur `deploy` déclenche alors le
  déploiement sans intervention.

> Le dépôt étant public, aucune clé SSH n'est nécessaire. S'il devenait
> privé, hPanel affiche une clé publique à déclarer dans
> *GitHub > Settings > Deploy keys*.

### Première mise en route

1. **La branche `deploy` existe déjà** : elle a été créée et publiée
   manuellement, avec les commandes exactes du workflow. Hostinger peut la
   cloner dès maintenant, sans attendre quoi que ce soit.
2. **Fusionner le travail dans `main` pour armer l'automatisation.** Le
   workflow ne se déclenche que sur `main` : tant que les correctifs vivent
   sur une branche de travail, `deploy` reste figée sur sa dernière
   publication manuelle.
3. **Vérifier que le workflow a réussi** — onglet *Actions* du dépôt. Il doit
   afficher « Build et publication vers Hostinger » au vert. En cas d'échec,
   le journal indique l'étape fautive et **rien n'est publié** : le site en
   ligne conserve sa version précédente.
4. **Activer le SSL** — *hPanel > Sécurité > SSL* — et attendre « Actif ».
   À faire **avant** le premier déploiement : le `.htaccess` force le HTTPS.
5. **Créer la boîte d'expédition** `site@votre-domaine.fr` —
   *hPanel > Emails*. Sans elle, le formulaire de devis n'envoie rien.
6. **Configurer Git dans hPanel** comme indiqué ci-dessus, puis *Deploy*.

### Vérifications après déploiement

| # | URL | Attendu |
|---|---|---|
| 1 | `http://votre-domaine.fr` | redirige vers `https://` |
| 2 | `https://www.votre-domaine.fr` | redirige vers la version sans `www` |
| 3 | `/` | **200** — la page d'accueil |
| 4 | `/tarifs` | **200**, sans `.html` dans l'URL |
| 5 | `/tarifs.html` | **301** vers `/tarifs` |
| 6 | `/blog/` | **200** |
| 7 | `/services/ouverture-de-porte` | **301** vers `/ouverture-porte` |
| 8 | `/une-url-inexistante` | **404**, la page 404 du site |
| 9 | `/robots.txt`, `/sitemap.xml` | **200** |
| 10 | `/.git/config` | **403** — le dépôt ne doit pas être lisible |
| 11 | `/devis-serrurerie` puis envoi | redirection vers `/merci`, message reçu |

Le point 10 n'est pas anecdotique : le déploiement Git dépose un dossier
`.git` dans la racine web. Le `.htaccess` le bloque, mais autant le vérifier.

### Si le site renvoie encore 403

Le diagnostic tient en deux requêtes — comparez `/` et `/tarifs` :

| Ce que vous obtenez | Cause | Correction |
|---|---|---|
| `/` **403** + `/tarifs` **404** | Racine web sans `index.html` | Hostinger pointe sur `main` au lieu de `deploy`, ou sur un sous-dossier |
| `/` **403** + `/tarifs` **200** | `index.html` absent ou illisible | Vérifier sa présence, droits 644 |
| **403 partout** | Droits, ou domaine non rattaché | Fichiers 644, dossiers 755 |
| **500 partout** | Directive refusée dans le `.htaccess` | Commenter `Options -MultiViews -Indexes` |
| `/` **200** + `/tarifs` **404** | `.htaccess` absent ou `mod_rewrite` inactif | Vérifier sa présence (fichier caché) |

Ou laissez le script trancher :

```bash
bash scripts/diag-hostinger.sh
```

### Méthodes de déploiement alternatives

Le déploiement Git est la voie recommandée. Deux replis existent, utiles si
GitHub Actions est indisponible :

**Envoi FTP depuis votre poste**

```bash
cp .env.exemple .env                      # identifiants FTP (hPanel > Comptes FTP)
bash scripts/build.sh
bash scripts/deploy-hostinger.sh --dry    # simulation
bash scripts/deploy-hostinger.sh          # envoi réel
```

**Dépôt manuel**

Le contenu de `public/` se dépose tel quel dans `public_html/`, par le
gestionnaire de fichiers de hPanel.

> **Attention au `.htaccess`** : il commence par un point et reste invisible
> par défaut dans les clients FTP et le gestionnaire de fichiers. Activez
> l'affichage des fichiers cachés avant de copier. Sans lui, toutes les URLs
> sans extension renvoient 404.

### HTTPS et HSTS

Le certificat SSL gratuit s'active dans *hPanel > Sécurité > SSL*. Le
`.htaccess` force ensuite le HTTPS de lui-même.

Le HSTS est présent mais **commenté** dans le `.htaccess` : ne l'activez
qu'une fois le certificat confirmé et stable, car la directive est mémorisée
par les navigateurs pendant deux ans.

## Indexation

`ROBOTS_POLICY` dans `src/config.sh` commande **tout** :

| Valeur | `robots.txt` | Chaque page |
|---|---|---|
| `index` | `Allow: /` + `Sitemap:` déclaré | `<meta name="robots" content="index, follow, max-image-preview:large">` |
| `noindex` | `Disallow: /` | `noindex, follow` |

Deux pages restent en `noindex` quoi qu'il arrive, par leurs propres
métadonnées : `/merci` (page de confirmation — sans intérêt pour un moteur, et
source de doublons) et la 404. Elles sont d'ailleurs absentes du sitemap :
une page en `noindex` listée au sitemap est un signal contradictoire que
Google signale.

```bash
python3 scripts/audit-indexation.py
```

Ce contrôle, intégré à `scripts/audit.sh`, vérifie la mécanique qu'un moteur
regarde — celle qui, mal réglée, fait qu'une page n'apparaît jamais quelle que
soit sa qualité :

- `robots.txt` cohérent avec `ROBOTS_POLICY`, et déclarant le sitemap ;
- une balise `meta robots` sur chaque page, et un `lang` sur chaque `<html>` ;
- une **canonique absolue, en https, sans www, qui pointe sur la page
  elle-même** — une canonique qui pointe ailleurs efface la page du résultat ;
- sitemap et pages indexables qui se correspondent **dans les deux sens** :
  aucune page oubliée, aucune URL fantôme ;
- titres et descriptions présents et **uniques** ;
- aucune valeur d'attente entre crochets publiée.

### Aucune valeur d'attente n'est publiée

`src/config.sh` contient des champs encore vides, écrits entre crochets :
`[ASSUREUR RC PRO]`, `[NOM DU MÉDIATEUR]`… Tant que le site n'était pas
indexé, les publier n'avait guère de conséquence. Ce n'est plus vrai : un
crochet dans une page, c'est un crochet dans le résultat Google — et dans les
données structurées que Google lit.

Le build les traite donc comme **vides** et compose les phrases en
conséquence. Une information absente est passée sous silence, jamais remplacée
par un texte d'attente, et jamais inventée :

| Champ vide | Ce que le site affiche |
|---|---|
| `ADRESSE_RUE` | le JSON-LD omet `streetAddress` — une entreprise qui se déplace chez le client n'a pas à en publier une, mais surtout pas une fausse |
| `ASSUREUR_RCPRO` | « attestation remise sur demande, et jointe au devis avant tout démarrage de travaux » |
| `ASSUREUR_DECENNALE` | la ligne disparaît |
| `MEDIATEUR_NOM` | le droit de recourir à un médiateur est rappelé, et ses coordonnées annoncées sur demande |

Le build liste à chaque construction les champs encore vides. **Remplissez-les
dès que vous les avez** : ce sont des mentions légalement obligatoires, et
leur absence finira par se voir.

### « J'ai publié, mais le site en ligne n'a pas changé »

C'est la question qui bloque tout, et tant qu'elle n'est pas tranchée on
corrige à l'aveugle des fichiers que personne ne lit. **Une commande y
répond :**

```bash
bash scripts/verifier-en-ligne.sh
```

Aucun identifiant, aucune dépendance — curl suffit. À lancer depuis votre
poste. Elle interroge le site en ligne et compare la version servie à celle
du dépôt :

```
2. Version servie
  en ligne : 2026-09-11 06:31:32 UTC
  commit   : c3e8c4792529
  local    : c3e8c4792529
  v le serveur sert exactement la version de ce dépôt.
```

Le fichier `version.txt`, publié à la racine du site et servi **sans cache**,
porte le commit, la date de construction, le nombre de pages et la politique
d'indexation. Vous pouvez aussi l'ouvrir simplement dans un navigateur :
`https://serrurier-richard.fr/version.txt`.

**Si le commit en ligne diffère de celui du dépôt, tout le reste en découle :**
le serveur n'a pas récupéré la nouvelle version. Corriger `robots.txt` dans le
dépôt n'y changera rien tant que ce point n'est pas réglé.

### Deux chaînes de publication, et pourquoi la seconde existe

```
   push sur main
        │
        ├─► GitHub Actions : build, contrôles, puis branche « deploy »   (automatique)
        │
        ├─► l'hébergeur récupère la branche « deploy »        (PAS automatique par défaut)
        │
        └─► publication FTP directe depuis GitHub Actions     (automatique, si activée)
```

Publier sur la branche `deploy` **ne met rien en ligne**. Il faut encore que
l'hébergement récupère cette branche. Sur une offre mutualisée, ce `git pull`
n'est pas automatique : tant que personne ne clique dans le panneau de
l'hébergeur, le site en ligne reste celui du dernier clic.

Deux façons de supprimer cet intermédiaire — **l'une ou l'autre suffit** :

**A. Le webhook de l'hébergeur, sans aucun identifiant.** Dans hPanel >
Avancé > Git, copiez l'URL de déploiement automatique, puis dans GitHub :
Settings > Webhooks > Add webhook, collez-la, content type
`application/json`, événement « Just the push event ». L'hébergeur récupère
alors la branche à chaque publication.

**B. La publication FTP directe depuis GitHub Actions.** Dans GitHub :
Settings > Secrets and variables > Actions > New repository secret, trois
secrets à créer :

| Secret | Valeur |
|---|---|
| `FTP_HOST` | l'hôte FTP donné par l'hébergeur |
| `FTP_USER` | l'identifiant FTP |
| `FTP_PASSWORD` | le mot de passe FTP |
| `FTP_DIR` | facultatif — le dossier servi, `public_html` par défaut |

Tant que ces secrets n'existent pas, l'étape est **sautée** et le workflow se
comporte exactement comme avant ; il écrit seulement un rappel dans son
journal. Dès qu'ils existent, chaque poussée écrit le site directement dans le
dossier servi par Apache, puis relit `version.txt` en ligne pour confirmer.

Le mot de passe reste dans les secrets GitHub : il n'apparaît ni dans le
dépôt, ni dans les journaux. TLS est exigé — sans lui, un mot de passe FTP
circule en clair.

### Search Console : la marche à suivre

**Le sitemap se soumet à son adresse, pas à celle d'une page.**

Dans *Sitemaps*, le champ « Ajouter un sitemap » est déjà préfixé par
`https://serrurier-richard.fr/`. Il ne reste donc qu'à taper :

```
sitemap.xml
```

Soumettre l'adresse d'un article (`blog/securiser-son-logement` par exemple)
produit `Type : Inconnu` et `Impossible de récupérer le sitemap` : Google
reçoit bien une réponse 200, mais du HTML là où il attend du XML. Supprimez
alors l'entrée fautive dans la liste des sitemaps envoyés, et soumettez la
bonne.

Ensuite, dans *Inspection d'URL* : coller l'adresse d'une page, puis
**Demander une indexation**. À faire pour l'accueil et les quelques pages qui
comptent le plus ; le reste suivra par le sitemap.

Pour vérifier depuis votre poste ce que Google va recevoir :

```bash
bash scripts/diag-hostinger.sh
```

Sa section « Ce que Google lit en premier » interroge le site EN LIGNE et dit
si `robots.txt` répond, s'il déclare le sitemap, si `/sitemap.xml` renvoie
bien du XML, et combien d'URLs il contient. Un site parfaitement affiché peut
très bien servir un sitemap introuvable : ces deux fichiers ne passent par
aucune des réécritures d'URL, ils se contrôlent donc à part.

## Cohérence géographique — à trancher avant publication

Le site est actuellement en `noindex` : il ne sera pas référencé tant que ce
point n'est pas résolu.

Données relevées le 08/09/2026 au registre national des entreprises pour le
SIREN 901133041 :

- **Siège social : 1 rue Albert Simonin, 92400 Courbevoie** (Hauts-de-Seine)
- **Code APE : 81.29A** — désinfection, désinsectisation, dératisation
- Aucun numéro de TVA intracommunautaire actif (vérifié auprès de VIES)

Or le site revendique une base à Rennes et une couverture des départements 22,
29, 35, 44, 49 et 56, avec des délais d'intervention chiffrés par secteur et un
balisage `LocalBusiness` géolocalisé en Bretagne.

Deux issues possibles, à choisir avant toute mise en ligne :

1. **Créer un établissement secondaire réel en Bretagne**, déclaré à l'INSEE,
   avec une adresse d'exploitation effective. Renseigner alors `ADRESSE_RUE`,
   `ADRESSE_CP`, `ADRESSE_VILLE`, `LATITUDE` et `LONGITUDE` dans
   `src/config.sh`. C'est la seule voie qui permet de conserver le contenu tel
   qu'il est écrit.

2. **Recentrer le site sur l'Île-de-France**, autour du siège de Courbevoie.
   Les six pages départementales, les trois pages de ville, les tableaux de
   délais, le nom de domaine et une partie du contenu éditorial sont alors à
   réécrire.

Publier en l'état — mentions légales à Courbevoie, contenu revendiquant une
implantation bretonne — cumule trois risques : mentions légales inexactes,
information trompeuse du consommateur dans un secteur étroitement surveillé par
la DGCCRF, et pénalité Google pour fausse implantation locale, le motif de
sanction le plus fréquent dans le référencement des serruriers.

Une fois la question tranchée, passez `ROBOTS_POLICY="index"` dans
`src/config.sh` et relancez le build : `robots.txt` et les balises `robots`
basculent ensemble.

**Point d'assurance :** un code APE en dératisation suggère que la RC Pro
souscrite couvre cette activité. Une intervention sur une serrure ne serait
alors pas garantie. À vérifier auprès de l'assureur avant toute intervention,
indépendamment du site.

---

## Avant la mise en ligne : informations à fournir

`bash scripts/check-seo.sh` doit afficher **0 défaut technique** et
**0 information à fournir**. Ces champs de `src/config.sh` restent à renseigner :

- `ASSUREUR_RCPRO`, `POLICE_RCPRO`, `ASSUREUR_DECENNALE`
- `MEDIATEUR_NOM` et `MEDIATEUR_URL`
- `ADRESSE_RUE` (voir la section précédente)

Ces informations ne sont pas optionnelles : les mentions légales, l'adhésion à
un médiateur de la consommation et l'affichage des prix sont des obligations
légales pour une activité de dépannage à domicile. Elles ne peuvent pas être
inventées, et le site les réclame explicitement plutôt que de les masquer.

Vérifiez aussi que les montants de la section « Tarifs » de `config.sh`
correspondent aux prix réellement pratiqués.

---

## Sécurité

- Aucun identifiant dans le dépôt : `.env` est ignoré par Git, seul
  `.env.exemple` est versionné et ne contient aucune valeur réelle.
- Aucune clé d'API, aucun secret dans le code livré au navigateur.
- Le formulaire valide et nettoie chaque entrée côté serveur, contrôle les
  fichiers joints par leur contenu réel, et neutralise l'injection d'en-têtes.
- Le `.htaccess` interdit l'accès aux fichiers sensibles (`.env`, `.sh`,
  `.log`, `.sql`…) et pose les en-têtes `X-Content-Type-Options`,
  `Referrer-Policy`, `X-Frame-Options`, `Permissions-Policy` et une
  `Content-Security-Policy`.
- Aucun cookie déposé sans consentement explicite.
