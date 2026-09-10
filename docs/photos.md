# Ajouter une photographie au site

Le site est prévu pour fonctionner **sans aucune photographie**, et pour les
adopter **une par une**, sans qu'aucune page ait à être modifiée. Ce document
décrit la marche à suivre complète.

---

## 1. En une phrase

Déposez le fichier au bon nom dans `static/assets/images/`, relancez
`bash scripts/build.sh` : la photo remplace l'illustration partout où
l'emplacement est utilisé — accueil, pages services, galerie, aperçu social,
sitemap images.

---

## 2. Où en est-on ?

```bash
bash scripts/verifier-photos.sh
```

Le script liste les emplacements qui attendent une photographie, le nom de
fichier exact à utiliser, et le format attendu. Il signale aussi les fichiers
trop lourds. Il ne modifie rien.

---

## 3. Le principe : deux candidats par emplacement

`src/images.conf` décrit chaque emplacement visuel du site et lui donne
**deux** candidats :

| Colonne | Rôle |
|---|---|
| `photo` | la photographie réelle de Serrurier Richard, si elle existe |
| `repli` | l'illustration vectorielle, toujours présente |

À chaque construction, le build regarde le disque :

- le fichier `photo` existe → il est utilisé, avec le texte alternatif « photo » ;
- sinon → l'illustration est utilisée, avec le texte alternatif « illustration ».

C'est le seul endroit du site où cet arbitrage est fait. Aucune page HTML ne
connaît le nom d'un fichier image.

### Le site dit lui-même ce qu'il affiche

Deux mécanismes, tous les deux automatiques :

- chaque vignette de la galerie porte la mention **« Illustration »** tant
  qu'elle en est une (elle disparaît dès qu'une photo la remplace) ;
- la phrase d'introduction de la section « Nos interventions » change selon ce
  que le build a réellement trouvé (`{{MENTION_VISUELS}}`).

Le site ne peut donc pas présenter une illustration comme un chantier réel,
ni continuer à s'excuser de n'avoir que des illustrations une fois les photos
livrées.

---

## 4. La marche à suivre

### Étape 1 — Choisir l'emplacement

Lancez `bash scripts/verifier-photos.sh` et repérez la ligne correspondante.
Exemple :

```
· HERO   attendue : static/assets/images/interventions/serrurier-richard-ouverture-serrure-porte-blindee.webp
```

### Étape 2 — Préparer le fichier

- **Format** : WebP de préférence (`.avif`, `.jpg` et `.png` fonctionnent
  aussi ; le build prend le meilleur disponible dans l'ordre
  `avif > webp > jpg > jpeg > png > svg`).
- **Définition** : au moins celle indiquée dans `src/images.conf`
  (1600 × 900 en 16/9 pour le héros, 1500 × 1000 en 3/2 pour les autres). Le
  **rapport** doit être respecté : le conteneur impose le sien, une photo au
  mauvais rapport sera recadrée (jamais déformée, mais recadrée).
- **Poids** : sous les 250 Ko. Qualité 80 en WebP suffit largement.

Avec `cwebp` :

```bash
cwebp -q 80 -resize 1500 0 photo-originale.jpg \
  -o static/assets/images/interventions/serrurier-richard-ouverture-non-destructive-porte.webp
```

### Étape 3 — Nommer le fichier

Le nom est **imposé** par `src/images.conf`, et il est déjà descriptif : c'est
lui que Google Images lit. N'utilisez jamais `IMG_2043.jpg`, `photo1.webp` ou
`capture.png` — le script d'audit les refuse.

### Étape 4 — Déposer et construire

```bash
bash scripts/build.sh
bash scripts/verifier-photos.sh   # la ligne passe de « · » à « ✓ »
```

### Étape 5 — Relire le texte alternatif

Le texte alternatif de la photo est **déjà écrit** dans `src/images.conf`,
sixième colonne. Il a été rédigé à partir de la photo attendue : relisez-le et
corrigez-le s'il ne décrit pas exactement le cliché déposé. C'est ce que lisent
les lecteurs d'écran et Google Images.

### Étape 6 — Vérifier

```bash
python3 scripts/audit-images.py
```

---

## 5. Variantes responsives (facultatif)

`scripts/preparer-photos.py` produit trois réductions : `-600`, `-1000` et
`-1200`. Le fichier maître reste à sa taille d'origine (1500 px de large pour
les photos, 1600 pour le héros).

```
serrurier-richard-ouverture-non-destructive-porte.webp        (maître, 1500 px)
serrurier-richard-ouverture-non-destructive-porte-600.webp
serrurier-richard-ouverture-non-destructive-porte-1000.webp
serrurier-richard-ouverture-non-destructive-porte-1200.webp
```

Le build construit tout seul l'attribut `srcset` correspondant, en y ajoutant
le fichier maître avec sa vraie largeur. Aucun code à modifier.

**L'attribut `sizes` n'est pas écrit à la main.** Il ne décrit pas le fichier,
il décrit la largeur à laquelle la page va l'afficher — c'est elle qui décide
quel fichier du `srcset` sera téléchargé. Comme un même identifiant d'image
sert dans plusieurs emplacements (héros, carte, vignette), une valeur unique
serait forcément fausse quelque part. La fonction `ajuster_visuels()` de
`scripts/build.sh` la réécrit page par page, d'après la classe du conteneur :

