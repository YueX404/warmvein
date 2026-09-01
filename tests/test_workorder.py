from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from services import workorder


class _FakeResult:
    def __init__(self, lastrowid=None, row=None, rows=None):
        self.lastrowid = lastrowid
        self._row = row
        self._rows = rows if rows is not None else ([row] if row else [])

    def mappings(self):
        return self

    def first(self):
        return self._row

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self):
        self.inserted = None
        self.store = {}
        self.traces = {}
        self.next_id = 1

    def execute(self, stmt, params):
        sql = str(stmt)
        if "INSERT" in sql:
            if "biz_work_order_trace" in sql:
                oid = params["o"]
                self.traces.setdefault(oid, []).append({
                    "action": params["act"],
                    "operator": params["op"],
                    "created_at": datetime(2026, 9, 1, 12, 0, 0),
                })
                return _FakeResult()
            oid = self.next_id
            self.next_id += 1
            now = datetime(2026, 9, 1, 12, 0, 0)
            self.store[oid] = {
                "order_id": oid,
                "alarm_id": params["a"],
                "assignee": params["as"],
                "status": 0,
                "created_at": now,
                "updated_at": now,
            }
            self.inserted = {"sql": sql, "params": params}
            return _FakeResult(lastrowid=oid)
        if "SELECT" in sql:
            if "biz_work_order_trace" in sql:
                return _FakeResult(rows=self.traces.get(params["o"], []))
            return _FakeResult(row=self.store.get(params["o"]))
        raise AssertionError(sql)

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_create_and_get():
    session = _FakeSession()
    with patch.object(workorder, "SessionLocal", lambda: session):
        oid = workorder.create_from_alarm(alarm_id=1, assignee="张三")
        assert oid > 0
        o = workorder.get_order(oid)
        assert o["status"] >= 0


def test_create_writes_repair_and_pending():
    session = _FakeSession()
    with patch.object(workorder, "SessionLocal", lambda: session):
        workorder.create_from_alarm(alarm_id=9, assignee="李四")
    sql = session.inserted["sql"]
    assert "status" in sql
    assert "'repair'" in sql
    assert ",0," in sql.replace(" ", "")
    assert session.inserted["params"] == {"a": 9, "as": "李四"}


def test_get_order_missing_returns_empty():
    session = _FakeSession()
    with patch.object(workorder, "SessionLocal", lambda: session):
        assert workorder.get_order(999) == {}


def test_workorder_create_validates():
    c = TestClient(app)
    r = c.post("/api/workorder/create", json={"alarmId": 0, "assignee": ""})
    assert r.json()["code"] == 40001


def test_workorder_get_not_found():
    session = _FakeSession()
    with patch("services.workorder.SessionLocal", lambda: session):
        c = TestClient(app)
        r = c.get("/api/workorder/404")
    assert r.json()["code"] == 40002


def test_workorder_create_and_get_via_api():
    session = _FakeSession()
    with patch("services.workorder.SessionLocal", lambda: session):
        c = TestClient(app)
        created = c.post(
            "/api/workorder/create",
            json={"alarmId": 3, "assignee": "王五"},
        )
        assert created.json()["code"] == 0
        oid = created.json()["data"]["orderId"]
        assert oid > 0
        got = c.get(f"/api/workorder/{oid}")
    body = got.json()
    data = body["data"]
    assert body["code"] == 0
    assert data["orderId"] == oid
    assert data["alarmId"] == 3
    assert data["assignee"] == "王五"
    assert data["status"] == 0
    assert data["statusName"] == "待派"
    assert data["createdAt"]
    assert data["updatedAt"]
    assert data["trace"][0]["action"] == "create"
    assert data["trace"][0]["operator"] == "系统"
    assert "alarm_id" not in data
    assert "order_id" not in data


def test_create_writes_trace_row():
    session = _FakeSession()
    with patch.object(workorder, "SessionLocal", lambda: session):
        oid = workorder.create_from_alarm(alarm_id=1, assignee="张三")
        o = workorder.get_order(oid)
    assert o["trace"][0]["action"] == "create"
    assert o["trace"][0]["operator"] == "系统"


def test_create_rejects_missing_alarm_id():
    c = TestClient(app)
    r = c.post("/api/workorder/create", json={"assignee": "张三"})
    assert r.json()["code"] == 40001


def test_create_rejects_missing_assignee():
    c = TestClient(app)
    r = c.post("/api/workorder/create", json={"alarmId": 1})
    assert r.json()["code"] == 40001


def test_create_rejects_non_int_alarm_id():
    c = TestClient(app)
    r = c.post("/api/workorder/create", json={"alarmId": "3", "assignee": "张三"})
    assert r.json()["code"] == 40001


def test_create_rejects_bool_alarm_id():
    c = TestClient(app)
    r = c.post("/api/workorder/create", json={"alarmId": True, "assignee": "张三"})
    assert r.json()["code"] == 40001


def test_create_rejects_blank_assignee():
    c = TestClient(app)
    r = c.post("/api/workorder/create", json={"alarmId": 1, "assignee": "  "})
    assert r.json()["code"] == 40001


def test_create_rejects_long_assignee():
    c = TestClient(app)
    r = c.post("/api/workorder/create", json={"alarmId": 1, "assignee": "a" * 33})
    assert r.json()["code"] == 40001
