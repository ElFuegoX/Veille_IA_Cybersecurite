#!/usr/bin/env python3
"""
P4 — Export des articles pour le site React.

Lit  : data/articles.csv
Écrit: site/src/data/articles.json

Le fichier JSON produit est directement importé par site/src/lib/veille.ts.
Il contient un objet { updatedAt, articles[] } dont les champs correspondent
exactement au type TypeScript `Article`.

Usage :
    python scripts/09_export_site.py
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Chemins ────────────────────────────────────────────────────────────
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "articles.csv"
JSON_PATH = ROOT / "site" / "src" / "data" / "articles.json"

# ── Seuils CRAAP (identiques à 05_evaluer_qualite.py) ─────────────────
SEUIL_PERTINENCE = 2   # /3
SEUIL_RIGUEUR    = 6   # /8  (actualité + autorité + exactitude + objectif)
SEUIL_FIABLE     = 8   # /11 (pertinence + rigueur)

# ── Source → nom affiché ───────────────────────────────────────────────
SOURCE_DISPLAY: dict[str, str] = {
    "thehackernews.com":       "The Hacker News",
    "bleepingcomputer.com":    "BleepingComputer",
    "darkreading.com":         "Dark Reading",
    "securityweek.com":        "SecurityWeek",
    "securityaffairs.com":     "Security Affairs",
    "cert.ssi.gouv.fr":        "CERT-FR",
    "microsoft.com":           "Microsoft",
    "research.google":         "Google Security Blog",
    "helpnetsecurity.com":     "Help Net Security",
    "theregister.com":         "The Register",
    "techcrunch.com":          "TechCrunch",
    "therecord.media":         "The Record",
    "scworld.com":             "SC World",
    "infosecuritymagazine.com":"Infosecurity Magazine",
    "reuters.com":             "Reuters",
    "theguardian.com":         "The Guardian",
}


def safe_int(value: str, default: int | None = None) -> int | None:
    """Convertit une chaîne en entier, renvoie *default* si vide."""
    value = value.strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def reliability(pertinence: int | None, rigueur: int | None) -> str:
    """Détermine le niveau de fiabilité CRAAP."""
    if pertinence is None:
        return "Non évalué"
    if pertinence < SEUIL_PERTINENCE:
        return "Écarté"
    if rigueur is not None and rigueur < SEUIL_RIGUEUR:
        return "À vérifier"
    return "Fiable"


def display_source(raw: str) -> str:
    """Transforme le domaine brut en nom lisible."""
    return SOURCE_DISPLAY.get(raw.lower(), raw or "Inconnu")


def convert_row(row: dict[str, str], idx: int) -> dict:
    """Mappe une ligne CSV vers un objet Article JSON."""

    # Scores CRAAP
    pertinence = safe_int(row.get("craap_pertinence", ""))
    actualite  = safe_int(row.get("craap_actualite", ""))
    autorite   = safe_int(row.get("craap_autorite", ""))
    exactitude = safe_int(row.get("craap_exactitude", ""))
    objectif   = safe_int(row.get("craap_objectif", ""))
    total      = safe_int(row.get("craap_total", ""))

    has_craap = pertinence is not None

    rigueur = None
    if actualite is not None and autorite is not None and exactitude is not None and objectif is not None:
        rigueur = actualite + autorite + exactitude + objectif

    craap = None
    if has_craap:
        craap = {
            "pertinence": pertinence,
            "actualite":  actualite  or 0,
            "autorite":   autorite   or 0,
            "exactitude": exactitude or 0,
            "objectif":   objectif   or 0,
            "rigueur":    rigueur    or 0,
            "total":      total      or 0,
        }

    # Reprises
    nb_reprises = safe_int(row.get("nb_sources_reprise", ""), 0) or 0

    # Langue normalisée
    langue_raw = row.get("langue", "").strip().upper()
    langue = langue_raw if langue_raw in ("EN", "FR") else "EN"

    # Thème principal
    theme = row.get("theme_principal", "").strip()
    if not theme:
        for col in ("s1", "s2", "s3", "s4", "s5"):
            if str(row.get(col, "")).strip() in ("1", "1.0", "true", "True"):
                theme = col.upper()
                break

    # Notabilité
    notabilite = safe_int(row.get("score_notabilite", ""), 0) or 0

    # Statut de collecte
    statut_extraction = row.get("statut_extraction", "ok").strip() or "ok"

    # Source lisible
    source_raw = row.get("source", "").strip()
    source = display_source(source_raw)

    return {
        "id":         idx + 1,
        "date":       row.get("date_publication", "").strip(),
        "title":      row.get("titre", "").strip(),
        "source":     source,
        "language":   langue,
        "theme":      theme,
        "craap":      craap,
        "score":      total,
        "reliability": reliability(pertinence, rigueur),
        "reprises":   nb_reprises,
        "reprises_sources": [],  # Non disponible dans le CSV, à enrichir ultérieurement
        "collection": statut_extraction,
        "url":        row.get("lien", "").strip(),
        "notability": notabilite,
        "resume":     row.get("resume", "").strip(),
        "justification_craap":  row.get("craap_justification", "").strip(),
        "justification_theme":  row.get("justification_theme", "").strip(),
    }


def main() -> None:
    if not CSV_PATH.exists():
        print(f"[09_export] ❌  Fichier introuvable : {CSV_PATH}")
        sys.exit(1)

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        articles = [convert_row(row, idx) for idx, row in enumerate(reader)]

    now = datetime.now(timezone.utc)
    updated_at = now.strftime("%d %B %Y").lstrip("0")

    # Assurer l'existence du répertoire de sortie
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "updatedAt": updated_at,
        "articles":  articles,
    }

    with JSON_PATH.open("w", encoding="utf-8", newline="\n") as out:
        json.dump(payload, out, ensure_ascii=False, indent=2)

    print(f"[09_export] ✅  {len(articles)} articles → {JSON_PATH.relative_to(ROOT)}")
    print(f"[09_export]     Mis à jour : {updated_at}")

    # Statistiques rapides
    fiables  = sum(1 for a in articles if a["reliability"] == "Fiable")
    prudence = sum(1 for a in articles if a["reliability"] == "À vérifier")
    ecartes  = sum(1 for a in articles if a["reliability"] == "Écarté")
    non_eval = sum(1 for a in articles if a["reliability"] == "Non évalué")
    print(f"[09_export]     Fiable={fiables}  Prudence={prudence}  Écarté={ecartes}  Non évalué={non_eval}")


if __name__ == "__main__":
    main()
