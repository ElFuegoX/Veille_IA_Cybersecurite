## Structure de l'application

- Les trois pages (`/`, `/veille`, `/rapport`) sont des routes TanStack avec navigation et footer partagés dans le layout racine.
- Le corpus fictif, les filtres, les scores et la sérialisation CSV public sont dans un module partagé côté navigateur ; cette maquette ne nécessite pas de stockage persistant.
- Les chiffres du tableau de bord et les graphiques sont dérivés du même corpus que l'explorateur d'articles, pour que les deux vues restent cohérentes.
- Les couleurs des séries de données et les surfaces d'interface utilisent des tokens CSS sémantiques, de sorte que graphiques et contrôles suivent le même système visuel.
