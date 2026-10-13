#!/usr/bin/env python3
"""P3 : CVE citées, entreprises citées, confirmation dans le catalogue CISA KEV.

Rejouable : ne traite que les lignes où cve_kev est vide (valeurs : aucun, oui, non).
Pas de clé API. Usage : python scripts/07_cve.py [--csv chemin]
Note : 04_qualite.py (P2) a sa propre regex CVE, volontairement indépendante.
"""
import argparse
import os
import re
import sys

import requests

from commun import DOSSIER_CONFIG, DOSSIER_DATA, DOSSIER_TEXTES, ecrire_csv, lire_csv, norm_id, pertinence_ok

URL_KEV = ("https://www.cisa.gov/sites/default/files/feeds/"
           "known_exploited_vulnerabilities.json")
RE_CVE = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)


def extraire_cves(texte):
    texte = (texte or "")
    for tiret in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"):
        texte = texte.replace(tiret, "-")
    return sorted({m.upper() for m in RE_CVE.findall(texte)})


def charger_entreprises():
    chemin = DOSSIER_CONFIG / "entreprises.txt"
    if not chemin.exists():
        return []
    motifs = []
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#"):
            continue
        noms = [n.strip() for n in ligne.split("|") if n.strip()]
        alternatives = "|".join(re.escape(n) for n in noms)
        motifs.append((noms[0], re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)")))
    return motifs


def extraire_entreprises(texte, motifs):
    return sorted({nom for nom, rx in motifs if rx.search(texte or "")})


def charger_kev():
    """Ensemble des CVE du catalogue KEV, ou None si le téléchargement échoue."""
    try:
        r = requests.get(URL_KEV, timeout=60)
        r.raise_for_status()
        return {v["cveID"].upper() for v in r.json()["vulnerabilities"]}
    except Exception as e:
        print(f"KEV indisponible ({e}) : cve_kev laissé vide.", file=sys.stderr)
        return None


def contenu(r):
    """Titre + résumé + texte complet s'il existe (le texte reste local)."""
    p = DOSSIER_TEXTES / f"{norm_id(r['id'])}.txt"
    texte = p.read_text(encoding="utf-8") if p.exists() else ""
    return f"{r.get('titre', '')} {r.get('resume', '')} {texte}"


def traiter(chemin, tout=False):
    lignes = lire_csv(chemin)
    a_faire = [r for r in lignes if pertinence_ok(r) and (tout or not (r.get("cve_kev") or "").strip())]
    print(f"{len(a_faire)} article(s) à traiter dans {chemin}")
    motifs = charger_entreprises()
    kev = "inconnu"
    nouveaux = {}
    for r in a_faire:
        texte = contenu(r)
        cves = extraire_cves(texte)
        v = {"cves": ";".join(cves),
             "entreprises": ";".join(extraire_entreprises(texte, motifs)),
             "cve_kev": "aucun"}
        if cves:
            if kev == "inconnu":
                kev = charger_kev()
            if kev is None:
                v["cve_kev"] = ""  # sera recalculé à la prochaine exécution
            else:
                v["cve_kev"] = "oui" if any(c in kev for c in cves) else "non"
        nouveaux[r["id"]] = v
    if nouveaux:
        lignes = lire_csv(chemin)  # relecture juste avant l'écriture
        for r in lignes:
            if r["id"] in nouveaux:
                r.update(nouveaux[r["id"]])
        ecrire_csv(chemin, lignes)
    print(f"{len(nouveaux)} article(s) mis à jour.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=str(DOSSIER_DATA / "echantillon.csv"))
    ap.add_argument("--tout", action="store_true", help="recalcule aussi les lignes déjà traitées")
    a = ap.parse_args()
    if os.path.basename(a.csv) == "articles.csv" and not os.environ.get("GITHUB_ACTIONS"):
        raise SystemExit("articles.csv n'est modifié que par les workflows.")
    traiter(a.csv, a.tout)


if __name__ == "__main__":
    main()