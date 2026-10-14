#!/usr/bin/env python3
"""P3 : classification des articles en sous-thèmes S1 à S5. Rejouable.

Ne traite que les lignes où justification_theme est vide, dont craap_pertinence >= 2
et dont le texte existe dans data/textes/<id>.txt (au moins MIN_MOTS mots).

Usage :
  python scripts/06_classifier.py                          # API, sur data/echantillon.csv
  python scripts/06_classifier.py --csv data/articles.csv  # workflow uniquement
  python scripts/06_classifier.py --lot 8 --sortie lot.txt # prompt à coller dans le chat
  python scripts/06_classifier.py --importer rep.json      # réponse JSON du chat
  python scripts/06_classifier.py --evaluer                # compare à l'annotation manuelle

Variables d'environnement (jamais dans le dépôt) :
  LLM_FOURNISSEUR = groq (défaut) ou gemini
  GROQ_API_KEY / GEMINI_API_KEY
  LLM_MODELE = nom du modèle (à vérifier dans la doc du fournisseur)
"""
import argparse
import json
import os
import re
import sys
import time

import requests

from commun import (
    DOSSIER_CONFIG, DOSSIER_DATA, DOSSIER_TEXTES, ecrire_csv, lire_csv,
    norm_id, pertinence_ok, re_extraire,
)

SOUS_THEMES = ["S1", "S2", "S3", "S4", "S5"]
COLS_S = [t.lower() for t in SOUS_THEMES]
# Colonnes P3 remplies par ce script
COLS_P3 = COLS_S + ["justification_theme", "theme_principal"]


MIN_MOTS = 50         # en dessous, le texte n'est pas exploitable
MAX_MOTS = 500        # troncature envoyée au modèle
TAILLE_LOT = 5
MAX_TENTATIVES = 3    # par appel API, dans une même exécution
ATTENTE_BASE = 20     # secondes ; doublée à chaque nouvel essai


# ----------------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------------
def cle_api(nom):
    valeur = os.environ.get(nom)
    if not valeur:
        raise SystemExit(f"Variable d'environnement manquante : {nom}")
    return valeur


# ----------------------------------------------------------------------------
# Sélection des lignes
# ----------------------------------------------------------------------------
def lire_texte(r):
    """Retourne le texte de l'article, avec re-extraction si nécessaire."""
    p = DOSSIER_TEXTES / f"{norm_id(r['id'])}.txt"
    if p.exists():
        texte = p.read_text(encoding="utf-8").strip()
        if texte:
            return texte
    # Pas de fichier texte : tenter la ré-extraction
    if r.get("statut_extraction") == "ok":
        texte, ok = re_extraire(r)
        if ok:
            return texte.strip()
    return ""


def tronquer(texte, n=MAX_MOTS):
    return " ".join(texte.split()[:n])


def est_traitee(r):
    return bool((r.get("justification_theme") or "").strip())


def preparer(lignes, limite=0):
    """Articles à classer : titre + texte tronqué (c'est ce qui est envoyé au modèle)."""
    out = []
    ignores = {"deja_traite": 0, "pertinence": 0, "sans_texte": 0, "texte_court": 0}
    for r in lignes:
        if est_traitee(r):
            ignores["deja_traite"] += 1
            continue
        if not pertinence_ok(r):
            ignores["pertinence"] += 1
            continue
        texte = tronquer(lire_texte(r))
        if not texte:
            # Fallback sur le résumé ou le titre pour que les flux RSS puissent être classés
            resume = (r.get("resume") or "").strip()
            titre = (r.get("titre") or "").strip()
            if resume and len(resume.split()) >= 6:
                texte = resume
            elif titre:
                texte = f"{titre}. {resume}".strip()
        if not texte or len(texte.split()) < 3:
            ignores["sans_texte"] += 1
            continue
        out.append({"id": norm_id(r["id"]), "titre": r["titre"],
                    "source": r["source"], "texte": texte})
        if limite and len(out) >= limite:
            break
    print("Ignorés :", ignores, file=sys.stderr)
    return out


