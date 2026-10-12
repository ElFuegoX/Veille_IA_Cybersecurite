# Veille IA et cybersécurité – P1 (collecte et données)

## Démarrage
1. `python init_arborescence.py` : crée/complète l'arborescence (idempotent).
2. `pip install -r requirements.txt` (feedparser, trafilatura, rapidfuzz).
3. Coller les adresses RSS dans `config/flux.txt` (déjà rempli avec vos flux).
4. Lancer, dans l'ordre :
   - `python scripts/01_collecte.py`  → flux + `config/articles_manuels.txt` vers `data/articles.csv`
   - `python scripts/02_extraction.py` → texte, auteur, date, langue, résumé, statut
   - `python scripts/03_reprises.py`  → `nb_sources_reprise` (même histoire, éditeurs différents)

Pour développer sur l'échantillon : ajouter `--csv data/echantillon.csv` à chaque commande.

## Colonnes remplies par P1
id, date_publication, titre, auteur, lien, source, langue, resume, statut_extraction, nb_sources_reprise.
Les autres colonnes (schéma de 26 colonnes dans `scripts/commun.py`) ne sont jamais modifiées.

## Règles
- Doublon = même lien, ou même titre (ou titre très proche) **chez la même source**. La même
  histoire chez un autre éditeur est conservée.
- `data/textes/` (texte complet) est ignoré par Git : jamais publié.
- `statut_extraction` : ok | vide | echec_http | robots | lien_redirection.
- Aucune clé API dans le dépôt.
