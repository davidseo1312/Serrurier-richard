# Référence de configuration

Toutes les valeurs partagées du site vivent dans **`src/config.sh`**. Aucune
n'est écrite en dur dans une page : les pages écrivent `{{NOM_DE_LA_VARIABLE}}`,
et le build substitue.

Après toute modification :

```bash
bash scripts/build.sh && bash scripts/check-seo.sh
```

`check-seo.sh` signale tout token resté non résolu — c'est le filet qui rattrape
une faute de frappe dans un nom de variable.

---

## Identité

| Variable | Rôle | Répercussions |
|---|---|---|
| `NOM_COMMERCIAL` | Nom affiché partout | En-tête, pied de page, `<title>`, JSON-LD, vignette sociale |
| `BASELINE` | Phrase d'accroche courte | Sous le logo, Open Graph, manifeste |
| `DOMAINE` | Domaine sans protocole | `robots.txt`, messages du script de déploiement |
| `BASE_URL` | URL complète, sans barre finale | URLs canoniques, sitemap, JSON-LD, Open Graph |

`BASE_URL` doit être **exactement** la forme servie en production, `https://`
compris et sans `www` si le `.htaccess` redirige vers la version sans `www`.
Une incohérence ici produit des URLs canoniques qui pointent ailleurs que la
page elle-même — l'une des erreurs de référencement les plus coûteuses.

Après un changement de `NOM_COMMERCIAL` ou de `BASELINE` :

```bash
python3 scripts/generer-images.py     # régénère la vignette de partage
```

---

## Contact

| Variable | Format | Exemple |
|---|---|---|
| `TELEPHONE` | Format d'affichage, avec espaces | `02 20 06 00 75` |
| `TELEPHONE_E164` | Format international, sans espaces | `+33220060075` |
| `EMAIL` | Adresse de contact générale | `contact@…` |

**Les deux variables de téléphone doivent être modifiées ensemble.** La
première s'affiche, la seconde fait fonctionner les liens `tel:` sur mobile.
Un numéro affiché correct avec un `tel:` périmé passe totalement inaperçu à la
relecture et fait perdre tous les appels mobiles.

Conversion : on retire le `0` initial et on préfixe par `+33`.
`06 12 34 56 78` devient `+33612345678`.

---

## Identité légale

| Variable | Rôle |
|---|---|
| `RAISON_SOCIALE` | Dénomination officielle |
| `FORME_JURIDIQUE` | SARL, SAS, entrepreneur individuel… |
| `CAPITAL` | Capital social — vide si sans objet |
| `SIRET`, `SIREN` | Numéros d'immatriculation |
| `RCS` | Mention d'immatriculation |
| `DATE_CREATION` | Date de création de l'entreprise |
| `TVA_NUMERO` | Numéro de TVA intracommunautaire, si assujetti |
| `MENTION_TVA` | Mention affichée sur les prix |
| `UNITE_PRIX` | `€` ou `€ TTC` selon l'assujettissement |
| `CODE_APE` | Code d'activité principale |

Ces valeurs alimentent les mentions légales, les conditions générales et le
pied de page. **Elles ne s'inventent pas** : elles se relèvent sur l'extrait
d'immatriculation ou sur `annuaire-entreprises.data.gouv.fr`.

Si l'entreprise devient assujettie à la TVA : renseignez `TVA_NUMERO`, passez
`MENTION_TVA` à une mention appropriée et `UNITE_PRIX` à `€ TTC`.

---

## Adresses

Deux adresses distinctes, à ne pas confondre.

| Groupe | Variables | Usage |
|---|---|---|
| **Siège** | `SIEGE_RUE`, `SIEGE_CP`, `SIEGE_VILLE` | Mentions légales — l'adresse déclarée au registre |
| **Exploitation** | `ADRESSE_RUE`, `ADRESSE_CP`, `ADRESSE_VILLE`, `LATITUDE`, `LONGITUDE` | Balisage `LocalBusiness`, délais annoncés |

