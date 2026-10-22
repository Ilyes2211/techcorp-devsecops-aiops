# Réponses — TP TECHCORP DevSecOps & AIOps

## A5 — Secrets et permissions
**Secrets GitHub Actions** : valeurs chiffrées stockées dans GitHub (Settings → Secrets and variables → Actions), injectées dans le job via `${{ secrets.NOM }}` et masquées dans les logs. Jamais écrites dans le code ; non transmises aux PR venant de forks.

**Permissions minimales GITHUB_TOKEN** : chaque job reçoit un jeton temporaire. On déclare `permissions: contents: read` : le workflow lit le code mais ne peut ni pousser, ni créer de release, ni modifier les PR. Si une action ou une dépendance du pipeline est compromise, les dégâts sont limités (moindre privilège).

**Pourquoi un Kubernetes Secret n'est pas un coffre-fort** : il est seulement encodé en **base64** (pas chiffré). Sans chiffrement au repos activé sur etcd, il est stocké en clair ; toute personne ayant le droit `get secrets` dans le namespace (ou l'accès à etcd / aux sauvegardes) peut le lire. Il manque ce qu'apporte un vrai coffre (Vault, AWS Secrets Manager…) : rotation automatique, secrets dynamiques à durée de vie courte, audit des accès, révocation centralisée.

## Retour d'expérience A4
- Gitleaks a détecté le secret fictif et bloqué la PR (preuve rouge), puis le retrait a remis le pipeline au vert.
- Incident constaté : la PR a quand même été mergée car le compte administrateur figurait dans la *bypass list* du ruleset. Correction : bypass supprimé, le quality gate s'applique désormais à tous.
- Le secret retiré reste dans l'historique Git (Gitleaks scanne ici les fichiers actuels). Avec un vrai secret : **révocation + remplacement immédiats**, la suppression seule ne suffit pas.
