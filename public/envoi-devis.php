<?php
/* ===========================================================================
 *  Traitement du formulaire de demande de devis.
 *
 *  Ce fichier est le SEUL élément dynamique du site. Il fonctionne sur un
 *  hébergement mutualisé Hostinger standard : PHP 7.4 ou supérieur, fonction
 *  mail() activée par défaut, aucune extension particulière, aucune base de
 *  données, aucune bibliothèque à installer.
 *
 *  Les valeurs {{...}} sont remplacées au build par scripts/build.sh à partir
 *  de src/config.sh. N'éditez pas la version présente dans public/ : elle est
 *  régénérée à chaque build. La source est static/envoi-devis.php.
 *
 *  Chaîne de contrôle, dans l'ordre :
 *    1. méthode POST uniquement
 *    2. limitation du nombre d'envois par adresse IP
 *    3. piège à robots (champ invisible) et horodatage minimal
 *    4. validation et nettoyage de chaque champ
 *    5. contrôle réel du fichier joint (type MIME et image déchiffrable)
 *    6. construction du message, en neutralisant l'injection d'en-têtes
 *    7. envoi, puis redirection 303 vers la page de remerciement
 * ======================================================================== */

declare(strict_types=1);

/* --- Paramètres, injectés depuis src/config.sh --------------------------- */
const DESTINATAIRE   = 'contact@serrurier-richard.fr';
const EXPEDITEUR     = 'site@serrurier-richard.fr';
const NOM_SITE       = 'Serrurier Richard';
const TELEPHONE      = '02 20 06 00 75';
const TELEPHONE_E164 = '+33220060075';
define('PHOTO_MAX_MO', max(1, (int) '5'));

/* Fenêtre anti-abus : nombre maximal d'envois par adresse IP et par heure. */
const ENVOIS_MAX_PAR_HEURE = 5;
/* Délai minimal entre l'affichage du formulaire et son envoi, en secondes.
   Un humain ne remplit pas huit champs en moins de trois secondes. */
const DELAI_MINIMAL = 3;

const PAGE_SUCCES = '/merci';

/* ========================================================================
 *  Utilitaires
 * ==================================================================== */

/** Supprime les caractères de contrôle et les retours à la ligne.
 *  Sans cela, un champ contenant « \r\nBcc: » injecterait un en-tête dans
 *  le courriel : c'est l'attaque classique sur les formulaires de contact. */
function nettoyer(string $valeur, int $longueur = 200): string
{
    $valeur = str_replace(["\r", "\n", "\0", "\t"], ' ', $valeur);
    $valeur = preg_replace('/[\x00-\x1F\x7F]/u', '', $valeur) ?? '';
    $valeur = trim(preg_replace('/\s+/u', ' ', $valeur) ?? '');
    return mb_substr($valeur, 0, $longueur);
}

/** Nettoie un texte long en conservant les retours à la ligne. */
function nettoyer_texte(string $valeur, int $longueur = 4000): string
{
    $valeur = str_replace(["\r\n", "\r"], "\n", $valeur);
    $valeur = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $valeur) ?? '';
    return mb_substr(trim($valeur), 0, $longueur);
}

function champ(string $nom, int $longueur = 200): string
{
    return isset($_POST[$nom]) && is_string($_POST[$nom])
        ? nettoyer($_POST[$nom], $longueur)
        : '';
}

/** Adresse IP du visiteur, en tenant compte du proxy Hostinger. */
function adresse_ip(): string
{
    foreach (['HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR'] as $cle) {
        if (!empty($_SERVER[$cle])) {
            $ip = trim(explode(',', (string) $_SERVER[$cle])[0]);
            if (filter_var($ip, FILTER_VALIDATE_IP)) {
                return $ip;
            }
        }
    }
    return '0.0.0.0';
}

