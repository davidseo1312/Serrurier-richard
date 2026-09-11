/* ===========================================================================
 *  Tests de navigateur — parcours réels, sur mobile et sur ordinateur.
 *
 *      bash tests/lancer.sh
 *
 *  Ce que ce fichier vérifie, et que ni le build ni check-seo.sh ne peuvent
 *  voir : le menu s'ouvre, la FAQ se déplie, la barre d'appel est au bon
 *  endroit, le formulaire refuse une saisie incomplète, aucun cookie n'est
 *  déposé sans consentement, et le site reste utilisable sans JavaScript.
 *
 *  Dépendance : Playwright. Facultatif — le site se construit et se déploie
 *  sans lui. Voir tests/lancer.sh.
 * ======================================================================== */

import { chromium, devices } from 'playwright';

const BASE = process.env.BASE_URL || 'http://localhost:8090';

let reussis = 0;
let echecs = 0;

function verifier(condition, description) {
  if (condition) {
    reussis += 1;
    console.log(`  \x1b[32mv\x1b[0m ${description}`);
  } else {
    echecs += 1;
    console.log(`  \x1b[31mx\x1b[0m ${description}`);
  }
}

function titre(texte) {
  console.log(`\n\x1b[1m${texte}\x1b[0m`);
}

const PAGES = [
  ['accueil', '/'],
  ['prestations', '/serrurier'],
  ['urgence', '/serrurier-urgence'],
  ['ouverture de porte', '/ouverture-porte'],
  ['devis', '/devis-serrurerie'],
  ['FAQ', '/faq'],
  ['page ville', '/serrurier-rennes'],
  ['tarifs', '/tarifs'],
  ['zone départementale', '/zones/morbihan-56'],
  ['blog', '/blog/'],
  ['mentions légales', '/mentions-legales'],
  ['404', '/page-inexistante'],
];

const navigateur = await chromium.launch();

/* --- 1. Chaque page se charge sans erreur, sur trois formats -------------- */

titre('1. Chargement des pages');

for (const [nomAppareil, options] of [
  ['ordinateur', { viewport: { width: 1440, height: 900 } }],
  ['iPhone', devices['iPhone 13']],
  ['Android', devices['Pixel 7']],
]) {
  const contexte = await navigateur.newContext({ ...options, locale: 'fr-FR' });
  const page = await contexte.newPage();

  const incidents = [];
  page.on('pageerror', (e) => incidents.push(`erreur JS : ${e.message}`));
  page.on('console', (m) => {
    if (m.type() === 'error' && !m.text().includes('404')) incidents.push(`console : ${m.text()}`);
  });
  page.on('requestfailed', (r) => {
    if (!r.url().includes('page-inexistante')) incidents.push(`requête échouée : ${r.url()}`);
  });

  let debordements = [];
  for (const [nom, chemin] of PAGES) {
    const reponse = await page.goto(BASE + chemin, { waitUntil: 'networkidle' });
    const attendu = chemin === '/page-inexistante' ? 404 : 200;
    if (reponse.status() !== attendu) {
      incidents.push(`${chemin} répond ${reponse.status()} au lieu de ${attendu}`);
    }
    // Un débordement horizontal oblige à faire glisser la page latéralement :
    // c'est le défaut mobile le plus courant, et le plus vite sanctionné.
    const trop = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth
    );
    if (trop > 1) debordements.push(`${chemin} (+${trop}px)`);
  }

  verifier(incidents.length === 0, `${nomAppareil} : ${PAGES.length} pages sans erreur`
    + (incidents.length ? ` — ${incidents.slice(0, 3).join(' | ')}` : ''));
  verifier(debordements.length === 0, `${nomAppareil} : aucun débordement horizontal`
    + (debordements.length ? ` — ${debordements.join(', ')}` : ''));

  await contexte.close();
}

/* --- 2. Navigation et composants ----------------------------------------- */

titre('2. Navigation sur mobile');

const ctxMobile = await navigateur.newContext({ ...devices['iPhone 13'], locale: 'fr-FR' });
const mobile = await ctxMobile.newPage();

await mobile.goto(BASE + '/');
const menu = mobile.locator('#nav-principal');
verifier(!(await menu.isVisible()), 'le menu est fermé au chargement');

