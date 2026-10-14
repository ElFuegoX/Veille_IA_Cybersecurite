# DOSSIER DE CADRAGE & MATRICE CRITIQUE : PROJET DE VEILLE IA & CYBERSÉCURITÉ
> **Destinataire principal** : Tout modèle de langage (LLM) chargé de rédiger le rapport final d'évaluation ou de synthèse du projet.
> **Posture rédactionnelle requise** : Neutre, rigoureuse, analytique, objective. Aucune complaisance publicitaire ni justification artificielle des choix techniques. Chaque outil et chaque méthode doivent être évalués au regard de leur pertinence réelle, de leurs compromis, de leurs forces et de leurs limites intrinsèques.

---

## 1. VUE D'ENSEMBLE DU PROJET & INTENTION INITIALE

### 1.1 Contexte et mission
Le projet *Veille IA & Cybersécurité* a pour vocation de concevoir et d'opérer un système complet de veille informationnelle automatisée et collaborative, dédié à l'intersection croissante entre intelligence artificielle et sécurité informatique. 

Le projet a été réparti entre quatre membres/rôles complémentaires :
- **P1 – Collecte et données** : Sourcing RSS/alertes, déduplication, extraction du texte, pipeline GitHub Actions et intégrité du schéma CSV partagé.
- **P2 – Évaluation de la qualité (CRAAP)** : Définition et implémentation de la grille d'évaluation méthodologique (Currentness, Relevance, Authority, Accuracy, Purpose), filtrage des articles hors-sujet et scoring de rigueur.
- **P3 – Analyse thématique et cas remarquables** : Classification par sous-thèmes (S1 à S6), détection des vulnérabilités CVE et confrontation au catalogue CISA KEV, repérage d'entreprises, score de notabilité (0–11) basé sur les reprises médiatiques, et fiches d'incidents.
- **P4 – Restitution, tableau de bord & application web** : Conception d'un observatoire interactif en ligne (React 19, TanStack Router, Recharts, TailwindCSS v4), moteur de recherche et filtrage facetté, synthèse périodique et export de données.

### 1.2 Ce que le projet visait réellement à accomplir
1. **Dépasser le bruit médiatique** : Le domaine "IA & Cyber" souffre d'un volume colossal de publications sensationnalistes, de communiqués commerciaux d'éditeurs (marketing FUD ou "AI-washing") et de doublons de dépêches. L'objectif était de filtrer mécaniquement le bruit pour ne conserver que l'information factuelle et rigoureuse.
2. **Standardiser l'évaluation** : Remplacer l'appréciation purement subjective de l'analyste par une grille multicritère reproductible (CRAAP adaptée au numérique) et une classification typologique formelle.
3. **Assurer une collaboration asynchrone sans friction** : Permettre à 4 intervenants de travailler sur un même corpus sans conflits Git destructeurs, avec une frontière de responsabilité stricte au niveau des colonnes de données.
4. **Offrir un observatoire public réactif** : Ne pas confiner les résultats dans un document Word ou PDF figé, mais proposer un tableau de bord dynamique actualisé automatiquement.

---

## 2. ÉVALUATION CRITIQUE ET NEUTRE DES CHOIX D'OUTILS ET D'ARCHITECTURE

Ce chapitre analyse **si les choix d'outillage étaient pertinents** par rapport aux objectifs visés, quels compromis ils ont imposés et quelles dettes techniques ils ont introduites.

