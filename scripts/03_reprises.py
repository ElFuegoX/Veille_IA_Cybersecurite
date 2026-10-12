#!/usr/bin/env python3
"""P1 (1.5) : compte combien de sources reprennent la même histoire (nb_sources_reprise).

Version prudente, fondée uniquement sur la similarité des titres : deux articles
de SOURCES DIFFÉRENTES racontent la même histoire si leurs titres sont très proches
(et, quand les deux dates sont connues, publiés à moins de 7 jours d'écart).
Aucun article n'est supprimé. Pour chaque article, nb_sources_reprise = nombre de
sources distinctes dans son groupe (1 = personne d'autre ne la reprend).

Limites :
  - deux éditeurs qui reformulent beaucoup leur titre ne seront pas rapprochés ;
  - une dépêche republiée telle quelle sur plusieurs sites compte plusieurs sources.
  Pistes pour P3 : titres + entités communes, similarité du texte complet.

Recalcule tout à chaque exécution (cette colonne appartient à P3 dans le plan :
ce script peut lui être transféré tel quel).

Usage : python scripts/03_reprises.py [--csv data/articles.csv]
"""
import argparse
from datetime import date

from rapidfuzz import fuzz

from commun import DOSSIER_DATA, cle_titre, ecrire_csv, lire_csv

SEUIL = 90
FENETRE_JOURS = 7
MIN_MOTS = 5


def jour(texte):
    try:
        return date.fromisoformat(texte[:10])
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=str(DOSSIER_DATA / "articles.csv"))
    args = ap.parse_args()

    lignes = lire_csv(args.csv)
    cles = [cle_titre(r["titre"]) for r in lignes]
    dates = [jour(r["date_publication"]) for r in lignes]
    parent = list(range(len(lignes)))

    def trouver(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(lignes)):
        if len(cles[i].split()) < MIN_MOTS:
            continue
        for j in range(i + 1, len(lignes)):
            if lignes[i]["source"] == lignes[j]["source"] or len(cles[j].split()) < MIN_MOTS:
                continue
            if dates[i] and dates[j] and abs((dates[i] - dates[j]).days) > FENETRE_JOURS:
                continue
            if fuzz.token_set_ratio(cles[i], cles[j]) >= SEUIL:
                parent[trouver(i)] = trouver(j)

    groupes = {}
    for i in range(len(lignes)):
        groupes.setdefault(trouver(i), []).append(i)

    repris = 0
    for membres in groupes.values():
        nb = len({lignes[i]["source"] for i in membres})
        repris += nb >= 2
        for i in membres:
            lignes[i]["nb_sources_reprise"] = str(nb)

    ecrire_csv(args.csv, lignes)
    print(f"{repris} histoire(s) reprise(s) par au moins 2 sources, sur {len(lignes)} article(s)")


if __name__ == "__main__":
    main()
