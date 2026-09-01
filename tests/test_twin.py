from algorithm.twin_recovery import simulate_recovery
from fastapi.testclient import TestClient

from main import app
from services.twin import TwinParamError, run_recovery

client = TestClient(app)


def test_converges_and_returns_time():
    curve = [70.0] * 20
    r = simulate_recovery(station_id=1, supply_curve=curve, steps=20)
    assert "tReach" in r and isinstance(r["chart"], list)
    assert r["tReach"] >= 1
    assert r["converged"] is True
    assert len(r["chart"]) == 20
    assert r["chart"][-1] >= 18.0


def test_short_curve_does_not_index_error():
    r = simulate_recovery(station_id=1, supply_curve=[70.0, 70.0], steps=8)
    assert len(r["chart"]) == 8
    assert r["converged"] is True


def test_low_supply_does_not_converge():
    r = simulate_recovery(station_id=1, supply_curve=[8.0] * 20, steps=20)
    assert r["tReach"] == 20
    assert r["converged"] is False
    assert r["hoursToReach"] is None


def test_run_recovery_accepts_curve_object():
    curve = {"targetSupplyTemp": 65.0, "rampRate": 2.0, "steps": 24}
    r = run_recovery(1, curve, 20)
    assert r["stationId"] == 1
    assert len(r["chart"]) == 24
    assert r["converged"] is True


def test_run_recovery_rejects_empty_curve():
    try:
        run_recovery(1, [], 20)
        assert False
    except TwinParamError:
        pass


def test_recovery_endpoint_ok():
    res = client.post(
        "/api/twin/simulate/recovery",
        json={"stationId": 1, "curve": [70.0] * 20},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["tReach"] >= 1
    assert isinstance(data["chart"], list)


def test_recovery_endpoint_missing_fields():
    res = client.post("/api/twin/simulate/recovery", json={"stationId": 1})
    assert res.status_code == 200
    assert res.json()["code"] == 40001


def test_recovery_endpoint_bad_station():
    res = client.post(
        "/api/twin/simulate/recovery",
        json={"stationId": 0, "curve": [70.0] * 5},
    )
    assert res.json()["code"] == 40002
