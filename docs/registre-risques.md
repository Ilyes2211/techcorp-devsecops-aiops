# Registre des risques — TECHCORP Orders API

| # | Risque | Où | Gravité | Probabilité | Mesure corrective |
|---|--------|----|---------|-------------|-------------------|
| R1 | Dépendances vulnérables (fastapi 0.115.12 tire une version ancienne de starlette avec des CVE connues) | app/requirements.txt | Élevée | Élevée | Mise à jour des versions + scan Trivy bloquant dans la CI |
| R2 | Secret commité par erreur dans le code (aucune détection avant) | Dépôt Git | Critique | Moyenne | Gitleaks bloquant sur chaque push/PR + secrets GitHub Actions |
| R3 | Image de base non mise à jour (paquets OS vulnérables) | Dockerfile (python:3.11-slim) | Élevée | Moyenne | `apt-get upgrade` au build + scan Trivy de l'image |
| R4 | Actions GitHub non épinglées / version obsolète (Node 20) : risque supply chain | .github/workflows/ci.yml | Moyenne | Moyenne | Versions fixées, outils lancés via images Docker versionnées, permissions minimales `contents: read` |
| R5 | Grafana en accès anonyme et /metrics sans authentification | docker-compose.yml, app/main.py | Moyenne | Faible (ports liés à 127.0.0.1) | Accès anonyme réservé au labo, ports sur 127.0.0.1, auth + réseau privé en production |

Points déjà bons : conteneur non-root (`USER appuser`), `read_only: true`, `no-new-privileges`, `permissions: contents: read`.
