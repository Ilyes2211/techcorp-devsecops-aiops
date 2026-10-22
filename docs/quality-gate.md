# Quality gate — TECHCORP Security CI

Le job `Quality gate` est le contrôle requis sur `main` : il échoue si un seul des jobs ci-dessous échoue, et la PR ne peut alors pas être fusionnée.

## Ce qui bloque automatiquement la PR
| Contrôle | Outil | Bloque si |
|---|---|---|
| Tests | Pytest | un test échoue |
| Secrets | Gitleaks | n'importe quel secret détecté (règles par défaut + règle `techcorp-fake-secret`) |
| Dépendances | Trivy fs | vulnérabilité **HIGH ou CRITICAL** avec un correctif disponible |
| Image | Trivy image | vulnérabilité **HIGH ou CRITICAL** avec un correctif disponible (OS + paquets Python) |

Non bloquant (suivi en revue) : sévérité LOW/MEDIUM, vulnérabilités sans correctif (`--ignore-unfixed`) → tickets de suivi.

## Distinguer les résultats
- **Vulnérabilité exploitable** : composant réellement utilisé par l'API + correctif disponible → on corrige (mise à jour), pas d'exception.
  Exemple réel : CVE HIGH dans pip/setuptools/urllib3 → corrigées en retirant pip/setuptools de l'image finale.
- **Faux positif** : le composant n'est pas présent ou pas atteignable → analyse écrite, puis exception dans `.trivyignore` (Trivy) ou `.gitleaksignore` (Gitleaks).
- **Exception approuvée** : risque accepté temporairement. Chaque ligne de `.trivyignore` doit indiquer la justification, l'approbateur (RSSI / responsable sécurité) et une date d'expiration. Revue à chaque sprint.

## Règles
- Un secret détecté n'est jamais « accepté » : on le retire ET on le révoque (il reste dans l'historique Git).
- Les outils sont lancés via des images Docker à version fixée (gitleaks v8.21.2, trivy 0.58.1).
- Permissions minimales du workflow : `contents: read`.
