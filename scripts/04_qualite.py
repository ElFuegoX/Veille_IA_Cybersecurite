#!/usr/bin/env python3
"""P2 (2.4) : notes CRAAP de chaque article (total sur 11).

Remplit : craap_actualite, craap_pertinence (0-3), craap_autorite, craap_exactitude,
craap_objectif, craap_total, craap_justification.
Grille : config/grille_qualite.yaml ; sources reconnues : config/sources_autorite.yaml.

Méthode, critère par critère :
  pertinence (0-3)  règles : termes IA / cyber dans le titre et dans le texte
  actualité (0-2)   règles : âge de date_publication
  autorité          règles : catégorie de la source + auteur identifié
  exactitude        règles (signaux de faits vérifiables), ou IA si disponible
  objectif          règles (signaux commerciaux), ou IA si disponible
L'IA (Groq ou Gemini) n'est appelée que si sa clé est dans l'environnement
(GROQ_API_KEY ou GEMINI_API_KEY), que le texte complet est disponible et que la
pertinence atteint le seuil d'analyse. Sinon, ou en cas d'erreur, les règles servent.

Texte utilisé : data/textes/<id>.txt (écrit par 02_extraction.py), sinon le résumé.
Sans texte complet, l'exactitude vaut 1 (neutre) et la ligne est à relire.

Rejouable : ne traite que les lignes déjà passées par l'extraction
(statut_extraction rempli) et dont craap_total est vide.
  --refaire     recalcule toutes les lignes (après un changement de grille)
  --limite N    au plus N articles par exécution
  --ia          auto (défaut) | groq | gemini | aucune

Usage : python scripts/04_qualite.py [--csv data/articles.csv]
"""
import argparse
import json
import os
import re
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import urllib.error
import urllib.request
from collections import Counter
from datetime import date

import yaml

from commun import (
    AGENT, DOSSIER_CONFIG, DOSSIER_DATA, DOSSIER_TEXTES, FILTRES, auteur_valide,
    domaine, ecrire_csv, lire_csv, re_extraire,
)

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
def charger_yaml(nom):
    with open(DOSSIER_CONFIG / nom, encoding="utf-8") as f:
        return yaml.safe_load(f)


def motif(termes):
    """Compile une liste de termes : mot entier (pluriel -s/-es accepté),
    ou début de mot si le terme finit par « * »."""
    parties = []
    for t in termes:
        t = str(t).strip().lower()
        prefixe = t.endswith("*")
        t = t.rstrip("*")
        if not t:
            continue
        debut = r"\b" if re.match(r"\w", t) else ""
        fin = r"[\w-]*" if prefixe else r"(?:s|es)?\b" if re.search(r"\w$", t) else ""
        parties.append(debut + re.escape(t) + fin)
    return re.compile("|".join(parties) or r"(?!)", re.IGNORECASE)


def normaliser_nom(texte):
    return re.sub(r"[^a-z0-9]", "", (texte or "").lower())


class Grille:
    def __init__(self):
        g = charger_yaml("grille_qualite.yaml")
        self.g = g
        p = g["pertinence"]
        self.seuil_analyse = p["seuil_analyse"]
        self.occurrences = p["occurrences_texte"]
        self.ia_en_plus = motif(p["termes_ia_en_plus"])
        self.cyber = motif(p["termes_cyber"])
        self.signaux_exactitude = {
            nom: motif(termes) for nom, termes in g["exactitude"]["signaux"].items()
        }
        self.commercial = motif(g["objectif"]["signaux_commerciaux"])
        self.accrocheur = motif(g["objectif"]["titre_accrocheur"])
        self.sources = Sources(charger_yaml("sources_autorite.yaml"))

    def termes_ia(self, texte):
        return [m.group(0) for m in FILTRES["ia"].finditer(texte)] + self.ia_en_plus.findall(texte)

    def niveau(self, total, pertinence=None):
        if pertinence is not None and int(pertinence) < self.seuil_analyse:
            return "écarté"
        s = self.g["seuils_craap"]
        return "fiable" if total >= s["fiable"] else "prudence" if total >= s["prudence"] else "écarté"


