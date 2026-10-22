"""TECHCORP — détecteur d'anomalies HTTP 500 (Mission B5).

Verdict explicable en 3 contrôles, sur une fenêtre temporelle glissante :
  1. seuil absolu   : nb de 500 sur la fenêtre >= threshold (comme la règle ElevatedHTTP500)
  2. taux d'erreur  : 500 / total >= min_ratio (évite d'alerter sur 3 erreurs parmi 10 000 requêtes)
  3. z-score        : écart à la baseline des 30 dernières minutes (anomalie statistique)
Anomalie = 1 ET 2 ET (3 OU baseline insuffisante).
"""
import json
import os
import statistics
import time
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlencode

PROMETHEUS = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
ERRORS_QUERY = 'sum(increase(techcorp_http_requests_total{{path="/orders",status="500"}}[{w}]))'
TOTAL_QUERY = 'sum(increase(techcorp_http_requests_total{{path="/orders"}}[{w}]))'
STD_FLOOR = 1.0     # évite la division par zéro quand la baseline est plate (0 erreur)
MIN_HISTORY = 5     # nb minimal de points de baseline pour faire confiance au z-score


def _prom(path, params):
    url = f"{PROMETHEUS}{path}?{urlencode(params)}"
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response).get("data", {}).get("result", [])


def prom_query(expr):
    """Valeur instantanée d'une requête PromQL (0.0 si aucune série)."""
    result = _prom("/api/v1/query", {"query": expr})
    return float(result[0]["value"][1]) if result else 0.0


def prom_range(expr, minutes=30, step=60, skip_last=2):
    """Série historique (baseline) : une valeur par `step` secondes, hors dernières minutes."""
    end = time.time() - skip_last * 60
    result = _prom("/api/v1/query_range",
                   {"query": expr, "start": end - minutes * 60, "end": end, "step": step})
    return [float(v[1]) for v in result[0]["values"]] if result else []


def get_error_count(window="1m"):
    return prom_query(ERRORS_QUERY.format(w=window))


def detect_anomaly(count, threshold=3):
    """Seuil simple (compatibilité starter) : insuffisant seul, voir evaluate()."""
    return count >= threshold


def evaluate(errors, total, history, threshold=3, min_ratio=0.05, z_limit=3.0, window="1m"):
    """Retourne un verdict explicable (dict) à partir des mesures de la fenêtre et de la baseline."""
    ratio = errors / total if total > 0 else 0.0
    baseline = history if history else [0.0]
    mean = statistics.fmean(baseline)
    std = statistics.pstdev(baseline)
    zscore = (errors - mean) / max(std, STD_FLOOR)
    enough_history = len(history) >= MIN_HISTORY

    checks = {
        "seuil_absolu": errors >= threshold,
        "taux_erreur": ratio >= min_ratio,
        "zscore": zscore >= z_limit,
    }
    anomaly = checks["seuil_absolu"] and checks["taux_erreur"] and (checks["zscore"] or not enough_history)

    reasons = [
        f"{errors:.0f} HTTP 500 sur {window} (seuil {threshold}) -> {'dépassé' if checks['seuil_absolu'] else 'OK'}",
        f"taux d'erreur {ratio:.1%} (seuil {min_ratio:.0%}) -> {'dépassé' if checks['taux_erreur'] else 'OK'}",
        f"z-score {zscore:.1f} vs baseline moyenne {mean:.2f} / écart-type {std:.2f} "
        f"sur {len(history)} points (limite {z_limit}) -> {'anormal' if checks['zscore'] else 'habituel'}",
    ]
    if not enough_history:
        reasons.append(f"baseline insuffisante (< {MIN_HISTORY} points) : z-score non décisif")

    severity = "none"
    if anomaly:
        severity = "critical" if ratio >= 0.5 else "warning"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": window,
        "anomaly": anomaly,
        "severity": severity,
        "errors": errors,
        "total": total,
        "error_ratio": round(ratio, 4),
        "baseline": {"points": len(history), "mean": round(mean, 3), "std": round(std, 3)},
        "zscore": round(zscore, 2),
        "checks": checks,
        "reasons": reasons,
    }


def run(window="1m"):
    errors = prom_query(ERRORS_QUERY.format(w=window))
    total = prom_query(TOTAL_QUERY.format(w=window))
    history = prom_range(ERRORS_QUERY.format(w=window))
    return evaluate(errors, total, history, window=window)


def make_report(count, logs, hypothesis, verdict=None):
    """Squelette de rapport (complété en Mission C). L'approbation humaine est toujours requise."""
    return {
        "incident_id": "INC-2026-1042",
        "observations": {"http_500_last_minute": count, "logs": logs},
        "verdict": verdict,
        "hypothesis": hypothesis,
        "checks_read_only": [],
        "confidence": "unverified",
        "human_approval_required": True,
    }


if __name__ == "__main__":
    verdict = run()
    print(json.dumps(verdict, indent=2, ensure_ascii=False))
    print("\nANOMALIE DÉTECTÉE" if verdict["anomaly"] else "\nPas d'anomalie")
