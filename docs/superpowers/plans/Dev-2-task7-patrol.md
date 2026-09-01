# Dev-2 Task 7: 巡检计划生成与工单页面 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **分支：** `dev-2/feature/task7-patrol`
> **基线：** Task 6（`dev-2/feature/task6-workorder`）已合入 `main`，或叠在该分支上。禁止与 Task 6 同时改 `routes_workorder.py`。
> **索引：** [Dev-2-处置流.md](./Dev-2-处置流.md)

**Goal:** 实现巡检计划生成 API，并填充工单/巡检前端。巡检作为 `WorkOrder.vue` 的 Tab，**不改** `web/src/router/index.ts`。

**Architecture:** 新建 `patrol.py`。只在 `routes_workorder.py` **追加** `/patrol/plan/generate`，保留 Task 6 的 create/get。表名是 `biz_patrol`。

**Tech Stack:** Python 3.10+ / FastAPI / MySQL；前端 Vue3+TS。

## Global Constraints

- 见索引文档 Global Constraints。
- 独占：`services/patrol.py`、`tests/test_patrol.py`、工单前端文件；`routes_workorder.py` 仅追加巡检路由。

---

### Task 7: 巡检计划生成 + 工单页面

**Files:**
- Create: `src/python/services/patrol.py`
- Modify: `src/python/routes_workorder.py`（仅追加）
- Create: `tests/test_patrol.py`
- Modify: `web/src/pages/workorder/WorkOrder.vue`
- Create（可选）: `web/src/pages/workorder/Patrol.vue`（仅被 WorkOrder 引用）
- Create: `web/src/services/workorder.api.ts`
- Modify: `web/src/mock/workorder.mock.ts`

**Interfaces:**
- Produces: `patrol.generate_plan(rule) -> int`、`POST /api/patrol/plan/generate`
- `rule` 至少含 `stationId`、`patrolType`（`daily`|`special`|`emergency`）、`assignee`、`planDate`

- [ ] **Step 1: 确认基线**

`routes_workorder.py` 中应已有 `/workorder/create` 与 `/workorder/{order_id}`。没有则先合入 Task 6。

- [ ] **Step 2: 写失败测试**

```python
from services import patrol

def test_generate_plan_returns_id():
    pid = patrol.generate_plan({
        "stationId": 1, "patrolType": "daily", "assignee": "李四", "planDate": "2026-09-02"
    })
    assert pid > 0
```

- [ ] **Step 3: 运行失败**

Run: `pytest tests/test_patrol.py -v`
Expected: FAIL

- [ ] **Step 4: 实现 services/patrol.py**

```python
from db import SessionLocal
from sqlalchemy import text

def generate_plan(rule: dict) -> int:
    with SessionLocal() as s:
        r = s.execute(text(
            "INSERT INTO biz_patrol(station_id, plan_name, patrol_type, assignee, plan_date, status, created_at, updated_at) "
            "VALUES(:sid,:name,:pt,:asg,:pd,0,NOW(),NOW())"),
            {"sid": rule["stationId"], "name": rule.get("planName", "auto"),
             "pt": rule["patrolType"], "asg": rule["assignee"], "pd": rule["planDate"]})
        s.commit()
        return r.lastrowid
```

- [ ] **Step 5: 在 routes_workorder.py 追加**

```python
from services import patrol

@router.post("/patrol/plan/generate")
def api_patrol_generate(body: dict):
    if not body.get("stationId") or not body.get("patrolType") or not body.get("assignee") or not body.get("planDate"):
        return fail(40001, "缺少 stationId/patrolType/assignee/planDate")
    return ok({"patrolId": patrol.generate_plan(body)})
```

- [ ] **Step 6: 补路由测试并跑通**

```python
from fastapi.testclient import TestClient
from main import app

def test_patrol_generate_validates():
    c = TestClient(app)
    r = c.post("/api/patrol/plan/generate", json={})
    assert r.json()["code"] == 40001
```

Run: `pytest tests/test_patrol.py tests/test_workorder.py -v`
Expected: PASS（不得破坏 Task 6 测试）

- [ ] **Step 7: 前端 workorder.api.ts + WorkOrder.vue**

```ts
import http from './api';
export const createWorkOrder = (alarmId: number, assignee: string) =>
  http.post('/workorder/create', { alarmId, assignee });
export const getWorkOrder = (orderId: number) =>
  http.get(`/workorder/${orderId}`);
export const generatePatrolPlan = (rule: {
  stationId: number; patrolType: string; assignee: string; planDate: string; planName?: string;
}) => http.post('/patrol/plan/generate', rule);
```

页面：工单创建/查询 + 巡检计划生成（Tab）。不要改 `router/index.ts`。

- [ ] **Step 8: 提交** `git commit -m "feat(9.x): 巡检计划生成与工单页面"`