/** Fichier compteur d'une adresse IP. Il vit dans le dossier temporaire du
 *  système, jamais dans public_html : il n'est donc pas accessible depuis le
 *  Web, et l'hébergeur le purge de lui-même. */
function fichier_compteur(): string
{
    return sys_get_temp_dir() . '/devis-' . sha1(adresse_ip() . '|' . NOM_SITE) . '.txt';
}

/** Horodatages des envois réussis de la dernière heure, pour cette IP. */
function envois_recents(): array
{
    $fichier = fichier_compteur();
    if (!is_readable($fichier)) {
        return [];
    }
    $limite = time() - 3600;
    $recents = [];
    foreach (explode("\n", (string) @file_get_contents($fichier)) as $ligne) {
        $t = (int) trim($ligne);
        if ($t > $limite) {
            $recents[] = $t;
        }
    }
    return $recents;
}

/** Le quota ne compte que les envois RÉELLEMENT partis. Un visiteur qui se
 *  trompe cinq fois dans son numéro de téléphone ne doit pas se retrouver
 *  bloqué une heure : seul l'abus d'envoi est limité, pas la maladresse. */
function quota_depasse(): bool
{
    return count(envois_recents()) >= ENVOIS_MAX_PAR_HEURE;
}

function enregistrer_envoi(): void
{
    $horodatages = envois_recents();
    $horodatages[] = time();
    @file_put_contents(fichier_compteur(), implode("\n", $horodatages), LOCK_EX);
}

/** Page d'erreur autonome. Le visiteur revient au formulaire par l'historique
 *  du navigateur, qui restaure nativement les valeurs déjà saisies : rien
 *  n'est perdu, et le formulaire n'existe qu'en un seul exemplaire dans le
 *  code. Le téléphone reste proposé en repli — c'est le point essentiel :
 *  une demande qui échoue ne doit jamais être une impasse. */
function page_erreur(array $messages, int $code = 400): void
{
    http_response_code($code);
    header('Content-Type: text/html; charset=UTF-8');
    header('X-Robots-Tag: noindex');

    $liste = '';
    foreach ($messages as $m) {
        $liste .= '<li>' . htmlspecialchars($m, ENT_QUOTES, 'UTF-8') . '</li>';
    }

    $site  = htmlspecialchars(NOM_SITE, ENT_QUOTES, 'UTF-8');
    $tel   = htmlspecialchars(TELEPHONE, ENT_QUOTES, 'UTF-8');
    $e164  = htmlspecialchars(TELEPHONE_E164, ENT_QUOTES, 'UTF-8');
    $mail  = htmlspecialchars(DESTINATAIRE, ENT_QUOTES, 'UTF-8');

    echo <<<HTML
<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Votre demande n'a pas pu être envoyée — {$site}</title>
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#0b2a4a">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
<main id="contenu">
<section>
  <div class="wrap" style="max-width:44em">
    <h1>Votre demande n'a pas pu être envoyée</h1>

    <div class="message-etat echec">
      <p><strong>Voici ce qui doit être corrigé :</strong></p>
      <ul>{$liste}</ul>
    </div>

    <p>
      Revenez au formulaire : votre navigateur y restaure les informations que
      vous aviez déjà saisies.
    </p>
    <p>
      <button type="button" class="btn btn-devis" onclick="history.back()">Corriger ma demande</button>
      <a class="btn btn-ghost" href="/devis-serrurerie">Revenir au formulaire</a>
    </p>

    <div class="encadre">
      <h2>Vous préférez ne pas recommencer ?</h2>
      <p>
        Appelez-nous, c'est immédiat et souvent plus rapide :
        <a href="tel:{$e164}"><strong>{$tel}</strong></a>.
        Vous pouvez aussi écrire directement à <a href="mailto:{$mail}">{$mail}</a>.
      </p>
    </div>
  </div>
</section>
</main>
</body>
</html>
HTML;
    exit;
}

/* ========================================================================
 *  1. Méthode
 * ==================================================================== */

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Location: /devis-serrurerie', true, 303);
    exit;
}

