# Déploiement sur Hostinger — marche à suivre complète

Ce document déroule une mise en ligne de bout en bout, en supposant que rien
n'est encore configuré. Comptez une heure la première fois, cinq minutes les
suivantes.

Le README donne la version courte. Celui-ci détaille chaque écran de hPanel et
les erreurs qu'on rencontre réellement.

---

## Avant de commencer

Trois choses doivent être vraies :

1. Le domaine est enregistré et pointe vers l'hébergement Hostinger.
2. Un plan mutualisé est actif (Premium, Business ou Cloud — tous conviennent).
3. `bash scripts/check-seo.sh` affiche **0 défaut technique**.

Ce site n'a besoin ni de Node.js, ni de base de données, ni de composer, ni
d'accès SSH. PHP 7.4 ou supérieur suffit, et c'est le réglage par défaut.

---

## Étape 1 — Certificat SSL

*hPanel > Sécurité > SSL*

Activez le certificat gratuit sur le domaine. Attendez qu'il passe en
« Actif » — de quelques minutes à une heure.

Ne passez pas à la suite avant : le `.htaccess` force HTTPS, et forcer HTTPS
sans certificat rend le site inaccessible.

---

## Étape 2 — Boîte e-mail d'expédition

*hPanel > Emails > Comptes e-mail > Créer*

Créez l'adresse déclarée dans `EMAIL_EXPEDITEUR` (`src/config.sh`), par défaut
`site@votre-domaine.fr`.

**Cette étape n'est pas facultative.** Le formulaire de devis expédie depuis
cette adresse. Sur un hébergement mutualisé, un message envoyé depuis une
adresse extérieure au domaine échoue aux contrôles SPF et DKIM : il est rejeté
par le serveur destinataire, ou classé en indésirable sans avertissement. C'est
de très loin la première cause de « le formulaire ne marche pas ».

Créez également, ou vérifiez l'existence de, l'adresse `EMAIL_DEVIS` qui
recevra les demandes. Les deux peuvent être identiques, mais les séparer permet
de filtrer.

---

## Étape 3 — Compte FTP

*hPanel > Fichiers > Comptes FTP*

Relevez :

- l'**hôte** (`ftp.votre-domaine.fr` ou une adresse en `.hostinger.com`) ;
- le **nom d'utilisateur** (de la forme `u123456789`) ;
- le **mot de passe** — celui du compte FTP, pas celui de votre compte
  Hostinger. Si vous ne l'avez pas, changez-le depuis cet écran.

Notez aussi le **répertoire racine**, presque toujours `/public_html`.

---

## Étape 4 — Configuration locale

```bash
cp .env.exemple .env
```

Renseignez `.env` :

```
FTP_HOST=ftp.votre-domaine.fr
FTP_USER=u123456789
FTP_PASS=le-mot-de-passe-du-compte-ftp
FTP_DIR=/public_html
FTP_PARALLELE=4
```

`.env` est ignoré par Git. Il ne doit jamais être versionné, ni transmis par
message.

---

## Étape 5 — Construction et contrôle

```bash
bash scripts/build.sh
bash scripts/check-seo.sh
```

Le second doit afficher **0 défaut technique**. Les « informations à fournir »
(assureur, médiateur) n'empêchent pas le déploiement technique, mais elles sont
juridiquement obligatoires avant l'ouverture au public.

---

## Étape 6 — Simulation puis envoi

```bash
bash scripts/deploy-hostinger.sh --dry
```

La simulation liste les fichiers sans rien envoyer. Vérifiez que `.htaccess`
figure en tête de liste — c'est lui qui produit les URLs sans extension.

```bash
bash scripts/deploy-hostinger.sh
```

Les fichiers en échec sont récapitulés à la fin. Relancez simplement la
commande : seuls les fichiers manquants sont réécrits.

---

## Étape 7 — Vérifications sur le site en ligne

Dans cet ordre, depuis un navigateur :