Le second groupe indique **d'où partent les techniciens**. Il ne doit être
renseigné que si un établissement réel y existe. Une adresse d'exploitation
fictive est le premier motif de suspension d'une fiche Google Business Profile.

Les coordonnées `LATITUDE` et `LONGITUDE` se relèvent sur une carte : clic
droit sur le point exact, les deux nombres apparaissent. Format décimal, point
comme séparateur : `48.117266`, `-1.677793`.

> Voir la section « Cohérence géographique » du README : ce point est
> actuellement non résolu et bloque l'indexation du site.

---

## Assurances et médiation

| Variable | Rôle |
|---|---|
| `ASSUREUR_RCPRO` | Nom de l'assureur en responsabilité civile professionnelle |
| `POLICE_RCPRO` | Numéro de police |
| `ASSUREUR_DECENNALE` | Assureur en garantie décennale |
| `MEDIATEUR_NOM` | Médiateur de la consommation |
| `MEDIATEUR_URL` | Son site, pour la saisine en ligne |

Obligatoires pour une activité de dépannage à domicile. L'adhésion à un
médiateur de la consommation est une obligation légale (art. L612-1 du code de
la consommation), et son absence est sanctionnable indépendamment de toute
réclamation client.

Tant que ces champs contiennent leurs valeurs entre crochets,
`check-seo.sh` les signale comme « informations à fournir ».

---

## Disponibilité et horaires

| Variable | Rôle | Exemple |
|---|---|---|
| `DISPONIBILITE` | Formule courte, très visible | `24h/24 et 7j/7` |
| `HORAIRES_URGENCE` | Formule longue, pour le dépannage | `24 heures sur 24, 7 jours sur 7, jours fériés compris` |
| `HORAIRES_BUREAU` | Traitement des devis et de l'administratif | `du lundi au vendredi, 8h – 19h` |
| `DELAI_REPONSE` | Délai de réponse annoncé sur les devis | `24 à 48 heures ouvrées` |

**N'annoncez que ce qui est réellement assuré.** Une disponibilité affichée et
non tenue est une pratique commerciale trompeuse au sens de l'article L121-2
du code de la consommation, et c'est le premier motif d'avis négatif dans ce
métier.

Ces valeurs alimentent aussi le champ `openingHoursSpecification` des données
structurées. Si la disponibilité n'est pas continue, modifiez également
`src/partials/schema-home.html` pour que le balisage corresponde à l'affichage :
Google recoupe les deux.

---

## Zone d'intervention

| Variable | Rôle |
|---|---|
| `ZONE_INTERVENTION` | Liste complète, affichée en toutes lettres |
| `ZONE_COURTE` | Formule courte pour la vignette sociale et le manifeste |

Pour modifier réellement la couverture géographique, il faut aussi :

1. ajouter ou retirer les pages de `src/pages/zones/` ;
2. mettre à jour `src/pages/zones-d-intervention.html` ;
3. mettre à jour la liste `areaServed` dans `src/partials/schema-home.html` et
   `schema-service.html` ;
4. mettre à jour les liens du pied de page.

---

## Tarifs

| Variable | Rôle |
|---|---|
| `TAUX_HORAIRE` | Main-d'œuvre, par heure |
| `FRAIS_DEPLACEMENT` | Déplacement, quelle que soit l'heure |
| `MAJORATION_NUIT` | Majoration en pourcentage : nuit, dimanche, jours fériés |
| `FORFAIT_OUVERTURE_SIMPLE` | Ouverture de porte claquée |
| `FORFAIT_OUVERTURE_VERROUILLEE` | Ouverture de porte fermée à clé |
| `FORFAIT_OUVERTURE_BLINDEE` | Ouverture de porte blindée |
| `FORFAIT_CHANGEMENT_CYLINDRE` | Changement de cylindre, pièce comprise |
| `FORFAIT_EXTRACTION_CLE` | Extraction d'une clé cassée |

