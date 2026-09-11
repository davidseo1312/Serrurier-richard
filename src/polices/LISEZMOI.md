# Police du site

`inter-latin-wght-normal.woff2` est le fichier **variable** d'Inter, tel que
distribué par le paquet npm `@fontsource-variable/inter` (version 5.3.0), sous
licence SIL Open Font License 1.1 — voir `Inter-OFL.txt`.

Un seul fichier, un seul axe (`wght`, 100 → 900), 230 caractères : le
sous-ensemble « latin » de Fontsource couvre **tout le français**, `œ` et `Œ`
compris. Le fichier « latin-ext » est donc inutile ici, et n'est pas embarqué.

Ce dossier n'est **pas publié** : le build ne copie que `static/`.

## Regénérer la police du site

```bash
python3 scripts/generer-polices.py
```

Le script réduit le fichier au répertoire réellement employé — latin de base,
accents français, guillemets typographiques, tirets cadratins, symbole euro,
flèches de l'interface — puis l'écrit en WOFF2 dans `static/assets/fonts/`.
47 Ko à l'entrée, 34 Ko à la sortie, pour les neuf graisses.

Il supprime au passage les fichiers des polices précédentes, s'ils traînent
encore : les laisser dans `static/` les ferait publier à chaque déploiement.

## Si vous changez de police

Déposez le `.woff2` (ou le `.ttf`) ici, ajustez `POLICES` en tête du script,
et relancez-le. Puis changez `--font-title` et `--font-body` en tête de
`static/assets/css/style.css`. Vérifiez ensuite les onze largeurs avec
`bash tests/lancer.sh` : une police plus large peut faire déborder un titre
sur les petits écrans.

**La licence doit être publiée avec la police.** La OFL l'exige, et le script
s'en charge en recopiant `Inter-OFL.txt` à côté du fichier.
