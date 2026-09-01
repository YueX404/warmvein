# Dev-2 Task 1: 预警判定与降噪聚合 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **分支：** `dev-2/feature/task1-alarm-engine`（从 `main` 切出）
> **索引：** [Dev-2-处置流.md](./Dev-2-处置流.md)

**Goal:** 消费 Dev-1 的 Kafka `heat-alarm-topic`，完成四级预警判定、5 分钟窗口降噪、入库，并向 `sms-notify-topic` 投递短信请求。本 Task **不写** HTTP API 与前端（Task 2）。

**Architecture:** 只新增 `alarm_engine.py` 与 `alarm_consumer.py`。短信投递只用 `KafkaProducer.send(SMS_NOTIFY_TOPIC)`，不 import 短信服务。不修改 `routes_alarm.py`。

**Tech Stack:** Python 3.10+ / Kafka / MySQL / Redis。

## Global Constraints

- 见索引文档 Global Constraints。
- 独占文件：`src/python/services/alarm_engine.py`、`consumers/alarm_consumer.py`、`tests/test_alarm_engine.py`。
- `biz_alarm` 已由 F0 建表。Kafka 消息约定：`{station_id, alarmType, level, phone?}`。

---

### Task 1: 预警判定与降噪聚合（消费 heat-alarm-topic）

**Files:**
- Create: `src/python/services/alarm_engine.py`
- Create: `src/python/consumers/alarm_consumer.py`
- Create: `tests/test_alarm_engine.py`

**Interfaces:**
- Consumes: `from kafka_topics import HEAT_ALARM_TOPIC, SMS_NOTIFY_TOPIC`、`from db import SessionLocal, redis_client`
- Produces: `judge_level(alarm_type, value) -> int`、`dedup_key(station_id, alarm_type) -> str`、`publish_sms(alarm)`、`risk_level_from_frost(level) -> int`

- [ ] **Step 1: 写失败测试**

```python
from services.alarm_engine import judge_level, dedup_key, risk_level_from_frost

def test_judge_frost_red():
    assert judge_level("frost", 4) == 4

def test_judge_corrosion_yellow():
    assert judge_level("corrosion", 2) == 2

def test_dedup_key_stable():
    assert dedup_key(1, "frost") == dedup_key(1, "frost")

def test_frost_high():
    assert risk_level_from_frost("high") == 4
```

- [ ] **Step 2: 运行失败**

Run: `pytest tests/test_alarm_engine.py -v`
Expected: FAIL with "cannot import" 或 "function not defined"

- [ ] **Step 3: 实现 alarm_engine.py**

```python
from kafka_topics import SMS_NOTIFY_TOPIC
from db import redis_client

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
    from kafka import KafkaProducer
    import json, os
    p = KafkaProducer(bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
                      value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode())
    p.send(SMS_NOTIFY_TOPIC, value=alarm)
    p.flush()
```

- [ ] **Step 4: 实现 alarm_consumer.py**

```python
from kafka import KafkaConsumer
import json, os, time
from db import SessionLocal, redis_client
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
        if now - last < 300:
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

- [ ] **Step 5: 运行测试通过**

Run: `pytest tests/test_alarm_engine.py -v`
Expected: PASS

- [ ] **Step 6: 提交** `git commit -m "feat(4.1): 预警判定与降噪聚合、Kafka 消费"`
