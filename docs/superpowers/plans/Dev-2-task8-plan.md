# Dev-2 Task 8: 预案匹配/启动与前端管理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **分支：** `dev-2/feature/task8-plan`（从 `main` 切出，可与 Task 1–3、6 并行）
> **索引：** [Dev-2-处置流.md](./Dev-2-处置流.md)

**Goal:** 按预警类型与级别匹配应急预案并启动执行，提供匹配/启动 API 与前端预案管理页。四类：冻堵 / 爆管 / 停暖 / 第三方破坏。

**Architecture:** 只改预案模块文件。不 import 预警服务。列名以 F0 `biz_plan` / `biz_plan_execution` 为准。

**Tech Stack:** Python 3.10+ / FastAPI / MySQL；前端 Vue3+TS。

## Global Constraints

- 见索引文档 Global Constraints。
- 独占：`services/plan.py`、`routes_plan.py`、`tests/test_plan.py`、`web/src/pages/plan/PlanManage.vue`、`web/src/services/plan.api.ts`、`web/src/mock/plan.mock.ts`。
- `plan_type`：`freeze` | `burst` | `shutdown` | `third_party`。启动写 `biz_plan_execution`，不要用 `plan_code` / `activated`。

---

### Task 8: 预案匹配/启动与前端管理

**Files:**
- Create: `src/python/services/plan.py`
- Modify: `src/python/routes_plan.py`
- Create: `tests/test_plan.py`
- Modify: `web/src/pages/plan/PlanManage.vue`
- Create: `web/src/services/plan.api.ts`
- Modify: `web/src/mock/plan.mock.ts`

**Interfaces:**
- Produces: `plan.match(alarm_type, level) -> dict`、`plan.activate(plan_id, alarm_id=None, operator="") -> int`、`POST /api/plan/match`、`POST /api/plan/activate`
- 映射：`frost→freeze`、`leak→burst`、停暖→`shutdown`

- [ ] **Step 1: 写失败测试**

```python
from services import plan

def test_match_frost_high():
    row = plan.match("frost", 4)
    assert row.get("plan_type") == "freeze" or row.get("plan_id") is not None

def test_activate_requires_existing():
    ok_flag = plan.activate(plan_id=0)
    assert ok_flag == 0 or ok_flag is False
```

- [ ] **Step 2: 运行失败**

Run: `pytest tests/test_plan.py -v`
Expected: FAIL with "cannot import" 或 "function not defined"

- [ ] **Step 3: 实现 services/plan.py**

```python
from db import SessionLocal
from sqlalchemy import text

_TYPE_MAP = {
    "frost": "freeze",
    "leak": "burst",
    "burst": "burst",
    "shutdown": "shutdown",
    "steal": "third_party",
}

def match(alarm_type: str, level: int) -> dict:
    ptype = _TYPE_MAP.get(alarm_type, alarm_type)
    with SessionLocal() as s:
        row = s.execute(text(
            "SELECT plan_id, name, plan_type, alarm_level, trigger_condition, steps, resource_list, status "
            "FROM biz_plan WHERE plan_type=:t AND status=1 "
            "AND (alarm_level IS NULL OR alarm_level=:lv) "
            "ORDER BY alarm_level DESC LIMIT 1"),
            {"t": ptype, "lv": level}).mappings().first()
    return dict(row) if row else {"plan_type": ptype, "plan_id": None}

def activate(plan_id: int, alarm_id: int = None, operator: str = "") -> int:
    if not plan_id:
        return 0
    with SessionLocal() as s:
        exists = s.execute(text("SELECT plan_id FROM biz_plan WHERE plan_id=:p"),
                           {"p": plan_id}).first()
        if not exists:
            return 0
        r = s.execute(text(
            "INSERT INTO biz_plan_execution(plan_id, alarm_id, operator, status, started_at) "
            "VALUES(:p,:a,:op,0,NOW())"),
            {"p": plan_id, "a": alarm_id, "op": operator or "system"})
        s.commit()
        return r.lastrowid
```

测试夹具可在测试里 INSERT 一条 `plan_type='freeze'`，不要改 `heat_init.sql`。

- [ ] **Step 4: 实现 routes_plan.py**

```python
from fastapi import APIRouter
from response import ok, fail
from services import plan
router = APIRouter()

@router.post("/plan/match")
def api_match(body: dict):
    if not body.get("alarmType"):
        return fail(40001, "缺少 alarmType")
    return ok(plan.match(body["alarmType"], body.get("level", 2)))

@router.post("/plan/activate")
def api_activate(body: dict):
    if not body.get("planId"):
        return fail(40001, "缺少 planId")
    exec_id = plan.activate(body["planId"], body.get("alarmId"), body.get("operator", ""))
    if not exec_id:
        return fail(40002, "预案不存在")
    return ok({"ok": True, "execId": exec_id})
```

- [ ] **Step 5: 补路由测试并跑通**

```python
from fastapi.testclient import TestClient
from main import app

def test_plan_match_validates():
    c = TestClient(app)
    r = c.post("/api/plan/match", json={})
    assert r.json()["code"] == 40001

def test_plan_activate_validates():
    c = TestClient(app)
    r = c.post("/api/plan/activate", json={})
    assert r.json()["code"] == 40001
```

Run: `pytest tests/test_plan.py -v`
Expected: PASS

- [ ] **Step 6: 前端 plan.api.ts + PlanManage.vue**

```ts
import http from './api';
export const matchPlan = (alarmType: string, level = 2) =>
  http.post('/plan/match', { alarmType, level });
export const activatePlan = (planId: number, alarmId?: number, operator = '') =>
  http.post('/plan/activate', { planId, alarmId, operator });
```

页面：匹配、启动；`steps` 按 JSON 展示动作/责任主体/资源。

- [ ] **Step 7: 提交** `git commit -m "feat(5.1): 预案匹配/启动与前端管理"`
