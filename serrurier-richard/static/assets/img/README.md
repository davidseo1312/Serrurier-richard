# Images du site

Ce fichier n'est pas publié : `scripts/build.sh` retire les `.md` de `public/`.

## Ce qui est en place

| Fichier | Rôle | Type |
|---|---|---|
| `hero-serrurier.svg` | Illustration du héros de l'accueil | vectoriel |
| `ouverture-porte.svg` | Illustration de la page ouverture de porte | vectoriel |
| `changement-serrure.svg` | Illustration de la page changement de serrure | vectoriel |
| `porte-blindee.svg` | Illustration de la page porte blindée | vectoriel |
| `apres-effraction.svg` | Illustration de la page après effraction | vectoriel |
| `rideau-metallique.svg` | Illustration de la page rideau métallique | vectoriel |
| `coffre-fort.svg` | Illustration disponible, non encore posée dans une page | vectoriel |
| `favicon.svg` | Icône d'onglet | vectoriel |
| `favicon.ico` | Repli pour les navigateurs qui ignorent le SVG | 16/32/48 px |
| `apple-touch-icon.png` | Icône d'écran d'accueil iOS | 180 × 180 |
| `icone-192.png`, `icone-512.png` | Icônes du manifeste | PNG |
| `icone-512-maskable.png` | Icône Android « maskable », 20 % de marge | PNG |
| `og-default.jpg` | Vignette de partage sur les réseaux sociaux | 1200 × 630 |

Les illustrations sont **vectorielles** : elles pèsent 2 à 3 Ko chacune,
s'affichent parfaitement sur tous les écrans, ne demandent aucune version
« retina » et se chargent instantanément. Le site est complet et déployable
tel quel.

Les fichiers matriciels (vignette sociale et icônes) sont régénérables :

```bash
python3 scripts/generer-images.py     # nécessite Pillow
```

À relancer après un changement de nom commercial, de baseline ou de couleurs.
Le numéro de téléphone n'y est volontairement pas incrusté : les réseaux
sociaux mettent ces images en cache des mois, et un numéro périmé y ferait plus
de dégâts que son absence.

---

## Passer à de vraies photos

Sur ce métier, **des photos réelles convertissent nettement mieux** que
n'importe quelle illustration : véhicule floqué, technicien identifiable,
chantier terminé. Elles alimentent aussi la fiche Google Business Profile, ce
qu'un visuel vectoriel ne peut pas faire.

### Remplacer une illustration

1. Préparer le fichier aux dimensions ci-dessous.
2. Le déposer dans ce dossier.
3. Dans la page concernée (`src/pages/…`), remplacer l'extension `.svg` par
   celle de la photo — il y a **une seule occurrence par page**.
4. `bash scripts/build.sh && bash scripts/check-seo.sh`

| Page | Fichier à remplacer | Dimensions cibles |
|---|---|---|
| Accueil (`index.html`) | `hero-serrurier` | 1440 × 1080 |
| `ouverture-porte.html` | `ouverture-porte` | 1120 × 620 |
| `changement-serrure.html` | `changement-serrure` | 1120 × 620 |
| `porte-blindee.html` | `porte-blindee` | 1120 × 620 |
| `effraction.html` | `apres-effraction` | 1120 × 620 |
| `rideau-metallique.html` | `rideau-metallique` | 1120 × 620 |

Pensez à mettre à jour l'attribut `alt` : il doit décrire ce que montre
réellement la nouvelle photo, pas l'ancienne illustration.

### Préparer les fichiers

<https://squoosh.app> fonctionne dans le navigateur, sans rien installer :

1. Ouvrir la photo, la recadrer aux dimensions du tableau.
2. Exporter en **MozJPEG qualité 78**, ou en **WebP qualité 80** — plus léger,
   accepté par tous les navigateurs actuels.
3. Viser **moins de 200 Ko** par fichier. `scripts/check-seo.sh` signale tout
   fichier au-delà de 250 Ko.

Le `.htaccess` sert déjà le WebP et l'AVIF avec le bon type MIME : vous pouvez
utiliser ces formats directement.

### Vignette sociale

Si vous remplacez `og-default.jpg` par une photo, gardez impérativement le
format **1200 × 630** et le format JPEG ou PNG : les réseaux sociaux
n'acceptent pas le SVG. Le nom de fichier doit rester identique, sans quoi il
faut modifier `src/partials/head.html`.

---

## Droits d'utilisation

Les mentions légales déclarent que les photographies sont la propriété de
l'éditeur ou utilisées avec l'autorisation de leurs auteurs. Vérifiez que c'est
exact avant publication : si les images viennent d'une banque d'images, la
licence doit autoriser l'usage commercial, et la formulation des mentions
légales doit être adaptée en conséquence.

Une photo de personne identifiable exige son accord écrit pour une utilisation
commerciale, y compris s'il s'agit d'un salarié de l'entreprise.
