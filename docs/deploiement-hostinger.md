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
3. `bash scripts/audit.sh` affiche **403 CHECK : OK**.

Ce site n'a besoin ni de Node.js, ni de base de données, ni de composer, ni
d'accès SSH. PHP 7.4 ou supérieur suffit, et c'est le réglage par défaut.

---

## Ce qu'il faut comprendre en premier

**Le déploiement Git de Hostinger n'exécute aucun build.** Sur une offre
mutualisée, il clone le dépôt dans le dossier choisi, et s'arrête là. Ce que
contient la branche est exactement ce qu'Apache servira.

C'est la source de l'erreur 403 rencontrée initialement : la branche `main`
place la page d'accueil dans `public/index.html`, donc la racine web se
retrouvait sans `index.html`, et Apache refusait de servir un dossier sans
page d'index.

D'où l'architecture retenue :

```
main    →  sources + scripts + public/
   │
   │  GitHub Actions : build, contrôles, publication
   ▼
deploy  →  index.html, assets/, blog/…   ← rien d'autre que le site
   │
   │  Hostinger : git clone / git pull
   ▼
public_html/index.html
```

**Hostinger doit donc pointer sur la branche `deploy`, jamais sur `main`.**

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

## Étape 3 — Vérifier que la branche `deploy` existe

Sur GitHub, ouvrez le sélecteur de branches du dépôt. `deploy` doit y figurer,
et son contenu doit commencer directement par `index.html`, `assets/`,
`blog/`… — sans dossier intermédiaire.

Si elle n'existe pas :

1. Les correctifs ne sont pas encore fusionnés dans `main`. Le workflow ne se
   déclenche que sur `main`.
2. Ou le workflow a échoué. Onglet *Actions* du dépôt : le journal indique
   l'étape fautive. Rien n'est publié tant qu'un contrôle échoue, ce qui est
   voulu — mieux vaut une branche périmée qu'un site cassé en ligne.

Vous pouvez aussi lancer la publication à la main : *Actions > Build et
publication vers Hostinger > Run workflow*.

---

## Étape 4 — Connecter Hostinger au dépôt

*hPanel > Avancé > Git > Créer un nouveau dépôt*

| Champ | Valeur |
|---|---|
| Repository | `https://github.com/davidseo1312/serrurier-richard.git` |
| Branch | `deploy` |
| Directory | *laisser vide* (installe dans `public_html`) |

Validez, puis cliquez sur **Deploy**.

Le dépôt étant public, aucune clé SSH n'est nécessaire. S'il devenait privé,
hPanel affiche une clé publique à déclarer dans *GitHub > Settings > Deploy
keys*, en lecture seule.

### Déploiement automatique

hPanel affiche une **URL de webhook** à côté du dépôt. Copiez-la, puis dans
GitHub : *Settings > Webhooks > Add webhook*, collez l'URL, laissez le type de
contenu par défaut, déclencheur « Just the push event ».

Chaque publication sur `deploy` déclenche alors le déploiement sans
intervention. Sans webhook, il faut cliquer sur *Deploy* dans hPanel après
chaque modification.

---

## Étape 5 — Vérifications sur le site en ligne

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
| 12 | `/.git/config` | **403** — le code source ne doit pas être lisible |
| 13 | `/devis-serrurerie` | le formulaire s'affiche |
| 14 | Envoyer une demande de test | redirection vers `/merci`, message reçu |
| 15 | Le site sur un vrai téléphone | barre d'appel en bas, bouton d'appel fonctionnel |

Le point 14 est le seul qui ne puisse pas être testé avant la mise en ligne :
aucun serveur de messagerie n'est disponible en local.

Le point 12 mérite une attention particulière : le déploiement Git dépose un
dossier `.git` dans la racine web. Le `.htaccess` le bloque, mais une
vérification coûte dix secondes et évite d'exposer tout l'historique du projet.

---

## Étape 6 — Repli : compte FTP

Le déploiement Git est la voie recommandée. Si vous préférez l'envoi FTP, ou
si GitHub Actions est indisponible, relevez dans *hPanel > Fichiers > Comptes
FTP* :

