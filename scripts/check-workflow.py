#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Contrôle du workflow de publication.
#
#   python3 scripts/check-workflow.py
#
# Un workflow ne se teste qu'en le poussant : l'erreur ne se voit qu'après
# coup, et pendant ce temps la branche deploy reste figée — le site en ligne
# aussi. Ce contrôle attrape en local les fautes qui coûtent un aller-retour.
#
# Il est né d'une panne réelle : l'ajout d'un bloc « env: » au niveau du job
# avait fait perdre au pas de publication son GITHUB_TOKEN, et la poussée
# échouait sur « Password authentication is not supported ».
# ---------------------------------------------------------------------------

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML est absent. Installez-le : pip install pyyaml")

RACINE = Path(__file__).resolve().parent.parent
FICHIER = RACINE / ".github" / "workflows" / "deploy.yml"
V, X = "\033[32mv\033[0m", "\033[31mx\033[0m"


def main() -> int:
    if not FICHIER.is_file():
        print(f"{X} {FICHIER.relative_to(RACINE)} est absent.")
        return 1

    try:
        doc = yaml.safe_load(FICHIER.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"{X} YAML invalide : {e}")
        return 1

    defauts = []
    jobs = doc.get("jobs") or {}
    if not jobs:
        defauts.append("aucun job défini")

    for nom, job in jobs.items():
        pas = job.get("steps") or []
        if not pas:
            defauts.append(f"{nom} : aucun pas")
            continue

        for p in pas:
            script = p.get("run") or ""
            env_pas = set(p.get("env") or {})
            env_job = set(job.get("env") or {})
            titre = p.get("name", "(sans nom)")

            # Toute variable lue par un script doit être fournie quelque part.
            for variable in ("GITHUB_TOKEN", "FTP_HOST", "FTP_USER", "FTP_PASS"):
                if f"${{{variable}}}" in script or f"${variable}" in script:
                    if variable not in env_pas | env_job:
                        defauts.append(
                            f"« {titre} » lit {variable} sans qu'il soit "
                            f"fourni par env (ni au pas, ni au job)"
                        )

            if "if" in p and "secrets." in str(p["if"]):
                defauts.append(
                    f"« {titre} » : « if » ne peut pas lire secrets.* "
                    f"directement, passer par env"
                )

    print("\033[1mContrôle du workflow de publication\033[0m")
    if defauts:
        for d in defauts:
            print(f"  {X} {d}")
        return 1
    print(f"  {V} YAML valide, et chaque variable lue est bien fournie.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
