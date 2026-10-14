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

## P3 – Analyse (sous-thèmes)
- `python scripts/06_classifier.py` → s1 à s5 (0/1),
  `justification_theme` (citation mot pour mot). Ne traite que les lignes pertinentes
  (`craap_pertinence` ≥ 2) dont le texte existe dans `data/textes/` ou est
  re-téléchargeable (`statut_extraction` = ok). Rejouable (lignes sans `justification_theme`).
- `python scripts/08_notabilite.py` → `score_notabilite`. Recalculé à chaque
  exécution. `nb_sources_reprise` est lu depuis `03_reprises.py` (P1), pas recalculé.
- Définitions des sous-thèmes et cas limites : `config/sous_themes.md`. Prompt envoyé au modèle :
  `config/prompt_classification.txt`.
- IA : Gemini (modèle `gemini-2.5-flash`), variables `LLM_FOURNISSEUR=gemini`,
  `GEMINI_API_KEY` (secret GitHub du même nom) et `LLM_MODELE`. Quota gratuit à vérifier
  dans Google AI Studio. Sans clé ou sans texte : aucune ligne classée.
- Workflow : `.github/workflows/p3_classification.yml` (déclenché après la collecte ou
  manuellement). Pour réannoter aussi les articles déjà classés, lancer le workflow depuis
  Actions > P3 classification avec l'option `refaire` activée : il reprend tous les articles
  éligibles sans limite de 60. Le CSV est alors mis à jour et commité par GitHub Actions.
  Même groupe `concurrency` que la collecte pour ne jamais écrire le CSV en même temps.
- Mode test sans API : `06_classifier.py --lot N` affiche le prompt de N articles à coller dans le
  chat, `--importer fichier.json` réinjecte la réponse, `--evaluer` compare à l'annotation manuelle
  (`data/echantillon.csv`) sans l'écraser (sortie dans `data/echantillon_auto.csv`).
  Vérifiez les options disponibles avec `--help`.

## Règles
- Doublon = même lien, ou même titre (ou titre très proche) **chez la même source**. La même
  histoire chez un autre éditeur est conservée.
- `data/textes/` (texte complet) est ignoré par Git : jamais publié.
- `statut_extraction` : ok | vide | echec_http | robots | lien_redirection.
- Aucune clé API dans le dépôt.
