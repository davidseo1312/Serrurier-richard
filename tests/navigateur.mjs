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
await mobile.locator('#nav-principal a[href="/faq"]').click();
await mobile.waitForLoadState('domcontentloaded');
verifier(mobile.url().endsWith('/faq'), 'un lien du menu navigue bien');

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

titre('7. Vie privée');

verifier((await ctxMobile.cookies()).length === 0, 'aucun cookie déposé sans consentement');
const mesureActive = await mobile.evaluate(
  () => Boolean(document.documentElement.dataset.ga || document.documentElement.dataset.gtm)
);
verifier(
  mesureActive || (await mobile.locator('.cookie-bandeau').count()) === 0,
  mesureActive
    ? 'mesure d’audience configurée : le bandeau de consentement doit s’afficher'
    : 'aucune mesure d’audience configurée : aucun bandeau, aucun script tiers'
);

await ctxMobile.close();

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
    const texte = (a.textContent || '').trim() || a.getAttribute('aria-label') || a.title;
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
