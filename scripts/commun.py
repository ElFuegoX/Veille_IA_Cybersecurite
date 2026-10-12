"""Éléments communs aux scripts : schéma du CSV, lecture/écriture, nettoyage.

Le schéma (26 colonnes) est gelé ici. Chaque script ne remplit que ses colonnes
et conserve toutes les autres telles quelles.
"""
import csv
import html
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qsl, parse_qs, urlencode, urlparse

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_CONFIG = RACINE / "config"
DOSSIER_DATA = RACINE / "data"
# Texte complet des articles : local uniquement, jamais commité (voir .gitignore)
DOSSIER_TEXTES = DOSSIER_DATA / "textes"

AGENT = "Mozilla/5.0 (compatible; veille-ifri/1.0)"

# ----------------------------------------------------------------------------
# Schéma du CSV : colonnes groupées par propriétaire
# ----------------------------------------------------------------------------
BLOCS = {
    "P1_identite": ["id", "date_publication", "titre", "auteur", "lien", "source", "langue"],
    "P1_contenu": ["resume", "statut_extraction"],
    "P2_craap": [
        "craap_actualite", "craap_pertinence", "craap_autorite", "craap_exactitude",
        "craap_objectif", "craap_total", "craap_justification",
    ],
    "P3_sous_themes": ["s1", "s2", "s3", "s4", "s5", "justification_theme"],
    "P3_cas": ["nb_sources_reprise", "score_notabilite"],
    "P4_controle": ["valide_manuel", "relecteur"],
}
COLONNES = [c for cols in BLOCS.values() for c in cols]
COLONNES_VALIDATION = ["id", "valide_manuel", "relecteur", "correction"]

# Filtres prédéfinis, utilisables dans config/flux.txt avec « filtre=ia ».
# Les « AI » / « IA » en majuscules uniquement (sinon « ai » français = « j'ai »).
FILTRES = {
    "ia": re.compile(
        r"(?i)\b(?-i:AI|IA|LLMs?)\b"
        r"|\b(artificial intelligence|intelligence artificielle|machine learning|"
        r"apprentissage automatique|deep learning|apprentissage profond|generative|"
        r"génératif|agentic|ChatGPT|OpenAI|Anthropic|Claude|Gemini|Copilot|GPT|"
        r"prompt injection|jailbreak|deepfake|large language model|modèle de langage)\b"
    ),
}


# ----------------------------------------------------------------------------
# Lecture / écriture du CSV
# ----------------------------------------------------------------------------
def lire_csv(chemin):
    """Retourne la liste des lignes (dict) avec toutes les colonnes du schéma."""
    chemin = Path(chemin)
    if not chemin.exists():
        return []
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        lignes = []
        for r in csv.DictReader(f):
            ligne = {c: (r.get(c) or "") for c in COLONNES}
            for k, v in r.items():  # colonnes inconnues : conservées
                if k and k not in ligne:
                    ligne[k] = v or ""
            lignes.append(ligne)
    return lignes