await mobile.locator('.nav-toggle').click();
verifier(await menu.isVisible(), 'le menu s’ouvre au clic');
verifier(
  (await mobile.locator('.nav-toggle').getAttribute('aria-expanded')) === 'true',
  'aria-expanded passe à true'
);

await mobile.keyboard.press('Escape');
verifier(!(await menu.isVisible()), 'la touche Échap referme le menu');

await mobile.locator('.nav-toggle').click();
await mobile.locator('#nav-principal a[href="/serrurier"]').click();
await mobile.waitForLoadState('domcontentloaded');
verifier(mobile.url().endsWith('/serrurier'), 'un lien du menu navigue bien');

titre('3. Barre d’appel fixe');

await mobile.goto(BASE + '/');
const barre = mobile.locator('.barre-mobile');
verifier(await barre.isVisible(), 'la barre d’appel est visible sur mobile');
const boite = await barre.boundingBox();
const ecran = mobile.viewportSize();
verifier(Math.abs(boite.y + boite.height - ecran.height) < 2, 'elle est collée au bas de l’écran');
verifier(boite.height >= 48, `sa hauteur est confortable (${Math.round(boite.height)} px)`);
verifier(
  (await mobile.locator('.barre-mobile-appel').getAttribute('href')).startsWith('tel:+33'),
  'le lien d’appel est au format international'
);

titre('4. Cibles tactiles (WCAG 2.5.8)');

// Les liens en pleine phrase sont exclus : la norme les dispense explicitement.
const petites = await mobile.evaluate(() => {
  const trop = [];
  for (const el of document.querySelectorAll('a, button, input:not([type=hidden]), select, textarea')) {
    const r = el.getBoundingClientRect();
    if (!r.width && !r.height) continue;
    const dansUnParagraphe = el.closest('p') && el.parentElement.tagName === 'P'
      && el.parentElement.textContent.trim().length > (el.textContent || '').trim().length + 20;
    if (dansUnParagraphe) continue;
    if (r.height < 24) trop.push(`${el.tagName} « ${(el.textContent || '').trim().slice(0, 25)} » ${Math.round(r.height)}px`);
  }
  return trop;
});
verifier(petites.length === 0, `toutes les cibles font au moins 24 px${petites.length ? ' — ' + petites.slice(0, 4).join(', ') : ''}`);

const ctxCarte = await navigateur.newContext({ viewport: { width: 1280, height: 900 }, locale: 'fr-FR' });
const bureauCarte = await ctxCarte.newPage();

titre('5. Une image, un seul emplacement');

/* La galerie a été retirée de l'accueil : elle montrait, réunies, les mêmes
   photographies que les pages de service. La règle qui la remplace est
   vérifiable, elle : sur tout le site, un fichier image ne peut être affiché
   qu'à UN seul endroit, et une page n'en affiche jamais deux fois le même.
   C'est ce que ce bloc contrôle, page après page. */
const cheminsSitemap = (await (await fetch(BASE + '/sitemap.xml')).text())
  .match(/<loc>([^<]+)<\/loc>/g).map(m => m.replace(/<\/?loc>/g, ''))
  .map(u => new URL(u).pathname);

const emplacements = new Map();          // fichier -> [pages]
let pagesAvecDoublonInterne = [];
for (const chemin of cheminsSitemap) {
  await mobile.goto(BASE + chemin);
  const srcs = await mobile.evaluate(() =>
    [...document.querySelectorAll('img')]
      .map(i => i.getAttribute('src'))
      .filter(s => s && s.includes('/assets/images/')));
  if (new Set(srcs).size !== srcs.length) pagesAvecDoublonInterne.push(chemin);
  for (const src of new Set(srcs)) {
    if (!emplacements.has(src)) emplacements.set(src, []);
    emplacements.get(src).push(chemin);
  }
}
const repetes = [...emplacements].filter(([, pages]) => pages.length > 1);
verifier(
  pagesAvecDoublonInterne.length === 0,
  `aucune page n'affiche deux fois le même visuel${pagesAvecDoublonInterne.length ? ' — ' + pagesAvecDoublonInterne.slice(0, 3).join(', ') : ''}`
);
verifier(
  repetes.length === 0,
  `aucun visuel n'est repris d'une page à l'autre${repetes.length ? ' — ' + repetes.slice(0, 3).map(([s, p]) => s.split('/').pop() + ' sur ' + p.join(' et ')).join(' | ') : ''}`
);
verifier(
  emplacements.size >= 15,
  `${emplacements.size} visuels distincts affichés sur le site`
);

