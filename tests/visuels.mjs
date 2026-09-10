/* ---------------------------------------------------------------------------
 * Contrôle visuel automatisé de toutes les pages du sitemap.
 *
 *     BASE_URL=http://localhost:8099 node tests/visuels.mjs
 *
 * Quatre vérifications, sur onze largeurs d'écran :
 *
 *   1. aucun débordement horizontal ;
 *   2. aucune cible tactile sous 24 px (WCAG 2.5.8), hors liens en ligne
 *      dans un bloc de texte, pour lesquels la norme prévoit une exception ;
 *   3. aucune image déformée, ni servie dans une définition trop faible pour
 *      la largeur à laquelle la page l'affiche — c'est ce que produit un
 *      attribut « sizes » inexact, et cela ne se voit qu'à l'œil ;
 *   4. contraste AA (4,5:1, ou 3:1 pour les grands textes) sur chaque nœud
 *      de texte réellement affiché.
 *
 * Ces quatre points se dégradent silencieusement : une règle CSS plus
 * spécifique suffit à repeindre un badge en gris clair sans rien casser.
 * D'où ce contrôle, qui échoue au lieu de laisser passer.
 * ------------------------------------------------------------------------- */
import { chromium } from 'playwright';
import fs from 'fs';

const BASE = process.env.BASE_URL || 'http://localhost:8099';
const LARGEURS = [320, 375, 390, 414, 430, 768, 820, 1024, 1280, 1440, 1920];

const V = '\x1b[32mv\x1b[0m', X = '\x1b[31mx\x1b[0m', G = '\x1b[1m', R = '\x1b[0m';
let reussis = 0, echecs = 0;
const verifier = (ok, texte, detail = '') => {
  if (ok) { reussis++; console.log(`  ${V} ${texte}`); }
  else { echecs++; console.log(`  ${X} ${texte}${detail ? ' — ' + detail : ''}`); }
};

const chemins = fs.readFileSync('public/sitemap.xml', 'utf8')
  .match(/<loc>([^<]+)<\/loc>/g).map(m => m.replace(/<\/?loc>/g, ''))
  .map(u => new URL(u).pathname);

const lum = c => { const [r, g, b] = c.map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return .2126 * r + .7152 * g + .0722 * b; };
const ratio = (a, b) => { const l1 = lum(a), l2 = lum(b); return (Math.max(l1, l2) + .05) / (Math.min(l1, l2) + .05); };

const nav = await chromium.launch();

/* --- 1 à 3 : mise en page, cibles tactiles, images ----------------------- */
console.log(`\n${G}1. Mise en page, cibles tactiles et images (11 largeurs)${R}`);
for (const w of LARGEURS) {
  const page = await nav.newPage({ viewport: { width: w, height: 900 } });
  const defauts = [];
  for (const chemin of chemins) {
    const rep = await page.goto(BASE + chemin, { waitUntil: 'load' });
    if (!rep.ok()) { defauts.push(`${chemin} : HTTP ${rep.status()}`); continue; }
    const r = await page.evaluate(() => {
      const out = { deborde: null, cibles: [], images: [] };
      const doc = document.documentElement;
      if (doc.scrollWidth > doc.clientWidth + 1) {
        let pire = null, max = doc.clientWidth;
        for (const el of document.querySelectorAll('body *')) {
          const b = el.getBoundingClientRect();
          if (b.right > max + 1 && b.width > 0) { pire = el; max = b.right; }
        }
        out.deborde = `${doc.scrollWidth} > ${doc.clientWidth} px (${pire ? pire.tagName + '.' + (pire.className || '').toString().split(' ')[0] : '?'})`;
      }
      for (const el of document.querySelectorAll('a[href], button, input, select, textarea, summary')) {
        const b = el.getBoundingClientRect();
        if (!b.width || !b.height) continue;
        const st = getComputedStyle(el);
        if (st.visibility === 'hidden' || st.display === 'none') continue;
        if (b.right < 0 || b.bottom < 0 || b.left > document.documentElement.clientWidth) continue;
        const p = el.parentElement;
        const enLigne = st.display.startsWith('inline') && p &&
          /^(P|LI|SPAN|STRONG|EM|TD|DD|DT|H1|H2|H3|H4|FIGCAPTION|LABEL)$/.test(p.tagName) &&
          p.textContent.trim().length > el.textContent.trim().length;
        if (enLigne) continue;
        if (b.width < 24 || b.height < 24)
          out.cibles.push(`${el.tagName} ${Math.round(b.width)}×${Math.round(b.height)} « ${el.textContent.trim().slice(0, 24)} »`);
      }
      for (const img of document.querySelectorAll('img')) {
        const b = img.getBoundingClientRect();
        if (!img.naturalWidth || !b.width) continue;
        const rn = img.naturalWidth / img.naturalHeight, ra = b.width / b.height;
        if (getComputedStyle(img).objectFit !== 'cover' && Math.abs(rn - ra) / rn > 0.02)
          out.images.push(`déformée : ${img.getAttribute('src')} (source ${rn.toFixed(2)}, affichée ${ra.toFixed(2)})`);
        if (b.width > img.naturalWidth * 1.35)
          out.images.push(`définition insuffisante : ${img.getAttribute('src')} affichée sur ${Math.round(b.width)} px pour ${img.naturalWidth} px de fichier`);
      }
      return out;
    });
    if (r.deborde) defauts.push(`${chemin} : débordement ${r.deborde}`);
    for (const c of r.cibles) defauts.push(`${chemin} : cible ${c}`);
    for (const i of r.images) defauts.push(`${chemin} : ${i}`);
  }
  verifier(defauts.length === 0, `${String(w).padStart(4)} px — ${chemins.length} pages`, defauts.slice(0, 3).join(' | '));
  await page.close();
}

