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


def test_predict_anomaly_uses_trained_pipeline(monkeypatch, tmp_path):
    import heat_train_model
    import services.forecast as forecast

    df = heat_train_model.generate_sample_data(n_samples=400, seed=42)
    model = heat_train_model.train_anomaly_model(df)
    monkeypatch.setattr(heat_train_model, "MODEL_DIR", str(tmp_path))
    monkeypatch.setattr(forecast, "MODEL_DIR", str(tmp_path))
    heat_train_model.save_model(model)
    result = forecast.predict_anomaly(
        {
            "supplyTemp": 0.5,
            "returnTemp": 40,
            "pressure": 0.4,
            "flow": 20,
            "corrosionRate": 0.15,
            "roomTemp": 18,
        }
    )
    assert result["model"] == "ml"
    assert result["is_anomaly"] == 1


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
        "description": "预计最低气温-12℃",
        "suggestion": "提升供水温度至50℃以上",
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
    assert body[0]["description"] == "预计最低气温-12℃"
    assert body[0]["suggestion"] == "提升供水温度至50℃以上"
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


def test_hive_sql_aliases_f0_columns():
    import heat_train_model

    sql = " ".join(heat_train_model.HIVE_FEATURE_SQL.split())
    assert "supply_temp AS supplyTemp" in sql
    assert "return_temp AS returnTemp" in sql
    assert "flow_rate AS flow" in sql
    assert "corrosion_rate AS corrosionRate" in sql
    assert "room_temp AS roomTemp" in sql
    assert "unavailable" not in heat_train_model.HIVE_FALLBACK_PREFIX.lower()


def test_synthetic_anomalies_are_split():
    import heat_train_model

    df = heat_train_model.generate_sample_data(n_samples=2000, seed=42)
    low_temp = df["supplyTemp"] < 5
    high_corr = df["corrosionRate"] > 0.05
    assert int(low_temp.sum()) > 0
    assert int(high_corr.sum()) > 0
    assert int((low_temp & ~high_corr).sum()) > 0
    assert int((high_corr & ~low_temp).sum()) > 0


def test_default_model_dir_is_absolute_under_repo_root():
    from pathlib import Path
    import services.forecast as forecast

    repo_root = Path(__file__).resolve().parents[1]
    resolved = Path(forecast.MODEL_DIR)
    assert resolved.is_absolute()
    assert resolved.parent == repo_root / "models" or resolved.parent == repo_root