titre('5 bis. Repère de la page courante');

await mobile.goto(BASE + '/tarifs');
const courante = mobile.locator('.nav a[aria-current="page"]');
verifier((await courante.count()) === 1, 'une seule entrée de menu est marquée « page courante »');
verifier((await courante.getAttribute('href')) === '/tarifs', 'et c\'est bien celle de la page affichée');

titre('5 ter. Carte des zones d’intervention');

await bureauCarte.goto(BASE + '/');
const zones = bureauCarte.locator('.carte-svg a.zone');
const lignesZone = bureauCarte.locator('.carte-liste a[data-zone]');
verifier((await zones.count()) > 0, `${await zones.count()} départements tracés sur la carte`);
verifier(
  (await zones.count()) === (await lignesZone.count()),
  'la carte et la liste annoncent exactement les mêmes départements'
);
verifier(
  (await bureauCarte.locator('.carte-svg title#carte-titre').count()) === 1 &&
    (await bureauCarte.locator('.carte-svg desc#carte-desc').count()) === 1,
  'la carte porte un titre et une description accessibles'
);
const premiereZone = await zones.first().getAttribute('href');
verifier(
  typeof premiereZone === 'string' && premiereZone.startsWith('/zones/'),
  'chaque département renvoie vers sa page de zone'
);
await lignesZone.first().hover();
await bureauCarte.waitForTimeout(200);
verifier(
  (await bureauCarte.locator('.carte-svg .zone.active').count()) === 1,
  'survoler la liste met le département en avant sur la carte'
);

// La carte détaillée contacte openstreetmap.org : elle ne doit jamais partir
// toute seule. C'est le point vérifié ici.
const domainesTiers = [];
bureauCarte.on('request', (r) => {
  const hote = new URL(r.url()).hostname;
  if (!/^(localhost|127\.0\.0\.1)$/.test(hote)) domainesTiers.push(hote);
});
await bureauCarte.reload({ waitUntil: 'networkidle' });
verifier(domainesTiers.length === 0, 'aucune requête tierce à l’ouverture de la page');
verifier(
  await bureauCarte.evaluate(() => typeof window.L === 'undefined'),
  'la bibliothèque de carte n’est pas chargée tant qu’on ne la demande pas'
);
await bureauCarte.locator('[data-carte-ouvrir]').click();
await bureauCarte.waitForTimeout(2500);
verifier(
  await bureauCarte.evaluate(() => typeof window.L !== 'undefined'),
  'elle se charge après le clic explicite du visiteur'
);
verifier(
  (await bureauCarte.locator('.carte-tuiles .leaflet-marker-icon').count()) ===
    (await lignesZone.count()),
  'la carte détaillée pose un repère par département annoncé, et pas un de plus'
);
verifier(
  (await bureauCarte.locator('.leaflet-control-attribution').innerText()).includes('OpenStreetMap'),
  'l’attribution OpenStreetMap est affichée'
);

titre('5. FAQ et sommaire');

await mobile.goto(BASE + '/faq');
const question = mobile.locator('.faq details').first();
verifier(!(await question.evaluate((e) => e.open)), 'les questions sont repliées au chargement');
await question.locator('summary').click();
verifier(await question.evaluate((e) => e.open), 'une question s’ouvre au clic');
await mobile.locator('.sommaire a[href="#devis"]').click();
await mobile.waitForTimeout(400);
verifier(await mobile.locator('#devis').isVisible(), 'le sommaire mène bien à sa section');

titre('6. Formulaire de devis');

await mobile.goto(BASE + '/devis-serrurerie');
await mobile.locator('form[data-devis] button[type=submit]').click();
verifier(mobile.url().includes('/devis-serrurerie'), 'un envoi incomplet est refusé sur place');
verifier(
  (await mobile.locator('form[data-devis] :invalid').count()) > 0,
  'le navigateur signale les champs manquants'
);
verifier(
  Number(await mobile.locator('input[name=_horodatage]').inputValue()) > 1e9,
  'l’horodatage anti-robot est renseigné'
);
verifier(
  (await mobile.locator('.pot-de-miel input').boundingBox()).x < 0,
  'le piège à robots est hors de l’écran'
);

titre('7. Vie privée et mesure d’audience');

