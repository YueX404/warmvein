"""Task 7: heating realtime monitor and algorithm orchestration APIs."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _offline_backends():
    """Force seed path so tests do not wait on MySQL/Redis TCP timeouts."""
    import services.heat_run as heat_run_mod

    heat_run_mod._DB_DOWN = False
    with patch("services.heat_run.SessionLocal", side_effect=OSError("offline")):
        with patch("services.heat_run.redis_client") as mock_redis:
            mock_redis.get.return_value = None
            yield
    heat_run_mod._DB_DOWN = False


def test_realtime_returns_data():
    r = client.get("/api/heat/station/1/realtime")
    assert r.status_code == 200 and r.json()["code"] == 0
    data = r.json()["data"]
    assert data["stationId"] == 1
    assert "supplyTemp" in data
    assert "frostRisk" in data
    assert data["frostRisk"] in ("low", "medium", "high")


def test_realtime_rejects_invalid_station():
    r = client.get("/api/heat/station/0/realtime")
    assert r.status_code == 200
    assert r.json()["code"] == 40002


def test_realtime_unknown_station():
    r = client.get("/api/heat/station/99999/realtime")
    assert r.status_code == 200
    assert r.json()["code"] == 40002


def test_balance_endpoint():
    r = client.get("/api/heat/balance", params={"stationId": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["stationId"] == 1
    assert isinstance(data["branches"], list)
    assert "unbalancedCount" in data
    if data["branches"]:
        branch = data["branches"][0]
        assert "beta" in branch
        assert "unbalanced" in branch


def test_balance_missing_station_id():
    r = client.get("/api/heat/balance")
    assert r.status_code == 200
    assert r.json()["code"] == 40001


def test_loss_endpoint():
    r = client.get("/api/heat/loss", params={"date": "2026-08-31"})
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["date"] == "2026-08-31"
    assert isinstance(data["pipeLoss"], list)
    assert "totalLossW" in data
    if data["pipeLoss"]:
        item = data["pipeLoss"][0]
        assert "heatLossW" in item
        assert item["heatLossW"] >= 0


def test_loss_rejects_bad_date():
    r = client.get("/api/heat/loss", params={"date": "08-31"})
    assert r.status_code == 200
    assert r.json()["code"] == 40001


def test_energy_endpoint():
    r = client.get("/api/heat/energy", params={"date": "2026-08-31", "region": "ansai"})
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["date"] == "2026-08-31"
    assert "totalHeatEnergy" in data
    assert "totalHeatLoss" in data


def test_climate_compensate():
    r = client.post("/api/console/climate-compensate", json={"stationId": 1, "tw": -5.0})
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["stationId"] == 1
    assert data["tw"] == -5.0
    assert "TgSet" in data
    assert "thSet" in data
    assert "actionId" in data


def test_climate_missing_fields():
    r = client.post("/api/console/climate-compensate", json={"stationId": 1})
    assert r.status_code == 200
    assert r.json()["code"] == 40001
