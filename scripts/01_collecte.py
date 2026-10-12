#!/usr/bin/env python3
"""P1 (1.1, 1.2, 1.5) : collecte des flux RSS et des articles manuels -> CSV.

Remplit : id, date_publication, titre, auteur, lien, source, langue, resume.
Les autres colonnes ne sont jamais modifiées. Le script est rejouable : une
exécution ajoute seulement les articles nouveaux.

Règles de doublons (on ne perd jamais « la même histoire chez un autre éditeur ») :
  - même lien                              -> doublon (supprimé)
  - même titre ET même source              -> doublon (supprimé)
  - titre très proche ET même source       -> doublon (supprimé)
  - même titre mais source différente      -> conservé (voir 03_clusters.py)

Usage : python scripts/01_collecte.py [--csv data/articles.csv]
"""
import argparse
import time
from collections import defaultdict
from datetime import datetime

import feedparser
from rapidfuzz import fuzz

from commun import (
    AGENT, COLONNES, DOSSIER_CONFIG, DOSSIER_DATA, FILTRES, auteur_valide, cle_lien,
    cle_titre, detecter_langue, domaine, ecrire_csv, formater_id, lien_reel, lire_csv,
    nettoyer_html, nettoyer_titre, prochain_id,
)

SEUIL_TITRE_PROCHE = 95  # rapidfuzz.ratio sur titres normalisés, même source


def lire_flux(chemin):
    """Lignes « nom | url [| filtre=ia] ». # = commentaire."""
    flux = []
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#"):
                continue
            parts = [p.strip() for p in ligne.split("|")]
            nom, url = (parts[0], parts[1]) if len(parts) > 1 else (parts[0], parts[0])
            filtre = ""
            for p in parts[2:]:
                if p.startswith("filtre="):
                    filtre = p.split("=", 1)[1].strip()
            flux.append({"nom": nom, "url": url, "filtre": filtre})
    return flux


def lire_manuels(chemin):
    """Lignes « titre | lien »."""
    articles = []
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#") or "|" not in ligne:
                    continue
                titre, lien = [p.strip() for p in ligne.split("|", 1)]
                articles.append((titre, lien))
    except FileNotFoundError:
        pass
    return articles


class IndexDoublons:
    def __init__(self, lignes):
        self.liens = set()
        self.titres_par_source = defaultdict(list)
        for r in lignes:
            self.enregistrer(r["titre"], r["source"], r["lien"])

    def enregistrer(self, titre, source, lien):
        kl = cle_lien(lien)
        if kl:
            self.liens.add(kl)
        self.titres_par_source[source].append(cle_titre(titre))

    def raison(self, titre, source, lien):
        """Retourne la raison du doublon, ou '' si l'article est nouveau."""
        kl = cle_lien(lien)
        if kl and kl in self.liens:
            return "même lien"
        kt = cle_titre(titre)
        for autre in self.titres_par_source.get(source, []):
            if kt == autre:
                return "même titre, même source"
            if kt and autre and fuzz.ratio(kt, autre) >= SEUIL_TITRE_PROCHE:
                return "titre très proche, même source"
        return ""


def date_entree(e):
    t = e.get("published_parsed") or e.get("updated_parsed")
    return time.strftime("%Y-%m-%d", t) if t else ""


def resume_flux(e):
    """Extrait du flux, utilisé tant que l'extraction de la page n'a pas eu lieu."""
    txt = nettoyer_html(e.get("summary") or "")
    return txt[:300].rsplit(" ", 1)[0] + "…" if len(txt) > 300 else txt


def nouvelle_ligne(n, titre, lien, source, date="", auteur="", resume="", langue=""):
    r = {c: "" for c in COLONNES}
    r.update({
        "id": formater_id(n), "date_publication": date, "titre": titre, "auteur": auteur,
        "lien": lien, "source": source, "langue": langue, "resume": resume,
    })
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--csv", default=str(DOSSIER_DATA / "articles.csv"))
    ap.add_argument("--flux", default=str(DOSSIER_CONFIG / "flux.txt"))
    ap.add_argument("--manuels", default=str(DOSSIER_CONFIG / "articles_manuels.txt"))
    args = ap.parse_args()

    existants = lire_csv(args.csv)
    index = IndexDoublons(existants)
    n = prochain_id(existants)
    nouvelles, resultats = [], []

    # ---- 1. Flux RSS ------------------------------------------------------
    for fl in lire_flux(args.flux):
        d = feedparser.parse(fl["url"], agent=AGENT)
        statut = d.get("status", "?")
        brut, nouveaux, filtres, doublons = len(d.entries), 0, 0, 0
        google = "google." in fl["url"]
        motif = FILTRES.get(fl["filtre"])
        for e in d.entries:
            titre, media = nettoyer_titre(e.get("title", ""), retirer_media=google)
            lien = lien_reel(e.get("link", ""))
            source = domaine(lien) or media
            resume = resume_flux(e)
            if motif and not motif.search(f"{titre} {resume}"):
                filtres += 1
                continue
            if index.raison(titre, source, lien):
                doublons += 1
                continue
            auteur = auteur_valide(e.get("author", ""), source)
            nouvelles.append(nouvelle_ligne(
                n, titre, lien, source, date_entree(e), auteur, resume,
                detecter_langue(f"{titre} {resume}"),
            ))
            index.enregistrer(titre, source, lien)
            n += 1
            nouveaux += 1
        resultats.append((fl["nom"], statut, brut, filtres, doublons, nouveaux))

    # ---- 2. Articles manuels (jamais filtrés) -----------------------------
    messages = []
    manuels = lire_manuels(args.manuels)
    if manuels:
        filtres = doublons = nouveaux = 0
        for titre, lien in manuels:
            titre, _ = nettoyer_titre(titre)
            source = domaine(lien)
            raison = index.raison(titre, source, lien)
            if raison:
                doublons += 1
                messages.append(f"  [déjà présent : {raison}] {titre}")
                continue
            nouvelles.append(nouvelle_ligne(n, titre, lien, source, langue=detecter_langue(titre)))
            index.enregistrer(titre, source, lien)
            n += 1
            nouveaux += 1
            messages.append(f"  [NOUVEAU] {titre}")
        resultats.append(("Articles manuels", "-", len(manuels), 0, doublons, nouveaux))

    # ---- 3. Bilan et écriture --------------------------------------------
    print(f"Collecte du {datetime.now():%d/%m/%Y %H:%M}\n")
    print(f"{'Flux':<34} {'HTTP':>5} {'Bruts':>6} {'Filtrés':>8} {'Doublons':>9} {'Nouveaux':>9}")
    print("-" * 76)
    for nom, statut, brut, filtres, doublons, nouveaux in resultats:
        print(f"{nom[:34]:<34} {str(statut):>5} {brut:>6} {filtres:>8} {doublons:>9} {nouveaux:>9}")
    print("-" * 76)
    print(f"{'TOTAL':<34} {'':>5} {sum(r[2] for r in resultats):>6} "
          f"{sum(r[3] for r in resultats):>8} {sum(r[4] for r in resultats):>9} {len(nouvelles):>9}")

    for nom, statut, brut, *_ in resultats:
        if brut == 0:
            print(f"\nAttention : aucun article lu pour « {nom} » (HTTP {statut}). Vérifie l'adresse.")
    if messages:
        print("\nArticles manuels :")
        print("\n".join(messages))

    toutes = existants + nouvelles
    ecrire_csv(args.csv, toutes)
    print(f"\n{len(nouvelles)} nouveaux articles, {len(toutes)} au total dans {args.csv}")


if __name__ == "__main__":
    main()
