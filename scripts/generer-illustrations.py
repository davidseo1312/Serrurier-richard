#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Génère les illustrations vectorielles du site.
#
#   python3 scripts/generer-illustrations.py
#
# Script FACULTATIF : les SVG produits sont versionnés dans
# static/assets/images/. À relancer seulement si la charte change.
#
# Pourquoi un générateur plutôt que dix-sept fichiers écrits à la main :
# toutes les illustrations partagent le même vocabulaire — même fond, même
# perspective, mêmes épaisseurs de trait, même accent orange sur l'élément
# d'action. Un réglage de charte se répercute partout d'un seul coup, et
# aucune illustration ne dérive visuellement des autres.
#
# Ces visuels sont des ILLUSTRATIONS, pas des photographies d'intervention.
# Ils sont conçus pour être remplacés : déposez une vraie photo au même nom
# avec l'extension .webp ou .jpg dans le même dossier, et le build la
# préférera automatiquement (voir scripts/build.sh, resolution des images).
# ---------------------------------------------------------------------------

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "static" / "assets" / "images"

# --- Charte, alignée sur les jetons CSS ------------------------------------
NUIT_1, NUIT_2 = "#0F172A", "#16233D"
BLEU, BLEU_CLAIR, BLEU_PALE = "#0284C7", "#0EA5E9", "#38BDF8"
ORANGE, ORANGE_CLAIR = "#F97316", "#FDBA74"
ACIER_1, ACIER_2 = "#334155", "#1E293B"
CLAIR = "#E2E8F0"

L, H = 1200, 750          # format des visuels de carte (16/10)


