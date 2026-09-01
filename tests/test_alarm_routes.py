"""Alarm list/ack API tests (Dev-2 Task 2). Kafka consumer and forecast are out of scope."""

from datetime import datetime

from fastapi.testclient import TestClient

from main import app
import routes_alarm

client = TestClient(app)


class _FakeResult:
    def __init__(self, rows=None, rowcount=0):
        self._rows = rows or []
        self.rowcount = rowcount

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None


class _FakeSession:
    def __init__(self, result=None, lookup_rows=None):
        self._result = result or _FakeResult()
        self._lookup = lookup_rows
        self.committed = False
        self.rolled_back = False
        self.calls = []

    def execute(self, stmt, params=None):
        sql = str(stmt)
        self.calls.append((sql, params or {}))
        if "UPDATE" in sql.upper() or self._lookup is None:
            return self._result
        return _FakeResult(self._lookup)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _sample_row(**overrides):
    row = {
        "alarm_id": 1,
        "station_id": 3,
        "level": 3,
        "type": "leak",
        "root_cause": "pressure",
        "title": "疑似泄漏",
        "status": 0,
        "created_at": datetime(2026, 8, 31, 10, 5, 0),
    }
    row.update(overrides)
    return row


def _patch_db(monkeypatch, session):
    monkeypatch.setattr(routes_alarm, "SessionLocal", lambda: session, raising=False)


def test_alarm_list(monkeypatch):
    session = _FakeSession(_FakeResult([_sample_row()]))
    _patch_db(monkeypatch, session)
    response = client.get("/api/alarm/list", params={"level": 3})
    assert response.status_code == 200 and response.json()["code"] == 0
    body = response.json()["data"]
    assert isinstance(body, list)
    assert body[0]["alarmId"] == 1
    assert body[0]["stationId"] == 3
    assert body[0]["level"] == 3
    assert body[0]["type"] == "leak"
    assert body[0]["rootCause"] == "pressure"
    assert body[0]["createdAt"] == "2026-08-31 10:05:00"
    assert ":level" in session.calls[0][0] or "level" in session.calls[0][1]


def test_alarm_list_filters_status(monkeypatch):
    session = _FakeSession(_FakeResult([]))
    _patch_db(monkeypatch, session)
    response = client.get("/api/alarm/list", params={"status": 0})
    assert response.status_code == 200 and response.json()["code"] == 0
    assert response.json()["data"] == []
    sql, params = session.calls[0]
    assert "status" in params
    assert params["status"] == 0


def test_alarm_list_rejects_invalid_level(monkeypatch):
    _patch_db(monkeypatch, _FakeSession())
    response = client.get("/api/alarm/list", params={"level": 9})
    assert response.json()["code"] == 40001


def test_alarm_ack_validates_id(monkeypatch):
    _patch_db(monkeypatch, _FakeSession())
    response = client.post("/api/alarm/ack", json={"alarmId": 0, "operator": "x"})
    assert response.json()["code"] == 40001


def test_alarm_ack_requires_operator(monkeypatch):
    _patch_db(monkeypatch, _FakeSession())
    response = client.post("/api/alarm/ack", json={"alarmId": 1})
    assert response.json()["code"] == 40001


def test_alarm_ack_not_found(monkeypatch):
    session = _FakeSession(_FakeResult(rowcount=0), lookup_rows=[])
    _patch_db(monkeypatch, session)
    response = client.post("/api/alarm/ack", json={"alarmId": 99, "operator": "张三"})
    assert response.json()["code"] == 40002
    assert session.committed is False


def test_alarm_ack_rejects_non_open_status(monkeypatch):
    session = _FakeSession(_FakeResult(rowcount=0), lookup_rows=[{"status": 3}])
    _patch_db(monkeypatch, session)
    response = client.post("/api/alarm/ack", json={"alarmId": 99, "operator": "张三"})
    assert response.json()["code"] == 40001
    assert session.committed is False


def test_alarm_ack_success(monkeypatch):
    session = _FakeSession(_FakeResult(rowcount=1))
    _patch_db(monkeypatch, session)
    response = client.post("/api/alarm/ack", json={"alarmId": 1001, "operator": "张三"})
    assert response.status_code == 200
    assert response.json()["code"] == 0
    assert response.json()["data"]["ok"] is True
    assert session.committed is True
    sql, params = session.calls[0]
    assert "status=0" in sql.replace(" ", "")
    assert params.get("alarm_id") == 1001
    assert "张三" in params.values()


def test_alarm_router_has_no_forecast():
    paths = {getattr(route, "path", "") for route in routes_alarm.router.routes}
    assert not any("forecast" in path for path in paths)
