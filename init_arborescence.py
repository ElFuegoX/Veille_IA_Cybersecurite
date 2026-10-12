#!/usr/bin/env python3
"""Étape 0 : crée (ou complète) l'arborescence locale du projet.

Idempotent : ne remplace jamais un fichier existant. Git ne suivant pas les
dossiers vides, on y place un .gitkeep.

Usage (depuis la racine du projet) : python init_arborescence.py
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE / "scripts"))
from commun import COLONNES, COLONNES_VALIDATION  # noqa: E402

DOSSIERS = ["config", "scripts", "data", "data/textes", "site", ".github/workflows"]
VIDES_A_SUIVRE = ["data/textes", "site"]

FLUX_PAR_DEFAUT = """\
# Loan
The Hacker News | https://feeds.feedburner.com/TheHackersNews
Google Actualités AI cybersecurity | https://news.google.com/rss/search?q=AI+cybersecurity+when:7d&hl=en-US&gl=US&ceid=US:en
Alerte Loan | https://www.google.fr/alerts/feeds/03912132933511960756/6914849082334786210

# Joanès
Alerte Joanès | https://www.google.com/alerts/feeds/12072149255981488419/8589077056019040891

# Donald
Alerte Donald 1 (AI-powered, adversarial AI...) | https://www.google.com/alerts/feeds/09157947447511513214/4020837709087679206
Alerte Donald 2 (artificial intelligence, LLM...) | https://www.google.com/alerts/feeds/09157947447511513214/1980280094891079751
BleepingComputer | https://www.bleepingcomputer.com/feed/
CERT-FR | https://www.cert.ssi.gouv.fr/cti/feed/
arXiv cs.CR | https://rss.arxiv.org/rss/cs.CR
Microsoft Security Blog | https://www.microsoft.com/en-us/security/blog/feed/
"""

GITIGNORE = """\
# Texte complet des articles : jamais publié
data/textes/*
!data/textes/.gitkeep
# Secrets et divers
.env
*.key
__pycache__/
*.pyc
*.tmp
"""


def ecrire_si_absent(chemin, contenu):
    p = RACINE / chemin
    if p.exists():
        print(f"  existe déjà   {chemin}")
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(contenu, encoding="utf-8-sig" if chemin.endswith(".csv") else "utf-8")
    print(f"  créé          {chemin}")


def main():
    print("Dossiers :")
    for d in DOSSIERS:
        (RACINE / d).mkdir(parents=True, exist_ok=True)
        print(f"  ok            {d}/")
    for d in VIDES_A_SUIVRE:
        (RACINE / d / ".gitkeep").touch()

    print("Fichiers :")
    ecrire_si_absent("config/flux.txt", FLUX_PAR_DEFAUT)
    ecrire_si_absent("config/articles_manuels.txt", "# titre | lien\n")
    ecrire_si_absent("data/articles.csv", ",".join(COLONNES) + "\n")
    ecrire_si_absent("data/echantillon.csv", ",".join(COLONNES) + "\n")
    ecrire_si_absent("data/validations.csv", ",".join(COLONNES_VALIDATION) + "\n")
    ecrire_si_absent(".gitignore", GITIGNORE)
    print("\nArborescence prête. Étape suivante : pip install -r requirements.txt")


if __name__ == "__main__":
    main()