def entete(titre: str, largeur=L, hauteur=H) -> str:
    """Fond commun : dégradé nuit, halo bleu, grille technique discrète."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largeur} {hauteur}" width="{largeur}" height="{hauteur}" role="img" aria-label="{titre}">
  <defs>
    <linearGradient id="fond" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{NUIT_2}"/><stop offset="1" stop-color="{NUIT_1}"/>
    </linearGradient>
    <radialGradient id="halo" cx="0.72" cy="0.18" r="0.75">
      <stop offset="0" stop-color="{BLEU_CLAIR}" stop-opacity="0.30"/>
      <stop offset="1" stop-color="{BLEU_CLAIR}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="acier" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#475569"/><stop offset="1" stop-color="{ACIER_2}"/>
    </linearGradient>
    <linearGradient id="cuivre" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{ORANGE_CLAIR}"/><stop offset="1" stop-color="#EA580C"/>
    </linearGradient>
    <linearGradient id="porte" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1E3A5F"/><stop offset="1" stop-color="#12233C"/>
    </linearGradient>
    <pattern id="grille" width="60" height="60" patternUnits="userSpaceOnUse">
      <path d="M60 0H0V60" fill="none" stroke="#ffffff" stroke-opacity="0.04" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="{largeur}" height="{hauteur}" fill="url(#fond)"/>
  <rect width="{largeur}" height="{hauteur}" fill="url(#grille)"/>
  <rect width="{largeur}" height="{hauteur}" fill="url(#halo)"/>'''


PIED = "\n</svg>\n"


# --- Primitives réutilisables ----------------------------------------------

def porte(x, y, w, h, entrouverte=False, blindee=False, panneaux=True):
    """Une porte dans son huisserie, vue de face."""
    s = f'<rect x="{x-14}" y="{y-14}" width="{w+28}" height="{h+14}" rx="6" fill="{ACIER_2}"/>'
    biais = ' transform="skewY(-0.9)"' if entrouverte else ''
    s += f'<g{biais}><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="url(#porte)"/>'
    if blindee:
        s += f'<rect x="{x+10}" y="{y+10}" width="{w-20}" height="{h-20}" rx="3" fill="none" stroke="{BLEU}" stroke-opacity="0.5" stroke-width="3"/>'
        for i in range(1, 5):
            s += f'<circle cx="{x+26}" cy="{y+40*i+20}" r="4" fill="{BLEU_PALE}" opacity="0.55"/>'
    if panneaux:
        s += (f'<rect x="{x+34}" y="{y+38}" width="{w-68}" height="{h*0.34:.0f}" rx="4" fill="none" stroke="{BLEU}" stroke-opacity="0.34" stroke-width="3"/>'
              f'<rect x="{x+34}" y="{y+h*0.46:.0f}" width="{w-68}" height="{h*0.44:.0f}" rx="4" fill="none" stroke="{BLEU}" stroke-opacity="0.34" stroke-width="3"/>')
    s += '</g>'
    return s


def cylindre(cx, cy, r=30, actif=True):
    """Un cylindre de serrure vu de face, avec son entrée de clé."""
    couleur = "url(#cuivre)" if actif else "url(#acier)"
    return (f'<circle cx="{cx}" cy="{cy}" r="{r+9}" fill="{ACIER_2}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{couleur}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r*0.34:.0f}" fill="{NUIT_1}"/>'
            f'<rect x="{cx-3}" y="{cy}" width="6" height="{r*0.8:.0f}" rx="3" fill="{NUIT_1}"/>')


def cle(x, y, angle=0, couleur="url(#cuivre)", echelle=1.0):
    """Une clé plate, anneau à gauche, panneton à droite."""
    return (f'<g transform="translate({x} {y}) rotate({angle}) scale({echelle})">'
            f'<circle cx="0" cy="0" r="26" fill="none" stroke="{couleur}" stroke-width="13"/>'
            f'<rect x="24" y="-6" width="112" height="12" rx="5" fill="{couleur}"/>'
            f'<rect x="104" y="-22" width="12" height="17" rx="3" fill="{couleur}"/>'
            f'<rect x="124" y="-26" width="12" height="21" rx="3" fill="{couleur}"/>'
            '</g>')


def poignee(cx, cy):
    return (f'<rect x="{cx-10}" y="{cy-46}" width="20" height="92" rx="10" fill="url(#acier)"/>'
            f'<rect x="{cx-34}" y="{cy-9}" width="42" height="18" rx="9" fill="url(#cuivre)"/>')


def sol(y, x1=60, x2=L-60):
    return f'<rect x="{x1}" y="{y}" width="{x2-x1}" height="14" rx="4" fill="#0A1120"/>'


def outil_tournevis(x, y, angle=-30):
    return (f'<g transform="translate({x} {y}) rotate({angle})">'
            f'<rect x="0" y="-9" width="86" height="18" rx="6" fill="url(#cuivre)"/>'
            f'<rect x="86" y="-5" width="80" height="10" rx="3" fill="#94A3B8"/>'
            f'<rect x="160" y="-7" width="16" height="14" rx="2" fill="{CLAIR}"/>'
            '</g>')


def crochet(x, y, angle=0):
    return (f'<g transform="translate({x} {y}) rotate({angle})" fill="none" stroke="{CLAIR}" '
            f'stroke-width="7" stroke-linecap="round">'
            f'<path d="M0 0 H92"/><path d="M92 0 q16 0 16 -14"/></g>')


def etincelles(cx, cy, couleur=ORANGE):
    return (f'<g stroke="{couleur}" stroke-width="6" stroke-linecap="round" opacity="0.8">'
            f'<path d="M{cx} {cy-46} v-26"/><path d="M{cx+38} {cy-32} l19 -19"/>'
            f'<path d="M{cx-38} {cy-32} l-19 -19"/></g>')


def caisse_outils(x, y):
    return (f'<g transform="translate({x} {y})">'
            f'<rect x="0" y="0" width="168" height="96" rx="10" fill="{ACIER_2}"/>'
            f'<rect x="0" y="-16" width="168" height="22" rx="9" fill="url(#cuivre)"/>'
            f'<rect x="66" y="-40" width="36" height="26" rx="8" fill="none" stroke="{ORANGE}" stroke-width="7"/>'
            f'<rect x="20" y="30" width="52" height="11" rx="5" fill="#64748B"/>'
            f'<rect x="20" y="56" width="88" height="11" rx="5" fill="#475569"/>'
            '</g>')


def lampe(x, y, vers_x, vers_y):
    return (f'<path d="M{x} {y} L{vers_x} {vers_y-70} L{vers_x} {vers_y+70} Z" fill="{ORANGE}" opacity="0.14"/>'
            f'<rect x="{x-46}" y="{y-13}" width="52" height="26" rx="8" fill="url(#acier)"/>'
            f'<rect x="{x+4}" y="{y-16}" width="14" height="32" rx="5" fill="url(#cuivre)"/>')


def badge_texte(x, y, texte, couleur=BLEU_PALE):
    largeur = 26 + len(texte) * 15
    return (f'<g transform="translate({x} {y})">'
            f'<rect x="0" y="0" width="{largeur}" height="46" rx="23" fill="{NUIT_1}" fill-opacity="0.72" '
            f'stroke="{couleur}" stroke-opacity="0.5" stroke-width="2"/>'
            f'<text x="{largeur/2:.0f}" y="31" text-anchor="middle" fill="{couleur}" '
            f'font-family="system-ui,sans-serif" font-size="22" font-weight="700" letter-spacing="1">{texte}</text>'
            '</g>')


# --- Les illustrations ------------------------------------------------------

def il_hero():
    """Visuel principal : porte d'entrée équipée, clé et outils au premier plan."""
    s = entete("Serrurier intervenant sur une porte d'entrée équipée d'une serrure de sécurité", 1100, 850)
    s += porte(330, 90, 420, 640, blindee=True)
    s += poignee(700, 430)
    s += cylindre(700, 500, 30)
    s += crochet(748, 500, 6)
    s += cle(180, 690, -14, echelle=1.05)
    s += caisse_outils(830, 636)
    s += etincelles(700, 470, BLEU_PALE)
    s += badge_texte(96, 96, "SERRURERIE", BLEU_PALE)
    s += sol(730, 60, 1040)
    return s + PIED


