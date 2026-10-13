#!/usr/bin/env python3
"""P3 : nb_sources_reprise, score_notabilite, cas_retenu.

Contrairement aux autres scripts, tout est RECALCULÉ à chaque exécution :
le nombre de reprises évolue quand le corpus grossit.
Dépendance : rapidfuzz.

Reprise = un autre éditeur traite la même histoire (titre proche ou CVE commune).
Les reprises sont comptées sur tout le corpus ; seules les lignes pertinentes
(craap_pertinence >= SEUIL_PERTINENCE) reçoivent une note.
Score (0 à 11) :
  + min(nb_sources_reprise, 5)
  + 3 si une CVE citée est dans le catalogue KEV, sinon +1 si une CVE est citée
  + 1 si une entreprise est citée
  + 2 si craap_total >= SEUIL_CRAAP
cas_retenu = "oui" si score >= SEUIL_CAS, ou si c'est le meilleur article de son
sous-thème (au moins un cas illustré par sous-thème pour la section 5 du rapport).
Usage : python scripts/08_notabilite.py [--csv chemin]
"""
import argparse
import os
import re

from rapidfuzz import fuzz

from commun import DOSSIER_DATA, cle_titre, domaine, ecrire_csv, lire_csv, pertinence_ok

SEUIL_TITRE = 70       # similarité de titres (0-100) ; à revérifier quand le corpus grossit
SEUIL_CAS = 8          # score minimal pour retenir un cas
SEUIL_CRAAP = 8        # craap_total donnant +2 (à confirmer avec P2 : échelle sur 11)
MAX_CVES_APPARIEMENT = 3   # au-delà (revue de la semaine...), les CVE ne servent plus à apparier
SOUS_THEMES = ["S1", "S2", "S3", "S4", "S5", "S6"]
COLS_P3 = ("nb_sources_reprise", "score_notabilite", "cas_retenu")


def nombre(valeur):
    try:
        return float(str(valeur).replace(",", "."))
    except ValueError:
        return 0.0


def editeur(r):
    """Clé d'éditeur : « The Hacker News » et « thehackernews.com » donnent la même clé,
    « KnowBe4 Blog » et « blog.knowbe4.com » aussi (lettres triées, extension retirée)."""
    brut = (domaine(r.get("lien", "")) or r.get("source", "")).lower()
    brut = re.sub(r"\.(com|org|net|io|ai|gov|fr|co\.uk|co)$", "", brut.strip())
    return "".join(sorted(re.sub(r"[^a-z0-9]", "", brut)))


def cves_de(r):
    return {c for c in r.get("cves", "").split(";") if c}


def calculer_reprises(articles):
    """Pour chaque article : nombre d'autres éditeurs qui traitent la même histoire."""
    cles = [cle_titre(r["titre"]) for r in articles]
    eds = [editeur(r) for r in articles]
    cves = [c if len(c) <= MAX_CVES_APPARIEMENT else set()
            for c in (cves_de(r) for r in articles)]
    reprises = []
    for i in range(len(articles)):
        autres = set()
        for j in range(len(articles)):
            if i == j or not eds[j] or eds[j] == eds[i]:
                continue
            if (cves[i] & cves[j]) or fuzz.token_sort_ratio(cles[i], cles[j]) >= SEUIL_TITRE:
                autres.add(eds[j])
        reprises.append(len(autres))
    return reprises


def score(r, nb):
    s = min(nb, 5)
    if r.get("cve_kev") == "oui":
        s += 3
    elif r.get("cves"):
        s += 1
    if r.get("entreprises"):
        s += 1
    if nombre(r.get("craap_total", "")) >= SEUIL_CRAAP:
        s += 2
    return s


def num_id(r):
    return int(r["id"]) if str(r["id"]).isdigit() else 0


def traiter(chemin):
    lignes = lire_csv(chemin)
    # reprises : sur tout le corpus, pour ne pas sous-compter les histoires très reprises
    nb_par_id = {r["id"]: nb for r, nb in zip(lignes, calculer_reprises(lignes))}

    eligibles = [r for r in lignes if pertinence_ok(r)]
    for r in lignes:  # une ligne devenue non pertinente ne garde pas d'anciennes valeurs
        if not pertinence_ok(r):
            for c in COLS_P3:
                r[c] = ""

    scores = {}
    for r in eligibles:
        scores[r["id"]] = score(r, nb_par_id[r["id"]])
        r["nb_sources_reprise"] = str(nb_par_id[r["id"]])
        r["score_notabilite"] = str(scores[r["id"]])

    retenus = {r["id"] for r in eligibles
               if scores[r["id"]] >= SEUIL_CAS and r.get("theme_principal")}
    for theme in SOUS_THEMES:
        candidats = [r for r in eligibles if r.get("theme_principal") == theme]
        if candidats:
            # à score égal : meilleur CRAAP, puis article le plus ancien (id le plus bas)
            meilleur = max(candidats, key=lambda r: (scores[r["id"]],
                                                     nombre(r.get("craap_total", "")),
                                                     -num_id(r)))
            retenus.add(meilleur["id"])
    for r in eligibles:
        r["cas_retenu"] = "oui" if r["id"] in retenus else "non"

    # relecture juste avant l'écriture : on ne met à jour que mes trois colonnes
    mes_valeurs = {r["id"]: {c: r[c] for c in COLS_P3} for r in lignes}
    frais = lire_csv(chemin)
    for r in frais:
        if r["id"] in mes_valeurs:
            r.update(mes_valeurs[r["id"]])
    ecrire_csv(chemin, frais)
    print(f"{len(eligibles)} article(s) notés, {len(retenus)} cas retenu(s).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--csv", default=str(DOSSIER_DATA / "echantillon.csv"))
    a = ap.parse_args()
    if os.path.basename(a.csv) == "articles.csv" and not os.environ.get("GITHUB_ACTIONS"):
        raise SystemExit("articles.csv n'est modifié que par les workflows.")
    traiter(a.csv)


if __name__ == "__main__":
    main()