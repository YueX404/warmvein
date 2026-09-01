"""Tests for 5.1 emergency plan match / activate."""

from fastapi.testclient import TestClient

from main import app
from services import plan


class _FakeResult:
    def __init__(self, row=None, lastrowid=0):
        self._row = row
        self.lastrowid = lastrowid

    def mappings(self):
        return self

    def first(self):
        return self._row


class _FakeSession:
    def __init__(self, rows=None, exists_ids=None, lastrowid=7):
        self.rows = list(rows or [])
        self.exists_ids = set(exists_ids or [])
        self.lastrowid = lastrowid
        self.inserted = None

    def execute(self, stmt, params):
        sql = str(stmt).lower()
        if "insert into biz_plan_execution" in sql:
            self.inserted = params
            return _FakeResult(lastrowid=self.lastrowid)
        if "from biz_plan where plan_id" in sql:
            found = params.get("p") in self.exists_ids
            return _FakeResult(row=(params.get("p"),) if found else None)
        ptype = params.get("t")
        level = params.get("lv")
        matched = [
            row
            for row in self.rows
            if row["plan_type"] == ptype
            and row.get("status", 1) == 1
            and (row.get("alarm_level") is None or row.get("alarm_level") == level)
        ]
        matched.sort(key=lambda r: r.get("alarm_level") or 0, reverse=True)
        return _FakeResult(row=matched[0] if matched else None)

    def commit(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_match_frost_high(monkeypatch):
    session = _FakeSession(
        rows=[
            {
                "plan_id": 1,
                "name": "冻堵应急处置预案",
                "plan_type": "freeze",
                "alarm_level": 4,
                "trigger_condition": "供回水温差异常且室外低温",
                "steps": '[{"step":1,"action":"提温加流","role":"调度","resource":"热源厂"}]',
                "resource_list": '["热源厂","抢修班"]',
                "status": 1,
            }
        ]
    )
    monkeypatch.setattr(plan, "SessionLocal", lambda: session)
    row = plan.match("frost", 4)
    assert row.get("plan_type") == "freeze" or row.get("plan_id") is not None


def test_match_maps_leak_to_burst(monkeypatch):
    session = _FakeSession(
        rows=[{"plan_id": 2, "plan_type": "burst", "alarm_level": 4, "status": 1}]
    )
    monkeypatch.setattr(plan, "SessionLocal", lambda: session)
    row = plan.match("leak", 4)
    assert row["plan_type"] == "burst"
    assert row["plan_id"] == 2


def test_match_maps_steal_to_third_party(monkeypatch):
    session = _FakeSession(
        rows=[{"plan_id": 4, "plan_type": "third_party", "alarm_level": 2, "status": 1}]
    )
    monkeypatch.setattr(plan, "SessionLocal", lambda: session)
    row = plan.match("steal", 2)
    assert row["plan_type"] == "third_party"


def test_match_empty_returns_type(monkeypatch):
    monkeypatch.setattr(plan, "SessionLocal", lambda: _FakeSession(rows=[]))
    row = plan.match("frost", 4)
    assert row["plan_type"] == "freeze"
    assert row["plan_id"] is None


def test_activate_requires_existing():
    ok_flag = plan.activate(plan_id=0)
    assert ok_flag == 0 or ok_flag is False


def test_activate_missing_plan(monkeypatch):
    monkeypatch.setattr(plan, "SessionLocal", lambda: _FakeSession(exists_ids=set()))
    assert plan.activate(plan_id=99) == 0


def test_activate_inserts_execution(monkeypatch):
    session = _FakeSession(exists_ids={3}, lastrowid=42)
    monkeypatch.setattr(plan, "SessionLocal", lambda: session)
    exec_id = plan.activate(plan_id=3, alarm_id=9, operator="dispatcher")
    assert exec_id == 42
    assert session.inserted["p"] == 3
    assert session.inserted["a"] == 9
    assert session.inserted["op"] == "dispatcher"


def test_plan_match_validates():
    client = TestClient(app)
    res = client.post("/api/plan/match", json={})
    assert res.json()["code"] == 40001


def test_plan_activate_validates():
    client = TestClient(app)
    res = client.post("/api/plan/activate", json={})
    assert res.json()["code"] == 40001
