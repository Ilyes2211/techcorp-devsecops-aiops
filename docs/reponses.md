# Réponses — TP TECHCORP DevSecOps & AIOps

## A5 — Secrets et permissions
**Secrets GitHub Actions** : valeurs chiffrées stockées dans GitHub (Settings → Secrets and variables → Actions), injectées dans le job via `${{ secrets.NOM }}` et masquées dans les logs. Jamais écrites dans le code ; non transmises aux PR venant de forks.

**Permissions minimales GITHUB_TOKEN** : chaque job reçoit un jeton temporaire. On déclare `permissions: contents: read` : le workflow lit le code mais ne peut ni pousser, ni créer de release, ni modifier les PR. Si une action ou une dépendance du pipeline est compromise, les dégâts sont limités (moindre privilège).

**Pourquoi un Kubernetes Secret n'est pas un coffre-fort** : il est seulement encodé en **base64** (pas chiffré). Sans chiffrement au repos activé sur etcd, il est stocké en clair ; toute personne ayant le droit `get secrets` dans le namespace (ou l'accès à etcd / aux sauvegardes) peut le lire. Il manque ce qu'apporte un vrai coffre (Vault, AWS Secrets Manager…) : rotation automatique, secrets dynamiques à durée de vie courte, audit des accès, révocation centralisée.

## Retour d'expérience A4
- Gitleaks a détecté le secret fictif et bloqué la PR (preuve rouge), puis le retrait a remis le pipeline au vert.
- Incident constaté : la PR a quand même été mergée car le compte administrateur figurait dans la *bypass list* du ruleset. Correction : bypass supprimé, le quality gate s'applique désormais à tous.
- Le secret retiré reste dans l'historique Git (Gitleaks scanne ici les fichiers actuels). Avec un vrai secret : **révocation + remplacement immédiats**, la suppression seule ne suffit pas.

## B4 — Seuil d'alerte vs détection d'anomalies statistique
La règle `ElevatedHTTP500` (`sum(increase(...{status="500"}[1m])) >= 3`, `for: 15s`) est un **seuil fixe** : simple et prévisible, mais elle ignore le volume de trafic (3 erreurs sur 10 000 requêtes déclenchent l'alerte) et le comportement habituel du service (un service qui produit normalement 10 erreurs/min alerte en permanence).
Une **détection statistique** compare la mesure à une **baseline** apprise sur l'historique (moyenne et écart-type glissants → z-score) : elle s'adapte au trafic et à la saisonnalité et ne signale que ce qui est inhabituel. En contrepartie, elle exige de l'historique et peut apprendre une situation dégradée comme « normale ».

## B5 — Fonctionnement du détecteur (aiops/detector.py)
Fenêtre de 1 min, 3 contrôles explicables :
1. seuil absolu : nb de 500 >= 3 ;
2. taux d'erreur : 500 / total >= 5 % ;
3. z-score = (erreurs − moyenne baseline) / max(écart-type, 1) >= 3, baseline = 30 dernières minutes (pas de 1 min) hors 2 dernières minutes.
Anomalie = 1 ET 2 ET (3 OU baseline < 5 points). Sévérité `critical` si taux >= 50 %. Chaque verdict liste ses raisons chiffrées.
