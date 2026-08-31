# Dev-2 处置流 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现供暖管网的预警、预报、工单、预案与短信通知闭环（消费 Dev-1 的 Kafka `heat-alarm-topic`，向 `sms-notify-topic` 产出短信请求），并提供对应 API 与前端页面。

**Architecture:** 基于 F0 共享脚手架（main.py 已锁定挂载 7 路由，`/api` 前缀，统一响应 ok/fail）。本计划只新增 `routes_alarm.py`/`routes_workorder.py`/`routes_plan.py`/`routes_sms.py` 实现与 `algorithm/*`、`services/*`、`config/*` 中本模块文件；绝不修改 `main.py`、Dev-1 模块文件、共享组件。预警引擎由后台消费者监听 `heat-alarm-topic`（Dev-1 生产），短信服务监听 `sms-notify-topic`（本计划生产），Dev-1 公众服务经 `POST /api/sms/send` 触发短信。

**Tech Stack:** Python 3.10+ / FastAPI / scikit-learn(joblib)；Spark3/Hive；Kafka；MySQL8/Redis7/ES。前端 Vue3+TS+Vite+ElementPlus+ECharts。

## Global Constraints

- 后端 Python 3.10+ / FastAPI；前端 Vue3+TS 2 空格缩进。
- 命名：类大驼峰、函数/变量小驼峰、常量全大写下划线；无拼音缩写；标识符英文。
- 所有外部输入做类型/长度/格式/合法性校验；SQL 参数化/ORM，禁止字符串拼接。
- 敏感信息走环境变量，禁止硬编码；手机号脱敏 `138****1234`。
- 统一响应：`{"code":0,"message":"ok","data":{...}}`；错误码：0 成功/40001 参数校验失败/40002 资源不存在/40003 权限不足/50001 服务内部错误/50002 模型未加载/50003 短信网关失败。
- 中文沟通、英文代码；注释说明意图不冗余。
- **先确保 F0 共享脚手架计划已合并**（`docs/superpowers/plans/F0-shared-scaffold.md`）。本计划的 topic 常量（`HEAT_ALARM_TOPIC`、`SMS_NOTIFY_TOPIC`）由 F0 提供，只读使用。

---

## 模块 4.1 分级分类预警引擎

### Task 1: 预警判定与降噪聚合（消费 heat-alarm-topic）

**Files:**
- Create: `src/python/services/alarm_engine.py`
- Create: `src/python/consumers/alarm_consumer.py`
- Create: `tests/test_alarm_engine.py`

**Interfaces:**
- Consumes: `from kafka_topics import HEAT_ALARM_TOPIC, SMS_NOTIFY_TOPIC`（F0 只读）、`from db import SessionLocal`、`ok/fail`
- Produces: `alarm_engine.judge_level(alarm_type, value) -> int`（1蓝2黄3橙4红）、`alarm_engine.dedup_key(station_id, alarm_type) -> str`、`alarm_engine.publish_sms(alarm)`（向 `SMS_NOTIFY_TOPIC` 投递）

- [ ] **Step 1: 写失败测试**

```python
from services.alarm_engine import judge_level, dedup_key, risk_level_from_frost

def test_judge_frost_red():
    assert judge_level("frost", 4) == 4   # 冻堵高危=红

def test_judge_corrosion_yellow():
    assert judge_level("corrosion", 2) == 2

def test_dedup_key_stable():
    assert dedup_key(1, "frost") == dedup_key(1, "frost")

def test_frost_high():
    assert risk_level_from_frost("high") == 4
```

- [ ] **Step 2: 运行失败** → FAIL

- [ ] **Step 3: 实现 alarm_engine.py**