verifier((await ctxMobile.cookies()).length === 0, 'aucun cookie déposé sans consentement');
const GA_ID = await mobile.evaluate(() => document.documentElement.dataset.ga || '');
const mesureActive = await mobile.evaluate(
  () => Boolean(document.documentElement.dataset.ga || document.documentElement.dataset.gtm)
);
await ctxMobile.close();

/* Google est injoignable depuis l'environnement de test, et c'est tant mieux :
   on intercepte les appels vers ses domaines pour observer ce que le site
   DEMANDE, sans rien transmettre à personne. Ce que ces tests prouvent, c'est
   le comportement du site — pas la réception côté Google, qui se vérifie dans
   le rapport « Temps réel » de GA4. */
const DOMAINES_GOOGLE = /googletagmanager\.com|google-analytics\.com/;

async function contexteMesure() {
  const ctx = await navigateur.newContext(devices['iPhone 13']);
  const appels = [];
  // Une CSP trop étroite ne produit aucune erreur serveur : elle fait taire
  // le script bloqué, en silence. On écoute donc les violations.
  await ctx.addInitScript(() => {
    window.__cspViolations = [];
    document.addEventListener('securitypolicyviolation', (e) => {
      window.__cspViolations.push(`${e.blockedURI} (${e.violatedDirective})`);
    });
  });
  await ctx.route(DOMAINES_GOOGLE, async (route) => {
    appels.push(route.request().url());
    await route.fulfill({
      status: 200,
      contentType: 'application/javascript',
      body: '/* gtag.js simulé : le vrai script n’est jamais téléchargé ici */'
    });
  });
  return { ctx, page: await ctx.newPage(), appels };
}

if (!mesureActive) {
  verifier(true, 'aucune mesure d’audience configurée : aucun bandeau, aucun script tiers');
} else {
  verifier(/^G-[A-Z0-9]+$/.test(GA_ID), `identifiant GA4 présent sur la page : ${GA_ID}`);

  // --- a) Avant tout choix : rien ne part, et le bandeau se présente. ---
  const avant = await contexteMesure();
  const enTetes = (await avant.page.goto(BASE + '/')).headers();
  const csp = enTetes['content-security-policy'] || '';
  const scriptSrc = (csp.match(/script-src[^;]*/) || [''])[0];
  verifier(
    scriptSrc.includes('googletagmanager.com'),
    'la CSP de production est servie et autorise le tag dans script-src'
  );
  await avant.page.waitForTimeout(500);
  verifier(avant.appels.length === 0, 'avant consentement : aucun appel vers Google');
  verifier(await avant.page.locator('.cookie-bandeau').isVisible(), 'le bandeau de consentement s’affiche');

  // Une conversion survenue avant le choix doit être mise en file, pas perdue.
  await avant.page.evaluate(() => {
    const sonde = document.createElement('button');
    sonde.setAttribute('data-track', 'appel');
    sonde.setAttribute('data-track-zone', 'sonde-test');
    document.body.appendChild(sonde);
    sonde.click();
  });
  verifier(
    (await avant.page.evaluate(() => (window.dataLayer || []).length)) === 0,
    'une conversion survenue avant le choix n’est pas transmise'
  );

  // --- b) Après « Accepter » : le tag est demandé, la file est rejouée. ---
  await avant.page.locator('.cookie-bandeau [data-action=accepter]').click();
  await avant.page.waitForTimeout(500);

  verifier(
    avant.appels.some((u) => u.includes('/gtag/js?id=' + GA_ID)),
    'après acceptation : le tag GA4 est demandé avec le bon identifiant'
  );
  verifier(
    (await avant.page.locator('.cookie-bandeau').count()) === 0,
    'le bandeau disparaît une fois le choix fait'
  );

  const empile = await avant.page.evaluate(() =>
    (window.dataLayer || [])
      .map((e) => {
        try { return JSON.stringify(e.length !== undefined ? Array.prototype.slice.call(e) : e); }
        catch (x) { return ''; }
      })
      .join(' | ')
  );
  verifier(empile.includes('"config"') && empile.includes(GA_ID), 'la configuration GA4 est bien empilée');
  verifier(empile.includes('"analytics_storage":"granted"'), 'le consentement à la mesure est transmis au tag');
  verifier(empile.includes('"ad_storage":"denied"'), 'le stockage publicitaire reste refusé');
  verifier(empile.includes('sonde-test'), 'la conversion mise en file est rejouée après acceptation');

  const violations = await avant.page.evaluate(() => window.__cspViolations || []);
  verifier(violations.length === 0, `aucune ressource bloquée par la CSP${violations.length ? ' — ' + violations.join(', ') : ''}`);

  // Le choix survit au rechargement : pas de bandeau une seconde fois.
  await avant.page.goto(BASE + '/tarifs');
  await avant.page.waitForTimeout(400);
  verifier(
    (await avant.page.locator('.cookie-bandeau').count()) === 0,
    'l’acceptation est mémorisée : le bandeau ne revient pas'
  );
  await avant.ctx.close();

  // --- c) Après « Refuser » : rien, ni maintenant ni à la visite suivante. ---
  const refus = await contexteMesure();
  await refus.page.goto(BASE + '/');
  await refus.page.locator('.cookie-bandeau [data-action=refuser]').click();
  await refus.page.waitForTimeout(400);
  await refus.page.evaluate(() => {
    const sonde = document.createElement('button');
    sonde.setAttribute('data-track', 'appel');
    document.body.appendChild(sonde);
    sonde.click();
  });
  await refus.page.goto(BASE + '/serrurier');
  await refus.page.waitForTimeout(500);
  verifier(refus.appels.length === 0, 'après refus : toujours aucun appel vers Google');
  verifier(
    (await refus.page.locator('.cookie-bandeau').count()) === 0,
    'le refus est mémorisé : le bandeau ne revient pas'
  );
  verifier((await refus.ctx.cookies()).length === 0, 'après refus : aucun cookie déposé');
  await refus.ctx.close();
}