Valeurs numériques nues, sans symbole : le `€` est ajouté par les pages.

**Ces montants doivent être ceux réellement pratiqués.** L'arrêté du 24 janvier
2017 impose que les prix affichés soient ceux appliqués, sous peine d'amende
administrative.

Ils apparaissent sur la page tarifs, sur les pages de services concernées, sur
la page d'accueil, sur les pages de ville et dans le catalogue d'offres des
données structurées : une modification ici se répercute partout.

---

## Formulaire de devis

| Variable | Rôle |
|---|---|
| `EMAIL_DEVIS` | Adresse qui **reçoit** les demandes |
| `EMAIL_EXPEDITEUR` | Adresse qui **expédie** — doit appartenir au domaine |
| `DEVIS_PHOTO_MAX_MO` | Poids maximal d'une photo jointe, en mégaoctets |

`EMAIL_EXPEDITEUR` doit exister réellement, créée dans *hPanel > Emails*. Voir
`docs/deploiement-hostinger.md`, étape 2.

`DEVIS_PHOTO_MAX_MO` ne peut pas dépasser les limites PHP de l'hébergement
(`upload_max_filesize` et `post_max_size`, généralement 64 Mo chez Hostinger).
5 Mo couvre largement une photo de téléphone.

---

## Mesure d'audience et Google

| Variable | Valeur attendue | Effet si vide |
|---|---|---|
| `GA4_ID` | `G-XXXXXXXXXX` | Aucun script chargé, aucun bandeau de consentement |
| `GTM_ID` | `GTM-XXXXXXX` | Idem |
| `GSC_CODE` | Le contenu de `content=` de la balise Search Console | Aucune balise écrite |
| `URL_GOOGLE_BUSINESS` | URL de la fiche | Champ `sameAs` omis |
| `URL_FACEBOOK`, `URL_LINKEDIN` | URLs des profils | Idem |

Vide est un état valide et propre : rien n'est chargé, rien n'est écrit.

N'utilisez **pas** `GA4_ID` et `GTM_ID` simultanément si le conteneur GTM
charge déjà GA4 : les visites seraient comptées deux fois.

Ne renseignez que des profils réellement existants : `sameAs` est un signal que
Google recoupe, et une URL morte y nuit plus qu'elle n'aide.

---

## Indexation

| Variable | Valeurs | Effet |
|---|---|---|
| `ROBOTS_POLICY` | `noindex` ou `index` | Bascule l'ensemble du site |

En `noindex` :

- toutes les pages portent `<meta name="robots" content="noindex, follow">` ;
- `robots.txt` contient `Disallow: /` ;
- le sitemap reste généré, mais n'est pas déclaré dans `robots.txt`.

En `index`, tout bascule ensemble. Une page peut toujours forcer son propre
comportement via la clé `robots:` de ses métadonnées — c'est ce que font la
page 404 et la page de remerciement, qui restent en `noindex` dans les deux
cas.

> Ne passez pas en `index` avant d'avoir lu la section « Cohérence
> géographique » du README.

---

## Ce qui n'est pas dans config.sh

| Élément | Où le modifier |
|---|---|
| Menu principal | `src/partials/header.html` |
| Pied de page | `src/partials/footer.html` |
| Barre d'appel mobile | fin de `src/partials/footer.html` |
| Formulaire de devis | `src/partials/formulaire-devis.html` |
| Couleurs, typographie, mise en page | `static/assets/css/style.css` (variables CSS en tête de fichier) |
| Redirections, cache, en-têtes de sécurité | `static/.htaccess` |
| Icônes et vignette sociale | `scripts/generer-images.py`, puis relancer le script |
| Données structurées | `src/partials/schema-*.html` |

Les couleurs sont regroupées en variables CSS au début de `style.css` : changer
`--bleu-800` et `--ambre` suffit à modifier toute la charte du site.