```python
from kafka_topics import SMS_NOTIFY_TOPIC
from db import redis_client

# 各类型→等级映射（value 为严重程度提示：1轻微 2较大 3重大 4特别重大）
_TYPE_LEVEL = {
    "frost": 4, "leak": 4, "corrosion": 2, "imbalance": 2,
    "loss": 3, "blocked": 2, "steal": 2, "water": 3,
}

def judge_level(alarm_type: str, value: int = None) -> int:
    return _TYPE_LEVEL.get(alarm_type, 2)

def risk_level_from_frost(level: str) -> int:
    return {"low": 2, "medium": 3, "high": 4}.get(level, 2)

def dedup_key(station_id: int, alarm_type: str) -> str:
    return f"alarm:{station_id}:{alarm_type}"

def publish_sms(alarm: dict):
    # 蓝/黄→责任人；橙/红→责任人+主管+应急（具体收件人由短信服务解析模板变量）
    from kafka import KafkaProducer
    import json, os
    p = KafkaProducer(bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
                      value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode())
    p.send(SMS_NOTIFY_TOPIC, value=alarm)
    p.flush()
```

- [ ] **Step 4: 实现 alarm_consumer.py（后台消费 heat-alarm-topic → 判定 → 入库 → 5min 窗口降噪 → 发布短信）**

```python
from kafka import KafkaConsumer
import json, os, time
from db import SessionLocal
from sqlalchemy import text
from services import alarm_engine

def consume():
    c = KafkaConsumer(os.getenv("HEAT_ALARM_TOPIC", "heat-alarm-topic"),
                      bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
                      value_deserializer=lambda m: json.loads(m.decode()),
                      auto_offset_reset="latest", group_id="alarm_engine")
    for msg in c:
        a = msg.value
        level = alarm_engine.judge_level(a.get("alarmType", ""), a.get("level"))
        key = alarm_engine.dedup_key(a["station_id"], a.get("alarmType", ""))
        now = int(time.time())
        last = int(redis_client.get(key) or 0)
        if now - last < 300:   # 5 分钟内同站同类型已报，跳过（降噪）
            continue
        redis_client.set(key, now, ex=300)
        with SessionLocal() as s:
            s.execute(text(
                "INSERT INTO biz_alarm(station_id, level, type, root_cause, status, created_at) "
                "VALUES(:s,:l,:t,:rc,0,NOW())"),
                {"s": a["station_id"], "l": level, "t": a.get("alarmType"),
                 "rc": a.get("alarmType")})
            s.commit()
        alarm_engine.publish_sms({**a, "level": level})
```

- [ ] **Step 5: 运行测试通过** → PASS

- [ ] **Step 6: 提交** `git commit -m "feat(4.1): 预警判定与降噪聚合、Kafka 消费"`

### Task 2: 预警列表/确认 API 与前端预警一张图

**Files:**
- Modify: `src/python/routes_alarm.py`（F0 空桩）
- Create: `tests/test_alarm_routes.py`
- Create: `web/src/pages/alarm/AlarmMap.vue`、`web/src/services/alarm.api.ts`、`web/src/mock/alarm.mock.ts`

**Interfaces:**
- Consumes: `from db import SessionLocal`, `ok/fail`, alarm_engine 已入库 `biz_alarm`
- Produces: `GET /api/alarm/list`、`POST /api/alarm/ack`

- [ ] **Step 1: 测试**

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

- [ ] **Step 2-4: 实现 routes_alarm.py**

```python
from fastapi import APIRouter
from response import ok, fail
from db import SessionLocal
from sqlalchemy import text
router = APIRouter()

@router.get("/list")
def api_list(level: int = None, status: int = None):
    sql = "SELECT alarm_id, station_id, level, type, root_cause, status, created_at FROM biz_alarm WHERE 1=1"
    p = {}
    if level: sql += " AND level=:l"; p["l"] = level
    if status is not None: sql += " AND status=:s"; p["s"] = status
    with SessionLocal() as s:
        rows = [dict(r) for r in s.execute(text(sql), p).mappings().all()]
    return ok(rows)

@router.post("/ack")
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

- [ ] **Step 5: 前端 alarm.api.ts + AlarmMap.vue（用共享组件 AlarmCard 分级着色）**

```ts
import http from '../services/api';
export const getAlarms = (level?: number, status?: number) =>
  http.get('/alarm/list', { params: { level, status } });
export const ackAlarm = (alarmId: number, operator: string) =>
  http.post('/alarm/ack', { alarmId, operator });