class Sources:
    """Catégorie d'autorité d'une source, d'après son domaine ou son nom."""

    def __init__(self, conf):
        self.suffixes = conf.get("suffixes_institution") or []
        self.domaines, self.noms, self.plafonds = {}, {}, {}
        for cat, info in conf["categories"].items():
            self.plafonds[cat] = info["plafond"]
            for s in info.get("sources") or []:
                s = str(s).strip()
                if "." in s and " " not in s:
                    self.domaines[s.lower().removeprefix("www.")] = cat
                else:
                    self.noms[normaliser_nom(s)] = cat

    def categorie(self, r):
        """Retourne (catégorie ou '', libellé de la source)."""
        # « Google Actualités AI cybersecurity / Federal News Network » -> le média
        nom = (r.get("source") or "").rsplit(" / ", 1)[-1].strip()
        dom = domaine(r.get("lien", ""))
        if not dom and "." in nom and " " not in nom:
            dom = nom.lower().removeprefix("www.")
        if dom:
            parties = dom.split(".")
            for i in range(len(parties) - 1):  # sous-domaines compris
                cat = self.domaines.get(".".join(parties[i:]))
                if cat:
                    return cat, dom
            if any(dom.endswith(s) for s in self.suffixes):
                return "institution", dom
        cat = self.noms.get(normaliser_nom(nom))
        return cat or "", nom or dom


# ----------------------------------------------------------------------------
# Critères
# ----------------------------------------------------------------------------
def texte_article(r):
    """(texte, complet) : texte extrait si disponible, sinon re-téléchargement,
    sinon le résumé (fallback).

    Quand statut_extraction est 'ok' mais que data/textes/<id>.txt est absent
    (runner GitHub Actions du job précédent l'a supprimé), on tente de
    re-télécharger le texte via re_extraire() depuis commun. Si cela réussit,
    le fichier est recréé pour les étapes suivantes de ce même job.
    """
    chemin = DOSSIER_TEXTES / f"{r['id']}.txt"
    if r["id"] and chemin.exists():
        texte = chemin.read_text(encoding="utf-8")
        if texte.strip():
            return texte, True

    # Fichier absent mais extraction marquée 'ok' : on tente la ré-extraction
    if r.get("statut_extraction") == "ok":
        texte, ok = re_extraire(r)
        if ok:
            return texte, True

    return r["resume"], False


def exemples(termes, n=4):
    vus = []
    for t in termes:
        if t.lower() not in [v.lower() for v in vus]:
            vus.append(t)
    return ", ".join(vus[:n])


def noter_pertinence(r, texte, complet, grille):
    """Échelle validée le 12/10/2026 : 0 aucun lien, 1 un seul thème développé,
    2 les deux thèmes dans le texte, 3 les deux dans le texte ET le titre."""
    titre = r["titre"]
    corps = f"{titre}\n{texte}" if complet else f"{titre}\n{r['resume']}"
    ia, cy = grille.termes_ia(corps), grille.cyber.findall(corps)
    ia_titre, cy_titre = bool(grille.termes_ia(titre)), bool(grille.cyber.search(titre))
    seuil = grille.occurrences if complet else 1
    ia_dev, cy_dev = len(ia) >= seuil, len(cy) >= seuil

    if not ia and not cy:
        note = 0
    elif ia_dev and cy_dev:
        note = 3 if ia_titre and cy_titre else 2
    else:
        note = 1

    def bilan(nom, termes, dans_titre):
        if not termes:
            return f"{nom} absent"
        return (f"{nom} : {len(termes)} occurrence(s) ({exemples(termes)})"
                + (", dans le titre" if dans_titre else ", absent du titre"))

    motifs = (f"{bilan('IA', ia, ia_titre)} ; {bilan('cyber', cy, cy_titre)}"
              + ("" if complet else " (titre et résumé seuls)"))
    return note, motifs


def noter_actualite(r, grille, aujourdhui):
    a = grille.g["actualite"]
    try:
        publie = date.fromisoformat(r["date_publication"][:10])
    except ValueError:
        return 0, "date introuvable"
    age = (aujourdhui - publie).days
    note = 2 if age < a["jours_2_points"] else 1 if age <= a["jours_1_point"] else 0
    return note, f"publié le {publie.isoformat()} ({age} j)"


def auteur_identifie(r):
    a = r.get("auteur") or ""
    # « info@thehackernews.com (The Hacker News) » : adresse de la rédaction, pas un auteur
    if "@" in a:
        return ""
    return auteur_valide(a, (r.get("source") or "").rsplit(" / ", 1)[-1])


def noter_autorite(r, grille):
    cat, libelle = grille.sources.categorie(r)
    auteur = auteur_identifie(r)
    if not cat:
        return 0, cat, f"{libelle or 'source vide'} : source inconnue (absente de config/sources_autorite.yaml)"
    plafond = grille.sources.plafonds[cat]
    note = min(plafond, 2 if auteur else 1)
    txt_auteur = f"auteur : {auteur}" if auteur else "auteur non identifié"
    return note, cat, f"{libelle} ({cat}), {txt_auteur}"


