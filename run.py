#!/usr/bin/env python3
"""
Pipeline complet de veille.  python run.py
Charge .env, installe les dépendances si besoin, lance P1-P2-P3-P4.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ── .env ───────────────────────────────────────────────────────────────
def load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        print("[run] .env introuvable. Copie .env.example et colle ta cle Gemini.")
        print("      https://aistudio.google.com/apikey")
        sys.exit(1)
    with env_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())
    if os.environ.get("GEMINI_API_KEY", "COLLE_TA_CLE_ICI") == "COLLE_TA_CLE_ICI":
        print("[run] GEMINI_API_KEY non configuree dans .env")
        sys.exit(1)


# ── Dépendances ────────────────────────────────────────────────────────
def install_deps() -> None:
    print("[run] Installation des dependances...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")],
        cwd=str(ROOT), check=True,
    )
    # google-generativeai nécessaire pour P3
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "google-generativeai"],
        cwd=str(ROOT), check=True,
    )


# ── Exécution ──────────────────────────────────────────────────────────
def run_step(name: str, cmd: list[str]) -> bool:
    t0 = time.time()
    result = subprocess.run(cmd, cwd=str(ROOT), env=os.environ.copy())
    dt = time.time() - t0
    tag = "ok" if result.returncode == 0 else "ERREUR"
    print(f"  [{tag}] {name} ({dt:.1f}s)")
    return result.returncode == 0


STEPS = [
    ("P1  Collecte RSS",              [sys.executable, "scripts/01_collecte.py"]),
    ("P1  Extraction (60 max)",       [sys.executable, "scripts/02_extraction.py", "--limite", "60"]),
    ("P1  Reprises",                  [sys.executable, "scripts/03_reprises.py"]),
    ("P2  Notation CRAAP",            [sys.executable, "scripts/04_qualite.py"]),
    ("P3  Classification IA",         [sys.executable, "scripts/06_classifier.py", "--csv", "data/articles.csv", "--limite", "60"]),
    ("P3  CVE & entreprises",         [sys.executable, "scripts/07_cve.py", "--csv", "data/articles.csv"]),
    ("P3  Notabilite",                [sys.executable, "scripts/08_notabilite.py", "--csv", "data/articles.csv"]),
    ("P4  Export JSON",               [sys.executable, "scripts/09_export_site.py"]),
]


def main() -> None:
    load_dotenv()
    print("[run] Cle Gemini detectee")

    install_deps()

    # Permettre aux scripts P3 de modifier articles.csv en local
    os.environ["GITHUB_ACTIONS"] = "true"
    # Dire au classifieur d'utiliser Gemini
    os.environ.setdefault("LLM_FOURNISSEUR", "gemini")
    os.environ.setdefault("LLM_MODELE", "gemini-3.5-flash-lite")

    print("[run] Lancement du pipeline\n")
    t0 = time.time()
    results = []
    for name, cmd in STEPS:
        ok = run_step(name, cmd)
        results.append((name, ok))

    dt = time.time() - t0
    fails = sum(1 for _, ok in results if not ok)
    print(f"\n[run] Termine en {dt:.0f}s — {len(results) - fails}/{len(results)} etapes OK")
    if fails:
        print(f"[run] {fails} etape(s) en erreur")
        sys.exit(1)


if __name__ == "__main__":
    main()