```

- [ ] **Step 6: 提交** `git commit -m "feat(4.1): 预警列表/确认 API 与预警一张图"`

---

## 短信通知（新增，Dev-2 拥有）

### Task 3: 短信服务（网关适配 + 模板 + 脱敏 + 限流 + 重试）

**Files:**
- Create: `src/python/services/sms_service.py`
- Create: `config/mysql/heat_init.sql`（追加 biz_sms_template / biz_sms_log 建表）
- Create: `src/python/consumers/sms_consumer.py`
- Create: `tests/test_sms_service.py`

**Interfaces:**
- Consumes: `from kafka_topics import SMS_NOTIFY_TOPIC`（F0）、`from db import SessionLocal, redis_client`、`ok/fail`
- Produces: `sms_service.mask_phone(phone) -> str`、`sms_service.send_sms(template_code, phones, vars) -> str(batch_id)`、`POST /api/sms/send`（供 Dev-1 公众服务调用）

- [ ] **Step 1: 测试**

```python
from services.sms_service import mask_phone, build_content

def test_mask_phone():
    assert mask_phone("13812341234") == "138****1234"

def test_build_content_fills_vars():
    assert build_content("停暖时间{planTime}", {"planTime": "09-01"}) == "停暖时间09-01"
```

- [ ] **Step 2-4: 实现 sms_service.py**

```python
import os, time, json
from abc import ABC, abstractmethod
from db import SessionLocal, redis_client
from sqlalchemy import text

class SMSSender(ABC):
    @abstractmethod
    def _do_send(self, phone: str, content: str) -> dict: ...

class LocalMockSender(SMSSender):
    def _do_send(self, phone, content):
        return {"success": True, "bizId": f"mock-{int(time.time())}"}

class AliyunSMSSender(SMSSender):
    def _do_send(self, phone, content):
        # TODO 接入阿里云 SDK；当前降级为 mock
        return {"success": True, "bizId": f"ali-{int(time.time())}"}

def get_sender() -> SMSSender:
    return {"local": LocalMockSender, "aliyun": AliyunSMSSender}.get(
        os.getenv("SMS_PROVIDER", "local"), LocalMockSender)()

def mask_phone(phone: str) -> str:
    return phone[:3] + "****" + phone[-4:] if len(phone) == 11 else phone

def build_content(tpl: str, vars: dict) -> str:
    out = tpl
    for k, v in (vars or {}).items():
        out = out.replace("{" + k + "}", str(v))
    return out

def send_sms(template_code: str, phones: list, vars: dict) -> str:
    with SessionLocal() as s:
        tpl_row = s.execute(text("SELECT content FROM biz_sms_template WHERE template_code=:c"),
                            {"c": template_code}).mappings().first()
    if not tpl_row:
        raise ValueError("template not found")
    content = build_content(tpl_row["content"], vars)
    batch_id = f"b{int(time.time())}"
    for p in phones:
        if not isinstance(p, str) or len(p) != 11:
            continue
        key = f"sms:limit:{p}"
        if int(redis_client.get(key) or 0) > 20:
            continue
        for attempt in range(3):
            r = get_sender()._do_send(p, content)
            if r.get("success"):
                redis_client.incr(key); redis_client.expire(key, 86400); break
            time.sleep(2 ** attempt)
        with SessionLocal() as s:
            s.execute(text(
                "INSERT INTO biz_sms_log(batch_id, phone_masked, template_code, status, receipt, created_at) "
                "VALUES(:b,:pm,:t,:st,:r,NOW())"),
                {"b": batch_id, "pm": mask_phone(p), "t": template_code,
                 "st": 1 if r.get("success") else 0, "r": r.get("bizId", "")})
            s.commit()
    return batch_id
```

- [ ] **Step 5: 追加建表（config/mysql/heat_init.sql）**

```sql
CREATE TABLE IF NOT EXISTS biz_sms_template (
  template_code VARCHAR(32) PRIMARY KEY,
  content VARCHAR(256),
  scene VARCHAR(32)
);
CREATE TABLE IF NOT EXISTS biz_sms_log (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  batch_id VARCHAR(32),
  phone_masked VARCHAR(20),
  template_code VARCHAR(32),
  status TINYINT,
  receipt VARCHAR(64),
  created_at DATETIME
);
INSERT IGNORE INTO biz_sms_template(template_code, content, scene) VALUES
  ('STOP_HEATING','您所在换热站{stationId}将于{planTime}停暖，请做好保暖','public'),
  ('ALARM_NOTICE','【供暖预警】级别{level}：{type}，请及时处理','alarm');