# ----------------------------------------------------------------------------
# Prompt et appel au modèle
# ----------------------------------------------------------------------------
def construire_prompt(articles):
    modele = (DOSSIER_CONFIG / "prompt_classification.txt").read_text(encoding="utf-8")

    def sur(t):  # empêche un article d'ouvrir ou de fermer une balise <article>
        return re.sub(r"<(?=/?\s*article)", "&lt;", t or "", flags=re.I)

    bloc = "\n".join(
        f'<article id="{a["id"]}">\ntitre: {sur(a["titre"])}\nsource: {sur(a["source"])}\n'
        f'texte: {sur(a["texte"])}\n</article>\n'
        for a in articles
    )
    return modele.replace("{ARTICLES}", bloc)


def appeler_modele(prompt):
    fournisseur = os.environ.get("LLM_FOURNISSEUR", "groq").lower()
    if fournisseur == "groq":
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {cle_api('GROQ_API_KEY')}"},
            json={
                "model": os.environ.get("LLM_MODELE", "llama-3.3-70b-versatile"),
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    if fournisseur == "gemini":
        modele = os.environ.get("LLM_MODELE", "gemini-3.5-flash-lite")
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent",
            headers={"x-goog-api-key": cle_api("GEMINI_API_KEY")},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    raise SystemExit(f"Fournisseur inconnu : {fournisseur}")


def avec_retries(prompt):
    for essai in range(MAX_TENTATIVES):
        try:
            return appeler_modele(prompt)
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else None
            if code in (429, 500, 502, 503) and essai < MAX_TENTATIVES - 1:
                time.sleep(ATTENTE_BASE * 2 ** essai)
                continue
            raise
        except (requests.ConnectionError, requests.Timeout):
            if essai < MAX_TENTATIVES - 1:
                time.sleep(ATTENTE_BASE * 2 ** essai)
                continue
            raise


# ----------------------------------------------------------------------------
# Validation de la réponse
# ----------------------------------------------------------------------------
def normaliser(t):
    t = (t or "").lower()
    for a, b in (("\u2018", "'"), ("\u2019", "'"), ("\u00ab", '"'), ("\u00bb", '"'), ("\u201c", '"'),
                 ("\u201d", '"'), ("\u2013", "-"), ("\u2014", "-"), ("\u00a0", " "),
                 ("\u2026", " "), ("...", " ")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def extraire_json(brut):
    brut = re.sub(r"^```(?:json)?|```$", "", brut.strip(), flags=re.M).strip()
    data = json.loads(brut)
    if isinstance(data, dict):
        data = data.get("resultats", [])
    return data if isinstance(data, list) else []


def valider(res, article):
    """Retourne les valeurs à écrire (chaînes) ou None si la réponse est inutilisable."""
    try:
        s = {c: int(res[c]) for c in COLS_S}
    except (KeyError, ValueError, TypeError):
        return None
    if any(v not in (0, 1) for v in s.values()):
        return None
    # Vérification : au moins un sous-thème doit être à 1
    if not any(v == 1 for v in s.values()):
        return None

    citation = str(res.get("justification_theme", "")).strip()
    reference = normaliser(f'{article["titre"]} {article["texte"]}')
    if citation and (len(citation.split()) >= 25 or normaliser(citation) not in reference):
        citation = ""  # citation invalide, on la vide
    if citation[:1] in ("=", "+", "-", "@"):
        citation = "'" + citation  # Excel ne doit pas l'exécuter comme une formule

    actifs = [c.upper() for c, v in s.items() if v == 1]
    out = {c: str(v) for c, v in s.items()}
    out["theme_principal"] = actifs[0] if actifs else ""
    out["justification_theme"] = citation
    return out


# ----------------------------------------------------------------------------
# Écriture : relecture juste avant, fusion par id, uniquement mes colonnes
# ----------------------------------------------------------------------------
def sauvegarder(chemin, nouveaux):
    lignes = lire_csv(chemin)
    for r in lignes:
        v = nouveaux.get(norm_id(r["id"]))
        if v:
            r.update(v)
    ecrire_csv(chemin, lignes)


def appliquer(chemin, articles_par_id, brut):
    try:
        data = extraire_json(brut)
    except json.JSONDecodeError:
        print("Réponse JSON illisible, lot ignoré.", file=sys.stderr)
        return 0
    nouveaux = {}
    for res in data:
        if not isinstance(res, dict):
            continue
        id_ = norm_id(res.get("id"))
        article = articles_par_id.get(id_)
        v = valider(res, article) if article else None
        if v:
            nouveaux[id_] = v
    manquants = sorted(set(articles_par_id) - set(nouveaux))
    if manquants:
        print("Non traités (seront retentés) :", ", ".join(manquants), file=sys.stderr)
    if nouveaux:
        sauvegarder(chemin, nouveaux)
    return len(nouveaux)


# ----------------------------------------------------------------------------
# Modes
# ----------------------------------------------------------------------------
def traiter(chemin, limite=0):
    a_faire = preparer(lire_csv(chemin), limite)
    print(f"{len(a_faire)} article(s) à classer dans {chemin}")
    total = 0
    for i in range(0, len(a_faire), TAILLE_LOT):
        lot = a_faire[i:i + TAILLE_LOT]
        try:
            brut = avec_retries(construire_prompt(lot))
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                print(f"Quota atteint, arrêt : {e}", file=sys.stderr)
                break
            print(f"Lot {i // TAILLE_LOT + 1} ignoré : {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Lot {i // TAILLE_LOT + 1} ignoré : {e}", file=sys.stderr)
            continue
        total += appliquer(chemin, {a["id"]: a for a in lot}, brut)

    if a_faire and total == 0:
        raise SystemExit("Aucun article classé : vérifier clé API, modèle et quota.")
    
    print(f"{total} article(s) classé(s).")


def evaluer(chemin_ref):
    """Classe une copie vierge de l'échantillon et compare à l'annotation manuelle."""
    ref = lire_csv(chemin_ref)
    copie = []
    for r in ref:
        c = dict(r)
        for k in COLS_P3:
            c[k] = ""
        copie.append(c)
    auto = DOSSIER_DATA / "echantillon_auto.csv"
    ecrire_csv(auto, copie)
    traiter(auto)
    machine = {norm_id(r["id"]): r for r in lire_csv(auto)}
    for col in COLS_S:
        paires = [(r[col].strip().upper(), machine[norm_id(r["id"])].get(col, "").strip().upper())
                  for r in ref
                  if (r.get(col) or "").strip() and (machine[norm_id(r["id"])].get(col) or "").strip()]
        if not paires:
            print(f"{col:16s} aucune référence humaine")
            continue
        ok = sum(1 for a, b in paires if a == b)
        print(f"{col:16s} accord {ok}/{len(paires)} ({100 * ok / len(paires):.0f} %)")
        humain = sum(1 for a, _ in paires if a == "1")
        modele = sum(1 for _, b in paires if b == "1")
        communs = sum(1 for a, b in paires if a == "1" and b == "1")
        print(f"{'':16s} positifs : humain {humain}, modèle {modele}, en commun {communs}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--csv", default=str(DOSSIER_DATA / "echantillon.csv"))
    ap.add_argument("--limite", type=int, default=0, help="nombre max d'articles (quota)")
    ap.add_argument("--lot", type=int, metavar="N", help="affiche le prompt de N articles")
    ap.add_argument("--sortie", metavar="FICHIER", help="avec --lot : écrit le prompt en UTF-8")
    ap.add_argument("--importer", metavar="FICHIER", help="importe une réponse JSON du chat")
    ap.add_argument("--evaluer", action="store_true")
    a = ap.parse_args()

    if os.path.basename(a.csv) == "articles.csv" and not os.environ.get("GITHUB_ACTIONS"):
        raise SystemExit("articles.csv n'est modifié que par les workflows.")

    if a.lot:
        prompt = construire_prompt(preparer(lire_csv(a.csv), a.lot))
        if a.sortie:
            with open(a.sortie, "w", encoding="utf-8") as f:
                f.write(prompt)
        else:
            print(prompt)
    elif a.importer:
        articles = {x["id"]: x for x in preparer(lire_csv(a.csv))}
        with open(a.importer, encoding="utf-8-sig") as f:
            brut = f.read()
        print(f"{appliquer(a.csv, articles, brut)} article(s) importé(s).")
    elif a.evaluer:
        evaluer(a.csv)
    else:
        traiter(a.csv, a.limite)


if __name__ == "__main__":
    main()