# Dev-2 Task 4: 短信 API 与前端模板管理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **分支：** `dev-2/feature/task4-sms-api`
> **基线：** Task 3（`dev-2/feature/task3-sms-core`）已合入 `main`，或叠在该分支上。本 Task import `sms_service`。
> **索引：** [Dev-2-处置流.md](./Dev-2-处置流.md)

**Goal:** 暴露 `POST /api/sms/send`、`GET /api/sms/log`（供 Dev-1 公众服务调用），并实现短信模板管理页。

**Architecture:** 只改 `routes_sms.py` 与短信前端。不改 `sms_service.py`。

**Tech Stack:** Python 3.10+ / FastAPI；前端 Vue3+TS。

## Global Constraints

- 见索引文档 Global Constraints。
- 独占：`routes_sms.py`、`tests/test_sms_routes.py`、`web/src/pages/sms/TemplateManage.vue`、`web/src/services/sms.api.ts`、`web/src/mock/sms.mock.ts`。
- 路由：`@router.post("/sms/send")` → `POST /api/sms/send`。

---

### Task 4: 短信 API 与前端模板管理

**Files:**
- Modify: `src/python/routes_sms.py`
- Create: `tests/test_sms_routes.py`
- Modify: `web/src/pages/sms/TemplateManage.vue`
- Create: `web/src/services/sms.api.ts`
- Modify: `web/src/mock/sms.mock.ts`

**Interfaces:**
- Consumes: `sms_service.send_sms`（Task 3）
- Produces: `POST /api/sms/send`、`GET /api/sms/log`

- [ ] **Step 1: 确认基线**

`src/python/services/sms_service.py` 必须已存在。否则先 rebase / 合入 Task 3。

- [ ] **Step 2: 写失败测试**

```python
from fastapi.testclient import TestClient
from main import app

def test_sms_send_validates():
    c = TestClient(app)
    r = c.post("/api/sms/send", json={"templateCode": "", "phones": [], "vars": {}})
    assert r.json()["code"] == 40001

def test_sms_log_list():
    c = TestClient(app)
    r = c.get("/api/sms/log", params={"batchId": "b1"})
    assert r.status_code == 200
```

- [ ] **Step 3: 运行失败**

Run: `pytest tests/test_sms_routes.py -v`
Expected: FAIL（空桩无 `/sms/send`）

- [ ] **Step 4: 实现 routes_sms.py**

```python
from fastapi import APIRouter
from response import ok, fail
from db import SessionLocal
from sqlalchemy import text
from services import sms_service
router = APIRouter()

@router.post("/sms/send")
def api_send(body: dict):
    if not body.get("templateCode") or not isinstance(body.get("phones"), list) or not body["phones"]:
        return fail(40001, "缺少 templateCode 或 phones")
    try:
        batch_id = sms_service.send_sms(body["templateCode"], body["phones"], body.get("vars", {}))
    except ValueError:
        return fail(40002, "短信模板不存在")
    return ok({"batchId": batch_id})

@router.get("/sms/log")
def api_log(batch_id: str = None):
    sql = "SELECT id, batch_id, phone_masked, template_code, status, receipt, created_at FROM biz_sms_log"
    p = {}
    if batch_id:
        sql += " WHERE batch_id=:b"; p["b"] = batch_id
    with SessionLocal() as s:
        rows = [dict(r) for r in s.execute(text(sql), p).mappings().all()]
    return ok(rows)
```

- [ ] **Step 5: 运行路由测试通过**

Run: `pytest tests/test_sms_routes.py tests/test_sms_service.py -v`
Expected: PASS

- [ ] **Step 6: 前端 sms.api.ts + TemplateManage.vue**

```ts
import http from './api';
export const sendSms = (templateCode: string, phones: string[], vars: Record<string, string> = {}) =>
  http.post('/sms/send', { templateCode, phones, vars });
export const getSmsLog = (batchId?: string) =>
  http.get('/sms/log', { params: { batch_id: batchId } });
```

页面：模板列表、手动发送、发送记录；手机号展示脱敏 `138****1234`。

- [ ] **Step 7: 提交** `git commit -m "feat(sms): 短信发送/记录 API 与模板管理页面"`