def il_ouverture_porte():
    s = entete("Ouverture d'une porte claquée à l'aide d'une feuille souple glissée le long du pêne")
    s += porte(300, 70, 380, 600)
    s += poignee(636, 380)
    s += cylindre(636, 452, 27)
    # Feuille souple engagée dans l'interstice
    s += f'<rect x="672" y="60" width="14" height="610" fill="{ORANGE}" opacity="0.22"/>'
    s += (f'<g transform="translate(694 402) rotate(-7)">'
          f'<rect width="176" height="112" rx="9" fill="#F8FAFC" opacity="0.95"/>'
          f'<rect width="176" height="24" rx="9" fill="{ORANGE}"/>'
          f'<rect x="16" y="46" width="96" height="9" rx="4" fill="#CBD5E1"/>'
          f'<rect x="16" y="68" width="136" height="9" rx="4" fill="#E2E8F0"/></g>')
    s += f'<path d="M694 430 L664 420" stroke="#F8FAFC" stroke-width="8" stroke-linecap="round"/>'
    s += badge_texte(80, 80, "SANS CASSE")
    s += sol(668, 60, 940)
    return s + PIED


def il_porte_bloquee():
    s = entete("Porte bloquée : la clé tourne dans le vide, le mécanisme est en cause")
    s += porte(340, 70, 400, 600)
    s += poignee(696, 380)
    s += cylindre(696, 452, 30, actif=False)
    s += cle(696, 452, 20, couleur="#94A3B8", echelle=0.55)
    # Symbole d'un mécanisme qui patine
    s += (f'<g transform="translate(880 300)" fill="none" stroke="{ORANGE}" stroke-width="9" stroke-linecap="round">'
          f'<path d="M0 0 a56 56 0 1 1 -40 96"/><path d="M-40 96 l-26 -14 M-40 96 l6 -28"/></g>')
    s += etincelles(696, 430)
    s += badge_texte(80, 80, "DIAGNOSTIC", ORANGE_CLAIR)
    s += sol(668, 60, 960)
    return s + PIED