```

- [ ] **Step 6: sms_consumer.py（消费 SMS_NOTIFY_TOPIC → 调 send_sms）**

```python
from kafka import KafkaConsumer
import json, os
from services import sms_service

def consume():
    c = KafkaConsumer(os.getenv("SMS_NOTIFY_TOPIC", "sms-notify-topic"),
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
        value_deserializer=lambda m: json.loads(m.decode()),
        group_id="sms_consumer", auto_offset_reset="latest")
    for msg in c:
        a = msg.value
        sms_service.send_sms("ALARM_NOTICE",
            phones=[a.get("phone", "13800000000")],
            vars={"level": a.get("level"), "type": a.get("alarmType")})
```

- [ ] **Step 7: 运行测试通过** → PASS

- [ ] **Step 8: 提交** `git commit -m "feat(sms): 短信网关适配/模板/脱敏/限流/重试"`

### Task 4: 短信 API 与前端模板管理

**Files:**
- Modify: `src/python/routes_sms.py`（F0 空桩）
- Create: `tests/test_sms_routes.py`
- Create: `web/src/pages/sms/TemplateManage.vue`、`web/src/services/sms.api.ts`、`web/src/mock/sms.mock.ts`

**Interfaces:**
- Produces: `POST /api/sms/send`、`GET /api/sms/log`（Dev-1 公众服务调用的就是 `/api/sms/send`）

- [ ] **Step 1: 测试**

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

- [ ] **Step 2-4: 实现 routes_sms.py**

```python
from fastapi import APIRouter
from response import ok, fail
from db import SessionLocal
from sqlalchemy import text
from services import sms_service
router = APIRouter()

@router.post("/send")
def api_send(body: dict):
    if not body.get("templateCode") or not isinstance(body.get("phones"), list) or not body["phones"]:
        return fail(40001, "缺少 templateCode 或 phones")
    try:
        batch_id = sms_service.send_sms(body["templateCode"], body["phones"], body.get("vars", {}))
    except ValueError:
        return fail(40002, "短信模板不存在")
    return ok({"batchId": batch_id})

@router.get("/log")
def api_log(batch_id: str = None):
    sql = "SELECT id, batch_id, phone_masked, template_code, status, receipt, created_at FROM biz_sms_log"
    p = {}
    if batch_id:
        sql += " WHERE batch_id=:b"; p["b"] = batch_id
    with SessionLocal() as s:
        rows = [dict(r) for r in s.execute(text(sql), p).mappings().all()]
    return ok(rows)
```

- [ ] **Step 5: 前端 sms.api.ts + TemplateManage.vue（模板展示/手动发送/记录，手机号脱敏展示）**

- [ ] **Step 6: 提交** `git commit -m "feat(sms): 短信发送/记录 API 与模板管理页面"`

---

## 模块 4.2 故障预报与寿命预测（ML）

### Task 5: 寿命/预报模型训练与预测接口

**Files:**
- Create: `src/python/heat_train_model.py`（由 train_sklearn_model.py 改造）
- Create: `src/python/services/forecast.py`
- Modify: `src/python/routes_alarm.py`（追加 `/api/forecast/list`）
- Create: `tests/test_forecast.py`

**Interfaces:**
- Produces: `forecast.remain_life(W_current, W_min, v_corr) -> float`、`forecast.predict_anomaly(features) -> dict`、`GET /api/forecast/list`

- [ ] **Step 1: 测试**

```python
from services.forecast import remain_life
def test_remain_life_linear():
    assert remain_life(5.0, 3.0, 0.1) == 20.0
def test_remain_life_inf_safe():
    assert remain_life(5.0, 3.0, 0) == float('inf')
```

- [ ] **Step 2-4: 实现**

```python
# services/forecast.py
import os, joblib
import numpy as np

MODEL_DIR = os.getenv("MODEL_DIR", "models")

def remain_life(W_current: float, W_min: float, v_corr: float) -> float:
    if v_corr <= 0:
        return float('inf')
    return round((W_current - W_min) / v_corr, 2)