- l'**hôte** (`ftp.votre-domaine.fr` ou une adresse en `.hostinger.com`) ;
- le **nom d'utilisateur** (de la forme `u123456789`) ;
- le **mot de passe** — celui du compte FTP, pas celui de votre compte
  Hostinger. Si vous ne l'avez pas, changez-le depuis cet écran.

Notez aussi le **répertoire racine**, presque toujours `/public_html`.

## Étape 7 — Repli : envoi FTP

```bash
cp .env.exemple .env     # renseignez FTP_HOST, FTP_USER, FTP_PASS, FTP_DIR
bash scripts/build.sh
bash scripts/deploy-hostinger.sh --dry    # simulation, aucun envoi
bash scripts/deploy-hostinger.sh          # envoi réel
```

`.env` est ignoré par Git : vos identifiants ne partiront jamais sur GitHub.

La simulation liste les fichiers sans rien envoyer. Vérifiez que `.htaccess`
y figure — c'est lui qui produit les URLs sans extension.

Les fichiers en échec sont récapitulés à la fin. Relancez simplement la
commande : seuls les fichiers manquants sont réécrits.

Ce chemin ne passe pas par la branche `deploy` : il envoie directement le
contenu de `public/` construit sur votre poste. Les deux méthodes peuvent
coexister, mais évitez de les mélanger sur un même déploiement — Hostinger
tiendrait un dépôt Git dont les fichiers auraient été modifiés en dehors de
lui, et le `git pull` suivant échouerait.

---

## Repli : dépôt manuel

Le contenu de `public/` se dépose tel quel dans `public_html/`, par le
gestionnaire de fichiers de hPanel.

**Attention au fichier `.htaccess`** : il commence par un point et reste
invisible par défaut dans beaucoup de clients FTP et dans le gestionnaire de
fichiers. Activez l'affichage des fichiers cachés avant de copier. Sans lui,
toutes les URLs sans extension renvoient une erreur 404.

---

## Dépannage

### Le site renvoie 403 Forbidden

Comparez deux URLs, la réponse est dans la combinaison :

| `/` | `/tarifs` | Cause | Correction |
|---|---|---|---|
| 403 | 404 | Racine web sans `index.html` | Hostinger pointe sur `main` au lieu de `deploy`, ou sur un sous-dossier |
| 403 | 200 | `index.html` absent ou illisible | Vérifier sa présence et ses droits (644) |
| 403 | 403 | Droits, ou domaine non rattaché | Fichiers 644, dossiers 755 |
| 500 | 500 | Directive refusée dans le `.htaccess` | Commenter `Options -MultiViews -Indexes` |
| 200 | 404 | `.htaccess` absent ou `mod_rewrite` inactif | Voir ci-dessous |

`bash scripts/diag-hostinger.sh` fait ce diagnostic automatiquement et nomme
la correction.

### Toutes les URLs sans extension renvoient 404

Le `.htaccess` n'est pas en place, ou n'est pas lu.

1. Dans *hPanel > Fichiers > Gestionnaire de fichiers*, activez l'affichage
   des fichiers cachés et vérifiez que `.htaccess` est bien à la racine de
   `public_html/`. C'est la cause dans la grande majorité des cas : les
   clients FTP masquent par défaut les fichiers commençant par un point.
2. Vérifiez que `mod_rewrite` est actif — *hPanel > Avancé > Configuration
   PHP*. Il l'est par défaut chez Hostinger.

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
bash scripts/audit.sh          # facultatif mais recommandé
git add -A && git commit -m "…" && git push
```

La poussée sur `main` déclenche le workflow, qui reconstruit, contrôle et
republie la branche `deploy`. Si le webhook est en place, Hostinger récupère
la nouvelle version dans la foulée ; sinon, cliquez sur *Deploy* dans hPanel.

Il n'y a jamais rien à reconfigurer côté serveur : le `.htaccess` fait partie
de la branche publiée, et aucun état n'est stocké en ligne.

Si un contrôle échoue, le workflow s'arrête et **`deploy` reste inchangée** :
le site en ligne conserve sa dernière version fonctionnelle.
