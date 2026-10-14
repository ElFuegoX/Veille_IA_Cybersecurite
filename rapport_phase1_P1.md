# Rapport méthodologique – Phase 1 : Collecte et données
## Projet *Veille IA et cybersécurité*

> **Périmètre de ce rapport** : travail réalisé par **P1** dans le cadre du projet de veille collaborative à quatre membres. Il couvre les étapes 1.1 à 1.5 du plan de travail, soit l'ensemble de la chaîne d'acquisition des données : collecte des flux RSS, extraction du texte, déduplication et comptage des reprises, ainsi que le workflow d'automatisation GitHub Actions.

---

## 1. Vue d'ensemble

La Phase 1 constitue le **socle de données** sur lequel reposent toutes les analyses ultérieures (qualité CRAAP, classification thématique, restitution). Son rôle est de produire et maintenir un fichier CSV central (`data/articles.csv`) contenant une ligne par article unique collecté, avec ses métadonnées d'identité et de contenu.

Le pipeline se décompose en quatre scripts exécutés en séquence par GitHub Actions, deux fois par jour :

```
config/flux.txt
       │
       ▼
01_collecte.py  ──► articles.csv  (identité + résumé RSS)
       │
       ▼
02_extraction.py ──► articles.csv  (texte complet → data/textes/ [local])
                                    (résumé enrichi, auteur, date, langue)
       │
       ▼
04_qualite.py   ──► articles.csv  (scores CRAAP — hors périmètre P1)
       │
       ▼
03_reprises.py  ──► articles.csv  (nb_sources_reprise)
       │
       ▼
   git commit data/articles.csv
```

---

## 2. Architecture du dépôt (périmètre P1)

| Chemin | Rôle |
|--------|------|
| `config/flux.txt` | Liste des flux RSS (nom \| URL \| filtre optionnel) |
| `config/articles_manuels.txt` | Articles ajoutés à la main (titre \| lien) |
| `scripts/commun.py` | Module partagé : schéma CSV, I/O, nettoyage, utilitaires |
| `scripts/01_collecte.py` | Collecte des flux → CSV |
| `scripts/02_extraction.py` | Extraction du texte par `trafilatura` |
| `scripts/03_reprises.py` | Comptage des reprises inter-sources |
| `data/articles.csv` | CSV maître (versionné dans Git) |
| `data/textes/<id>.txt` | Textes complets (local uniquement, ignorés par Git) |
| `.github/workflows/collecte.yml` | Workflow d'automatisation |
| `requirements.txt` | Dépendances Python |

---

## 3. Schéma du CSV partagé

Le schéma (26 colonnes) est gelé dans `commun.py` et organisé par propriétaire. Chaque script ne touche **que ses propres colonnes**, sans jamais écraser celles des autres.

| Bloc | Colonnes | Propriétaire |
|------|----------|--------------|
| **Identité** | `id`, `date_publication`, `titre`, `auteur`, `lien`, `source`, `langue` | **P1** |
| **Contenu** | `resume`, `statut_extraction` | **P1** |
| **CRAAP** | `craap_actualite`, `craap_pertinence`, `craap_autorite`, `craap_exactitude`, `craap_objectif`, `craap_total`, `craap_justification` | P2 |
| **Sous-thèmes** | `s1`–`s5`, `justification_theme` | P3 |
| **Cas** | `nb_sources_reprise`, `score_notabilite` | P3 (calculé par P1) |
| **Contrôle** | `valide_manuel`, `relecteur` | P4 |

L'identifiant `id` est un entier à quatre chiffres (ex. `0412`), formaté par `formater_id()` et incrémenté par `prochain_id()`. Le script de collecte est **rejouable** : il ne crée jamais de doublon d'`id`, même en cas de relance.

---

## 4. Sources configurées (1.2)

Les sources sont listées dans `config/flux.txt` au format :

```
Nom de la source | URL du flux RSS | filtre=<clé>  (optionnel)
```

### Flux actuellement configurés

