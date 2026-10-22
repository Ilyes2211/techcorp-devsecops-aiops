from aiops import detector
from aiops.detector import detect_anomaly, evaluate, make_report


def test_threshold():
    assert not detect_anomaly(2)
    assert detect_anomaly(3)


def test_approval_required():
    assert make_report(4, [], "pending")["human_approval_required"] is True


def test_normal_traffic_no_anomaly():
    v = evaluate(errors=0, total=50, history=[0] * 20)
    assert v["anomaly"] is False
    assert v["severity"] == "none"


def test_incident_detected_and_explained():
    v = evaluate(errors=20, total=20, history=[0] * 20)
    assert v["anomaly"] is True
    assert v["severity"] == "critical"
    assert v["checks"] == {"seuil_absolu": True, "taux_erreur": True, "zscore": True}
    assert len(v["reasons"]) >= 3


def test_low_ratio_is_not_an_incident():
    # 3 erreurs sur 1000 requêtes : le seuil simple alerterait, le taux d'erreur non
    v = evaluate(errors=3, total=1000, history=[0] * 20)
    assert detect_anomaly(3) is True
    assert v["anomaly"] is False


def test_usual_errors_within_baseline():
    # erreurs habituelles (baseline ~10/min) : pas d'anomalie statistique
    v = evaluate(errors=11, total=100, history=[10, 12, 9, 11, 10, 8, 12])
    assert v["checks"]["seuil_absolu"] and v["checks"]["taux_erreur"]
    assert v["checks"]["zscore"] is False
    assert v["anomaly"] is False


def test_short_history_falls_back_to_threshold_and_ratio():
    v = evaluate(errors=5, total=10, history=[])
    assert v["anomaly"] is True
    assert any("baseline insuffisante" in r for r in v["reasons"])


def test_run_uses_prometheus(monkeypatch):
    values = {"500": 12.0, "total": 12.0}
    monkeypatch.setattr(detector, "prom_query",
                        lambda q: values["500"] if 'status="500"' in q else values["total"])
    monkeypatch.setattr(detector, "prom_range", lambda q: [0.0] * 10)
    v = detector.run()
    assert v["anomaly"] is True and v["errors"] == 12.0