| Conteneur | Largeur affichée mesurée | `sizes` posé |
|---|---|---|
| `.hero-media` | 358 → 1118 px puis 598 px | `(max-width: 1150px) 96vw, 600px` |
| `.media-large` | 356 → 1198 px | `(max-width: 1240px) 96vw, 1200px` |
| `.hero-local-media` | 358 → 736 px | `… 96vw, 560px` |
| `.intervention-media` | 356 → 734 px | `… 96vw, 680px` |
| `.carte-media` | 313 → 400 px | `(max-width: 560px) 92vw, 400px` |
| `.apparait` (galerie) | 286 → 358 px | `(max-width: 560px) 92vw, 360px` |

La même passe retire le chargement différé de la première image d'un grand
conteneur et lui pose `fetchpriority="high"` : c'est presque toujours l'image
la plus grande au premier écran, donc celle que le navigateur doit demander en
premier. Elle est aussi préchargée depuis l'en-tête, avec exactement les mêmes
`srcset` et `sizes` — sinon le navigateur téléchargerait deux fichiers.

---

## 6. Ouvrir un nouvel emplacement

Pour accueillir une photo à un endroit qui n'en attend pas encore, remplissez
la deuxième colonne de la ligne concernée dans `src/images.conf`, et la sixième
(le texte alternatif de la photo) :

```
EFFRACTION|interventions/serrurier-richard-securisation-apres-effraction|effraction/securisation-porte-apres-effraction|1200|750|Serrurier posant une serrure neuve sur une porte forcée lors d'une mise en sécurité|Porte forcée après effraction et remise en sécurité du logement
```

---

## 7. Ajouter une vignette à la galerie

La galerie est pilotée par `src/galerie.conf`. Une ligne = une vignette :

```
ID D'IMAGE | FAMILLE | TITRE | LÉGENDE
```

La `FAMILLE` alimente le filtre affiché au-dessus de la galerie ; les boutons
sont déduits du fichier, dans l'ordre de première apparition. Ajouter une
famille ne demande donc ni CSS ni JavaScript.

---

## 8. Ce qu'il ne faut jamais faire

- **Ne prenez jamais une image au hasard dans Google Images.** Les photos y
  sont protégées par le droit d'auteur, et les recherches inversées rendent la
  reprise triviale à détecter.
- **Ne reprenez jamais les photos d'un concurrent**, même retouchées.
- **Ne faites jamais de lien direct (hotlink)** vers une image hébergée
  ailleurs : la CSP du site le bloque, et cela dépend d'un serveur tiers.
- **Ne présentez jamais une photo de banque d'images comme une intervention
  réelle.** C'est une pratique commerciale trompeuse (art. L121-2 du code de la
  consommation), et cela se repère.
- **Ne publiez pas la porte, la serrure ou l'adresse d'un client sans son
  accord.** Une porte d'entrée reconnaissable est une information sur la
  sécurité d'un logement occupé. Cadrez serré, et demandez l'accord.
- **Ne laissez pas les données GPS** dans les fichiers. Pour les retirer :

  ```bash
  exiftool -all= photo.jpg
  ```

---

## 9. Préparer une photo automatiquement

Un script fait le recadrage, la conversion et les variantes responsives :

```bash
python3 scripts/preparer-photos.py ~/photos/IMG_2043.jpg HERO
```

Il lit `src/images.conf`, y trouve le chemin, le nom et les dimensions attendus
pour cet identifiant, écrit le fichier WebP au bon endroit, produit les
variantes `-800` et `-1200`, et rappelle le texte alternatif enregistré pour
que vous le relisiez. Le recadrage est fait **au centre** : si un cadrage
particulier est nécessaire, recadrez la source avant.

Les métadonnées EXIF, position GPS comprise, ne sont pas recopiées.

---

## 10. Schémas explicatifs

Une planche pédagogique — texte, repères, vue éclatée — n'est pas une
photographie d'intervention. La recadrer au format d'une carte couperait ses
légendes. Elle passe donc par `src/schemas.conf`, pas par `src/images.conf` :

```
ID | chemin sans extension | largeur | hauteur | alt | légende
```

Le jeton `{{SCHEMA_ID}}` pose la figure complète, à ses proportions natives,
légende comprise. Un schéma ne rejoint ni les cartes ni la galerie.

**Le texte alternatif d'un schéma est long, et c'est voulu.** Le contenu de la
planche *est* du texte : un lecteur d'écran n'y a accès que par l'`alt`. Le
raccourcir supprimerait l'information au lieu de la clarifier —
`scripts/audit-images.py` accepte donc jusqu'à 400 caractères pour ces
fichiers, contre 160 ailleurs.

> **Une planche « avant / après » ne documente pas un chantier.** Elle illustre
> en quoi consiste une prestation. La légende affichée doit le dire, et elle le
> dit. Ne présentez jamais un schéma comme l'intervention réelle d'un client :
> ce serait exactement la fausse preuve que le reste du site s'interdit.

