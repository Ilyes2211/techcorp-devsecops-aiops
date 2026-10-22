
## B4 — Seuil d'alerte vs détection d'anomalies statistique
La règle `ElevatedHTTP500` (`sum(increase(...{status="500"}[1m])) >= 3`, `for: 15s`) est un **seuil fixe** : simple et prévisible, mais elle ignore le volume de trafic (3 erreurs sur 10 000 requêtes déclenchent l'alerte) et le comportement habituel du service (un service qui produit normalement 10 erreurs/min alerte en permanence).
Une **détection statistique** compare la mesure à une **baseline** apprise sur l'historique (moyenne et écart-type glissants → z-score) : elle s'adapte au trafic et à la saisonnalité et ne signale que ce qui est inhabituel. En contrepartie, elle exige de l'historique et peut apprendre une situation dégradée comme « normale ».

## B5 — Fonctionnement du détecteur (aiops/detector.py)
Fenêtre de 1 min, 3 contrôles explicables :
1. seuil absolu : nb de 500 >= 3 ;
2. taux d'erreur : 500 / total >= 5 % ;
3. z-score = (erreurs − moyenne baseline) / max(écart-type, 1) >= 3, baseline = 30 dernières minutes (pas de 1 min) hors 2 dernières minutes.
Anomalie = 1 ET 2 ET (3 OU baseline < 5 points). Sévérité `critical` si taux >= 50 %. Chaque verdict liste ses raisons chiffrées.
