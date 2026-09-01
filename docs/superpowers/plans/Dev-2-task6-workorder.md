# Dev-2 Task 6: 工单状态机与智能派单 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **分支：** `dev-2/feature/task6-workorder`（从 `main` 切出）
> **索引：** [Dev-2-处置流.md](./Dev-2-处置流.md)

**Goal:** 实现由预警 ID 创建工单与按 ID 查询。本 Task **不写** 巡检与前端（Task 7）。

**Architecture:** 只新增 `workorder.py` 并填充 `routes_workorder.py` 的 create/get。不 import 预警服务。`order_type` 插入时写 `repair`。合入后 Task 7 才能追加巡检路由。

**Tech Stack:** Python 3.10+ / FastAPI / MySQL。

## Global Constraints

- 见索引文档 Global Constraints。
- 独占：`services/workorder.py`、`routes_workorder.py`（仅 create/get）、`tests/test_workorder.py`。
- 状态机：`0=待派 1=已派 2=处置中 3=待核验 4=已销号`。

---

### Task 6: 工单状态机与智能派单

**Files:**
- Create: `src/python/services/workorder.py`
- Modify: `src/python/routes_workorder.py`
- Create: `tests/test_workorder.py`

**Interfaces:**
- Produces: `create_from_alarm(alarm_id, assignee) -> int`、`get_order(order_id) -> dict`、`POST /api/workorder/create`、`GET /api/workorder/{id}`

- [ ] **Step 1: 写失败测试**

```python
from services import workorder
def test_create_and_get():
    oid = workorder.create_from_alarm(alarm_id=1, assignee="张三")
    assert oid > 0
    o = workorder.get_order(oid)
    assert o["status"] >= 0
```

- [ ] **Step 2: 运行失败**

Run: `pytest tests/test_workorder.py::test_create_and_get -v`
Expected: FAIL with "cannot import" 或 "function not defined"

- [ ] **Step 3: 实现 services/workorder.py**

```python
from db import SessionLocal
from sqlalchemy import text

def create_from_alarm(alarm_id: int, assignee: str) -> int:
    with SessionLocal() as s:
        r = s.execute(text(
            "INSERT INTO biz_work_order(alarm_id, assignee, order_type, status, created_at, updated_at) "
            "VALUES(:a,:as,'repair',0,NOW(),NOW())"), {"a": alarm_id, "as": assignee})
        s.commit()
        return r.lastrowid

def get_order(order_id: int) -> dict:
    with SessionLocal() as s:
        row = s.execute(text(
            "SELECT order_id, alarm_id, assignee, status, created_at, updated_at "
            "FROM biz_work_order WHERE order_id=:o"),
            {"o": order_id}).mappings().first()
        return dict(row) if row else {}
```

- [ ] **Step 4: 实现 routes_workorder.py（不要加 patrol）**

```python
from fastapi import APIRouter
from response import ok, fail
from services import workorder
router = APIRouter()

@router.post("/workorder/create")
def api_create(body: dict):
    if not body.get("alarmId") or not body.get("assignee"):
        return fail(40001, "缺少 alarmId 或 assignee")
    return ok({"orderId": workorder.create_from_alarm(body["alarmId"], body["assignee"])})

@router.get("/workorder/{order_id}")
def api_get(order_id: int):
    o = workorder.get_order(order_id)
    return ok(o) if o else fail(40002, "工单不存在")
```

- [ ] **Step 5: 补路由测试并跑通**

```python
from fastapi.testclient import TestClient
from main import app

def test_workorder_create_validates():
    c = TestClient(app)
    r = c.post("/api/workorder/create", json={"alarmId": 0, "assignee": ""})
    assert r.json()["code"] == 40001
```

Run: `pytest tests/test_workorder.py -v`
Expected: PASS

- [ ] **Step 6: 提交** `git commit -m "feat(9.x): 工单状态机与智能派单"`