def il_cle_cassee():
    s = entete("Fragment de clé cassée resté dans le cylindre, extraction à l'outil dédié")
    s += f'<circle cx="600" cy="380" r="240" fill="{BLEU}" opacity="0.07"/>'
    s += cylindre(600, 380, 128)
    # Fragment resté engagé
    s += f'<rect x="594" y="380" width="13" height="104" rx="5" fill="#94A3B8"/>'
    s += f'<path d="M600 484 l-9 22 l18 0 z" fill="#64748B"/>'
    # Extracteur
    s += (f'<g transform="translate(600 556) rotate(4)">'
          f'<rect x="-6" y="-90" width="12" height="230" rx="5" fill="url(#cuivre)"/>'
          f'<path d="M-6 -90 l-10 -20 h32 l-10 20z" fill="{ORANGE_CLAIR}"/></g>')
    # Moitié de clé restée en main
    s += cle(160, 600, -18, couleur="#94A3B8", echelle=0.85)
    s += f'<path d="M240 566 l26 -22" stroke="{ORANGE}" stroke-width="7" stroke-linecap="round"/>'
    s += badge_texte(80, 80, "EXTRACTION", ORANGE_CLAIR)
    return s + PIED


def il_cle_perdue():
    s = entete("Trousseau de clés perdu et remplacement du cylindre de la porte")
    s += porte(660, 70, 340, 600)
    s += poignee(956, 380)
    s += cylindre(956, 452, 27)
    # Trousseau qui s'éloigne
    s += f'<circle cx="300" cy="360" r="196" fill="{ORANGE}" opacity="0.07"/>'
    s += cle(250, 330, -22, echelle=0.95)
    s += cle(238, 430, 12, couleur="#94A3B8", echelle=0.8)
    s += (f'<g transform="translate(190 300)" fill="none" stroke="{ORANGE}" stroke-width="9" stroke-linecap="round" opacity="0.85">'
          f'<path d="M0 0 l-56 -46"/><path d="M-56 -46 l6 32 M-56 -46 l32 6"/></g>')
    s += badge_texte(80, 596, "NOUVEAU CYLINDRE", ORANGE_CLAIR)
    s += sol(668, 60, 1040)
    return s + PIED


def il_changement_serrure():
    s = entete("Remplacement du cylindre d'une serrure sur le chant d'une porte")
    s += f'<rect x="120" y="60" width="300" height="630" rx="6" fill="url(#porte)"/>'
    s += f'<rect x="420" y="60" width="64" height="630" fill="{ACIER_2}"/>'
    # Têtière et coffre de serrure
    s += f'<rect x="432" y="240" width="40" height="270" rx="6" fill="url(#acier)"/>'
    for i in range(3):
        s += f'<rect x="484" y="{276+96*i}" width="66" height="26" rx="7" fill="url(#cuivre)"/>'
    s += cylindre(330, 376, 34)
    s += outil_tournevis(560, 376, -18)
    s += caisse_outils(820, 570)
    # Cylindre neuf posé à côté
    s += (f'<g transform="translate(840 300)">'
          f'<rect width="200" height="72" rx="14" fill="url(#acier)"/>'
          f'<circle cx="52" cy="36" r="26" fill="url(#cuivre)"/>'
          f'<circle cx="52" cy="36" r="9" fill="{NUIT_1}"/>'
          f'<rect x="94" y="28" width="92" height="16" rx="6" fill="#475569"/></g>')
    s += badge_texte(820, 240, "PIÈCE NEUVE")
    s += sol(688, 60, 1040)
    return s + PIED


def il_installation_serrure():
    s = entete("Installation d'une serrure sur une porte, relevé des cotes et perçage")
    s += porte(300, 70, 420, 600, panneaux=False)
    # Tracé de pose, cotes
    s += (f'<g stroke="{BLEU_PALE}" stroke-width="3" stroke-dasharray="10 8" opacity="0.75" fill="none">'
          f'<path d="M300 400 H720"/><path d="M620 70 V670"/></g>')
    s += (f'<g stroke="{BLEU_PALE}" stroke-width="3" opacity="0.9">'
          f'<path d="M740 400 v-120 M732 292 l8 -14 8 14 M732 388 l8 14 8 -14"/></g>')
    s += f'<text x="768" y="352" fill="{BLEU_PALE}" font-family="system-ui,sans-serif" font-size="26" font-weight="700">axe</text>'
    s += cylindre(620, 400, 30)
    s += outil_tournevis(700, 470, 22)
    s += caisse_outils(200, 600)
    s += badge_texte(80, 80, "POSE SUR MESURE")
    s += sol(668, 60, 1040)
    return s + PIED