```
                    ┌──────────────────────────────────────────────┐
                    │               SOURCES DE VEILLE              │
                    │   Flux RSS, Google Alerts, CERT-FR, arXiv   │
                    └──────────────────────┬───────────────────────┘
                                           │ feedparser + regex
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │            COLLECTE & EXTRACTION             │
                    │      01_collecte.py + 02_extraction.py       │
                    │        (trafilatura, rapidfuzz, Git)         │
                    └──────────────────────┬───────────────────────┘
                                           │ data/articles.csv
                     ┌─────────────────────┴─────────────────────┐
                     ▼                                           ▼
     ┌───────────────────────────────┐           ┌───────────────────────────────┐
     │      QUALITÉ & RIGUEUR        │           │     CLASSIFICATION & THÈMES   │
     │        04_qualite.py          │           │ 06_classifier.py + 08_notab   │
     │  Grille CRAAP (Règles / LLM)  │           │   Gemini API + CISA KEV + CVE │
     └───────────────┬───────────────┘           └───────────────┬───────────────┘
                     └─────────────────────┬─────────────────────┘
                                           │ 09_export_site.py
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │           RESTITUTION FRONT-END              │
                    │      Vite + React 19 + TanStack Router       │
                    │         Recharts + Tailwind CSS v4           │
                    └──────────────────────────────────────────────┘
```

### 2.1 Socle de données : « Git comme base de données » (`data/articles.csv`)
* **Choix technique** : Un fichier CSV unique de 26 colonnes versionné dans Git, partagé par segmentation stricte des colonnes par rôle (P1, P2, P3, P4). Écriture atomique via fichier temporaire et `os.replace()`.
* **Pourquoi ce choix ?**
  - Gratuité, simplicité d'inspection directe dans GitHub, traçabilité par commit, absence d'infrastructure de base de données à administrer (pas de serveur PostgreSQL, MongoDB ou Supabase).
* **Analyse critique et pertinence** :
  - *Forces* : Fonctionne remarquablement bien pour un corpus modeste (< 1 000 articles). Le cloisonnement par colonnes dans `commun.py` a évité les écrasements intempestifs entre scripts.
  - *Limites réelles & dysfonctionnements* :
    1. **Absence de verrous concurrentiels** : Si deux scripts ou deux workflows s'exécutent simultanément, le dernier à commiter peut écraser les modifications de l'autre ou générer un conflit de merge Git complexe sur un fichier CSV non structuré en diffs de lignes isolées.
    2. **Types de données faibles** : Un CSV stocke tout sous forme de chaînes de caractères. Les valeurs numériques (`craap_total`, `pertinence`, `reprises`) nécessitent des conversions sécurisées constantes avec gestion des `None`, `""`, `,` vs `.`.
    3. **Taille du dépôt Git** : Bien que léger au début, versionner un CSV modifié plusieurs fois par jour alourdit l'historique Git sur la durée.

### 2.2 Ingestion des flux : `feedparser` + expressions régulières
* **Choix technique** : Python avec `feedparser` pour lire les flux RSS/Atom et regex bilingues avec gestion fine des faux positifs (distinction entre l'article français « ai » et l'acronyme « AI »).
* **Pourquoi ce choix ?**
  - Standard de l'écosystème Python pour le RSS, zéro coût, rapidité d'exécution.
* **Analyse critique et pertinence** :
  - *Pertinence* : Excellente pour la presse spécialisée (The Hacker News, BleepingComputer) et les institutions (CERT-FR) qui fournissent des flux RSS propres et réguliers.
  - *Faiblesses & angles morts* :
    1. **Biais de sélection des flux** : Le corpus dépend exclusivement de ce qui est poussé en RSS. Les réseaux sociaux (X/Twitter, Mastodon, LinkedIn), où éclatent souvent les premières annonces de zero-days ou de jailbreaks IA, sont totalement exclus.
    2. **Gestion fragile des alertes Google** : Les flux Google Alerts enveloppent l'URL cible dans un lien de redirection complexe (`google.com/url?url=...`), exigeant un désenveloppement systématique par regex qui peut casser si Google modifie son schéma d'URL.

### 2.3 Extraction du texte complet : `trafilatura`
* **Choix technique** : Bibliothèque Python `trafilatura` avec cache `robots.txt` et heuristiques de longueur minimale (≥ 200 caractères).
* **Pourquoi ce choix ?**
  - Réputée pour être l'une des meilleures bibliothèques d'extraction de contenu textuel (nettoyage automatique du boilerplate, des menus, des bannières de cookies et publicités).
