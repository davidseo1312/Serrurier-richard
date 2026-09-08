# Photos du site — où déposer quoi

Les pages référencent désormais des fichiers `.jpg` qui **ne sont pas encore
présents**. Le contrôle SEO les signale comme manquants tant qu'ils n'ont pas
été déposés dans ce dossier (`static/assets/img/`).

Les photos transmises dans la conversation ne peuvent pas être écrites
automatiquement sur le disque : il faut les enregistrer ici à la main, en
respectant exactement les noms ci-dessous.

## Correspondance à respecter

Les photos sont numérotées dans l'ordre où elles ont été transmises.

| Fichier à créer          | Photo à utiliser | Description de la photo                                          | Dimensions cibles |
|--------------------------|------------------|------------------------------------------------------------------|-------------------|
| `hero-serrurier.jpg`     | photo 1          | Veste bleu marine, crochetage d'un cylindre sur porte blindée     | 1440 × 1080       |
| `ouverture-porte.jpg`    | photo 6          | Gros plan, lampe torche, inspection du cylindre                   | 1120 × 620        |
| `changement-serrure.jpg` | photo 2          | Tournevis sur la crémone en tranche de porte                      | 1120 × 620        |
| `porte-blindee.jpg`      | photo 3          | Porte alu grise, crochetage, caisse à outils ouverte              | 1120 × 620        |
| `apres-effraction.jpg`   | photo 4          | Lampe torche, ceinture porte-outils, ambiance de soirée           | 1120 × 620        |
| `rideau-metallique.jpg`  | photo 8          | Intervention en bas d'une porte sectionnelle grise                | 1120 × 620        |
| `og-default.jpg`         | photo 5          | Recadrer en **1200 × 630** — image de partage sur les réseaux     | 1200 × 630        |

`og-default.jpg` est obligatoire : c'est la vignette affichée quand un lien du
site est partagé. Un format vectoriel n'y est pas accepté.

## Photos non utilisées pour l'instant

- **Photo 7** — portail métallique
- **Photo 9** — seconde photo de porte de garage

Elles ne correspondent à aucune page existante. Le site couvre l'ouverture de
porte, le changement de serrure, la porte blindée, l'après-effraction, le
rideau métallique et le coffre-fort. Si le portail et la porte de garage font
partie des prestations réellement proposées, il faut créer les pages
correspondantes — sinon ces photos induiraient en erreur.

## Préparation des fichiers

Aucun outil de traitement d'image n'est installé sur ce poste. Utilisez
<https://squoosh.app> (dans le navigateur, rien à installer) pour recadrer,
redimensionner et compresser :

1. Ouvrir la photo dans Squoosh
2. Redimensionner aux dimensions du tableau ci-dessus
3. Exporter en **MozJPEG qualité 78**
4. Viser **moins de 200 Ko** par fichier
5. Enregistrer dans ce dossier sous le nom exact indiqué

Puis relancer :

```bash
bash scripts/build.sh && bash scripts/check-seo.sh
```

## Droits d'utilisation

Les mentions légales déclarent que ces photographies sont la propriété de
l'éditeur ou utilisées avec l'autorisation de leurs auteurs. Assurez-vous que
c'est exact avant publication : si les images proviennent d'une banque
d'images, la licence doit autoriser l'usage commercial, et la formulation des
mentions légales doit être adaptée en conséquence.

Si ces photos ne représentent pas l'entreprise elle-même, sachez que des
clichés réels — véhicule floqué, technicien identifiable, chantier terminé —
convertissent nettement mieux sur ce métier et alimentent la fiche Google
Business Profile, que des visuels génériques ne peuvent pas nourrir.