def il_serrure_3_points():
    s = entete("Serrure trois points : condamnation en haut, au centre et en bas de la porte")
    s += porte(320, 60, 420, 620, blindee=False, panneaux=False)
    s += f'<rect x="734" y="60" width="26" height="620" fill="{ACIER_2}"/>'
    for cy in (170, 370, 570):
        s += f'<rect x="740" y="{cy-17}" width="76" height="34" rx="10" fill="url(#cuivre)"/>'
        s += f'<circle cx="700" cy="{cy}" r="11" fill="{BLEU_PALE}" opacity="0.65"/>'
    # Tringlerie verticale
    s += f'<rect x="694" y="170" width="12" height="400" rx="6" fill="{BLEU}" opacity="0.5"/>'
    s += cylindre(640, 370, 30)
    s += badge_texte(80, 80, "3 POINTS")
    s += sol(678, 60, 1000)
    return s + PIED


def il_serrure_5_points():
    s = entete("Serrure cinq points répartis sur toute la hauteur d'une porte de grande dimension")
    s += porte(320, 40, 420, 660, blindee=False, panneaux=False)
    s += f'<rect x="734" y="40" width="26" height="660" fill="{ACIER_2}"/>'
    for cy in (120, 260, 380, 500, 636):
        s += f'<rect x="740" y="{cy-16}" width="76" height="32" rx="9" fill="url(#cuivre)"/>'
        s += f'<circle cx="700" cy="{cy}" r="10" fill="{BLEU_PALE}" opacity="0.65"/>'
    s += f'<rect x="694" y="120" width="12" height="516" rx="6" fill="{BLEU}" opacity="0.5"/>'
    s += cylindre(640, 380, 28)
    s += badge_texte(80, 80, "5 POINTS")
    s += sol(698, 60, 1000)
    return s + PIED


def il_porte_blindee():
    s = entete("Porte blindée équipée d'une serrure multipoints certifiée")
    s += porte(330, 60, 430, 620, blindee=True, panneaux=False)
    s += poignee(716, 370)
    s += cylindre(716, 452, 32)
    for cy in (150, 300, 450, 600):
        s += f'<rect x="762" y="{cy-15}" width="60" height="30" rx="9" fill="url(#cuivre)"/>'
    s += f'<rect x="756" y="150" width="10" height="450" rx="5" fill="{BLEU}" opacity="0.45"/>'
    s += badge_texte(80, 80, "HAUTE SÉCURITÉ")
    s += sol(678, 60, 1020)
    return s + PIED


def il_blindage_porte():
    s = entete("Blindage d'une porte existante : plaque d'acier, cornière anti-pince et gâches renforcées")
    s += porte(300, 60, 400, 620, panneaux=False)
    # Plaque d'acier plaquée, en cours de pose
    s += f'<rect x="316" y="76" width="368" height="588" rx="6" fill="url(#acier)" opacity="0.95"/>'
    s += (f'<g fill="{BLEU_PALE}" opacity="0.45">' +
          "".join(f'<circle cx="{cx}" cy="{cy}" r="6"/>'
                  for cx in (346, 654) for cy in range(120, 640, 74)) + '</g>')
    # Cornière anti-pince
    s += f'<rect x="690" y="60" width="30" height="620" rx="5" fill="url(#cuivre)"/>'
    s += badge_texte(748, 300, "CORNIÈRE", ORANGE_CLAIR)
    s += outil_tournevis(760, 470, 12)
    s += caisse_outils(180, 596)
    s += badge_texte(80, 80, "RENFORCEMENT")
    s += sol(678, 60, 1000)
    return s + PIED


