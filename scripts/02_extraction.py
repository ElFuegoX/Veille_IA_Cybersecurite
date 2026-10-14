#!/usr/bin/env python3
"""P1 (1.3, 1.4) : extraction du texte de chaque article (trafilatura).

Remplit : statut_extraction, resume, et complète auteur / date_publication /
langue / titre quand ils sont vides. Le texte complet est enregistré dans
data/textes/<id>.txt (local, ignoré par Git : jamais publié).

Rejouable : ne traite que les lignes dont statut_extraction est vide.
  --refaire-echecs   retente aussi les lignes en « echec_http »
  --limite N         au plus N téléchargements par exécution (les liens inutilisables
                     et les sites interdits par robots.txt ne comptent pas)

Statuts : ok | vide (page lue, pas de texte) | echec_http | robots (interdit par
robots.txt) | lien_redirection (lien Google inutilisable).

Usage : python scripts/02_extraction.py [--csv data/articles.csv]
"""
import argparse
import sys
import time
import urllib.request
from collections import Counter
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import trafilatura

from commun import (
    AGENT, DOSSIER_DATA, DOSSIER_TEXTES, auteur_valide, detecter_langue, ecrire_csv,
    lire_csv, resume_court,
)

DELAI = 1.0              # secondes entre deux téléchargements
TAILLE_MAX = 5_000_000   # octets lus au maximum par page
_robots = {}


import re

def resoudre_url(url):
    """Tente de résoudre l'URL finale si l'URL est une redirection (Google News / Alertes)."""
    if not url:
        return ""
    if "news.google.com" in url or "google.com/url" in url:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "fr,en;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=12) as resp:
                url_finale = resp.geturl()
                if url_finale and "news.google.com" not in url_finale:
                    return url_finale
                # Tentative d'extraction du lien dans le HTML de redirection Google
                html_deb = resp.read(25000).decode("utf-8", errors="ignore")
                m = re.search(r'data-n-au="([^"]+)"', html_deb) or re.search(r'<c-wiz[^>]*>.*?<a[^>]+href="([^"]+)"', html_deb, re.DOTALL)
                if m and m.group(1).startswith("http"):
                    return m.group(1)
        except Exception:
            pass
    return url


def autorise(url):
    """Respect de robots.txt (si robots.txt est inaccessible : autorisé)."""
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = RobotFileParser()
        try:
            req = urllib.request.Request(base + "/robots.txt", headers={"User-Agent": AGENT})
            with urllib.request.urlopen(req, timeout=5) as r:
                rp.parse(r.read(500_000).decode("utf-8", "ignore").splitlines())
            _robots[base] = rp
        except Exception:
            _robots[base] = None
    rp = _robots[base]
    return True if rp is None else rp.can_fetch(AGENT, url)


def telecharger(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "fr,en;q=0.9",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        charset = r.headers.get_content_charset() or "utf-8"
        return r.read(TAILLE_MAX).decode(charset, errors="replace")


def analyser_html(html_page, url=""):
    """Retourne un dict : texte, auteur, date, langue, titre, description."""
    texte = trafilatura.extract(
        html_page, url=url or None, include_comments=False, include_tables=False,
        favor_precision=True,
    ) or ""
    meta = None
    try:
        meta = trafilatura.extract_metadata(html_page, default_url=url or None)
    except Exception:
        pass
    g = lambda champ: (getattr(meta, champ, None) or "") if meta else ""
    return {
        "texte": texte, "auteur": g("author"), "date": g("date"),
        "langue": g("language"), "titre": g("title"), "description": g("description"),
        "nom_site": g("sitename"),
    }


def traiter_ligne(r):
    """Met à jour la ligne r (dict) et retourne le statut."""
    url = r["lien"]
    if not url:
        return "lien_redirection"
    
    # Résolution de redirection si lien Google
    if "news.google.com" in url or "google.com/url" in url:
        url_resolue = resoudre_url(url)
        if url_resolue and "news.google.com" not in url_resolue:
            url = url_resolue
        else:
            return "lien_redirection"

    if not autorise(url):
        return "robots"
    try:
        page = telecharger(url)
    except Exception:
        return "echec_http"
    info = analyser_html(page, url)
    if len(info["texte"]) < 200:
        return "vide"

    DOSSIER_TEXTES.mkdir(parents=True, exist_ok=True)
    (DOSSIER_TEXTES / f"{r['id']}.txt").write_text(info["texte"], encoding="utf-8")

    if not r["auteur"]:
        r["auteur"] = auteur_valide(info["auteur"], r["source"], info["nom_site"])
    if not r["date_publication"] and info["date"]:
        r["date_publication"] = info["date"][:10]
    if not r["titre"] and info["titre"]:
        r["titre"] = info["titre"]
    langue = (info["langue"] or "")[:2].lower() or detecter_langue(info["texte"][:3000])
    if langue:
        r["langue"] = langue
    description = info["description"]
    r["resume"] = resume_court(description if len(description) >= 80 else info["texte"])
    return "ok"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--csv", default=str(DOSSIER_DATA / "articles.csv"))
    ap.add_argument("--refaire-echecs", action="store_true")
    ap.add_argument("--limite", type=int, default=0)
    args = ap.parse_args()

    lignes = lire_csv(args.csv)
    a_faire = [
        r for r in lignes
        if not r["statut_extraction"] or (args.refaire_echecs and r["statut_extraction"] in ("echec_http", "lien_redirection"))
    ]
    print(f"{len(a_faire)} article(s) à traiter sur {len(lignes)}")

    bilan = Counter()
    telecharges = 0
    try:
        for i, r in enumerate(a_faire, start=1):
            if args.limite and telecharges >= args.limite:
                break
            statut = traiter_ligne(r)
            r["statut_extraction"] = statut
            bilan[statut] += 1
            print(f"[{i}/{len(a_faire)}] {statut:<16} {r['id']} {r['titre'][:60]}")
            if statut not in {"lien_redirection", "robots"}:
                telecharges += 1
                time.sleep(DELAI)
    finally:  # on enregistre même si le script est interrompu
        ecrire_csv(args.csv, lignes)
    print("\nBilan :", dict(bilan) or "rien à faire")


if __name__ == "__main__":
    main()