| # | À tester | Résultat attendu |
|---|---|---|
| 1 | `http://votre-domaine.fr` | redirige vers `https://` |
| 2 | `https://www.votre-domaine.fr` | redirige vers la version sans `www` |
| 3 | `https://votre-domaine.fr/` | la page d'accueil s'affiche |
| 4 | `/tarifs` | la page s'affiche, sans `.html` dans l'URL |
| 5 | `/tarifs.html` | redirige en 301 vers `/tarifs` |
| 6 | `/blog/` | la liste des articles s'affiche |
| 7 | `/services/ouverture-de-porte` | redirige en 301 vers `/ouverture-porte` |
| 8 | `/une-url-qui-nexiste-pas` | la page 404 du site, pas celle d'Apache |
| 9 | `/sitemap.xml` | le sitemap s'affiche |
| 10 | `/robots.txt` | le fichier s'affiche |
| 11 | `/manifest.webmanifest` | le manifeste s'affiche |
| 12 | `/devis-serrurerie` | le formulaire s'affiche |
| 13 | Envoyer une demande de test | redirection vers `/merci`, message reçu |
| 14 | Le site sur un vrai téléphone | barre d'appel en bas, bouton d'appel fonctionnel |

Le point 13 est le seul qui ne puisse pas être testé avant la mise en ligne :
aucun serveur de messagerie n'est disponible en local.

---

## Dépannage

### Toutes les URLs sans extension renvoient 404

Le `.htaccess` n'est pas en place, ou n'est pas lu.

1. Dans *hPanel > Fichiers > Gestionnaire de fichiers*, activez l'affichage
   des fichiers cachés et vérifiez que `.htaccess` est bien à la racine de
   `public_html/`. C'est la cause dans la grande majorité des cas : les
   clients FTP masquent par défaut les fichiers commençant par un point.
2. Vérifiez que `mod_rewrite` est actif — *hPanel > Avancé > Configuration
   PHP*. Il l'est par défaut chez Hostinger.

### Le site répond 403, ou affiche l'index d'un dossier

Les fichiers sont probablement dans un sous-dossier
(`public_html/public/index.html` au lieu de `public_html/index.html`).

```bash
bash scripts/diag-hostinger.sh
```

Ce script se connecte en FTP, cherche où se trouve réellement `index.html` et
indique la valeur de `FTP_DIR` à corriger.

### Le formulaire affiche « le serveur de messagerie n'a pas pu transmettre »

Dans l'ordre de probabilité :

1. La boîte `EMAIL_EXPEDITEUR` n'existe pas (étape 2).
2. `EMAIL_EXPEDITEUR` n'appartient pas au domaine du site.
3. La fonction `mail()` est désactivée sur le plan d'hébergement — rare, à
   vérifier auprès du support Hostinger.

### Le message part mais arrive en indésirable

Vérifiez dans *hPanel > Emails > Enregistrements DNS* que les entrées SPF et
DKIM du domaine sont bien celles proposées par Hostinger. Une entrée SPF
héritée d'un ancien hébergeur suffit à faire classer tous les messages.

### Une modification n'apparaît pas en ligne

Le `.htaccess` demande aux navigateurs de conserver les fichiers CSS, JS et
images pendant un an. Après une modification de la feuille de style, forcez le
rechargement (`Ctrl+F5`, ou `Cmd+Maj+R`), ou renommez le fichier et mettez à
jour `src/partials/head.html`.

Le HTML, lui, n'est jamais mis en cache longuement : une correction de contenu
est visible immédiatement.

---

## Après la première mise en ligne

1. **Passer le site en index.** Une fois la question géographique tranchée
   (voir le README), mettez `ROBOTS_POLICY="index"` dans `src/config.sh`,
   relancez le build et redéployez.
2. **Google Search Console.** Ajoutez la propriété, vérifiez-la, puis soumettez
   `https://votre-domaine.fr/sitemap.xml`.
3. **Google Business Profile.** C'est le premier levier de visibilité locale
   pour un serrurier, avant le site lui-même. Renseignez ensuite
   `URL_GOOGLE_BUSINESS` dans `src/config.sh`.
4. **Google Analytics**, si vous le souhaitez : renseignez `GA4_ID` et
   redéployez. Le bandeau de consentement apparaît alors automatiquement.

---

## Mises à jour ultérieures

```bash
# modifier src/config.sh ou src/pages/…
bash scripts/build.sh
bash scripts/check-seo.sh
bash scripts/deploy-hostinger.sh
```

Il n'y a jamais rien à reconfigurer côté serveur : le `.htaccess` est renvoyé
à chaque déploiement, et aucun état n'est stocké en ligne.