| Source | Type | Filtre IA |
|--------|------|-----------|
| The Hacker News | Presse spécialisée cybersécurité | ✅ |
| Google Actualités AI cybersecurity | Agrégateur (requête ciblée 7 j) | ✅ |
| Alerte Google (×4 membres) | Alertes personnalisées | — |
| BleepingComputer | Presse spécialisée cybersécurité | ✅ |
| CERT-FR | Source institutionnelle | ✅ |
| arXiv cs.CR | Prépublications académiques | ✅ |
| Microsoft Security Blog | Blog éditeur | ✅ |

Le filtre `filtre=ia` applique une expression régulière (définie dans `commun.py`) qui détecte les termes relatifs à l'IA (``AI``, ``IA``, ``LLM``, ``ChatGPT``, ``deepfake``, ``prompt injection``, etc.), tout en évitant les faux positifs sur le mot français « ai » (présence d'article).

---

## 5. Script `01_collecte.py` – Collecte des flux (1.1, 1.2, 1.5)

### 5.1 Objectif

Lire tous les flux RSS configurés, filtrer les articles non pertinents, éliminer les doublons, et ajouter les nouveaux articles au CSV avec leurs métadonnées d'identité.

### 5.2 Étapes principales

1. **Lecture du CSV existant** – `lire_csv()` charge l'ensemble des articles déjà présents et initialise l'index des doublons.
2. **Parcours des flux RSS** – `feedparser` parse chaque flux. Pour les flux Google Actualités, le titre est nettoyé du suffixe « – Nom du média » et le vrai lien est extrait (les alertes Google enveloppent le lien cible dans `google.com/url?url=...`).
3. **Filtrage thématique** – Si un flux a le paramètre `filtre=ia`, chaque article doit contenir au moins un terme de l'expression régulière dans son titre ou son résumé.
4. **Détection des doublons** (`IndexDoublons`) – Trois niveaux de détection :
   - **Même lien** (après normalisation : suppression de `www.`, des paramètres UTM, `fbclid`, `gclid`, `ref`) ;
   - **Même titre exact ET même source** ;
   - **Titre très proche ET même source** (seuil `rapidfuzz.ratio ≥ 95`).
   - Un article avec le même titre mais une **source différente** est conservé (il sera compté par `03_reprises.py`).
5. **Articles manuels** – `config/articles_manuels.txt` (format `titre | lien`) est lu en complément ; ces articles ne subissent aucun filtrage thématique.
6. **Écriture atomique** – `ecrire_csv()` écrit dans un fichier temporaire puis effectue un `os.replace()` pour garantir l'intégrité du CSV en cas d'interruption.

### 5.3 Données renseignées

| Colonne | Source |
|---------|--------|
| `id` | Incrémentation automatique |
| `date_publication` | `published_parsed` ou `updated_parsed` du flux |
| `titre` | Champ `title` nettoyé |
| `auteur` | Champ `author` (filtré des auteurs génériques) |
| `lien` | URL réelle (désenveloppée si Google) |
| `source` | Domaine extrait du lien |
| `langue` | Heuristique bilingue fr/en |
| `resume` | 300 premiers caractères du `summary` RSS |

---

## 6. Script `02_extraction.py` – Extraction du texte (1.3, 1.4)

### 6.1 Objectif

Télécharger la page web de chaque article dont `statut_extraction` est encore vide, en extraire le texte complet avec `trafilatura`, enrichir les métadonnées et produire un résumé court (chapeau).

### 6.2 Mécanisme

