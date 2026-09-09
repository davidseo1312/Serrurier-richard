#!/usr/bin/env python3
"""
Génère la carte des zones d'intervention, au format SVG, dans
src/partials/carte-zones.svg.

POURQUOI UNE CARTE MAISON PLUTÔT QU'UNE CARTE EN LIGNE
------------------------------------------------------
Une carte à tuiles (Google Maps, OpenStreetMap…) envoie l'adresse IP de
chaque visiteur à un tiers dès l'affichage de la page, ce qui relève du
consentement préalable. Elle ajoute aussi 200 à 400 Ko et une dizaine de
requêtes réseau sur une page dont l'enjeu est la vitesse.

Cette carte-ci est un simple SVG servi par le site : aucune requête tierce,
aucune donnée personnelle transmise, environ 30 Ko, et elle s'affiche même
sans JavaScript. La carte à tuiles reste disponible, mais uniquement si le
visiteur la demande explicitement (voir static/assets/js/site.js).

DONNÉES
-------
Contours : IGN, base Admin Express, via le projet france-geojson de Grégoire
David — Licence ouverte (Etalab). Simplifiés à environ 450 m de tolérance,
ce qui est invisible à l'échelle d'affichage.
Villes et départements : src/zones.conf, source unique du site.
"""

import json
import math
import os
import sys
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "src", "partials", "carte-zones.svg")

LARGEUR = 900          # unités du viewBox ; le SVG est ensuite fluide en CSS
MARGE = 34             # laisse la place aux étiquettes des villes de bord


def lire_conf():
    departements, villes = [], []
    chemin = os.path.join(RACINE, "src", "zones.conf")
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#"):
                continue
            champs = ligne.split("|")
            if champs[0] == "VILLE":
                villes.append({
                    "nom": champs[1],
                    "lat": float(champs[2]),
                    "lon": float(champs[3]),
                    "dep": champs[4],
                    "etiquette": champs[5] == "1",
                })
            else:
                departements.append({
                    "code": champs[0], "nom": champs[1], "url": champs[2],
                })
    if not departements:
        sys.exit("src/zones.conf ne déclare aucun département.")
    return departements, villes


def echapper(texte):
    return (texte.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))


def identifiant(texte):
    """Un identifiant HTML sûr, sans accent ni espace."""
    sans = unicodedata.normalize("NFD", texte)
    sans = "".join(c for c in sans if unicodedata.category(c) != "Mn")
    return "".join(c if c.isalnum() else "-" for c in sans.lower()).strip("-")


def main():
    departements, villes = lire_conf()

    contours = {}
    for dep in departements:
        chemin = os.path.join(RACINE, "src", "geo", f"{dep['code']}.json")
        if not os.path.isfile(chemin):
            sys.exit(f"Contour manquant : {chemin}")
        contours[dep["code"]] = json.load(open(chemin, encoding="utf-8"))

    # --- Projection ---------------------------------------------------------
    # Équirectangulaire centrée sur la latitude moyenne de la zone : à cette
    # échelle (moins de 300 km), la déformation est inférieure au pixel.
    tous = [p for rings in contours.values() for r in rings for p in r]
    lon_min = min(p[0] for p in tous); lon_max = max(p[0] for p in tous)
    lat_min = min(p[1] for p in tous); lat_max = max(p[1] for p in tous)
    k = math.cos(math.radians((lat_min + lat_max) / 2))

    largeur_geo = (lon_max - lon_min) * k
    hauteur_geo = lat_max - lat_min
    echelle = (LARGEUR - 2 * MARGE) / largeur_geo
    hauteur = round(hauteur_geo * echelle + 2 * MARGE)

    def projeter(lon, lat):
        x = MARGE + (lon - lon_min) * k * echelle
        y = MARGE + (lat_max - lat) * echelle
        return round(x, 1), round(y, 1)

    # --- Tracés -------------------------------------------------------------
    morceaux = []
    for rang, dep in enumerate(departements):
        chemins = []
        for anneau in contours[dep["code"]]:
            points = [projeter(lon, lat) for lon, lat in anneau]
            chemins.append("M" + "L".join(f"{x},{y}" for x, y in points) + "Z")
        libelle = f"{dep['nom']} ({dep['code']})"
        morceaux.append(
            f'    <a class="zone" href="{echapper(dep["url"])}" '
            f'id="zone-{dep["code"]}" data-teinte="{rang % 6 + 1}" '
            f'aria-label="Serrurier en {echapper(libelle)}">\n'
            f'      <title>{echapper(libelle)} — voir la page</title>\n'
            f'      <path d="{" ".join(chemins)}"/>\n'
            f"    </a>"
        )

    points_villes, etiquettes = [], []
    for ville in villes:
        if ville["dep"] not in contours:
            sys.exit(f"La ville {ville['nom']} vise un département absent de la carte.")
        x, y = projeter(ville["lon"], ville["lat"])
        rayon = 5 if ville["etiquette"] else 3.2
        points_villes.append(
            f'    <circle class="ville{" ville-forte" if ville["etiquette"] else ""}" '
            f'cx="{x}" cy="{y}" r="{rayon}"/>'
        )
        if ville["etiquette"]:
            # Les villes de la façade ouest reçoivent leur étiquette à gauche,
            # sinon elle sortirait du cadre.
            a_gauche = x > LARGEUR * 0.62
            dx, ancre = (-10, "end") if a_gauche else (10, "start")
            etiquettes.append(
                f'    <text class="etiquette" x="{round(x + dx, 1)}" y="{round(y + 4, 1)}" '
                f'text-anchor="{ancre}">{echapper(ville["nom"])}</text>'
            )

    liste = ", ".join(f"{d['nom']} ({d['code']})" for d in departements)
    description = (
        f"Carte des départements où Serrurier Richard intervient : {liste}. "
        "Chaque département est cliquable et renvoie vers sa page."
    )

    svg = f"""<svg class="carte-svg" viewBox="0 0 {LARGEUR} {hauteur}"
     xmlns="http://www.w3.org/2000/svg" role="img"
     aria-labelledby="carte-titre carte-desc">
  <title id="carte-titre">Zones d'intervention de Serrurier Richard</title>
  <desc id="carte-desc">{echapper(description)}</desc>

  <g class="zones">
{chr(10).join(morceaux)}
  </g>

  <g class="villes" aria-hidden="true">
{chr(10).join(points_villes)}
{chr(10).join(etiquettes)}
  </g>
</svg>
"""

    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    with open(SORTIE, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Carte écrite : {os.path.relpath(SORTIE, RACINE)} "
          f"({os.path.getsize(SORTIE) // 1024} Ko, {LARGEUR}×{hauteur}, "
          f"{len(departements)} départements, {len(villes)} villes)")


if __name__ == "__main__":
    main()