def ecrire_csv(chemin, lignes):
    """Écriture atomique (fichier temporaire puis remplacement)."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    extras = []
    for r in lignes:
        for k in r:
            if k not in COLONNES and k not in extras:
                extras.append(k)
    champs = COLONNES + extras
    fd, tmp = tempfile.mkstemp(dir=chemin.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=champs)
            w.writeheader()
            w.writerows(lignes)
        os.replace(tmp, chemin)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def prochain_id(lignes):
    nums = [int(r["id"]) for r in lignes if str(r.get("id", "")).isdigit()]
    return max(nums, default=0) + 1


def formater_id(n):
    return f"{n:04d}"


# ----------------------------------------------------------------------------
# Nettoyage
# ----------------------------------------------------------------------------
def nettoyer_html(texte):
    texte = html.unescape(texte or "")
    texte = re.sub(r"<[^>]+>", " ", texte)
    texte = html.unescape(texte)
    return re.sub(r"\s+", " ", texte).strip()


def nettoyer_titre(titre, retirer_media=False):
    """Retourne (titre, media). Google Actualités ajoute « - Nom du média » au titre."""
    t = html.unescape(titre or "")
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"\s+", " ", html.unescape(t)).strip()
    media = ""
    if retirer_media:
        debut, sep, fin = t.rpartition(" - ")
        if sep and debut and len(fin) <= 40:
            t, media = debut, fin
    return t, media


def cle_titre(titre):
    return re.sub(r"[\W_]+", " ", (titre or "").lower()).strip()


def lien_reel(lien):
    """Les alertes Google enveloppent le vrai lien dans google.com/url?...&url=..."""
    if not lien:
        return ""
    p = urlparse(lien)
    if "google." in p.netloc and p.path == "/url":
        cible = parse_qs(p.query).get("url")
        if cible:
            return cible[0]
    return lien


def cle_lien(lien):
    """Clé de comparaison d'un lien (sans schéma, www, fragment ni paramètres de suivi).
    Les liens de redirection Google Actualités sont inutilisables : clé vide."""
    if not lien or "news.google.com" in lien:
        return ""
    p = urlparse(lien)
    params = [
        (k, v) for k, v in parse_qsl(p.query)
        if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid", "ref"}
    ]
    hote = p.netloc.lower()
    if hote.startswith("www."):
        hote = hote[4:]
    q = urlencode(params)
    return f"{hote}{p.path.rstrip('/')}" + (f"?{q}" if q else "")


def domaine(lien):
    """Domaine du lien sans « www. » ; vide pour les liens Google (redirections)."""
    if not lien:
        return ""
    h = urlparse(lien).netloc.lower().split(":")[0]
    if h.startswith("www."):
        h = h[4:]
    return "" if "google." in h else h


# ----------------------------------------------------------------------------
# Langue (heuristique simple, sans dépendance)
# ----------------------------------------------------------------------------
_MOTS_FR = {"le", "la", "les", "des", "une", "du", "et", "pour", "dans", "sur", "avec",
            "est", "sont", "que", "qui", "au", "aux", "ce", "cette", "par", "pas", "plus",
            "ont", "être", "fait", "après", "contre", "vers", "sans"}
_MOTS_EN = {"the", "and", "of", "to", "in", "for", "with", "is", "are", "that", "on", "as",
            "by", "from", "this", "it", "be", "at", "an", "was", "has", "after", "how",
            "new", "its", "into", "not"}


def detecter_langue(texte):
    mots = re.findall(r"[a-zàâçéèêëîïôûùüÿœ']+", (texte or "").lower())
    fr = sum(1 for m in mots if m in _MOTS_FR)
    en = sum(1 for m in mots if m in _MOTS_EN)
    if fr >= 2 and fr > en * 1.3:
        return "fr"
    if en >= 2 and en > fr * 1.3:
        return "en"
    return ""


# ----------------------------------------------------------------------------
# Auteur et résumé
# ----------------------------------------------------------------------------
_AUTEURS_GENERIQUES = {
    "admin", "administrator", "staff", "editorial team", "editors", "redaction",
    "rédaction", "équipe éditoriale", "press release", "team", "webmaster",
    "news desk", "staff writer", "contributor", "contributors",
}


def auteur_valide(auteur, source="", nom_site=""):
    """Rejette les auteurs génériques (« admin », nom du site...). Retourne '' sinon."""
    a = re.sub(r"\s+", " ", nettoyer_html(auteur)).strip()
    if not a or a.lower() in _AUTEURS_GENERIQUES:
        return ""

    def n(x):
        return re.sub(r"[^a-z0-9]", "", (x or "").lower())

    interdits = {n(nom_site), n(source), n(source.split(".")[0] if source else "")} - {""}
    if n(a) in interdits:
        return ""
    return a[:200]


def resume_court(texte, max_car=400):
    """Chapeau ou premières phrases, 400 caractères maximum."""
    texte = re.sub(r"\s+", " ", texte or "").strip()
    if len(texte) <= max_car:
        return texte
    out = ""
    for ph in re.split(r"(?<=[.!?])\s+", texte):
        if len(out) + len(ph) + 1 > max_car:
            break
        out = (out + " " + ph).strip()
        if len(out) >= 250:
            break
    if not out:
        out = texte[:max_car].rsplit(" ", 1)[0] + "…"
    return out
