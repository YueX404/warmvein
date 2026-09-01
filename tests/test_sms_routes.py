"""SMS send/log API tests (Dev-2 Task 4). sms_service internals are out of scope."""

from datetime import datetime

from fastapi.testclient import TestClient

from main import app
import routes_sms
from services import sms_service

client = TestClient(app)


class _FakeResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, rows=None):
        self._rows = rows or []
        self.calls = []

    def execute(self, stmt, params=None):
        self.calls.append((str(stmt), params or {}))
        return _FakeResult(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _sample_log(**overrides):
    row = {
        "id": 1,
        "batch_id": "b1",
        "phone_masked": "138****1234",
        "template_code": "ALARM_RED",
        "status": 2,
        "receipt": "mock-1",
        "created_at": datetime(2026, 9, 1, 10, 5, 0),
    }
    row.update(overrides)
    return row


def _patch_db(monkeypatch, session):
    monkeypatch.setattr(routes_sms, "SessionLocal", lambda: session, raising=False)


def test_sms_send_validates():
    r = client.post("/api/sms/send", json={"templateCode": "", "phones": [], "vars": {}})
    assert r.json()["code"] == 40001


def test_sms_send_rejects_missing_phones():
    r = client.post("/api/sms/send", json={"templateCode": "ALARM_RED"})
    assert r.json()["code"] == 40001


def test_sms_send_rejects_non_list_phones():
    r = client.post("/api/sms/send", json={"templateCode": "ALARM_RED", "phones": "13812341234"})
    assert r.json()["code"] == 40001


def test_sms_send_rejects_non_string_phone():
    r = client.post("/api/sms/send", json={"templateCode": "ALARM_RED", "phones": [13812341234]})
    assert r.json()["code"] == 40001


def test_sms_send_rejects_short_phone():
    r = client.post("/api/sms/send", json={"templateCode": "ALARM_RED", "phones": ["1381234"]})
    assert r.json()["code"] == 40001


def test_sms_send_rejects_non_digit_phone():
    r = client.post(
        "/api/sms/send",
        json={"templateCode": "ALARM_RED", "phones": ["abcdefghijk"]},
    )
    assert r.json()["code"] == 40001


def test_sms_send_rejects_too_many_phones():
    phones = [f"1381234{i:04d}" for i in range(21)]
    r = client.post("/api/sms/send", json={"templateCode": "ALARM_RED", "phones": phones})
    assert r.json()["code"] == 40001


def test_sms_send_rejects_long_template_code():
    r = client.post(
        "/api/sms/send",
        json={"templateCode": "A" * 33, "phones": ["13812341234"]},
    )
    assert r.json()["code"] == 40001


def test_sms_send_rejects_non_dict_vars():
    r = client.post(
        "/api/sms/send",
        json={"templateCode": "ALARM_RED", "phones": ["13812341234"], "vars": []},
    )
    assert r.json()["code"] == 40001


def test_sms_send_template_not_found(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise ValueError("template not found")

    monkeypatch.setattr(sms_service, "send_sms", _raise)
    r = client.post(
        "/api/sms/send",
        json={"templateCode": "NO_SUCH", "phones": ["13812341234"]},
    )
    assert r.json()["code"] == 40002


def test_sms_send_ok(monkeypatch):
    monkeypatch.setattr(sms_service, "send_sms", lambda *args, **kwargs: "b1770000000")
    r = client.post(
        "/api/sms/send",
        json={
            "templateCode": "ALARM_RED",
            "phones": ["13812341234"],
            "vars": {"stationName": "一号站"},
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["batchId"] == "b1770000000"


def test_sms_log_list(monkeypatch):
    _patch_db(monkeypatch, _FakeSession(rows=[_sample_log()]))
    r = client.get("/api/sms/log", params={"batchId": "b1"})
    assert r.status_code == 200
    assert r.json()["code"] == 0


def test_sms_log_filters_batch_id(monkeypatch):
    session = _FakeSession(rows=[_sample_log()])
    _patch_db(monkeypatch, session)
    r = client.get("/api/sms/log", params={"batch_id": "b1"})
    assert r.json()["code"] == 0
    sql, params = session.calls[0]
    assert "batch_id" in sql.lower()
    assert "b1" in params.values()


def test_sms_log_returns_masked_phone(monkeypatch):
    _patch_db(monkeypatch, _FakeSession(rows=[_sample_log()]))
    r = client.get("/api/sms/log", params={"batchId": "b1"})
    row = r.json()["data"][0]
    assert row["phoneMasked"] == "138****1234"
    assert row["batchId"] == "b1"
    assert row["createdAt"] == "2026-09-01 10:05:00"


def test_sms_log_caps_result_size(monkeypatch):
    session = _FakeSession(rows=[])
    _patch_db(monkeypatch, session)
    r = client.get("/api/sms/log")
    assert r.json()["code"] == 0
    sql, params = session.calls[0]
    assert "limit" in sql.lower()
    assert params.get("limit") == 200


def test_sms_log_rejects_long_batch_id(monkeypatch):
    _patch_db(monkeypatch, _FakeSession(rows=[]))
    r = client.get("/api/sms/log", params={"batchId": "b" * 33})
    assert r.json()["code"] == 40001


def test_sms_log_returns_error_msg(monkeypatch):
    _patch_db(
        monkeypatch,
        _FakeSession(
            rows=[
                _sample_log(
                    status=3,
                    receipt="",
                    error_msg="Timeout",
                    content="【暖脉供热】一号站紧急预警",
                )
            ]
        ),
    )
    r = client.get("/api/sms/log", params={"batchId": "b1"})
    row = r.json()["data"][0]
    assert row["errorMsg"] == "Timeout"
    assert row["content"] == "【暖脉供热】一号站紧急预警"
