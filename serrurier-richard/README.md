# Serrurier Richard

Site vitrine et blog SEO — serrurier-richard.fr — pour une entreprise de dépannage en serrurerie
intervenant sur six départements du Grand Ouest : Ille-et-Vilaine (35),
Morbihan (56), Finistère (29), Côtes-d'Armor (22), Loire-Atlantique (44) et
Maine-et-Loire (49).

HTML statique, sans dépendance ni framework. Une feuille de style, un fichier
JavaScript, aucune requête réseau externe au chargement.

---

## Démarrage rapide

```bash
bash scripts/build.sh        # génère public/
bash scripts/check-seo.sh    # contrôle SEO et pré-vol de mise en ligne
```

Pour prévisualiser en local, ouvrez `public/index.html` dans un navigateur.
Les URLs sans extension ne fonctionneront pas en local (elles dépendent du
`.htaccess`), mais la mise en page et le contenu sont fidèles.

---

## Organisation

```
src/
  config.sh              Valeurs globales : nom, téléphone, tarifs, SIRET…
  partials/              En-tête, pied de page, JSON-LD
  pages/                 Contenu des pages (métadonnées + corps)
static/                  Copié tel quel : CSS, JS, images, .htaccess
public/                  Généré par le build — ne pas éditer à la main
scripts/
  build.sh               Assemble les pages
  gen-sitemap.sh         Génère sitemap.xml et robots.txt
  check-seo.sh           Contrôle SEO complet
  deploy-hostinger.sh    Envoi FTP vers Hostinger
```

`public/` n'est pas versionné. Si vous préférez le déploiement automatique par
Git de Hostinger plutôt que le FTP, retirez la ligne `public/` du `.gitignore`
et configurez le dépôt dans hPanel.

### Modifier une valeur partout à la fois

Tout ce qui apparaît sur plusieurs pages — numéro de téléphone, tarifs, nom
commercial, SIRET — vit dans `src/config.sh`. Les pages y font référence par
des tokens `{{NOM_DE_LA_VARIABLE}}`, remplacés au build.

### Ajouter un article de blog

1. Créer `src/pages/blog/mon-article.html`
2. Commencer par un bloc de métadonnées :

```html
<!--meta
title: Titre de moins de 60 caractères
description: Description de 120 à 158 caractères.
schema: article
breadcrumb: Titre affiché dans les données structurées
date: 2026-09-15
priority: 0.7
-->
```

3. Ajouter la carte correspondante dans `src/pages/blog/index.html`
4. `bash scripts/build.sh && bash scripts/check-seo.sh`

Le sitemap est régénéré automatiquement.

### Clés de métadonnées disponibles

| Clé           | Rôle                                                        |
|---------------|-------------------------------------------------------------|
| `title`       | Balise `<title>` — viser moins de 60 caractères              |
| `description` | Meta description — viser 120 à 158 caractères                |
| `schema`      | `home`, `service`, `zone` ou `article` — injecte le JSON-LD  |
| `breadcrumb`  | Nom court utilisé dans les données structurées               |
| `image`       | Image Open Graph de la page                                  |
| `date`        | Date de publication (articles)                               |
| `priority`    | Priorité dans le sitemap (0.1 à 1.0)                         |
| `robots`      | Surcharge locale, ex. `noindex`                              |
| `sitemap`     | `non` pour exclure la page du sitemap                        |

---

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
   Les six pages départementales, les tableaux de délais, le nom de domaine et
   une partie du contenu éditorial sont alors à réécrire.

Publier en l'état — mentions légales à Courbevoie, contenu revendiquant une
implantation bretonne — cumule trois risques : mentions légales inexactes,
information trompeuse du consommateur dans un secteur étroitement surveillé par
la DGCCRF, et pénalité Google pour fausse implantation locale, le motif de
sanction le plus fréquent dans le référencement des serruriers.

**Point d'assurance :** un code APE en dératisation suggère que la RC Pro
souscrite couvre cette activité. Une intervention sur une serrure ne serait
alors pas garantie. À vérifier auprès de l'assureur avant toute intervention,
indépendamment du site.

---

## Avant la mise en ligne

`bash scripts/check-seo.sh` doit afficher **0 erreur bloquante**. Il vérifie
notamment que ces champs de `src/config.sh` ont été renseignés :

- `TELEPHONE` et `TELEPHONE_E164` — le numéro réel
- `RAISON_SOCIALE`, `FORME_JURIDIQUE`, `CAPITAL`, `SIRET`, `RCS`, `TVA`
- `ADRESSE_RUE`, `ADRESSE_CP`, `ADRESSE_VILLE`
- `ASSUREUR_RCPRO`, `POLICE_RCPRO`, `ASSUREUR_DECENNALE`
- `MEDIATEUR_NOM` et `MEDIATEUR_URL`

Ces informations ne sont pas optionnelles : les mentions légales, l'adhésion à
un médiateur de la consommation et l'affichage des prix sont des obligations
légales pour une activité de dépannage à domicile.

Vérifiez aussi que les montants de la section « Tarifs » de `config.sh`
correspondent bien aux prix réellement pratiqués. L'arrêté du 24 janvier 2017
impose que les prix affichés soient ceux appliqués.

---

## Mise sur GitHub

Le dépôt est déjà initialisé, sur la branche `main`, avec l'historique complet.
Aucun identifiant n'y figure : `.env` est ignoré et seul `.env.exemple`, qui ne
contient aucune valeur secrète, est versionné.

Créez un dépôt **privé** sur github.com sans l'initialiser (ni README, ni
`.gitignore`, ni licence — ils existent déjà ici), puis :

```bash
git remote add origin https://github.com/VOTRE-COMPTE/serrurier-richard.git
git push -u origin main
```

Le dossier `public/` n'est pas versionné : c'est un résultat de build,
régénérable par `bash scripts/build.sh`. Si vous préférez le déploiement
automatique par Git de Hostinger plutôt que le FTP, retirez la ligne `public/`
du `.gitignore` avant de pousser.

---

## Déploiement

```bash
cp .env.exemple .env     # puis renseigner les identifiants FTP Hostinger
bash scripts/build.sh
bash scripts/deploy-hostinger.sh --dry   # simulation
bash scripts/deploy-hostinger.sh         # envoi réel
```

`.env` est ignoré par Git et ne doit jamais être versionné.

---

## Mesure d'audience

`GA4_ID` dans `src/config.sh` est vide par défaut : aucun script tiers n'est
chargé. Une fois la propriété Google Analytics créée, renseignez l'identifiant
`G-XXXXXXXXXX` et relancez le build.

Le script n'est chargé qu'après acceptation explicite du bandeau de
consentement, conformément aux exigences de la CNIL sur les cookies de mesure
d'audience.