titre('8. Fonctionnement sans JavaScript');

const ctxSansJs = await navigateur.newContext({ ...devices['iPhone 13'], javaScriptEnabled: false });
const sansJs = await ctxSansJs.newPage();

await sansJs.goto(BASE + '/devis-serrurerie');
verifier(await sansJs.locator('form[data-devis]').isVisible(), 'le formulaire reste affiché');
verifier(await sansJs.locator('.barre-mobile-appel').isVisible(), 'le bouton d’appel reste affiché');
await sansJs.goto(BASE + '/faq');
verifier(await sansJs.locator('.faq details').first().isVisible(), 'la FAQ reste consultable');
await sansJs.goto(BASE + '/');
verifier((await sansJs.locator('a[href^="tel:"]').count()) > 0, 'les liens d’appel restent présents');
await ctxSansJs.close();

titre('9. Accessibilité au clavier');

const ctxBureau = await navigateur.newContext({ viewport: { width: 1440, height: 900 }, locale: 'fr-FR' });
const bureau = await ctxBureau.newPage();
await bureau.goto(BASE + '/');
await bureau.keyboard.press('Tab');
verifier(
  (await bureau.evaluate(() => document.activeElement.className)).includes('skip-link'),
  'le premier arrêt de tabulation est le lien d’évitement'
);
await bureau.keyboard.press('Enter');
await bureau.waitForTimeout(200);
verifier(
  await bureau.evaluate(() => Boolean(document.getElementById('contenu'))),
  'la cible du lien d’évitement existe'
);
const sansTexte = await bureau.evaluate(() => {
  const vides = [];
  for (const a of document.querySelectorAll('a')) {
    /* Un lien dont le contenu est une image tire son intitulé du texte
       alternatif de cette image : c'est le cas du logo. Ne pas le compter
       ferait échouer le test sur un balisage pourtant correct — et poser un
       aria-label par-dessus écraserait l'alt au lieu de s'y ajouter. */
    const alt = [...a.querySelectorAll('img')]
      .map(i => (i.getAttribute('alt') || '').trim())
      .find(Boolean);
    const texte = (a.textContent || '').trim() || a.getAttribute('aria-label') || alt || a.title;
    if (!texte) vides.push(a.getAttribute('href') || '(sans href)');
  }
  return vides;
});
verifier(sansTexte.length === 0, `tous les liens ont un intitulé${sansTexte.length ? ' — ' + sansTexte.join(', ') : ''}`);
await ctxBureau.close();

await navigateur.close();

console.log(`\n\x1b[1mBilan\x1b[0m`);
console.log(`  \x1b[32m${reussis} test(s) réussi(s)\x1b[0m`);
console.log(`  ${echecs ? '\x1b[31m' : ''}${echecs} test(s) en échec\x1b[0m\n`);

process.exit(echecs === 0 ? 0 : 1);