_CVE = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)
_CHIFFRES = re.compile(
    r"\d+(?:[.,]\d+)?\s?(?:%|(?:percent|pour cent|millions?|milliards?|billions?|thousands?)\b)"
    r"|[$€£]\s?\d|\d\s?[$€£]|\b\d{1,3}(?:[ ,.]\d{3})+\b",
    re.IGNORECASE,
)
_CITATION = re.compile(r"[\"“«][^\"”»]{20,}[\"”»]")


def noter_exactitude(texte, complet, grille):
    trouves = [nom for nom, m in grille.signaux_exactitude.items() if m.search(texte)]
    for nom, m in (("CVE", _CVE), ("chiffres", _CHIFFRES), ("citation", _CITATION)):
        if m.search(texte):
            trouves.append(nom)
    n = len(trouves)
    note = 2 if n >= grille.g["exactitude"]["categories_pour_2_points"] else 1 if n else 0
    motif_ = f"signaux : {', '.join(trouves)}" if trouves else "aucun fait vérifiable repéré"
    if not complet:
        # Sans texte, on ne peut ni confirmer des faits ni conclure à leur absence
        note, motif_ = 1, motif_ + " (note neutre 1 : résumé seul, à vérifier à la main)"
    return note, motif_


def noter_objectif(r, texte, categorie, grille):
    signaux = sorted({s.lower() for s in grille.commercial.findall(texte)})
    accroche = grille.accrocheur.findall(r["titre"])
    if accroche or len(signaux) >= 2:
        note = 0
    elif signaux or categorie == "editeur":
        note = 1
    else:
        note = 2
    details = []
    if accroche:
        details.append(f"titre accrocheur ({exemples(accroche)})")
    if signaux:
        details.append(f"signaux commerciaux ({exemples(signaux)})")
    if categorie == "editeur":
        details.append("source éditeur (intérêt propre)")
    return note, "; ".join(details) or "informatif, aucun signal commercial"


# ----------------------------------------------------------------------------
# IA (optionnelle) : exactitude et objectif
# ----------------------------------------------------------------------------
PROMPT_SYSTEME = """Tu évalues un article de veille sur « l'IA dans la cybersécurité » avec la grille CRAAP.
Note uniquement deux critères, de 0 à 2 :
- exactitude : 2 = faits vérifiables et sources citées (CVE, étude, chiffres attribués, personnes ou organisations nommées) ; 1 = quelques éléments vérifiables ; 0 = affirmations sans preuve.
- objectif : 2 = informer ou analyser de façon neutre ; 1 = intérêt commercial visible (produit de l'auteur ou de l'éditeur mis en avant, contenu partenaire) ; 0 = promotionnel ou accrocheur.
Réponds uniquement avec un objet JSON :
{"exactitude": 0, "exactitude_motif": "une phrase en français", "objectif": 0, "objectif_motif": "une phrase en français"}"""


class ClientIA:
    def __init__(self, choix, conf):
        self.nom, self.cfg, self.cle = None, None, None
        self.conf, self.echecs = conf, 0
        fournisseurs = conf["fournisseurs"]
        candidats = list(fournisseurs) if choix == "auto" else [] if choix == "aucune" else [choix]
        for nom in candidats:
            cle = os.environ.get(fournisseurs[nom]["variable_cle"], "").strip()
            if cle:
                self.nom, self.cfg, self.cle = nom, fournisseurs[nom], cle
                break
        if choix not in ("auto", "aucune") and not self.cle:
            raise SystemExit(f"Clé absente : définir {fournisseurs[choix]['variable_cle']}")

    @property
    def actif(self):
        return self.cle is not None and self.echecs < 3

    def noter(self, r, texte):
        message = (
            f"Titre : {r['titre']}\nSource : {r['source']}\nAuteur : {r['auteur'] or 'inconnu'}\n"
            f"Date : {r['date_publication'] or 'inconnue'}\n\n"
            f"Texte (extrait) :\n{texte[: self.conf['caracteres_max']]}"
        )
        corps = json.dumps({
            "model": self.cfg["modele"],
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": PROMPT_SYSTEME},
                {"role": "user", "content": message},
            ],
        }).encode()
        req = urllib.request.Request(self.cfg["url"], data=corps, headers={
            "Authorization": f"Bearer {self.cle}",
            "Content-Type": "application/json",
            "User-Agent": AGENT,
        })
        for essai in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as rep:
                    donnees = json.load(rep)
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 and e.code < 500 or essai == 3:
                    raise
                attente = float(e.headers.get("retry-after") or 10 * (essai + 1))
                time.sleep(min(attente, 60))
        contenu = donnees["choices"][0]["message"]["content"]
        contenu = re.sub(r"^```(?:json)?|```$", "", contenu.strip()).strip()
        res = json.loads(contenu)
        notes = {}
        for k in ("exactitude", "objectif"):
            v = int(res[k])
            if v not in (0, 1, 2):
                raise ValueError(f"{k} hors échelle : {v}")
            notes[k] = (v, str(res.get(f"{k}_motif", "")).strip())
        return notes