---

## 11. Aucun pictogramme inventé

Le site n'embarque **aucune icône vectorielle décorative** : ni logo de marque,
ni combiné téléphonique sur les boutons d'appel, ni bouclier, ni horloge, ni
maison. Ils ont été remplacés par ce qu'ils prétendaient représenter :

| Ancien pictogramme | Ce qui l'a remplacé |
|---|---|
| Clé stylisée de l'en-tête | Le nom composé, sans dessin |
| Combiné sur les boutons d'appel | Le numéro en toutes lettres |
| Icônes de la réassurance | Quatre photographies d'intervention |
| Icônes de la grille des problèmes | Typographie et barre d'accent |
| Coche et « + » en SVG embarqué | Des caractères (`✓`, `+`) |
| Clé de l'icône d'onglet | Les initiales composées |

Le seul SVG restant est `src/partials/carte-zones.svg` : le tracé réel des six
départements, produit à partir de données IGN. C'est une donnée, pas une
décoration.

**Si vous ajoutez un composant, n'y remettez pas d'icône de banque.** Une
photographie de l'acte, un chiffre réel ou un mot suffisent — et disent
quelque chose de vrai.

---

## 11 bis. Une photo, un emplacement principal

Le défaut le plus visible d'un site de dépannage est la même photographie
répétée de page en page. Trois règles l'évitent, et deux d'entre elles sont
vérifiées automatiquement.

1. **Aucune page n'affiche deux fois le même fichier.**
   `scripts/audit-images.py` échoue si elle le fait — c'est une erreur
   bloquante, pas un avertissement. L'audit compte les `src` réellement
   présents dans le HTML produit, pas les intentions du code source.

2. **Chaque photo a un emplacement principal.** Une page de service montre la
   photo de son service ; une landing page de zone reçoit une photo qui lui est
   propre, jamais les trois mêmes que l'accueil. Les six pages de zone ont donc
   six photos d'ouverture différentes, et les pages de ville n'ont pas la même
   que la page de département correspondante.

3. **Quand il n'y a pas assez de photos, on écrit du texte.** Les cartes de
   prestations des landing pages locales sont volontairement sans image
   (`.carte-locale`) : mieux vaut un bloc de texte utile que la quatrième
   apparition de la même serrure. Ajouter une photo vraiment nouvelle est
   toujours préférable à en recycler une.

Pour voir la répartition réelle :

```bash
bash scripts/build.sh
grep -ro 'src="/assets/images/[^"]*"' public --include='*.html' \
  | cut -d/ -f5- | sort | uniq -c | sort -rn | head -20
```

Aucun fichier ne devrait dominer la liste. Si l'un d'eux apparaît deux fois
plus que les suivants, c'est qu'il a été utilisé par défaut faute de mieux :
c'est le signal qu'il faut une photo de plus, pas une répétition de plus.

---

## 11 ter. Formats d'affichage

Les rapports d'image sont imposés par le conteneur, jamais laissés au fichier :
un remplacement au mauvais format ne peut donc pas déformer la mise en page.
Aucune image n'est étirée — `object-fit: cover` recadre, il ne déforme pas.

| Emplacement | Rapport affiché | Remarque |
|---|---|---|
| Héros, une colonne (≤ 1150 px) | 16/9 | le fichier maître est déjà en 16/9 : aucun recadrage |
| Héros, deux colonnes (≥ 1151 px) | 3/2 | environ 16 % de largeur retirés sur les bords |
| `.media-large` | 3/2 | pleine largeur du conteneur de texte |
| Cartes de service | 3/2 | hauteur identique sur toute une grille |
| Vignettes de galerie | 3/2 | |
| Interventions locales | 4/3 | |
| Planches explicatives (`.schema`) | rapport natif | jamais recadrées : les annotations doivent rester lisibles |

Le cadrage horizontal (`object-position`) est réglé à 42 % sur le héros : le
technicien est à gauche du cadre et la serrure au centre, ce réglage garde les
deux. Une nouvelle photo dont le sujet est ailleurs demande un réglage
différent — `scripts/preparer-photos.py` accepte un troisième argument de
cadrage vertical (0 = haut, 0.5 = centre, 1 = bas).

---

## 12. Les visuels actuels

Huit emplacements affichent aujourd'hui de **vraies photographies
d'intervention** (`bash scripts/verifier-photos.sh` en donne la liste à jour),
et trois planches explicatives sont déclarées dans `src/schemas.conf`. Les
autres emplacements sont encore illustrés.

Les illustrations sont produites par `scripts/generer-illustrations.py` : ce
sont des dessins vectoriels créés pour ce projet, sans photographie source. Elles expliquent un geste technique ;
elles ne représentent aucun chantier. Elles pèsent 3 à 4 Ko chacune et se
remplacent une par une, dans n'importe quel ordre.

Les aperçus sociaux (`static/assets/images/og/`) sont produits à partir de ces
mêmes illustrations par `scripts/generer-og.mjs`, au format JPEG 1200 × 630 —
les réseaux sociaux ignorent le SVG.