def il_effraction():
    s = entete("Porte forcée après une effraction, remise en sécurité par un serrurier")
    s += porte(280, 60, 400, 620, entrouverte=True, panneaux=False)
    # Zone arrachée
    s += f'<rect x="656" y="330" width="52" height="140" rx="8" fill="{NUIT_1}"/>'
    s += (f'<path d="M656 356 l52 16 -52 18 52 16" fill="none" stroke="#DC2626" '
          f'stroke-width="7" stroke-linejoin="round"/>')
    s += (f'<g fill="#8a5a2b">'
          f'<path d="M712 300 l40 -14 -10 26z"/><path d="M718 372 l46 8 -34 18z"/>'
          f'<path d="M712 448 l32 24 -38 6z"/></g>')
    # Plaque de remise en sécurité
    s += (f'<g transform="translate(830 250)">'
          f'<rect width="180" height="240" rx="12" fill="#F8FAFC" opacity="0.95"/>'
          f'<rect width="180" height="34" rx="12" fill="#059669"/>'
          f'<circle cx="90" cy="150" r="42" fill="none" stroke="#059669" stroke-width="9"/>'
          f'<path d="M70 150 l15 16 30 -34" fill="none" stroke="#059669" stroke-width="9" '
          f'stroke-linecap="round" stroke-linejoin="round"/></g>')
    s += lampe(180, 220, 640, 380)
    s += badge_texte(80, 596, "MISE EN SÉCURITÉ", "#6EE7B7")
    s += sol(678, 60, 1040)
    return s + PIED


def il_coffre_fort():
    s = entete("Ouverture d'un coffre-fort dont le mécanisme est bloqué")
    s += f'<rect x="300" y="120" width="480" height="460" rx="18" fill="url(#acier)"/>'
    s += f'<rect x="326" y="146" width="428" height="408" rx="10" fill="#0F2C47"/>'
    s += f'<rect x="340" y="160" width="360" height="380" rx="8" fill="url(#porte)"/>'
    # Cadran
    s += f'<circle cx="470" cy="350" r="76" fill="{NUIT_1}"/>'
    s += f'<circle cx="470" cy="350" r="58" fill="none" stroke="url(#cuivre)" stroke-width="9"/>'
    s += (f'<g stroke="{BLEU_PALE}" stroke-width="5" stroke-linecap="round">'
          f'<path d="M470 286v16M470 398v16M406 350h16M518 350h16"/></g>')
    s += f'<circle cx="470" cy="350" r="15" fill="url(#cuivre)"/>'
    s += f'<path d="M470 350 l42 -32" stroke="#F8FAFC" stroke-width="9" stroke-linecap="round"/>'
    # Poignée et pênes
    s += f'<rect x="630" y="306" width="24" height="100" rx="12" fill="url(#cuivre)"/>'
    s += f'<circle cx="642" cy="356" r="26" fill="none" stroke="url(#cuivre)" stroke-width="11"/>'
    for cy in (230, 350, 470):
        s += f'<rect x="700" y="{cy-13}" width="56" height="26" rx="9" fill="url(#cuivre)"/>'
    # Stéthoscope d'auscultation
    s += (f'<g transform="translate(850 300)" fill="none" stroke="#F8FAFC" stroke-width="9" stroke-linecap="round">'
          f'<path d="M0 0 q46 66 4 122"/><circle cx="4" cy="140" r="23" fill="{NUIT_1}" stroke="url(#cuivre)"/></g>')
    s += badge_texte(80, 80, "OUVERTURE FINE")
    s += sol(580, 260, 820)
    return s + PIED


def il_rideau_metallique():
    s = entete("Rideau métallique de commerce bloqué, intervention de déblocage")
    s += f'<rect x="150" y="60" width="900" height="44" rx="6" fill="{ACIER_2}"/>'
    s += f'<rect x="168" y="104" width="864" height="12" fill="#1E3A5F"/>'
    s += f'<rect x="168" y="104" width="30" height="470" fill="{ACIER_2}"/>'
    s += f'<rect x="1002" y="104" width="30" height="470" fill="{ACIER_2}"/>'
    s += f'<rect x="198" y="116" width="804" height="300" fill="url(#acier)"/>'
    s += ('<g stroke="#26415A" stroke-width="3">' +
          "".join(f'<path d="M198 {y}h804"/>' for y in range(146, 416, 30)) + '</g>')
    s += f'<rect x="198" y="398" width="804" height="22" rx="5" fill="#2B4A66"/>'
    # Serrure centrale forcée
    s += f'<circle cx="600" cy="410" r="24" fill="{NUIT_1}"/>'
    s += f'<circle cx="600" cy="410" r="10" fill="url(#cuivre)"/>'
    s += (f'<g stroke="#DC2626" stroke-width="7" stroke-linecap="round">'
          f'<path d="M560 402 l-20 -18"/><path d="M640 402 l20 -18"/></g>')
    s += caisse_outils(760, 470)
    s += f'<path d="M300 574 v-84 h48" fill="none" stroke="url(#cuivre)" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>'
    s += badge_texte(80, 596, "COMMERCE", ORANGE_CLAIR)
    s += sol(574, 120, 1080)
    return s + PIED


