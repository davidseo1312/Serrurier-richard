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
  - [Remplacer les illustrations par des photos](#remplacer-les-illustrations-par-des-photos)
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

### Remplacer les illustrations par des photos

Voir `static/assets/img/README.md`, qui donne la correspondance page par page
et les dimensions cibles. Sur ce métier, des photos réelles convertissent
nettement mieux que des illustrations.

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

**Search Console.** La vérification par fichier HTML ou par enregistrement DNS
est préférable : elle ne pèse rien sur les pages. Si vous choisissez la méthode
« balise HTML », copiez uniquement la valeur de `content=` dans `GSC_CODE`.

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
