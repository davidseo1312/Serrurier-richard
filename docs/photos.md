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
  (1100 × 850 pour le héros, 1200 × 750 pour les autres). Le **rapport**
  doit être respecté, sinon la photo sera recadrée par le navigateur.
- **Poids** : sous les 250 Ko. Qualité 80 en WebP suffit largement.

Avec `cwebp` :

```bash
cwebp -q 80 -resize 1200 0 photo-originale.jpg \
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

Déposez en plus des fichiers suffixés `-800`, `-1200` ou `-1600` :

```
serrurier-richard-ouverture-non-destructive-porte.webp
serrurier-richard-ouverture-non-destructive-porte-800.webp
serrurier-richard-ouverture-non-destructive-porte-1200.webp
```

Le build construit tout seul l'attribut `srcset` correspondant. Aucun code à
modifier.

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

## 9. Les visuels actuels

Les illustrations livrées avec le site sont produites par
`scripts/generer-illustrations.py` : ce sont des dessins vectoriels créés pour
ce projet, sans photographie source. Elles expliquent un geste technique ;
elles ne représentent aucun chantier. Elles pèsent 3 à 4 Ko chacune et se
remplacent une par une, dans n'importe quel ordre.

Les aperçus sociaux (`static/assets/images/og/`) sont produits à partir de ces
mêmes illustrations par `scripts/generer-og.mjs`, au format JPEG 1200 × 630 —
les réseaux sociaux ignorent le SVG.