/* ========================================================================
 *  2. Limitation d'usage
 * ==================================================================== */

if (quota_depasse()) {
    page_erreur([
        'Plusieurs demandes ont déjà été envoyées depuis cette connexion au cours de la dernière heure. Si votre demande est urgente, appelez-nous : nous répondons immédiatement.',
    ], 429);
}

/* ========================================================================
 *  3. Pièges à robots
 *     Le champ « _site » est invisible pour un visiteur. S'il est rempli,
 *     c'est un automate : on répond « merci » sans rien envoyer, pour ne pas
 *     lui signaler que le piège a fonctionné.
 * ==================================================================== */

if (champ('_site') !== '') {
    header('Location: ' . PAGE_SUCCES, true, 303);
    exit;
}

$depart = (int) champ('_horodatage', 20);
if ($depart > 0 && (time() - $depart) < DELAI_MINIMAL) {
    header('Location: ' . PAGE_SUCCES, true, 303);
    exit;
}

/* ========================================================================
 *  4. Validation des champs
 * ==================================================================== */

$erreurs = [];

$nom = champ('nom', 80);
if (mb_strlen($nom) < 2) {
    $erreurs[] = 'Le nom est obligatoire.';
}

/* Téléphone : on ne conserve que les chiffres et le « + » initial, puis on
   vérifie le format français, fixe ou mobile, avec ou sans indicatif. */
$telephone_saisi = champ('telephone', 30);
$telephone = preg_replace('/[^0-9+]/', '', $telephone_saisi) ?? '';
if (!preg_match('/^(?:\+33|0033|0)[1-9][0-9]{8}$/', $telephone)) {
    $erreurs[] = 'Le numéro de téléphone doit être un numéro français à dix chiffres, par exemple 06 12 34 56 78.';
}

$email = champ('email', 120);
if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    $erreurs[] = 'L\'adresse e-mail saisie n\'est pas valide.';
}

$ville = champ('ville', 80);
if (mb_strlen($ville) < 2) {
    $erreurs[] = 'La ville d\'intervention est obligatoire.';
}

$code_postal = champ('code_postal', 10);
if ($code_postal !== '' && !preg_match('/^[0-9]{5}$/', $code_postal)) {
    $erreurs[] = 'Le code postal doit comporter cinq chiffres.';
}

/* Listes fermées : toute valeur hors liste est rejetée, jamais réaffichée. */
$types_autorises = [
    'ouverture-porte'      => 'Ouverture de porte',
    'porte-bloquee'        => 'Porte bloquée',
    'cle-perdue'           => 'Clé perdue',
    'cle-cassee'           => 'Clé cassée',
    'changement-serrure'   => 'Changement ou remplacement de serrure',
    'installation-serrure' => 'Installation de serrure',
    'serrure-multipoints'  => 'Serrure multipoints (3 ou 5 points)',
    'blindage'             => 'Blindage de porte',
    'effraction'           => 'Sécurisation après effraction',
    'rideau-metallique'    => 'Rideau métallique',
    'coffre-fort'          => 'Coffre-fort',
    'autre'                => 'Autre demande',
];

$type = champ('type', 40);
if (!isset($types_autorises[$type])) {
    $erreurs[] = 'Merci de choisir le type d\'intervention dans la liste.';
}

$urgences_autorisees = [
    'immediate' => 'Urgent — intervention immédiate souhaitée',
    'jour'      => 'Dans la journée',
    'semaine'   => 'Dans la semaine',
    'devis'     => 'Pas urgent — demande de devis',
];

$urgence = champ('urgence', 20);
if (!isset($urgences_autorisees[$urgence])) {
    $erreurs[] = 'Merci d\'indiquer le degré d\'urgence.';
}

$description = isset($_POST['description']) && is_string($_POST['description'])
    ? nettoyer_texte($_POST['description'])
    : '';