def il_intervention():
    s = entete("Technicien serrurier au travail sur une porte, outils et matériel de sécurité")
    s += porte(220, 70, 360, 600, panneaux=False)
    s += poignee(546, 380)
    s += cylindre(546, 452, 28)
    s += crochet(590, 452, 5)
    s += outil_tournevis(640, 300, -26)
    s += caisse_outils(700, 560)
    s += cle(950, 250, -16, echelle=0.9)
    s += lampe(1080, 200, 620, 400)
    s += badge_texte(80, 80, "INTERVENTION")
    s += sol(668, 60, 1080)
    return s + PIED


def il_devis():
    s = entete("Devis de serrurerie détaillé remis avant intervention")
    s += (f'<g transform="translate(340 110) rotate(-3)">'
          f'<rect width="440" height="560" rx="16" fill="#F8FAFC"/>'
          f'<rect width="440" height="70" rx="16" fill="{BLEU}"/>'
          f'<rect x="40" y="120" width="240" height="16" rx="8" fill="#CBD5E1"/>'
          f'<rect x="40" y="158" width="360" height="12" rx="6" fill="#E2E8F0"/>')
    for i in range(5):
        y = 220 + i * 54
        s += (f'<rect x="40" y="{y}" width="200" height="13" rx="6" fill="#E2E8F0"/>'
              f'<rect x="308" y="{y}" width="92" height="13" rx="6" fill="{BLEU_PALE}" opacity="0.6"/>')
    s += (f'<rect x="40" y="500" width="140" height="18" rx="9" fill="{ACIER_1}"/>'
          f'<rect x="270" y="496" width="130" height="26" rx="13" fill="url(#cuivre)"/></g>')
    s += cle(900, 520, -18, echelle=0.9)
    s += badge_texte(80, 80, "AVANT TRAVAUX")
    return s + PIED


# id de fichier -> (dossier, fonction)
ILLUSTRATIONS = {
    "serrurerie/serrurier-intervention-porte-entree": il_hero,
    "ouverture-porte/serrurier-ouverture-porte-claquee": il_ouverture_porte,
    "porte-bloquee/diagnostic-porte-bloquee-serrure": il_porte_bloquee,
    "cle-cassee/extraction-cle-cassee-cylindre": il_cle_cassee,
    "cle-perdue/remplacement-cylindre-cles-perdues": il_cle_perdue,
    "serrure/remplacement-cylindre-serrure": il_changement_serrure,
    "installation/installation-serrure-porte": il_installation_serrure,
    "serrure-3-points/serrure-trois-points-porte": il_serrure_3_points,
    "serrure-5-points/serrure-cinq-points-porte": il_serrure_5_points,
    "porte-blindee/porte-blindee-serrure-multipoints": il_porte_blindee,
    "blindage/blindage-porte-corniere-anti-pince": il_blindage_porte,
    "effraction/securisation-porte-apres-effraction": il_effraction,
    "coffre-fort/ouverture-coffre-fort": il_coffre_fort,
    "rideau-metallique/deblocage-rideau-metallique-commerce": il_rideau_metallique,
    "interventions/serrurier-au-travail": il_intervention,
    "interventions/devis-serrurerie-detaille": il_devis,
}


if __name__ == "__main__":
    total = 0
    for chemin, fabrique in ILLUSTRATIONS.items():
        destination = SORTIE / f"{chemin}.svg"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(fabrique(), encoding="utf-8")
        total += destination.stat().st_size
        print(f"  {chemin}.svg  ({destination.stat().st_size // 1024} Ko)")
    print(f"\n{len(ILLUSTRATIONS)} illustrations, {total // 1024} Ko au total.")
