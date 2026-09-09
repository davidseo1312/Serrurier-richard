/* ===========================================================================
 *  Génère les vignettes de partage social, une par visuel du catalogue.
 *
 *      node scripts/generer-og.mjs
 *
 *  Script FACULTATIF : les fichiers produits sont versionnés dans
 *  static/assets/images/og/. À relancer après une modification des
 *  illustrations ou de la charte.
 *
 *  POURQUOI CE SCRIPT EXISTE
 *  Les réseaux sociaux et les messageries n'affichent pas les images SVG :
 *  Facebook, LinkedIn, WhatsApp et X les ignorent purement et simplement, et
 *  le lien partagé apparaît alors sans aperçu. Une vignette matricielle est
 *  donc obligatoire, au format 1200 × 630 attendu par ces plateformes.
 *
 *  Le rendu passe par Chromium plutôt que par une bibliothèque d'images :
 *  c'est le seul moyen d'obtenir une conversion fidèle d'un SVG, dégradés et
 *  masques compris.
 *
 *  Dépendance : Playwright. npm install playwright && npx playwright install chromium
 * ======================================================================== */

import { chromium } from 'playwright';
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'fs';
import { dirname, join, basename } from 'path';

const RACINE = process.cwd();
const IMAGES = join(RACINE, 'static/assets/images');
const SORTIE = join(IMAGES, 'og');

const LARGEUR = 1200;
const HAUTEUR = 630;   // proportion 1.91:1 attendue par les réseaux sociaux

// Le catalogue est la source de vérité : une image ajoutée à src/images.conf
// obtient sa vignette sans qu'on touche à ce script.
//
// Chaque ligne donne deux candidats — la photographie réelle puis
// l'illustration de repli. L'arbitrage est le même que dans scripts/build.sh :
// la photographie prime, sinon l'illustration. La vignette sociale montre donc
// toujours ce que la page affiche réellement.
const catalogue = readFileSync(join(RACINE, 'src/images.conf'), 'utf8')
  .split('\n')
  .filter((l) => /^[A-Z]/.test(l))
  .map((l) => {
    const [id, photo, repli, , , altPhoto, altRepli] = l.split('|');
    return { id, photo, repli, altPhoto, altRepli };
  });

function trouverSource(chemin) {
  for (const ext of ['avif', 'webp', 'jpg', 'jpeg', 'png', 'svg']) {
    const f = join(IMAGES, `${chemin}.${ext}`);
    if (existsSync(f)) return f;
  }
  return null;
}

// Le dossier est vidé avant régénération : sinon une vignette produite pour
// une illustration remplacée par une photographie resterait sur le disque, et
// finirait par être servie à Facebook ou LinkedIn alors que la page montre
// autre chose.
rmSync(SORTIE, { recursive: true, force: true });
mkdirSync(SORTIE, { recursive: true });

const navigateur = await chromium.launch();
const page = await navigateur.newPage({
  viewport: { width: LARGEUR, height: HAUTEUR },
  deviceScaleFactor: 1,
});

let produites = 0;

for (const { id, photo, repli, altPhoto, altRepli } of catalogue) {
  const source = (photo && trouverSource(photo)) || trouverSource(repli);
  const chemin = photo && trouverSource(photo) ? photo : repli;
  const alt = photo && trouverSource(photo) ? altPhoto : altRepli;
  if (!source) {
    console.log(`  source introuvable pour ${id}`);
    continue;
  }

  // Le visuel est cadré en « cover » : il remplit la vignette sans se
  // déformer, quitte à rogner légèrement en haut et en bas.
  const html = `<!doctype html><meta charset="utf-8">
    <style>
      html,body{margin:0;width:${LARGEUR}px;height:${HAUTEUR}px;overflow:hidden;background:#0F172A}
      img{width:100%;height:100%;object-fit:cover;display:block}
    </style>
    <img src="file://${source}" alt="">`;

  const temporaire = join(IMAGES, '_og-temporaire.html');
  writeFileSync(temporaire, html);
  await page.goto('file://' + temporaire);
  await page.waitForTimeout(120);

  const destination = join(SORTIE, `${basename(chemin)}.jpg`);
  mkdirSync(dirname(destination), { recursive: true });
  await page.screenshot({ path: destination, type: 'jpeg', quality: 86 });
  produites += 1;
  console.log(`  og/${basename(chemin)}.jpg`);
}

try { writeFileSync(join(IMAGES, '_og-temporaire.html'), ''); } catch {}
const fs = await import('fs');
try { fs.unlinkSync(join(IMAGES, '_og-temporaire.html')); } catch {}

await navigateur.close();
console.log(`\n${produites} vignette(s) de partage générée(s) dans static/assets/images/og/`);
