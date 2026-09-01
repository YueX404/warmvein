"""Fault forecast and remaining-life tests (Dev-2 Task 5)."""

from datetime import date, datetime

from fastapi.testclient import TestClient

from main import app
import routes_alarm
from services.forecast import FEATURE_KEYS, predict_anomaly, remain_life

client = TestClient(app)


def test_remain_life_linear():
    assert remain_life(5.0, 3.0, 0.1) == 20.0


def test_remain_life_inf_safe():
    assert remain_life(5.0, 3.0, 0) == float("inf")


def test_predict_anomaly_rule_low_supply_temp(monkeypatch, tmp_path):
    import services.forecast as forecast

    monkeypatch.setattr(forecast, "MODEL_DIR", str(tmp_path))
    result = predict_anomaly({"supplyTemp": 4, "corrosionRate": 0.01})
    assert result == {"is_anomaly": 1, "model": "rule"}


def test_predict_anomaly_rule_high_corrosion(monkeypatch, tmp_path):
    import services.forecast as forecast

    monkeypatch.setattr(forecast, "MODEL_DIR", str(tmp_path))
    result = predict_anomaly({"supplyTemp": 70, "corrosionRate": 0.06})
    assert result == {"is_anomaly": 1, "model": "rule"}


def test_predict_anomaly_rule_normal(monkeypatch, tmp_path):
    import services.forecast as forecast

    monkeypatch.setattr(forecast, "MODEL_DIR", str(tmp_path))
    result = predict_anomaly({"supplyTemp": 70, "corrosionRate": 0.01})
    assert result == {"is_anomaly": 0, "model": "rule"}


def test_predict_anomaly_uses_ml_when_model_exists(monkeypatch, tmp_path):
    import joblib
    from sklearn.ensemble import IsolationForest
    import services.forecast as forecast

    model = IsolationForest(n_estimators=8, random_state=42)
    model.fit([[70, 40, 0.4, 20, 0.01, 18]] * 30)
    joblib.dump(model, tmp_path / "anomaly_model.pkl")
    monkeypatch.setattr(forecast, "MODEL_DIR", str(tmp_path))
    result = forecast.predict_anomaly(
        {
            "supplyTemp": 70,
            "returnTemp": 40,
            "pressure": 0.4,
            "flow": 20,
            "corrosionRate": 0.01,
            "roomTemp": 18,
        }
    )
    assert result["model"] == "ml"
    assert result["is_anomaly"] in (0, 1)


class _FakeResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, rows=None):
        self._result = _FakeResult(rows)
        self.calls = []

    def execute(self, stmt, params=None):
        self.calls.append((str(stmt), params or {}))
        return self._result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _sample_forecast(**overrides):
    row = {
        "forecast_id": 201,
        "station_id": 1,
        "type": "freeze",
        "title": "未来3天冻堵风险",
        "risk_level": "high",
        "forecast_date": date(2026, 9, 2),
        "status": 0,
        "created_at": datetime(2026, 8, 31, 14, 30, 0),
    }
    row.update(overrides)
    return row


def _patch_db(monkeypatch, session):
    monkeypatch.setattr(routes_alarm, "SessionLocal", lambda: session, raising=False)


def test_forecast_list(monkeypatch):
    session = _FakeSession([_sample_forecast()])
    _patch_db(monkeypatch, session)
    response = client.get("/api/forecast/list")
    assert response.status_code == 200 and response.json()["code"] == 0
    body = response.json()["data"]
    assert isinstance(body, list)
    assert body[0]["forecastId"] == 201
    assert body[0]["stationId"] == 1
    assert body[0]["type"] == "freeze"
    assert body[0]["riskLevel"] == "high"
    assert body[0]["forecastDate"] == "2026-09-02"
    assert body[0]["createdAt"] == "2026-08-31 14:30:00"


def test_forecast_list_filters_type(monkeypatch):
    session = _FakeSession([])
    _patch_db(monkeypatch, session)
    response = client.get("/api/forecast/list", params={"type": "lifetime"})
    assert response.status_code == 200 and response.json()["code"] == 0
    _sql, params = session.calls[0]
    assert params.get("t") == "lifetime"


def test_forecast_list_rejects_invalid_type(monkeypatch):
    _patch_db(monkeypatch, _FakeSession())
    response = client.get("/api/forecast/list", params={"type": "unknown"})
    assert response.json()["code"] == 40001


def test_train_script_feature_columns_match_predictor():
    import heat_train_model

    assert tuple(heat_train_model.FEATURE_COLS) == FEATURE_KEYS
