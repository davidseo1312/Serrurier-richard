# Fichiers de marque

`logo-fourni.webp` est le logo **tel qu'il a été livré** : 1774 × 887, fond
blanc opaque, avec la bande de services en bas (« Dépannage | Installation |
Sécurisation | Ouverture »).

Ce dossier n'est **pas publié** : le build ne copie que `static/`.

## Regénérer les fichiers du site

```bash
python3 scripts/preparer-logo.py src/marque/logo-fourni.webp
```

Le script produit six fichiers dans `static/assets/img/` :

| Fichier | Rôle |
|---|---|
| `logo-serrurier-richard.webp` (+ `@2x`, `@3x`) | l'en-tête, au-dessus de 560 px |
| `logo-marque.webp` (+ `@2x`, `@3x`) | l'en-tête en dessous de 560 px |

Il retire la bande de services — elle serait illisible à la taille d'un
en-tête, et elle répète ce que dit déjà la navigation — puis détoure le fond
blanc **par propagation depuis les bords**. C'est ce point qui compte : un
« tout le blanc devient transparent » aurait percé le trou de serrure au
centre du bouclier, qui est du blanc enfermé.

## Si vous livrez une nouvelle version du logo

Déposez-la ici sous le même nom et relancez la commande ci-dessus. Rien
d'autre à modifier : `src/partials/header.html` pointe vers des noms de
fichiers fixes.

Un logo **vectoriel** (SVG, AI, EPS) serait préférable au fichier matriciel
actuel : net à toutes les tailles, quelques kilo-octets, et sans détourage à
deviner. Si votre graphiste en a un, il remplacera avantageusement celui-ci.