1. **Filtre de rejouabilité** – Seules les lignes sans `statut_extraction` sont traitées. L'option `--refaire-echecs` permet de retenter les statuts `echec_http`.
2. **Limite d'exécution** – `--limite N` (60 dans le workflow) plafonne le nombre de téléchargements par run pour respecter le timeout de 30 minutes.
3. **Respect de `robots.txt`** – `RobotFileParser` est consulté avant tout téléchargement ; le résultat est mis en cache par domaine pour éviter les requêtes répétées.
4. **Extraction** – `trafilatura.extract()` avec `favor_precision=True` extrait le corps de l'article en minimisant les éléments parasites (navigation, publicités). `trafilatura.extract_metadata()` récupère auteur, date, langue, titre et description.
5. **Seuil de qualité** – Un texte extrait de moins de 200 caractères est classé `vide` et rien n'est écrit.
6. **Enrichissement des colonnes** – Auteur, date, titre et langue sont complétés **uniquement si la colonne est encore vide** dans le CSV (principe de non-écrasement).
7. **Résumé enrichi** – `resume_court()` préfère la description de la page (≥ 80 car.) sinon prend les premières phrases, avec un plafond à 400 caractères.

### 6.3 Statuts de sortie

| Statut | Signification |
|--------|--------------|
| `ok` | Texte extrait avec succès (≥ 200 car.) |
| `vide` | Page lue mais texte trop court |
| `echec_http` | Erreur réseau ou HTTP |
| `robots` | Interdit par `robots.txt` |
| `lien_redirection` | Lien Google non résolu (inutilisable) |

### 6.4 Textes complets : stockage local uniquement

Le fichier `data/textes/<id>.txt` est écrit **localement** sur le runner GitHub Actions. Il est **systématiquement ignoré par Git** (`.gitignore : data/textes/*`). Il est utilisé uniquement pendant le job par `04_qualite.py` pour le scoring CRAAP, puis disparaît avec le runner.

> **Conséquence** : aucun texte intégral d'article n'est jamais publié dans le dépôt ni dans le site. Seul le résumé court (≤ 400 caractères) est public. Ceci respecte les droits des éditeurs et la bonne pratique définie en Phase 0.

---

## 7. Script `03_reprises.py` – Comptage des reprises (1.5)

### 7.1 Objectif

Remplir la colonne `nb_sources_reprise` : pour chaque article, indiquer combien de sources distinctes ont publié la même histoire.

### 7.2 Algorithme

L'algorithme utilise une **Union-Find (union par chemin)** appliquée sur les titres normalisés :

1. Chaque article est son propre représentant (`parent[i] = i`).
2. Pour chaque paire d'articles `(i, j)` :
   - Si même source → ignoré (on ne fusionne pas un article avec lui-même).
   - Si les deux dates sont connues et distantes de plus de **7 jours** → ignoré.
   - Si `rapidfuzz.token_set_ratio(titre_i, titre_j) ≥ 90` → les deux groupes sont fusionnés.
