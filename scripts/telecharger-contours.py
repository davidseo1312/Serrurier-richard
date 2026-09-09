#!/usr/bin/env python3
"""
Télécharge et simplifie les contours des départements desservis.

    python3 scripts/telecharger-contours.py

À ne lancer QUE si src/zones.conf gagne ou perd un département : les contours
obtenus sont versionnés dans src/geo/, si bien que la construction du site ne
demande ni réseau ni Python. Après ce script, relancez :

    python3 scripts/generer-carte.py
    bash scripts/build.sh

SOURCE DES DONNÉES
------------------
Projet france-geojson de Grégoire David, conversion GeoJSON de la base
Admin Express de l'IGN. Licence ouverte (Etalab) : réutilisation libre, y
compris commerciale, à condition de mentionner la source — ce que fait la
légende de la carte et la présente en-tête.

SIMPLIFICATION
--------------
Algorithme de Douglas-Peucker, tolérance 0,012° soit environ 900 m. À la
largeur d'affichage de la carte (900 unités pour près de 400 km), cela
représente à peu près 2 pixels : la différence avec le tracé d'origine n'est
pas perceptible, et le fichier pèse 40 % de moins.

Les îlots de moins de 40 km² sont retirés : à cette échelle ils ne
représentent qu'un ou deux pixels, et alourdissent le fichier sans rien
apprendre au visiteur.
"""

import json
import math
import os
import sys
import urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINATION = os.path.join(RACINE, "src", "geo")
BASE = ("https://raw.githubusercontent.com/gregoiredavid/france-geojson"
        "/master/departements")

TOLERANCE = 0.012      # degrés, soit environ 900 m
AIRE_MINIMALE = 0.004  # degrés carrés, soit environ 40 km²

# Le nom de dossier du projet source n'est pas déductible du seul code : il
# est donné ici, une fois pour toutes.
DOSSIERS = {
    "22": "22-cotes-d-armor",
    "29": "29-finistere",
    "35": "35-ille-et-vilaine",
    "44": "44-loire-atlantique",
    "49": "49-maine-et-loire",
    "56": "56-morbihan",
}


def distance_au_segment(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def douglas_peucker(points, tolerance):
    if len(points) < 3:
        return points
    ecart_max, indice = 0, 0
    for i in range(1, len(points) - 1):
        d = distance_au_segment(points[i], points[0], points[-1])
        if d > ecart_max:
            ecart_max, indice = d, i
    if ecart_max > tolerance:
        return (douglas_peucker(points[:indice + 1], tolerance)[:-1]
                + douglas_peucker(points[indice:], tolerance))
    return [points[0], points[-1]]


def aire(anneau):
    total = 0
    for i in range(len(anneau) - 1):
        total += anneau[i][0] * anneau[i + 1][1] - anneau[i + 1][0] * anneau[i][1]
    return abs(total) / 2


def codes_demandes():
    """Les départements réellement déclarés dans src/zones.conf."""
    codes = []
    with open(os.path.join(RACINE, "src", "zones.conf"), encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or ligne.startswith("VILLE|"):
                continue
            codes.append(ligne.split("|")[0])
    return codes


def main():
    sys.setrecursionlimit(20000)
    os.makedirs(DESTINATION, exist_ok=True)

    for code in codes_demandes():
        dossier = DOSSIERS.get(code)
        if not dossier:
            sys.exit(
                f"Département {code} inconnu de ce script. Ajoutez son nom de "
                f"dossier dans DOSSIERS, en le relevant sur\n  {BASE}/"
            )

        url = f"{BASE}/{dossier}/departement-{dossier}.geojson"
        with urllib.request.urlopen(url, timeout=60) as reponse:
            geometrie = json.loads(reponse.read())["geometry"]

        polygones = (geometrie["coordinates"]
                     if geometrie["type"] == "MultiPolygon"
                     else [geometrie["coordinates"]])

        contours = []
        for polygone in polygones:
            exterieur = polygone[0]
            if aire(exterieur) < AIRE_MINIMALE:
                continue
            simplifie = douglas_peucker([tuple(p) for p in exterieur], TOLERANCE)
            if len(simplifie) >= 4:
                contours.append(simplifie)

        if not contours:
            sys.exit(f"Aucun contour exploitable pour le département {code}.")

        chemin = os.path.join(DESTINATION, f"{code}.json")
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(contours, f, separators=(",", ":"))

        points = sum(len(c) for c in contours)
        print(f"  {code} : {len(contours)} contour(s), {points} points, "
              f"{os.path.getsize(chemin)} octets")

    print("\nContours écrits dans src/geo/. Relancez maintenant :")
    print("  python3 scripts/generer-carte.py && bash scripts/build.sh")


if __name__ == "__main__":
    main()