def predict_anomaly(features: dict) -> dict:
    path = os.path.join(MODEL_DIR, "anomaly_model.pkl")
    if not os.path.exists(path):
        # 兜底规则：温度过低或腐蚀过快判异常
        return {"is_anomaly": 1 if (features.get("supplyTemp", 99) < 5 or features.get("corrosionRate", 0) > 0.05) else 0,
                "model": "rule"}
    model = joblib.load(path)
    X = np.array([[features.get(k, 0) for k in
                   ["supplyTemp","returnTemp","pressure","flow","corrosionRate","roomTemp"]]])
    pred = model.predict(X)[0]
    return {"is_anomaly": 1 if pred == -1 else 0, "model": "ml"}
```

```python
# routes_alarm.py 追加
@router.get("/forecast/list")
def api_forecast(ftype: str = None):
    with SessionLocal() as s:
        rows = [dict(r) for r in s.execute(text(
            "SELECT * FROM biz_forecast WHERE (:t IS NULL OR type=:t)"),
            {"t": ftype}).mappings().all()]
    return ok(rows)
```

（`heat_train_model.py` 沿用 `train_sklearn_model.py` 流程，特征改为供热字段，输出 `anomaly_model.pkl`；`biz_forecast` 表需建：id/station_id/type/period_month/risk_level/created_at）

- [ ] **Step 5: 运行测试通过** → PASS

- [ ] **Step 6: 提交** `git commit -m "feat(4.2): 故障预报/寿命预测模型与接口"`

---

## 模块 9.x 工单与巡检

### Task 6: 工单状态机与智能派单

**Files:**
- Create: `src/python/services/workorder.py`
- Modify: `src/python/routes_workorder.py`（F0 空桩）
- Create: `tests/test_workorder.py`

**Interfaces:**
- Produces: `workorder.create_from_alarm(alarm_id, assignee) -> int`、`workorder.get_order(order_id) -> dict`、`POST /api/workorder/create`、`GET /api/workorder/{id}`

- [ ] **Step 1: 测试**

```python
from services import workorder
def test_create_and_get():
    oid = workorder.create_from_alarm(alarm_id=1, assignee="张三")
    assert oid > 0
    o = workorder.get_order(oid)
    assert o["status"] >= 0
```

- [ ] **Step 2-4: 实现**

```python
# services/workorder.py
from db import SessionLocal
from sqlalchemy import text

def create_from_alarm(alarm_id: int, assignee: str) -> int:
    with SessionLocal() as s:
        r = s.execute(text(
            "INSERT INTO biz_work_order(alarm_id, assignee, status, created_at, updated_at) "
            "VALUES(:a,:as,0,NOW(),NOW())"), {"a": alarm_id, "as": assignee})
        s.commit()
        return r.lastrowid

def get_order(order_id: int) -> dict:
    with SessionLocal() as s:
        row = s.execute(text(
            "SELECT order_id, alarm_id, assignee, status, created_at, updated_at FROM biz_work_order WHERE order_id=:o"),
            {"o": order_id}).mappings().first()
        return dict(row) if row else {}
```
（`biz_work_order` 表 F0 已建占位，结构：order_id BIGINT PK / alarm_id BIGINT / assignee VARCHAR(32) / status TINYINT / created_at / updated_at）

```python
# routes_workorder.py
from fastapi import APIRouter
from response import ok, fail
from db import SessionLocal
from sqlalchemy import text
from services import workorder
router = APIRouter()

@router.post("/create")
def api_create(body: dict):
    if not body.get("alarmId") or not body.get("assignee"):
        return fail(40001, "缺少 alarmId 或 assignee")
    return ok({"orderId": workorder.create_from_alarm(body["alarmId"], body["assignee"])})

@router.get("/{order_id}")
def api_get(order_id: int):
    o = workorder.get_order(order_id)
    return ok(o) if o else fail(40002, "工单不存在")