if (mb_strlen($description) < 10) {
    $erreurs[] = 'Merci de décrire votre situation en quelques mots (dix caractères minimum).';
}

if (empty($_POST['consentement'])) {
    $erreurs[] = 'Vous devez accepter que vos coordonnées soient utilisées pour vous répondre.';
}

/* ========================================================================
 *  5. Photo jointe (facultative)
 *     Trois contrôles successifs : taille, type MIME réel lu dans le fichier
 *     — jamais l'extension ni le type annoncé par le navigateur, tous deux
 *     falsifiables — et capacité à être décodée comme image.
 * ==================================================================== */

$piece_jointe = null;

if (!empty($_FILES['photo']['name']) && (int) ($_FILES['photo']['error'] ?? 4) !== UPLOAD_ERR_NO_FILE) {
    $f = $_FILES['photo'];

    if ((int) $f['error'] === UPLOAD_ERR_INI_SIZE || (int) $f['error'] === UPLOAD_ERR_FORM_SIZE) {
        $erreurs[] = 'La photo dépasse la taille autorisée (' . PHOTO_MAX_MO . ' Mo maximum).';
    } elseif ((int) $f['error'] !== UPLOAD_ERR_OK) {
        $erreurs[] = 'La photo n\'a pas pu être reçue. Réessayez, ou envoyez votre demande sans photo.';
    } elseif (!is_uploaded_file($f['tmp_name'])) {
        $erreurs[] = 'Le fichier reçu n\'est pas valide.';
    } elseif ((int) $f['size'] > PHOTO_MAX_MO * 1024 * 1024) {
        $erreurs[] = 'La photo dépasse ' . PHOTO_MAX_MO . ' Mo. Réduisez-la ou envoyez la demande sans photo.';
    } else {
        $types_images = [
            'image/jpeg' => 'jpg',
            'image/png'  => 'png',
            'image/webp' => 'webp',
            'image/gif'  => 'gif',
        ];

        $mime = '';
        if (function_exists('finfo_open')) {
            $finfo = finfo_open(FILEINFO_MIME_TYPE);
            if ($finfo !== false) {
                $mime = (string) finfo_file($finfo, $f['tmp_name']);
                finfo_close($finfo);
            }
        }
        if ($mime === '') {
            $info = @getimagesize($f['tmp_name']);
            $mime = is_array($info) ? (string) ($info['mime'] ?? '') : '';
        }

        if (!isset($types_images[$mime]) || @getimagesize($f['tmp_name']) === false) {
            $erreurs[] = 'Le fichier joint doit être une photo au format JPG, PNG, WEBP ou GIF. Les photos iPhone au format HEIC ne sont pas acceptées : activez « Le plus compatible » dans Réglages > Appareil photo > Formats.';
        } else {
            $piece_jointe = [
                'nom'       => 'photo-' . date('Ymd-His') . '.' . $types_images[$mime],
                'mime'      => $mime,
                'contenu'   => (string) file_get_contents($f['tmp_name']),
            ];
        }
    }
}

if ($erreurs !== []) {
    page_erreur($erreurs);
}

/* ========================================================================
 *  6. Construction du message
 * ==================================================================== */

$libelle_type    = $types_autorises[$type];
$libelle_urgence = $urgences_autorisees[$urgence];
$prefixe         = ($urgence === 'immediate') ? '[URGENT] ' : '';

$sujet = $prefixe . 'Demande de devis — ' . $libelle_type . ' — ' . $ville;

