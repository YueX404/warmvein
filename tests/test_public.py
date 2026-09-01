from unittest import mock

from fastapi.testclient import TestClient

from main import app
from services import public_svc

client = TestClient(app)


def _session_insert(lastrowid=1):
    session = mock.MagicMock()
    result = mock.MagicMock()
    result.lastrowid = lastrowid
    session.execute.return_value = result
    session.__enter__.return_value = session
    session.__exit__.return_value = False
    return session


def test_notify_calls_sms_api():
    with mock.patch("services.public_svc.requests.post") as p:
        p.return_value = mock.Mock(status_code=200, json=lambda: {"code": 0}, content=b"{}")
        with mock.patch(
            "services.public_svc.master_data.list_subscribed_phones",
            return_value=["13800001001"],
        ):
            r = public_svc.notify_stop_heating(station_id=1, plan_time="2026-09-01 08:00")
        assert r["sent"] is True
        p.assert_called_once()


@mock.patch("services.public_svc.SessionLocal")
def test_repair_report_creates_record(mock_session_local):
    mock_session_local.return_value = _session_insert(lastrowid=12)
    r = public_svc.create_repair_report(user_id=1, desc="不热")
    assert r["order_id"] > 0


def test_notify_no_subscriber():
    with mock.patch(
        "services.public_svc.master_data.list_subscribed_phones",
        return_value=[],
    ):
        r = public_svc.notify_stop_heating(station_id=1, plan_time="2026-09-01 08:00")
    assert r["sent"] is False
    assert r["reason"] == "no_subscriber"


def test_notify_sms_gateway_fail():
    with mock.patch("services.public_svc.requests.post") as p:
        p.side_effect = public_svc.requests.RequestException("timeout")
        with mock.patch(
            "services.public_svc.master_data.list_subscribed_phones",
            return_value=["13800001001"],
        ):
            r = public_svc.notify_stop_heating(station_id=1, plan_time="2026-09-01 08:00")
    assert r["sent"] is False
    assert r["reason"] == "sms_gateway"


@mock.patch(
    "services.public_svc.notify_stop_heating",
    return_value={"sent": True, "count": 1},
)
def test_notify_api_envelope(_mock_notify):
    res = client.post(
        "/api/public/notify/stop-heating",
        json={"stationId": 1, "planTime": "2026-09-01 08:00"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["sent"] is True


def test_notify_api_rejects_missing_station():
    res = client.post("/api/public/notify/stop-heating", json={"planTime": "2026-09-01"})
    assert res.status_code == 200
    assert res.json()["code"] == 40001


@mock.patch(
    "services.public_svc.notify_stop_heating",
    return_value={"sent": False, "reason": "sms_gateway", "count": 1},
)
def test_notify_api_sms_fail(_mock_notify):
    res = client.post("/api/public/notify/stop-heating", json={"stationId": 1})
    assert res.status_code == 200
    assert res.json()["code"] == 50003


@mock.patch("services.public_svc.create_repair_report", return_value={"order_id": 7})
def test_repair_api_envelope(_mock_create):
    res = client.post("/api/public/repair/report", json={"userId": 1, "desc": "不热"})
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["order_id"] == 7


def test_repair_api_rejects_empty_desc():
    res = client.post("/api/public/repair/report", json={"userId": 1, "desc": "  "})
    assert res.status_code == 200
    assert res.json()["code"] == 40001
