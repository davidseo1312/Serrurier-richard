<?php
/* ===========================================================================
 *  Routeur pour le serveur de développement PHP.
 *
 *      bash scripts/apercu.sh
 *
 *  Il reproduit les règles du .htaccess de production : URLs sans extension,
 *  redirections 301 des anciennes adresses, page 404 personnalisée. Sans lui,
 *  l'aperçu local ne ressemblerait pas au site en ligne et les liens internes
 *  tomberaient tous en erreur.
 *
 *  Ce fichier ne part JAMAIS en production : il vit dans scripts/, pas dans
 *  static/, et n'est donc pas copié dans public/.
 * ======================================================================== */

$racine = __DIR__ . '/../public';
$chemin = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) ?? '/';
$chemin = rawurldecode($chemin);

/* La Content-Security-Policy de production, relue directement dans le
   .htaccess pour que les deux ne puissent pas diverger.

   Sans elle, l'aperçu local et les tests tournent sans filet : une CSP trop
   étroite ne produit aucun message côté serveur, elle fait juste taire le
   script bloqué. C'est exactement ainsi qu'une mesure d'audience peut
   sembler installée et ne rien remonter. */
$htaccess = $racine . '/.htaccess';
if (is_file($htaccess) && preg_match(
        '/^\s*Header always set Content-Security-Policy "(.+)"\s*$/m',
        file_get_contents($htaccess), $m)) {
    header('Content-Security-Policy: ' . $m[1]);
}

// Les mêmes redirections 301 que le .htaccess.
$redirections = [
    '/services/ouverture-de-porte'    => '/ouverture-porte',
    '/services/changement-de-serrure' => '/changement-serrure',
    '/services/porte-blindee'         => '/porte-blindee',
    '/services/apres-effraction'      => '/effraction',
    '/services/rideau-metallique'     => '/rideau-metallique',
    '/services/coffre-fort'           => '/coffre-fort',
    '/services'                       => '/serrurier',
    '/politique-de-confidentialite'   => '/politique-confidentialite',
    '/serrurier-urgent'               => '/serrurier-urgence',
    '/urgence'                        => '/serrurier-urgence',
    '/devis'                          => '/devis-serrurerie',
    '/tarif'                          => '/tarifs',
];

$sansSlash = rtrim($chemin, '/');
if ($sansSlash !== '' && isset($redirections[$sansSlash])) {
    header('Location: ' . $redirections[$sansSlash], true, 301);
    exit;
}

// /page.html -> /page
if (preg_match('#^(.*)\.html$#', $chemin, $m)) {
    $cible = ($m[1] === '/index') ? '/' : preg_replace('#/index$#', '/', $m[1]);
    header('Location: ' . $cible, true, 301);
    exit;
}

$fichier = $racine . $chemin;

// Fichier réel : servi tel quel (assets, sitemap, robots…).
if (is_file($fichier)) {
    return false;   // le serveur intégré s'en charge, en-têtes compris
}

// Dossier : on sert son index.
if (is_dir($fichier) && is_file(rtrim($fichier, '/') . '/index.html')) {
    readfile(rtrim($fichier, '/') . '/index.html');
    return true;
}

// URL sans extension : on cherche le .html correspondant.
$candidat = $racine . rtrim($chemin, '/') . '.html';
if ($chemin !== '/' && is_file($candidat)) {
    readfile($candidat);
    return true;
}

if ($chemin === '/' && is_file($racine . '/index.html')) {
    readfile($racine . '/index.html');
    return true;
}

http_response_code(404);
if (is_file($racine . '/404.html')) {
    readfile($racine . '/404.html');
}
return true;