$corps = "Nouvelle demande de devis déposée sur " . NOM_SITE . "\n"
       . str_repeat('=', 60) . "\n\n"
       . "Nom .............. : {$nom}\n"
       . "Téléphone ........ : {$telephone_saisi}\n"
       . "E-mail ........... : " . ($email !== '' ? $email : 'non renseigné') . "\n"
       . "Ville ............ : {$ville}" . ($code_postal !== '' ? " ({$code_postal})" : '') . "\n"
       . "Type d'intervention : {$libelle_type}\n"
       . "Urgence .......... : {$libelle_urgence}\n"
       . "Photo jointe ..... : " . ($piece_jointe !== null ? 'oui' : 'non') . "\n\n"
       . "Description\n"
       . str_repeat('-', 60) . "\n"
       . $description . "\n\n"
       . str_repeat('=', 60) . "\n"
       . "Reçu le " . date('d/m/Y à H:i') . "\n"
       . "Adresse IP : " . adresse_ip() . "\n";

/* En-têtes. Toutes les valeurs issues du formulaire ont été débarrassées de
   leurs retours à la ligne par nettoyer() : aucune ne peut ouvrir un en-tête.
   L'expéditeur est une adresse du domaine — condition SPF/DKIM sur Hostinger,
   sans quoi le message est rejeté ou classé en indésirable. */
$entetes = [
    'From'         => NOM_SITE . ' <' . EXPEDITEUR . '>',
    'Reply-To'     => $email !== '' ? $nom . ' <' . $email . '>' : EXPEDITEUR,
    'MIME-Version' => '1.0',
    'X-Mailer'     => 'PHP/' . phpversion(),
    'Auto-Submitted' => 'auto-generated',
];

if ($piece_jointe !== null) {
    $limite = 'sep-' . bin2hex(random_bytes(12));
    $entetes['Content-Type'] = 'multipart/mixed; boundary="' . $limite . '"';

    $message = "--{$limite}\r\n"
             . "Content-Type: text/plain; charset=UTF-8\r\n"
             . "Content-Transfer-Encoding: 8bit\r\n\r\n"
             . $corps . "\r\n"
             . "--{$limite}\r\n"
             . 'Content-Type: ' . $piece_jointe['mime'] . '; name="' . $piece_jointe['nom'] . "\"\r\n"
             . "Content-Transfer-Encoding: base64\r\n"
             . 'Content-Disposition: attachment; filename="' . $piece_jointe['nom'] . "\"\r\n\r\n"
             . chunk_split(base64_encode($piece_jointe['contenu'])) . "\r\n"
             . "--{$limite}--";
} else {
    $entetes['Content-Type'] = 'text/plain; charset=UTF-8';
    $entetes['Content-Transfer-Encoding'] = '8bit';
    $message = $corps;
}

$entetes_texte = '';
foreach ($entetes as $cle => $valeur) {
    $entetes_texte .= $cle . ': ' . str_replace(["\r", "\n"], '', (string) $valeur) . "\r\n";
}

/* L'objet est encodé en base64 : il contient des accents, que certains
   serveurs de messagerie tronquent s'ils sont transmis bruts. */
$sujet_encode = '=?UTF-8?B?' . base64_encode($sujet) . '?=';

/* Le cinquième paramètre force l'enveloppe d'expédition. Certains hébergeurs
   le refusent en mode sécurisé : on retente alors sans lui. */
enregistrer_envoi();

$envoye = @mail(DESTINATAIRE, $sujet_encode, $message, $entetes_texte, '-f' . EXPEDITEUR);
if (!$envoye) {
    $envoye = @mail(DESTINATAIRE, $sujet_encode, $message, $entetes_texte);
}

if (!$envoye) {
    error_log('[devis] Échec de mail() vers ' . DESTINATAIRE);
    page_erreur([
        'Le serveur de messagerie n\'a pas pu transmettre votre demande. Ce n\'est pas de votre fait : appelez-nous, nous prenons votre demande immédiatement.',
    ], 500);
}

/* ========================================================================
 *  7. Redirection vers la page de remerciement
 *     Une redirection 303 empêche le renvoi du formulaire si le visiteur
 *     actualise la page.
 * ==================================================================== */

header('Location: ' . PAGE_SUCCES, true, 303);
exit;