/* --- 4 : contraste ------------------------------------------------------- */
console.log(`\n${G}2. Contraste (WCAG AA)${R}`);
const page = await nav.newPage({ viewport: { width: 1440, height: 900 } });
const mauvais = new Map();
for (const chemin of chemins) {
  await page.goto(BASE + chemin, { waitUntil: 'load' });
  const noeuds = await page.evaluate(() => {
    const parse = s => (s.match(/[\d.]+/g) || [0, 0, 0]).slice(0, 3).map(Number);
    const fondDe = el => {
      for (let e = el; e; e = e.parentElement) {
        const bg = getComputedStyle(e).backgroundColor;
        if (bg && bg !== 'rgba(0, 0, 0, 0)' && !/^rgba\(.*,\s*0\)$/.test(bg)) return parse(bg);
      }
      return [255, 255, 255];
    };
    const out = [];
    for (const el of document.querySelectorAll('p,li,strong,em,span,h1,h2,h3,h4,a,summary,figcaption,td,th,label,button,small')) {
      if (!el.textContent.trim() || el.children.length > 0) continue;
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      const st = getComputedStyle(el);
      if (st.visibility === 'hidden' || st.display === 'none' || +st.opacity === 0) continue;
      if (r.right < 0 || r.left > innerWidth) continue;
      const px = parseFloat(st.fontSize), gras = (+st.fontWeight) >= 700;
      out.push({ texte: el.textContent.trim().slice(0, 32), fg: parse(st.color), bg: fondDe(el),
                 seuil: (px >= 24 || (px >= 18.66 && gras)) ? 3 : 4.5,
                 sel: el.tagName + '.' + (el.className || '').toString().split(' ')[0] });
    }
    return out;
  });
  for (const n of noeuds) {
    const c = ratio(n.fg, n.bg);
    if (c < n.seuil) {
      const cle = `${n.sel} ${c.toFixed(2)}:1 (seuil ${n.seuil}) « ${n.texte} »`;
      if (!mauvais.has(cle)) mauvais.set(cle, chemin);
    }
  }
}
await page.close();
verifier(mauvais.size === 0, `${chemins.length} pages relues nœud par nœud`,
         [...mauvais].slice(0, 3).map(([k, v]) => `${v} ${k}`).join(' | '));

await nav.close();
console.log(`\n${G}Bilan${R}`);
console.log(`  \x1b[32m${reussis} contrôle(s) réussi(s)\x1b[0m`);
console.log(`  ${echecs ? '\x1b[31m' : ''}${echecs} contrôle(s) en échec\x1b[0m`);
process.exit(echecs ? 1 : 0);