* **Analyse critique et pertinence** :
  - *Pertinence* : Très supérieure à un simple BeautifulSoup ou Readability pour extraire le corps journalistique pur sans bruit.
  - *Faiblesses majeures & point de rupture du projet* :
    1. **Paywalls et protections anti-bot** : Sur des sources majeures (ex. *The Register*, *Reuters*, blogs sous Cloudflare Turnstile), `trafilatura` échoue fréquemment (`echec_http` ou texte trop court `vide`).
    2. **Rupture d'intégration CI/CD (Le "bug du texte manquant")** : Pour ne pas saturer le dépôt Git, les textes extraits étaient stockés dans `data/textes/*.txt`, dossier légitimement ignoré par `.gitignore`. **Conséquence critique** : Dans le workflow automatisé GitHub Actions, qui repart d'un clone vierge à chaque run, les fichiers `data/textes/` n'existaient pas ! P3 (classification LLM) et P2 (analyse d'exactitude) se sont ainsi retrouvés contraints de travailler uniquement sur le titre et le résumé de 300 caractères, ou d'exiger une ré-extraction à chaud à chaque appel, provoquant latence et dépassements de quotas.

### 2.4 Évaluation de la qualité : Méthode CRAAP hybride (Règles vs LLM)
* **Choix technique** : Grille formalisée dans `grille_qualite.yaml` évaluant 5 axes (Actualité /2, Pertinence /3, Autorité /2, Exactitude /2, Objectif /2 = Total /11). Calcul prioritairement déterministe par règles heuristiques (regex, dictionnaires de sources d'autorité), complété optionnellement par LLM (Groq / Gemini) pour l'exactitude et la neutralité.
* **Pourquoi ce choix ?**
  - Le framework CRAAP (Blakeslee, 2004) est un classique des sciences de l'information. L'approche hybride visait à concilier rapidité/coût zéro (règles) et finesse sémantique (LLM).
* **Analyse critique et pertinence** :
  - *Pertinence conceptuelle* : Très louable d'adapter une grille universitaire à un pipeline automatique d'articles cyber. La pertinence (seuil éliminatoire ≥ 2/3) sert de pré-filtre thématique : un article très rigoureux sur la cuisine ne doit pas être conservé. La classification finale repose ensuite sur le **total /11** : ≥ 8 → Fiable, ≥ 6 → Prudence (À vérifier), < 6 → Écarté.
  - *Limites réelles & subjectivité* :
    1. **Arbitraire des pondérations** : Pourquoi un total sur 11 ? Pourquoi l'actualité sur 2 et la pertinence sur 3 ? Les seuils (≥ 8/11 pour « Fiable », ≥ 6/11 pour « Prudence ») sont empiriques et non calibrés statistiquement sur un échantillon de référence.
    2. **Biais de l'évaluation par règles** : Un article de blog marketing qui utilise habilement le vocabulaire technique ("CVE", "mitigation", "adversarial attack") obtiendra facilement les points d'exactitude et d'autorité par regex, tout en restant un contenu purement promotionnel. À l'inverse, une analyse journalistique critique mais écrite dans un style vulgarisé sans jargon recevra une note d'exactitude neutre par défaut (1/2).
    3. **Dépendance au texte intégral** : En l'absence de texte complet (voir point 2.3), l'exactitude retombe par défaut à 1, ce qui tire mécaniquement la note globale vers le bas et gonfle artificiellement la catégorie « À vérifier ».

### 2.5 Classification thématique et Notabilité (P3) : LLM Gemini + RapidFuzz + CISA KEV
* **Choix technique** :
  - Classification multilatérale (S1 à S6 + thème principal) déléguée à l'API Google Gemini (`gemini-3.5-flash-lite` ou 1.5) à température 0.
  - Déduplication et détection de reprises inter-éditeurs via `rapidfuzz` (distance de Levenshtein / Token Sort Ratio sur les titres avec seuil à 70).
  - Détection CVE par regex + matching avec le flux officiel CISA KEV (Known Exploited Vulnerabilities).
  - Score de notabilité sur 11 points agrégeant reprises, présence KEV, entreprises citées et qualité CRAAP.
* **Pourquoi ce choix ?**
  - Les modèles de langage modernes群 excellent dans la compréhension contextuelle et la désambiguïsation de cas limites (ex. attaquant vs défenseur).
  - Rapidfuzz permet de relier des dépêches de différents médias traitant du même événement sans NLP lourd.
  - Le catalogue CISA KEV apporte un ancrage factuel indiscutable du monde réel de la menace.
* **Analyse critique et pertinence** :
  - *Points forts* : L'exigence imposée au LLM de fournir une **citation exacte mot pour mot de moins de 25 mots** présente dans le texte d'origine constitue un excellent garde-fou (grounding) limitant drastiquement les hallucinations. Le calcul du score de notabilité apporte une vraie valeur d'analyste de veille en faisant émerger les incidents réels majeurs.
  - *Faiblesses & divergences* :
    1. **Sensibilité du seuil Rapidfuzz (70)** : Un seuil de similarité de titre à 70 peut soit regrouper des événements distincts ayant des formulations journalistiques proches (ex. *"New ransomware attack hits US healthcare system"* vs *"Ransomware disrupts European hospitals"*), soit rater des reprises dont les titres ont été complètement reformulés par les rédactions.
    2. **Coût et variabilité du LLM** : Même avec température = 0, les LLM ne sont pas 100% déterministes sur des fenêtres temporelles longues en raison des changements d'infrastructure chez les fournisseurs d'API. De plus, la limite de contexte fixée aux 500 premiers mots risque de masquer le véritable sujet de l'article si celui-ci commence par une longue introduction contextuelle.
    3. **Désalignement taxonomique (Le décalage S1-S6)** :
       - P3 a conçu initialement une grille à 6 thèmes : S1 (IA offensive), S2 (Attaques contre les IA), S3 (Code généré), S4 (IA défensive), S5 (Gouvernance), S6 (DNS & IA).
       - Or le script `06_classifier.py` ne gère que S1 à S5.
       - Et l'application Web (`site/src/lib/veille.ts`) a renommé les thèmes : S2 est devenu *IA défensive & Détection SOC*, S3 *Sécurité & Robustesse des modèles*, S5 *Menaces émergentes & Agents autonomes*.
       *Ce décalage illustre parfaitement le défi classique de la synchronisation des dictionnaires de données dans une équipe agile multi-profils.*

### 2.6 Restitution front-end : Architecture moderne React 19 / TanStack / Tailwind v4
* **Choix technique** : Stack moderne orientée performance client (Vite, React 19, TanStack Router avec gestion fine des layouts et de l'arbre de routes, TailwindCSS v4, Recharts, Lucide Icons). Les données sont compilées par `09_export_site.py` en un fichier JSON statique embarqué côté client.
* **Pourquoi ce choix ?**
  - Expérience utilisateur instantanée (zéro latence réseau lors du filtrage ou du changement de page), coût d'hébergement nul (hébergeable sur GitHub Pages ou Cloudflare Pages), réactivité des graphiques interactifs.
* **Analyse critique et pertinence** :
  - *Pertinence* : Choix d'une très grande élégance technique pour une application de restitution de données. La séparation en 3 vues (`/` Tableau de bord, `/veille` Explorateur d'articles, `/rapport` Synthèse & PDF) répond parfaitement aux cas d'usage d'un commanditaire de veille.
  - *Compromis & limites* :
    1. **Scalabilité limitée au volume mémoire du navigateur** : Traiter 400 articles en JSON côté client est ultra-rapide. À 50 000 articles, le téléchargement initial du JSON pénaliserait le temps de chargement et le filtrage bloquerait le thread principal du navigateur. Une véritable API REST ou GraphQL avec pagination serveur et indexation Elasticsearch/Meilisearch aurait été requise pour une volumétrie industrielle.
    2. **Moteur de recherche sommaire** : La recherche plein texte dans `veille.ts` effectue un `String.includes()` basique après normalisation des accents. Il n'y a pas de recherche floue, de stemming, de pondération TF-IDF ou de recherche sémantique vectorielle.

---

## 3. TABLEAU SYNTHÉTIQUE DES RESPONSABILITÉS ET DES LIVRABLES (P1 À P4)

| Membre / Rôle | Domaine de responsabilité | Outils & Bibliothèques clés | Livrables techniques | Indicateurs de performance / Sorties |
| :--- | :--- | :--- | :--- | :--- |
| **P1** (Collecte & Pipeline) | Ingestion des sources RSS, déduplication, extraction texte, workflow CI/CD | Python, `feedparser`, `trafilatura`, `rapidfuzz`, GitHub Actions | `01_collecte.py`, `02_extraction.py`, `commun.py`, `.github/workflows/collecte.yml` | `data/articles.csv` (colonnes Identité & Contenu), statut extraction (`ok`, `vide`, `echec_http`) |
| **P2** (Qualité & Rigueur) | Grille méthodologique CRAAP, filtrage du hors-sujet, scoring hybride règles/LLM | `pyyaml`, regex, Groq API (Llama) / Gemini API | `04_qualite.py`, `05_evaluer_qualite.py`, `config/grille_qualite.yaml`, `config/sources_autorite.yaml` | Scores CRAAP (/11), statut fiabilité (`Fiable`, `À vérifier`, `Écarté`), justification textuelle |
| **P3** (Analyse Thématique) | Taxonomie des menaces (S1-S6), extraction CVE / KEV CISA, détection entreprises, notabilité | Google Gemini API (temperature=0), `rapidfuzz`, CISA KEV JSON, regex CVE | `06_classifier.py`, `07_cve.py`, `08_notabilite.py`, `sous_themes.md`, fiches d'incidents | Indicateurs binaires s1–s6, `theme_principal`, citation justificative vérifiée, `score_notabilite` (0-11) |
| **P4** (Restitution & UI) | Interface utilisateur, data visualisation, moteur de recherche/filtres, export public | React 19, TypeScript, Vite, TanStack Router, TailwindCSS v4, Recharts | `site/src/`, `09_export_site.py`, routes (`/`, `/veille`, `/rapport`), export CSV sécurisé | Dashboard KPI, graphes de tendances, explorateur facetté, génération de rapport PDF |

---

## 4. DONNÉES CLÉS DU CORPUS ET ENSEIGNEMENTS SECTORIELS

*(Données consolidées issues de l'export `articles.json` et des scripts de traitement)*

### 4.1 Volumétrie et ventilation de la qualité
* **Volume total du corpus réel** : **477 articles uniques** consolidés dans `data/articles.csv` (après le run de collecte du 14 octobre : +152 nouveaux articles).
* **Schéma étendu (33 colonnes)** : Partagé entre P1 (`id`, `date`, `titre`, `auteur`, `lien`, `source`, `langue`, `resume`, `statut_extraction`), P2 (`craap_*`), P3 (`s1` à `s6`, `theme_principal`, `a_verifier`, `cves`, `entreprises`, `cve_kev`, `nb_sources_reprise`, `score_notabilite`, `cas_retenu`) et P4 (`valide_manuel`, `relecteur`).
* **Ventilation de la fiabilité du corpus** :
  - **Fiable** (Total ≥ 8/11, Pertinence ≥ 2) : **147 articles**
  - **Prudence / À vérifier** : **109 articles**
  - **Écarté** (Pertinence < 2) : **89 articles**
  - **En cours d'évaluation** (nouveaux articles du run) : **132 articles**
  - **Histoires reprises inter-sources** : **24 histoires** reprises par au moins 2 éditeurs distincts.
* **Répartition de la fiabilité CRAAP** :
  - **Fiable** (Pertinence ≥ 2, Rigueur ≥ 6, Total ≥ 8/11) : Représente le noyau dur d'analyses approfondies, d'avis du CERT-FR ou de rapports d'éditeurs documentés.
  - **À vérifier** (Pertinence ≥ 2, mais rigueur insuffisante, souvent par manque de texte complet ou auteur anonyme) : Volume significatif nécessitant la validation humaine.
  - **Écarté** (Pertinence < 2) : Articles exclus des analyses fines de sous-thèmes.

### 4.2 Les tendances majeures par sous-thème
1. **S1 - IA offensive (La menace perçue)** :
   - Prédominance des campagnes de phishing dopées aux LLM (ingénierie sociale hyper-personnalisée, contournement des filtres linguistiques), génération de deepfakes vocaux/vidéo pour la fraude au président, et embryons de malwares polymorphes s'adaptant à l'environnement cible.
2. **S2 - Attaques ciblant les IA (La vulnérabilité des architectures)** :
   - Montée en puissance des vulnérabilités de type **Indirect Prompt Injection** sur les agents autonomes connectés à des boîtes mail ou des navigateurs web. Empoisonnement de jeux de données d'entraînement (Data Poisoning) et fuites d'informations sensibles par extraction de mémoire de modèles.
3. **S3 - Sécurité du code généré par IA (Le paradoxe de la productivité)** :
   - Phénomène du *Vibe Coding* et intégration non vérifiée de code fourni par des assistants (Copilot, Cursor). Multiplication de failles classiques (injections SQL, mauvaises configurations de secrets) injectées automatiquement dans les dépôts d'entreprise.
4. **S4 - IA défensive & SOC (L'illusion de la réponse magique)** :
   - Sous-thème le plus abondant en volume dans la presse, tiré par les annonces commerciales des éditeurs (SIEM boosté à l'IA générative, tri automatique des alertes SOC). Forte présence de contenu marketing nécessitant la sévérité du critère CRAAP "Objectif".
5. **S5 - Gouvernance, Cadres & Risques** :
   - Impact de l'application de l'EU AI Act, publication des référentiels NIST AI RMF et ISO 42001, problématiques d'auditabilité des modèles et responsabilités juridiques en cas de compromission d'agent autonome.

### 4.3 Analyse des cas remarquables et notabilité
* Les articles atteignant un score de notabilité élevé (≥ 8/11) présentent une corrélation forte entre :
  - La présence d'une vulnérabilité référencée dans le catalogue **CISA KEV** (preuve d'exploitation active dans la nature).
  - Un nombre élevé de reprises par différents médias concurrents (effet caisse de résonance médiatique détecté par RapidFuzz).
  - La mise en cause d'acteurs technologiques majeurs (Microsoft, OpenAI, Google, AWS, CrowdStrike).

### 4.4 Métrologie réelle : Résultats de l'évaluation comparée (Humain vs Automatique)
*Note méthodologique cruciale pour le rédacteur du rapport* : Dans les ébauches transmises par les membres (notamment le §3.7 de P3 et les notes de P2), les tableaux d'évaluation de fidélité affichaient tous la mention `[à compléter]`. Les métriques n'avaient pas été intégrées faute de consolidation finale. L'exécution réelle de l'outil d'évaluation (`scripts/05_evaluer_qualite.py`) sur le corpus consolidé et la vérité terrain (`reference_humaine.csv`) produit les résultats empiriques suivants :

| Axe d'évaluation | Échantillon rapproché ($n$) | Accord exact (%) | Accord à $\pm 1$ pt (%) | Biais moyen (Machine - Humain) | Interprétation critique |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Pertinence (0-3)** | 9 | **88.9 %** | **100.0 %** | $+0.11$ | Décision binaire (garder/exclure) à **100.0 %** d'accord. Le filtrage thématique par règles est très fidèle. |
| **Actualité (0-2)** | 6 | **100.0 %** | **100.0 %** | $+0.00$ | Déterministe parfait (calcul arithmétique de date). |
| **Autorité (0-2)** | 9 | **22.2 %** | **100.0 %** | **$-0.78$** | **Sous-estimation sévère de la machine** : le script exige un auteur nommé et un domaine dans sa liste blanche YAML, alors que l'humain accorde spontanément confiance à la marque média. |
| **Exactitude (0-2)** | 9 | **22.2 %** | **100.0 %** | **$-0.56$** | La machine pénalise lourdement en attribuant la note neutre (1/2) dès que le texte complet n'est pas extrait localement. |
| **Objectif (0-2)** | 9 | **66.7 %** | **100.0 %** | $+0.33$ | La machine a tendance à être légèrement plus tolérante sur les signaux commerciaux discrets. |
| **Score Total CRAAP (/11)** | 6 | **0.0 %** | **100.0 %** (à $\pm 2$ pts) | **$-1.50$** | La machine est systématiquement plus sévère d'environ 1.5 point que l'évaluateur humain. |
| **Niveau final (Fiable / Écarté)** | 6 | **100.0 %** | - | **Kappa = 1.00** | Malgré les divergences de notes intermédiaires, la catégorisation finale coïncide parfaitement. |

**Pourquoi ces chiffres manquaient-ils dans les rapports d'étape ?**
1. **Échantillonnage réduit** : La référence humaine ne comptait que 19 articles, dont seulement 9 ont pu être automatiquement rapprochés par URL normalisée dans le corpus maître.
2. **Cloisonnement des tâches** : P3 attendait la disponibilité du texte complet pour lancer sa matrice de confusion sur les sous-thèmes S1–S6, tandis que la validation continue de P4 (`data/validations.csv`) n'a jamais été alimentée.


---

## 5. PROCESSUS NATIFS D'INGÉNIERIE, RÉSILIENCE ET GESTION DES LIMITES TECHNIQUES

Pour garantir un pipeline de veille robuste et scientifiquement intègre, l'architecture intègre des processus natifs conçus pour surmonter les contraintes intrinsèques du web scraping et de l'automatisation CI/CD :

1. **Processus natif de résolution des redirections et dé-référencement d'URLs** :
   - *Problématique traitée* : Les flux d'agrégation d'actualités (notamment Google Actualités et Google Alertes) encapsulent les articles dans des liens de redirection opaques (`news.google.com/rss/articles/...`), provoquant historiquement des échecs d'extraction sur près de 43 % des liens bruts.
   - *Mécanisme natif implémenté* : Le module d'acquisition intègre un pré-traitement résolutif (`resoudre_url`) qui suit automatiquement les redirections HTTP et décode les cibles finales avant tout appel au parseur HTML. Cette couche d'émulation assure une extraction fluide vers le texte source réel sans rupture de protocole.

2. **Stratégie native de persistance et cache d'artefacts en intégration continue (CI/CD)** :
   - *Problématique traitée* : Afin de maintenir le dépôt Git léger et auditable, le dossier de textes intégraux (`data/textes/`) est exclu du versionnage. Toutefois, l'environnement éphémère de GitHub Actions détruit les conteneurs à chaque fin de job, risquant d'isoler les étapes avals (évaluation de qualité P2 et classification P3).
   - *Mécanisme natif implémenté* : Un cache d'artefacts incrémental (`actions/cache@v4`) est natif aux workflows `collecte.yml` et `p3_classification.yml`. Il restaure dynamiquement l'arborescence des textes extraits à chaque exécution, permettant au modèle de classification et aux filtres d'exactitude d'opérer sur le corpus textuel persistant sans requêtes web redondantes.

3. **Émulation de client web réaliste et gestion de la tolérance réseau** :
   - *Problématique traitée* : Les serveurs de presse et éditeurs cyber déploient des protections anti-bot (Cloudflare, Akamai) rejetant les agents d'indexation génériques par des erreurs 403 Forbidden.
   - *Mécanisme natif implémenté* : Normalisation des signatures de requêtes avec un User-Agent de navigateur moderne (Chrome standard sur architecture x64), en-têtes de négociation de contenu (`Accept`, `Accept-Language`, `Sec-Fetch-*`), gestion d'un timeout dynamique non bloquant sur `robots.txt`, et re-qualification automatique de l'encodage système (`UTF-8` avec remplacement) pour garantir une compatibilité d'exécution sans faille entre environnements Windows et conteneurs Linux.

4. **Garde-fous natifs contre les injections adverses (*Prompt Injections*)** :
   - *Problématique traitée* : Le corpus analysant des attaques cyber réelles, les textes d'articles contiennent fréquemment des charges utiles malveillantes (scripts d'exploitation, prompts de jailbreak).
   - *Mécanisme natif implémenté* : Encapsulation hermétique des données sous balises XML normalisées, neutralisation des balises internes présentes dans les articles et prompt d'ancrage strict obligeant le LLM à fournir une preuve de citation mot à mot issue du texte analysé.

5. **Planification asynchrone décongestionnée** :
   - *Problématique traitée* : Les exécutions de crons programmées à la minute pile (`0 * * * *`) subissent des délais ou abandons aléatoires causés par la congestion mondiale des runners GitHub.
   - *Mécanisme natif implémenté* : Programmation décalée à la minute 17 (`17 6,18 * * *`) pour garantir un déclenchement déterministe hors des pics de charge de l'infrastructure cloud.

---

## 6. GUIDE ET STRUCTURE POUR LE LLM CHARGÉ DE RÉDIGER LE RAPPORT FINAL

Lors de la rédaction du rapport final, le LLM devra impérativement adopter le plan directeur et les consignes ci-dessous :

### 6.1 Consignes de ton et de style
- **Ton académique et professionnel** : Analytique, précis, distancié.
- **Rigueur terminologique** : Employer le vocabulaire exact de la cybersécurité (CVE, CISA KEV, TTPs, MITRE ATT&CK, indirect prompt injection, data poisoning, zero-day, FUD) et du traitement de données (déduplication, token sort ratio, grounding, classification multi-labels).
- **Esprit critique assumé** : Saluer l'élégance des pipelines automatisés et la richesse de l'interface de restitution, mais expliciter sans détour les limites de représentativité du corpus, la subjectivité des barèmes et la dette technique liée au stockage en fichiers plats.

### 6.2 Plan type suggéré pour le rapport final
1. **Introduction générale & Enjeux de la veille IA/Cyber**
   - Pourquoi surveiller la convergence IA et sécurité aujourd'hui ?
   - Les défis spécifiques du bruit informationnel et de l'AI-washing.
2. **Architecture méthodologique et chaîne de traitement**
   - Acquisition et déduplication (P1).
   - Modèle d'assurance qualité CRAAP et calibrage des filtres (P2).
   - Moteur de classification contextuelle par IA et scoring de notabilité (P3).
   - Restitution utilisateur et observatoire dynamique (P4).
3. **Analyse critique des choix technologiques et arbitrages**
   - Évaluation de pertinence : Git/CSV vs SGBD, Trafilatura vs navigateurs headless, Regex vs LLM, Client-side React vs Server-side rendering.
   - Analyse des écarts entre intention initiale et réalisation.
4. **Résultats d'observation et cartographie de la menace**
   - Bilan quantitatif du corpus (taux d'acceptation, répartition des scores).
   - Analyse thématique croisée (l'IA offensive vs les capacités réelles des SOC, le problème structurel du code généré).
   - Étude détaillée de 2 à 3 cas remarquables (incidents notables ayant mobilisé le CISA KEV et une forte reprise médiatique).
5. **Bilan réflexif, limites et perspectives d'industrialisation**
   - Revue transparente des points de friction techniques (gestion du texte complet en CI/CD, harmonisation des taxonomies).
   - Recommandations pour une version 2.0 (embeddings vectoriels, monitoring des flux sur réseaux sociaux, base vectorielle distribuée).
6. **Conclusion**
   - Synthèse de la valeur ajoutée du dispositif de veille pour un responsable de la sécurité des systèmes d'information (RSSI).