# ----------------------------------------------------------------------------
# Ligne complète
# ----------------------------------------------------------------------------
def noter_ligne(r, grille, ia, aujourdhui):
    """Remplit les colonnes P2 de la ligne. Retourne la méthode utilisée."""
    texte, complet = texte_article(r)
    corps = f"{r['titre']}\n{texte}"

    pert, pert_m = noter_pertinence(r, texte, complet, grille)
    act, act_m = noter_actualite(r, grille, aujourdhui)
    aut, cat, aut_m = noter_autorite(r, grille)
    exa, exa_m = noter_exactitude(corps, complet, grille)
    obj, obj_m = noter_objectif(r, corps, cat, grille)

    methode = "règles"
    if ia.actif and complet and pert >= grille.seuil_analyse:
        try:
            notes = ia.noter(r, texte)
            (exa, exa_m), (obj, obj_m) = notes["exactitude"], notes["objectif"]
            methode = f"IA {ia.nom}"
            ia.echecs = 0
        except Exception as e:  # repli sur les règles
            ia.echecs += 1
            methode = f"règles (IA en échec : {type(e).__name__})"
        time.sleep(ia.conf["pause_secondes"])

    total = act + pert + aut + exa + obj
    r["craap_actualite"] = str(act)
    r["craap_pertinence"] = str(pert)
    r["craap_autorite"] = str(aut)
    r["craap_exactitude"] = str(exa)
    r["craap_objectif"] = str(obj)
    r["craap_total"] = str(total)
    r["craap_justification"] = (
        f"Total {total}/11 ({grille.niveau(total, pert)}). "
        f"Actualité({act}) : {act_m}. "
        f"Pertinence({pert}/3) : {pert_m}. "
        f"Autorité({aut}) : {aut_m}. "
        f"Exactitude({exa}) : {exa_m}. "
        f"Objectif({obj}) : {obj_m}. "
        f"[{methode}]"
    )
    return methode, cat


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--csv", default=str(DOSSIER_DATA / "articles.csv"))
    ap.add_argument("--refaire", action="store_true")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--ia", default="auto", choices=["auto", "groq", "gemini", "aucune"])
    args = ap.parse_args()

    grille = Grille()
    ia = ClientIA(args.ia, grille.g["llm"])
    print(f"IA : {ia.nom or 'aucune (règles seules)'}")

    lignes = lire_csv(args.csv)
    a_faire = [
        r for r in lignes
        if r["statut_extraction"] and (args.refaire or not r["craap_total"])
    ]
    if args.limite:
        a_faire = a_faire[: args.limite]
    print(f"{len(a_faire)} article(s) à noter sur {len(lignes)}")

    aujourdhui = date.today()
    methodes, niveaux, pertinences, inconnues = Counter(), Counter(), Counter(), Counter()
    try:
        for i, r in enumerate(a_faire, start=1):
            chemin_texte = DOSSIER_TEXTES / f"{r['id']}.txt"
            avait_texte = chemin_texte.exists()
            methode, cat = noter_ligne(r, grille, ia, aujourdhui)
            # Indique si une ré-extraction a eu lieu durant la notation
            reextrait = not avait_texte and chemin_texte.exists()
            tag_reext = " [re-ext]" if reextrait else ""
            methodes[methode.split(" (")[0]] += 1
            niveaux[grille.niveau(int(r["craap_total"]), int(r["craap_pertinence"]))] += 1
            pertinences[r["craap_pertinence"]] += 1
            if not cat:
                inconnues[grille.sources.categorie(r)[1] or "(vide)"] += 1
            print(f"[{i}/{len(a_faire)}] P{r['craap_pertinence']} CRAAP {r['craap_total']:>2}/11 "
                  f"{r['id']} {r['titre'][:55]}{tag_reext}")
    finally:
        ecrire_csv(args.csv, lignes)

    print(f"Pertinence : {dict(sorted(pertinences.items()))} (seuil d'analyse : {grille.seuil_analyse})")
    print(f"Niveaux CRAAP : {dict(niveaux)}")
    print(f"Méthodes : {dict(methodes)}")
    if inconnues:
        print("Sources inconnues (autorité 0) — à classer dans config/sources_autorite.yaml :")
        for nom, n in inconnues.most_common(20):
            print(f"  {n:>3}  {nom}")


if __name__ == "__main__":
    main()
