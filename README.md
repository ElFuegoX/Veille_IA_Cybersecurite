# Veille IA et cybersécurité – P1 (collecte et données)

## Démarrage
1. `python init_arborescence.py` : crée/complète l'arborescence (idempotent).
2. `pip install -r requirements.txt` (feedparser, trafilatura, rapidfuzz, pyyaml).
3. Coller les adresses RSS dans `config/flux.txt` (déjà rempli avec vos flux).
4. Lancer, dans l'ordre :
   - `python scripts/01_collecte.py`  → flux + `config/articles_manuels.txt` vers `data/articles.csv`
   - `python scripts/02_extraction.py` → texte, auteur, date, langue, résumé, statut
   - `python scripts/03_reprises.py`  → `nb_sources_reprise` (même histoire, éditeurs différents)

Pour développer sur l'échantillon : ajouter `--csv data/echantillon.csv` à chaque commande.

## Site Web & Application (React / Vite)
Le site de veille est situé dans le dossier `site/` :

```sh
cd site
npm install
npm run dev
```

Trois pages principales :
- **Accueil / Tableau de bord** : statistiques, graphiques par sous-thèmes, fiabilité CRAAP, timeline.
- **Veille** : tableau complet filtrable/triable des articles, recherche, export CSV public.
- **Rapport** : téléchargement du rapport PDF final.



## Colonnes remplies par P1
id, date_publication, titre, auteur, lien, source, langue, resume, statut_extraction, nb_sources_reprise.
Les autres colonnes (schéma de 26 colonnes dans `scripts/commun.py`) ne sont jamais modifiées.

## P2 – Qualité (CRAAP sur 11)
- `python scripts/04_qualite.py` → les 5 notes CRAAP (pertinence 0-3, les autres 0-2),
  craap_total (/11) et craap_justification. Seuils : 9 et plus = fiable ; 6 à 8 = à utiliser
  avec prudence ; 5 et moins = écarté (sauf cas d'étude). Rejouable (lignes extraites et non notées) ;
  `--refaire` après un changement de grille, `--ia aucune` pour les règles seules.
- Grille et mots-clés : `config/grille_qualite.yaml`. Sources reconnues (Autorité) :
  `config/sources_autorite.yaml` ; le script liste à la fin les sources inconnues à y classer.
- IA optionnelle pour exactitude et objectif : variable `GROQ_API_KEY` (ou `GEMINI_API_KEY`),
  secret GitHub du même nom pour le workflow. Sans clé : règles seules.
- Évaluation (2.5) : `data/reference_humaine.csv` = notes humaines.
  1. `python scripts/05_evaluer_qualite.py --remplir-echantillon` (ajoute ces articles à l'échantillon)
  2. `02_extraction.py` puis `04_qualite.py` avec `--csv data/echantillon.csv`
  3. `python scripts/05_evaluer_qualite.py` → accord par critère, kappa, désaccords à examiner.

## Règles
- Doublon = même lien, ou même titre (ou titre très proche) **chez la même source**. La même
  histoire chez un autre éditeur est conservée.
- `data/textes/` (texte complet) est ignoré par Git : jamais publié.
- `statut_extraction` : ok | vide | echec_http | robots | lien_redirection.
- Aucune clé API dans le dépôt.
