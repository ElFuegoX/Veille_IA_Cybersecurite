#!/usr/bin/env python3
"""P2 (2.5) : compare les notes automatiques (04_qualite.py) aux notes humaines.

Référence humaine : data/reference_humaine.csv (séparateur , ou ; détecté).
Les articles sont rapprochés par lien, sinon par titre (les id diffèrent).
Le total humain est recalculé à partir des 5 notes (pertinence 0-3, autres 0-2 : /11).

Mesures, par critère : accord exact, accord à 1 point près, écart moyen
(automatique - humain : positif = script plus généreux). Puis accord sur la décision
« garder pour l'analyse » (pertinence >= seuil), accord sur le niveau
(fiable / prudence / écarté, seuils de config/grille_qualite.yaml) avec le kappa
de Cohen, et la liste des désaccords à examiner pour ajuster la grille.

  --remplir-echantillon   ajoute d'abord à --csv les articles de la référence qui
                          n'y sont pas (titre, lien, source, date), puis s'arrête.
                          Ensuite : 02_extraction.py puis 04_qualite.py sur --csv.

Usage : python scripts/05_evaluer_qualite.py [--csv data/echantillon.csv]
                                             [--reference data/reference_humaine.csv]
"""
import argparse
import csv
import re
import sys
from collections import Counter
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml

from commun import (
    DOSSIER_CONFIG, DOSSIER_DATA, cle_lien, cle_titre, ecrire_csv, formater_id, lire_csv,
    prochain_id,
)

CRITERES = ["craap_actualite", "craap_pertinence", "craap_autorite",
            "craap_exactitude", "craap_objectif"]
NOMS = {"craap_actualite": "Actualité", "craap_pertinence": "Pertinence 0-3",
        "craap_autorite": "Autorité", "craap_exactitude": "Exactitude",
        "craap_objectif": "Objectif", "craap_total": "Total /11"}
NIVEAUX = ["fiable", "prudence", "écarté"]

with open(DOSSIER_CONFIG / "grille_qualite.yaml", encoding="utf-8") as _f:
    GRILLE = yaml.safe_load(_f)
SEUILS = GRILLE["seuils_craap"]
SEUIL_ANALYSE = GRILLE["pertinence"]["seuil_analyse"]


def lire_reference(chemin):
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        echantillon = f.read(4096)
        f.seek(0)
        sep = ";" if echantillon.count(";") > echantillon.count(",") else ","
        lignes = [{k.strip(): (v or "").strip() for k, v in r.items() if k}
                  for r in csv.DictReader(f, delimiter=sep)]

    def entier(v):
        return int(v) if re.fullmatch(r"\d+", v or "") else None

    for r in lignes:
        notes = {c: entier(r.get(c)) for c in CRITERES}
        complet = all(v is not None for v in notes.values())
        notes["craap_total"] = sum(notes.values()) if complet else None
        r["_notes"] = notes
    return lignes


def cle(r):
    return cle_lien(r.get("lien", "")) or "t:" + cle_titre(r.get("titre", ""))