3. Après clustering, `nb_sources_reprise` = nombre de **sources distinctes** dans le groupe (et non pas le nombre d'articles).

### 7.3 Paramètres

| Paramètre | Valeur | Justification |
|-----------|--------|---------------|
| `SEUIL` | 90 (token_set_ratio) | Tolérant à l'ordre des mots et aux variations mineures |
| `FENETRE_JOURS` | 7 | Une dépêche est rarement reprise au-delà d'une semaine |
| `MIN_MOTS` | 5 | Évite les faux positifs sur les titres très courts |

> **Note** : Ce script recalcule l'ensemble de la colonne à chaque exécution (pas de rejouabilité partielle). Il est prévu qu'il soit éventuellement transféré à P3 pour être enrichi (entités nommées, similarité du texte complet).

---

## 8. Module `commun.py` – Utilitaires partagés

Ce module est le **contrat entre tous les scripts** : il définit le schéma du CSV, les fonctions d'I/O et les utilitaires de nettoyage utilisés par P1 (et par P2 pour ses propres scripts).

### Fonctions clés

| Fonction | Rôle |
|----------|------|
| `lire_csv()` | Lecture robuste avec `utf-8-sig`, conservation des colonnes inconnues |
| `ecrire_csv()` | Écriture atomique via fichier temporaire + `os.replace()` |
| `nettoyer_html()` | Suppression des balises HTML, désentitement HTML |
| `nettoyer_titre()` | Suppression du suffixe « – Média » des titres Google |
| `cle_lien()` | Normalisation d'URL (sans `www.`, sans UTM, sans fragment) |
| `lien_reel()` | Désenveloppement des redirections `google.com/url?url=...` |
| `domaine()` | Extraction du domaine sans `www.` |
| `detecter_langue()` | Heuristique bilingue fr/en basée sur des listes de mots outils |
| `auteur_valide()` | Rejet des auteurs génériques (`admin`, `staff`, nom du site…) |
| `resume_court()` | Chapeau de 250–400 caractères par découpe en phrases |
| `FILTRES["ia"]` | Expression régulière de filtrage thématique IA/cybersécurité |

---

## 9. Workflow GitHub Actions (`collecte.yml`)

### 9.1 Déclencheurs

| Déclencheur | Valeur | Heure locale (UTC+1/+2) |
|-------------|--------|------------------------|
| Cron matin | `0 6 * * *` (UTC) | 07h00 (hiver) / 08h00 (été) |
| Cron soir | `0 18 * * *` (UTC) | 19h00 (hiver) / 20h00 (été) |
| Manuel | `workflow_dispatch` | À la demande |

### 9.2 Séquence d'exécution

```
1. actions/checkout@v4           → clone le dépôt
2. actions/setup-python@v5       → Python 3.12 avec cache pip
3. pip install -r requirements.txt
4. python scripts/01_collecte.py
5. python scripts/02_extraction.py --limite 60
6. python scripts/04_qualite.py  (avec GROQ_API_KEY / GEMINI_API_KEY si configurés)
7. python scripts/03_reprises.py
8. git add data/articles.csv
   git commit -m "Collecte automatique YYYY-MM-DD HH:MM UTC"
   git pull --rebase && git push
```

### 9.3 Garanties techniques

| Garantie | Mécanisme |
|----------|-----------|
| **Pas d'exécutions simultanées** | `concurrency: group: collecte / cancel-in-progress: false` |
| **Timeout** | `timeout-minutes: 30` |
| **Intégrité du CSV** | Écriture atomique dans chaque script (`os.replace`) |
| **Aucune clé dans le dépôt** | Variables d'environnement injectées depuis les secrets GitHub |
| **Aucun texte complet publié** | `data/textes/*` dans `.gitignore`, `git add` limité à `articles.csv` |
| **Commit conditionnel** | `git diff --cached --quiet` → pas de commit si aucun changement |

### 9.4 Dépendances Python

```
feedparser    # parsing des flux RSS/Atom
trafilatura   # extraction du texte des pages web
rapidfuzz     # similarité de chaînes pour la déduplication
pyyaml        # lecture des fichiers de configuration YAML (P2)
```

---

## 10. Sécurité et confidentialité

| Mesure | Détail |
|--------|--------|
| Clés API | Stockées exclusivement dans les **secrets GitHub** (`GROQ_API_KEY`, `GEMINI_API_KEY`) ; jamais dans le code ni dans le dépôt |
| Textes complets | Ignorés par `.gitignore` (`data/textes/*`) ; conservés uniquement le temps du job |
| `.gitkeep` | Le dossier `data/textes/` est représenté par un fichier vide versionné pour maintenir la structure du dépôt sans publier de contenu |
| User-Agent | Identifié (`veille-ifri/1.0`) pour respecter les pratiques de bon voisinage des éditeurs |
| `robots.txt` | Consulté et respecté avant tout téléchargement |

---

## 11. Principes de développement appliqués

- **Rejouabilité** : chaque script peut être relancé sans créer de doublons ni écraser les colonnes des autres scripts.
- **Idempotence** : une ligne déjà traitée (statut non vide) est systématiquement ignorée.
- **Isolation des responsabilités** : chaque script ne touche que ses propres colonnes du CSV.
- **Développement sur l'échantillon** : pendant le développement, `data/echantillon.csv` sert de jeu de test ; le CSV maître n'est écrit que par le workflow.
- **Pas d'attente entre les équipes** : la Phase 1 ayant été priorisée (1.1 en priorité absolue), le corpus a commencé à se remplir dès la mise en place du workflow, permettant aux phases P2, P3 et P4 de travailler en parallèle sur des données réelles.
