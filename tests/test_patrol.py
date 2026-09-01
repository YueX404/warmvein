"""Tests for 9.x patrol plan generate."""

from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from services import patrol


class _FakeResult:
    def __init__(self, lastrowid=None):
        self.lastrowid = lastrowid


class _FakeSession:
    def __init__(self, lastrowid=11):
        self.lastrowid = lastrowid
        self.inserted = None
        self.committed = False

    def execute(self, stmt, params):
        sql = str(stmt)
        if "INSERT" in sql and "biz_patrol" in sql:
            self.inserted = {"sql": sql, "params": params}
            return _FakeResult(lastrowid=self.lastrowid)
        raise AssertionError(sql)

    def commit(self):
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_generate_plan_returns_id():
    session = _FakeSession()
    with patch.object(patrol, "SessionLocal", lambda: session):
        pid = patrol.generate_plan({
            "stationId": 1, "patrolType": "daily", "assignee": "李四", "planDate": "2026-09-02"
        })
    assert pid > 0
    assert session.committed is True


def test_generate_plan_writes_biz_patrol():
    session = _FakeSession(lastrowid=22)
    with patch.object(patrol, "SessionLocal", lambda: session):
        pid = patrol.generate_plan({
            "stationId": 3,
            "patrolType": "special",
            "assignee": "王五",
            "planDate": "2026-09-03",
            "planName": "换热站专项巡检",
        })
    assert pid == 22
    sql = session.inserted["sql"]
    compact = "".join(sql.split())
    assert "biz_patrol" in sql
    for col in ("station_id", "plan_name", "patrol_type", "assignee", "plan_date", "status"):
        assert col in sql
    assert ",0," in compact or "status,created_at" in compact.lower()
    assert session.inserted["params"] == {
        "sid": 3,
        "name": "换热站专项巡检",
        "pt": "special",
        "asg": "王五",
        "pd": "2026-09-03",
    }


def test_generate_plan_defaults_plan_name():
    session = _FakeSession()
    with patch.object(patrol, "SessionLocal", lambda: session):
        patrol.generate_plan({
            "stationId": 1, "patrolType": "daily", "assignee": "李四", "planDate": "2026-09-02"
        })
    assert session.inserted["params"]["name"] == "auto"


def test_generate_plan_rejects_missing_id():
    session = _FakeSession(lastrowid=None)
    with patch.object(patrol, "SessionLocal", lambda: session):
        try:
            patrol.generate_plan({
                "stationId": 1, "patrolType": "daily", "assignee": "李四", "planDate": "2026-09-02"
            })
            raised = False
        except RuntimeError:
            raised = True
    assert raised is True
    assert session.committed is False


def test_patrol_generate_validates():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={})
    body = r.json()
    assert body["code"] == 40001
    assert body["message"] == "stationId 非法"


def test_patrol_generate_ok():
    session = _FakeSession(lastrowid=6001)
    with patch("services.patrol.SessionLocal", lambda: session):
        c = TestClient(app)
        r = c.post("/api/patrol/plan/generate", json={
            "stationId": 1,
            "patrolType": "daily",
            "assignee": "王五",
            "planDate": "2026-09-01",
        })
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["patrolId"] == 6001
    assert "plan_id" not in body["data"]


def test_patrol_generate_rejects_invalid_type():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={
        "stationId": 1, "patrolType": "weekly", "assignee": "李四", "planDate": "2026-09-02"
    })
    assert r.json()["code"] == 40001


def test_patrol_generate_rejects_bool_station():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={
        "stationId": True, "patrolType": "daily", "assignee": "李四", "planDate": "2026-09-02"
    })
    assert r.json()["code"] == 40001


def test_patrol_generate_rejects_string_station():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={
        "stationId": "1", "patrolType": "daily", "assignee": "李四", "planDate": "2026-09-02"
    })
    assert r.json()["code"] == 40001


def test_patrol_generate_rejects_blank_assignee():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={
        "stationId": 1, "patrolType": "daily", "assignee": "  ", "planDate": "2026-09-02"
    })
    assert r.json()["code"] == 40001


def test_patrol_generate_rejects_long_assignee():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={
        "stationId": 1, "patrolType": "daily", "assignee": "a" * 33, "planDate": "2026-09-02"
    })
    assert r.json()["code"] == 40001


def test_patrol_generate_rejects_bad_date():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={
        "stationId": 1, "patrolType": "emergency", "assignee": "李四", "planDate": "09-02"
    })
    body = r.json()
    assert body["code"] == 40001
    assert body["message"] == "planDate 非法"


def test_patrol_generate_rejects_zero_station():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={
        "stationId": 0, "patrolType": "daily", "assignee": "李四", "planDate": "2026-09-02"
    })
    body = r.json()
    assert body["code"] == 40001
    assert body["message"] == "stationId 非法"


def test_patrol_generate_rejects_negative_station():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={
        "stationId": -1, "patrolType": "daily", "assignee": "李四", "planDate": "2026-09-02"
    })
    assert r.json()["code"] == 40001


def test_patrol_generate_rejects_long_plan_name():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={
        "stationId": 1,
        "patrolType": "daily",
        "assignee": "李四",
        "planDate": "2026-09-02",
        "planName": "a" * 65,
    })
    body = r.json()
    assert body["code"] == 40001
    assert body["message"] == "planName 非法"


def test_patrol_generate_rejects_non_string_plan_name():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={
        "stationId": 1,
        "patrolType": "daily",
        "assignee": "李四",
        "planDate": "2026-09-02",
        "planName": 12,
    })
    assert r.json()["code"] == 40001


def test_patrol_generate_accepts_date_object_via_service():
    session = _FakeSession(lastrowid=8)
    with patch.object(patrol, "SessionLocal", lambda: session):
        pid = patrol.generate_plan({
            "stationId": 2,
            "patrolType": "emergency",
            "assignee": "赵六",
            "planDate": date(2026, 9, 4),
        })
    assert pid == 8
    assert session.inserted["params"]["pd"] == date(2026, 9, 4)
    assert session.inserted["params"]["pt"] == "emergency"