def date_iso(texte):
    texte = (texte or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y", "%B %d, %Y", "%d-%b-%y", "%d %B %Y"):
        try:
            return datetime.strptime(texte, fmt).date().isoformat()
        except ValueError:
            pass
    mois = {"janv": "jan", "févr": "feb", "mars": "mar", "avr": "apr", "mai": "may",
            "juin": "jun", "juil": "jul", "août": "aug", "sept": "sep", "oct": "oct",
            "nov": "nov", "déc": "dec"}
    m = re.fullmatch(r"(\d{1,2})-([a-zéû]+)\.?-(\d{2})", texte.lower())
    if m and m.group(2) in mois:
        return date_iso(f"{m.group(1)}-{mois[m.group(2)]}-{m.group(3)}")
    return ""


def remplir_echantillon(chemin, reference):
    lignes = lire_csv(chemin)
    connues = {cle(r) for r in lignes}
    n = prochain_id(lignes)
    ajouts = 0
    for ref in reference:
        if cle(ref) in connues:
            continue
        ligne = {k: "" for k in lignes[0]} if lignes else {}
        ligne.update({
            "id": formater_id(n), "titre": ref.get("titre", ""), "lien": ref.get("lien", ""),
            "source": ref.get("source", "").rsplit(" / ", 1)[-1],
            "date_publication": date_iso(ref.get("date", "")),
        })
        lignes.append(ligne)
        connues.add(cle(ref))
        n += 1
        ajouts += 1
    ecrire_csv(chemin, lignes)
    print(f"{ajouts} article(s) ajouté(s) à {chemin}.")
    print("Étapes suivantes : 02_extraction.py puis 04_qualite.py avec --csv", chemin)


def niveau(total, pertinence=None):
    if pertinence is not None and int(pertinence) < SEUIL_ANALYSE:
        return "écarté"
    if total is None:
        return None
    return "fiable" if total >= SEUILS["fiable"] else "prudence" if total >= SEUILS["prudence"] else "écarté"


def kappa(paires):
    n = len(paires)
    if not n:
        return None
    accord = sum(a == h for a, h in paires) / n
    ca, ch = Counter(a for a, _ in paires), Counter(h for _, h in paires)
    hasard = sum(ca[k] * ch[k] for k in NIVEAUX) / (n * n)
    return None if hasard == 1 else (accord - hasard) / (1 - hasard)


def pct(x, n):
    return f"{100 * x / n:5.1f} %" if n else "   – "


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--csv", default=str(DOSSIER_DATA / "echantillon.csv"))
    ap.add_argument("--reference", default=str(DOSSIER_DATA / "reference_humaine.csv"))
    ap.add_argument("--remplir-echantillon", action="store_true")
    args = ap.parse_args()

    reference = lire_reference(args.reference)
    if args.remplir_echantillon:
        remplir_echantillon(args.csv, reference)
        return

    auto = {cle(r): r for r in lire_csv(args.csv) if r["craap_total"]}
    paires = [(auto[cle(h)], h) for h in reference if cle(h) in auto]
    print(f"Référence : {len(reference)} article(s)")
    print(f"Notés automatiquement et rapprochés : {len(paires)}\n")
    if not paires:
        print("Aucun article commun : lancer d'abord --remplir-echantillon, 02 puis 04.")
        return

    print(f"{'Critère':<20} {'n':>3}  {'exact':>7}  {'±1 pt':>7}  {'écart moyen':>11}")
    for c in CRITERES + ["craap_total"]:
        ecarts = [int(a[c]) - h["_notes"][c] for a, h in paires
                  if a.get(c, "").isdigit() and h["_notes"][c] is not None]
        n = len(ecarts)
        if not n:
            continue
        exact = sum(e == 0 for e in ecarts)
        proche = sum(abs(e) <= (1 if c != "craap_total" else 2) for e in ecarts)
        print(f"{NOMS[c]:<20} {n:>3}  {pct(exact, n)}  {pct(proche, n)}  {sum(ecarts) / n:+11.2f}")
    print("(pour le total : « ±1 pt » signifie à 2 points près)\n")

    # Décision « garder pour l'analyse » (pertinence >= seuil)
    garde = [(int(a["craap_pertinence"]) >= SEUIL_ANALYSE,
              h["_notes"]["craap_pertinence"] >= SEUIL_ANALYSE) for a, h in paires
             if a["craap_pertinence"].isdigit() and h["_notes"]["craap_pertinence"] is not None]
    if garde:
        print(f"Décision pertinence >= {SEUIL_ANALYSE} (garder / exclure) : "
              f"accord {pct(sum(x == y for x, y in garde), len(garde))}"
              f" sur {len(garde)} article(s)\n")

    niv = [(niveau(int(a["craap_total"]), int(a["craap_pertinence"])),
            niveau(h["_notes"]["craap_total"], h["_notes"]["craap_pertinence"])) for a, h in paires
           if h["_notes"]["craap_total"] is not None]
    if niv:
        print("Niveau CRAAP (lignes : automatique, colonnes : humain)")
        print(" " * 12 + "".join(f"{k:>10}" for k in NIVEAUX))
        mat = Counter(niv)
        for a in NIVEAUX:
            print(f"{a:<12}" + "".join(f"{mat[(a, h)]:>10}" for h in NIVEAUX))
        k = kappa(niv)
        print(f"Accord : {pct(sum(x == y for x, y in niv), len(niv))} ; kappa de Cohen : "
              + (f"{k:.2f}" if k is not None else "non calculable") + "\n")

    print("Désaccords à examiner (niveau différent ou total à 3 points ou plus) :")
    vus = 0
    for a, h in paires:
        th = h["_notes"]["craap_total"]
        ta = int(a["craap_total"])
        niv_a = niveau(ta, int(a["craap_pertinence"]))
        niv_h = niveau(th, h["_notes"]["craap_pertinence"])
        if th is None or (niv_a == niv_h and abs(ta - th) < 3):
            continue
        vus += 1
        detail = "  ".join(
            f"{NOMS[c].split()[0][:4]} {a[c]}/{h['_notes'][c] if h['_notes'][c] is not None else '?'}"
            for c in CRITERES)
        print(f"- {a['id']} {a['titre'][:70]}\n    total {ta}/{th}  ({detail})  [auto/humain]")
    if not vus:
        print("  aucun")


if __name__ == "__main__":
    main()
