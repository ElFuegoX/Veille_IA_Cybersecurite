# Sous-thèmes S1 à S6 : définitions et règles

## Les six sous-thèmes

| Code | Nom | L'article parle de… |
|---|---|---|
| S1 | IA offensive | des attaquants qui utilisent l'IA comme arme : malware, phishing, deepfakes, agents d'attaque autonomes |
| S2 | Attaques contre les IA | un système d'IA pris pour cible ou point d'entrée par un tiers : prompt injection, jailbreak, empoisonnement, fuites de données |
| S3 | Code généré par IA | la qualité ou la sécurité du code produit par une IA : vibe coding, failles introduites par les assistants de code |
| S4 | IA défensive | l'IA qui protège, détecte ou répond : SOC, réponse automatisée, découverte de vulnérabilités, offres des éditeurs |
| S5 | Gouvernance et risques | la régulation, les normes, les incidents et les retours d'expérience organisationnels |
| S6 | IA et réseaux DNS | le DNS au cœur du sujet : détection, DGA, tunneling, attaques |

## Quand mettre sN à 1

Un sous-thème vaut 1 s'il occupe une part réelle de l'article : il apparaît dans le titre, ou il est développé sur au moins un paragraphe. Une mention en passant vaut 0. Plusieurs sous-thèmes peuvent valoir 1, mais en cas de doute, mettre 0.

## Thème principal

`theme_principal` est le sous-thème qui occupe l'essentiel de l'article (titre et début). Il vaut toujours S1 à S6, et son `sN` vaut forcément 1. Le tri des articles hors sujet appartient à P2 (pertinence), pas à P3.

En cas d'égalité, le plus spécifique l'emporte : S6 > S3 > S2 > (S1 ou S4) > S5.

## Cas limites

- **S1 ou S4** : suivre le point de vue de l'article (attaquant ou défenseur). Un programme d'accès réservé à des équipes de défense, qui mentionne les tests offensifs, reste S4 avec s1 = 0.
- **S1, S2 ou S5** : se demander qui agit.
  - Des humains attaquent avec l'IA : S1.
  - Quelqu'un attaque un système d'IA : S2.
  - Un modèle ou un agent agit de lui-même hors du cadre prévu : ce n'est pas S2. Si l'article porte sur l'incident et la réponse de l'organisation, thème principal S5, avec s1 = 1 seulement si le modèle a lui-même mené une attaque.
- **Injection** : une injection classique (SQL, commande) n'est pas de la prompt injection. Seule la prompt injection contre un système d'IA relève de S2.
- **S2 ou S3** : une faille dans le code produit par un assistant = S3. Une attaque contre l'assistant de code lui-même = S2.
- **S5** : seulement si la leçon organisationnelle, l'incident ou la réglementation est le cœur de l'article. Sinon, classer selon la nature technique.
- **S6** : seulement si le DNS est central. Si c'est le cas, S6 est principal et les autres sN restent à 1 s'ils s'appliquent.
- **Article ambigu** : choisir le sous-thème le plus proche et marquer `a_verifier = true`. Ne jamais forcer une étiquette en silence.

## À trancher en équipe (non résolu)

- Un programme d'accès contrôlé à des modèles (type « programme de vérification cyber ») relève-t-il de S5 ? Le consensus reste à établir.
- Les rapports généralistes (panorama des menaces, rapport annuel) où l'IA n'est qu'une section : quels sN à 1 ?
