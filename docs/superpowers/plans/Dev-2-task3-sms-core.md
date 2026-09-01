# Dev-2 Task 3: 短信服务（网关/模板/脱敏/限流/重试） Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **分支：** `dev-2/feature/task3-sms-core`（从 `main` 切出）
> **索引：** [Dev-2-处置流.md](./Dev-2-处置流.md)

**Goal:** 实现短信网关适配、模板渲染、手机号脱敏、限流与重试，并消费 `sms-notify-topic` 发预警短信。本 Task **不写** HTTP API 与前端（Task 4）。

**Architecture:** 只新增 `sms_service.py` 与 `sms_consumer.py`。不 import 预警引擎。表与种子模板已在 F0 `heat_init.sql`，禁止改该文件。

**Tech Stack:** Python 3.10+ / Kafka / MySQL / Redis。

## Global Constraints

- 见索引文档 Global Constraints。
- 独占：`src/python/services/sms_service.py`、`consumers/sms_consumer.py`、`tests/test_sms_service.py`。
- F0 模板编码：`ALARM_BLUE` / `ALARM_YELLOW` / `ALARM_ORANGE` / `ALARM_RED` / `SHUTDOWN` / `FROST` / `PUBLIC`。不要使用不存在的 `ALARM_NOTICE`。

---

### Task 3: 短信服务（网关适配 + 模板 + 脱敏 + 限流 + 重试）

**Files:**
- Create: `src/python/services/sms_service.py`
- Create: `src/python/consumers/sms_consumer.py`
- Create: `tests/test_sms_service.py`

**Interfaces:**
- Consumes: `SMS_NOTIFY_TOPIC`、`SessionLocal`、`redis_client`
- Produces: `mask_phone(phone) -> str`、`build_content(tpl, vars) -> str`、`send_sms(template_code, phones, vars) -> str`

- [ ] **Step 1: 写失败测试**

```python
from services.sms_service import mask_phone, build_content

def test_mask_phone():
    assert mask_phone("13812341234") == "138****1234"

def test_build_content_fills_vars():
    assert build_content("停暖时间{planTime}", {"planTime": "09-01"}) == "停暖时间09-01"
```

- [ ] **Step 2: 运行失败**

Run: `pytest tests/test_sms_service.py -v`
Expected: FAIL with "cannot import" 或 "function not defined"

- [ ] **Step 3: 实现 sms_service.py**

```python
import os, time
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
        r = {"success": False}
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

- [ ] **Step 4: 实现 sms_consumer.py**

```python
from kafka import KafkaConsumer
import json, os
from services import sms_service

_LEVEL_TPL = {1: "ALARM_BLUE", 2: "ALARM_YELLOW", 3: "ALARM_ORANGE", 4: "ALARM_RED"}

def consume():
    c = KafkaConsumer(os.getenv("SMS_NOTIFY_TOPIC", "sms-notify-topic"),
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
        value_deserializer=lambda m: json.loads(m.decode()),
        group_id="sms_consumer", auto_offset_reset="latest")
    for msg in c:
        a = msg.value
        tpl = _LEVEL_TPL.get(int(a.get("level") or 2), "ALARM_YELLOW")
        sms_service.send_sms(tpl,
            phones=[a.get("phone", "13800000000")],
            vars={"level": a.get("level"), "type": a.get("alarmType"),
                  "stationName": a.get("stationName", a.get("station_id", ""))})
```

- [ ] **Step 5: 运行测试通过**

Run: `pytest tests/test_sms_service.py -v`
Expected: PASS

- [ ] **Step 6: 提交** `git commit -m "feat(sms): 短信网关适配/模板/脱敏/限流/重试"`
