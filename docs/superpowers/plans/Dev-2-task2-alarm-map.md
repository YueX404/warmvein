# Dev-2 Task 2: 预警列表/确认 API 与前端预警一张图 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **分支：** `dev-2/feature/task2-alarm-map`（从 `main` 切出，可与 Task 1 并行）
> **索引：** [Dev-2-处置流.md](./Dev-2-处置流.md)

**Goal:** 提供 `GET /api/alarm/list`、`POST /api/alarm/ack`，并实现前端预警一张图。本 Task **不写** Kafka 消费者（Task 1），**不写** `/forecast/list`（Task 5）。

**Architecture:** 只改 `routes_alarm.py` 与预警前端。列表直接查 `biz_alarm`，不 import `alarm_engine`。合入后 Task 5 才能在此文件末尾追加预报路由。

**Tech Stack:** Python 3.10+ / FastAPI / MySQL；前端 Vue3+TS。共享组件 `AlarmCard` 只读。

## Global Constraints

- 见索引文档 Global Constraints。
- 独占：`routes_alarm.py`（仅 list/ack）、`tests/test_alarm_routes.py`、`web/src/pages/alarm/AlarmMap.vue`、`web/src/services/alarm.api.ts`、`web/src/mock/alarm.mock.ts`。
- 路由：`@router.get("/alarm/list")` → `GET /api/alarm/list`。

---

### Task 2: 预警列表/确认 API 与前端预警一张图

**Files:**
- Modify: `src/python/routes_alarm.py`
- Create: `tests/test_alarm_routes.py`
- Modify: `web/src/pages/alarm/AlarmMap.vue`
- Create: `web/src/services/alarm.api.ts`
- Modify: `web/src/mock/alarm.mock.ts`

**Interfaces:**
- Consumes: `from db import SessionLocal`、`ok/fail`、表 `biz_alarm`
- Produces: `GET /api/alarm/list`、`POST /api/alarm/ack`

- [ ] **Step 1: 写失败测试**

```python
from fastapi.testclient import TestClient
from main import app

def test_alarm_list():
    c = TestClient(app)
    r = c.get("/api/alarm/list", params={"level": 3})
    assert r.status_code == 200 and r.json()["code"] == 0

def test_alarm_ack_validates_id():
    c = TestClient(app)
    r = c.post("/api/alarm/ack", json={"alarmId": 0, "operator": "x"})
    assert r.json()["code"] == 40002 or r.json()["code"] == 40001
```

- [ ] **Step 2: 运行失败**

Run: `pytest tests/test_alarm_routes.py -v`
Expected: FAIL（空桩无 `/alarm/list`）

- [ ] **Step 3: 实现 routes_alarm.py（不要加 forecast）**

```python
from fastapi import APIRouter
from response import ok, fail
from db import SessionLocal
from sqlalchemy import text
router = APIRouter()

@router.get("/alarm/list")
def api_list(level: int = None, status: int = None):
    sql = "SELECT alarm_id, station_id, level, type, root_cause, status, created_at FROM biz_alarm WHERE 1=1"
    p = {}
    if level: sql += " AND level=:l"; p["l"] = level
    if status is not None: sql += " AND status=:s"; p["s"] = status
    with SessionLocal() as s:
        rows = [dict(r) for r in s.execute(text(sql), p).mappings().all()]
    return ok(rows)

@router.post("/alarm/ack")
def api_ack(body: dict):
    if not body.get("alarmId"):
        return fail(40001, "缺少 alarmId")
    with SessionLocal() as s:
        r = s.execute(text("UPDATE biz_alarm SET status=1 WHERE alarm_id=:a"),
                      {"a": body["alarmId"]})
        s.commit()
        if r.rowcount == 0:
            return fail(40002, "预警不存在")
    return ok({"ok": True})
```

- [ ] **Step 4: 运行路由测试通过**

Run: `pytest tests/test_alarm_routes.py -v`
Expected: PASS

- [ ] **Step 5: 前端 alarm.api.ts + AlarmMap.vue（AlarmCard 分级着色）**

```ts
import http from './api';
export const getAlarms = (level?: number, status?: number) =>
  http.get('/alarm/list', { params: { level, status } });
export const ackAlarm = (alarmId: number, operator: string) =>
  http.post('/alarm/ack', { alarmId, operator });
```

- [ ] **Step 6: 提交** `git commit -m "feat(4.1): 预警列表/确认 API 与预警一张图"`