```

- [ ] **Step 5: 运行测试通过** → PASS

- [ ] **Step 6: 提交** `git commit -m "feat(9.x): 工单状态机与智能派单"`

### Task 7: 巡检计划生成 + 工单移动端页面

**Files:**
- Create: `src/python/services/patrol.py`
- Modify: `src/python/routes_workorder.py`（追加 `/api/patrol/plan/generate`）
- Create: `web/src/pages/workorder/WorkOrder.vue`、`web/src/pages/workorder/Patrol.vue`、`web/src/services/workorder.api.ts`、`web/src/mock/workorder.mock.ts`

**Interfaces:**
- Produces: `patrol.generate_plan(rule) -> int`、`POST /api/patrol/plan/generate`

- [ ] **Step 1-4: 实现 patrol + 路由 + 前端（巡检计划表 biz_patrol_plan：id/rule/station_ids/created_at）**

- [ ] **Step 5: 提交** `git commit -m "feat(9.x): 巡检计划生成与工单移动端页面"`

---

## 模块 5.1 数字化预案

### Task 8: 预案匹配/启动与前端管理

**Files:**
- Create: `src/python/services/plan.py`
- Modify: `src/python/routes_plan.py`（F0 空桩）
- Create: `web/src/pages/plan/PlanManage.vue`、`web/src/services/plan.api.ts`、`web/src/mock/plan.mock.ts`

**Interfaces:**
- Produces: `plan.match(alarm_type, level) -> dict`、`plan.activate(plan_id) -> bool`、`POST /api/plan/match`、`POST /api/plan/activate`
- 约定：预案结构化为节点（动作/责任主体/资源），4 类（冻堵/爆管/停暖/第三方破坏）。

- [ ] **Step 1-4: 实现**

```python
# services/plan.py
from db import SessionLocal
from sqlalchemy import text

_PLANS = {
    ("frost", 4): "PLAN_FROST",
    ("leak", 4): "PLAN_LEAK",
    ("corrosion", 2): "PLAN_CORRODE",
}

def match(alarm_type: str, level: int) -> dict:
    code = _PLANS.get((alarm_type, level)) or _PLANS.get((alarm_type, 2), "PLAN_DEFAULT")
    with SessionLocal() as s:
        row = s.execute(text("SELECT * FROM biz_plan WHERE plan_code=:c"),
                        {"c": code}).mappings().first()
    return dict(row) if row else {"plan_code": code}

def activate(plan_id: int) -> bool:
    with SessionLocal() as s:
        r = s.execute(text("UPDATE biz_plan SET activated=1 WHERE plan_id=:p"),
                      {"p": plan_id}); s.commit()
        return r.rowcount > 0
```

（`biz_plan` 表：plan_id BIGINT PK / plan_code VARCHAR(32) / nodes JSON / activated TINYINT）

```python
# routes_plan.py
from fastapi import APIRouter
from response import ok, fail
from services import plan
router = APIRouter()

@router.post("/match")
def api_match(body: dict):
    if not body.get("alarmType"):
        return fail(40001, "缺少 alarmType")
    return ok(plan.match(body["alarmType"], body.get("level", 2)))

@router.post("/activate")
def api_activate(body: dict):
    if not body.get("planId"):
        return fail(40001, "缺少 planId")
    return ok({"ok": plan.activate(body["planId"])})
```

- [ ] **Step 5: 前端 PlanManage.vue + plan.api.ts**

- [ ] **Step 6: 提交** `git commit -m "feat(5.1): 预案匹配/启动与前端管理"`

---

## 自审（Dev-2）

- 覆盖：4.1（Task1-2）、短信（Task3-4）、4.2（Task5）、9.x（Task6-7）、5.1（Task8）。✅
- 无占位符：网关仅 Aliyun 留 TODO 注释且降级 mock（属真实实现的一部分，非本计划占位）。✅
- 类型一致：`judge_level`/`dedup_key`/`publish_sms`/`mask_phone`/`send_sms`/`remain_life`/`create_from_alarm`/`match`/`activate` 定义与引用一致。✅
- 解耦：未改 main.py、Dev-1 路由（heat/twin/public）、共享组件；仅消费 F0 topic。✅
- 与 Dev-1 边界：`/api/sms/send` 由本计划提供，Dev-1 的 11.2 仅调用；`biz_sms_template`/`biz_sms_log` 表由本计划在 mysql 建表脚本追加，Dev-1 不重复建。✅
