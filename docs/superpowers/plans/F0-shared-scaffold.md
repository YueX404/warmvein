# F0 共享脚手架 — 双人开发解耦总则（必读）

> 本文件是《Dev-1 运行流》《Dev-2 处置流》两份实现计划的公共前置。
> **由 Dev-1 在本仓库先提交（F0），Dev-2 只读不改。** 之后双方各自只新增本模块文件，绝不修改 `main.py`、共享组件与对方模块文件。

---

## 0. 为什么需要 F0（解耦原理）

为保证两人 PR 互不阻塞：

1. **`main.py` 一次性挂载全部 7 个模块路由**（空桩），之后无人再改 → 两人都不碰它。
2. **每个模块 = 独立文件**：`routes_<mod>.py` + `services/<mod>.py` + `algorithm/<mod>.py` + 各自 `config/*/<mod>.sql` + 各自 `web/pages/<mod>.vue`。新增模块不触碰他人文件。
3. **消息总线解耦**：Dev-1 的采集产生 Kafka `heat-alarm-topic`；Dev-2 的预警引擎消费它 → 两人**不共享代码**，仅共享 topic 名（见 §2）。
4. **短信归属 Dev-2**：Dev-1 的公众服务只调 `POST /api/sms/send`，不碰 `sms_service`。
5. **前端共享组件**（StationMap/AlarmCard/LineChart/GaugePanel）在 F0 建好，两人只读用，不修改。

---

## 1. 全局约束（两计划共用，逐条来自规范/设计文档）

- 后端 Python 3.10+ / FastAPI / scikit-learn / joblib；Spark 3.x / Hive；Kafka；MySQL 8；Redis 7；ES。
- 前端 Vue3 + TS + Vite + Element Plus + ECharts，2 空格缩进。
- 命名：类大驼峰、函数/变量小驼峰、常量全大写下划线；无拼音缩写；标识符英文。
- 所有外部输入做类型/长度/格式/合法性校验；SQL 参数化/ORM，禁止字符串拼接。
- 敏感信息（密码/密钥/Token）走环境变量/配置，禁止硬编码；手机号脱敏 `138****1234`。
- 统一响应结构：`{"code":0,"message":"ok","data":{...}}`；错误码见 §3。
- 中文沟通、英文代码；注释说明意图，不写冗余注释。

---

## 2. 共享常量与契约（两计划引用的唯一真相）

`src/python/kafka_topics.py`：
```python
HEAT_SENSOR_TOPIC = "heat-sensor-topic"
HEAT_ALARM_TOPIC = "heat-alarm-topic"   # Dev-1 生产，Dev-2 消费
HEAT_FORECAST_TOPIC = "heat-forecast-topic"
SMS_NOTIFY_TOPIC = "sms-notify-topic"   # Dev-2 生产，短信服务消费
```

`src/python/response.py`：
```python
from fastapi import Response
from fastapi.encoders import jsonable_encoder
from typing import Any

def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}

def fail(code: int, message: str, data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
```

统一错误码：`0` 成功 / `40001` 参数校验失败 / `40002` 资源不存在 / `40003` 权限不足 / `50001` 服务内部错误 / `50002` 模型未加载 / `50003` 短信网关失败。

---

## 3. 文件结构（F0 创建全部桩，标注归属）

```
src/python/
  main.py                # F0 创建并挂载全部路由，之后锁定
  config/settings.py     # F0：环境变量读取
  db.py                  # F0：MySQL 引擎 + Redis 客户端
  kafka_topics.py        # F0：topic 常量（§2）
  response.py            # F0：统一响应（§2）
  routes_heat.py         # F0 空桩 → Dev-1 填充
  routes_alarm.py        # F0 空桩 → Dev-2 填充
  routes_workorder.py    # F0 空桩 → Dev-2 填充
  routes_plan.py         # F0 空桩 → Dev-2 填充
  routes_sms.py          # F0 空桩 → Dev-2 填充
  routes_twin.py         # F0 空桩 → Dev-1 填充
  routes_public.py       # F0 空桩 → Dev-1 填充
  services/              # 各模块服务（归属对应 dev）
  algorithm/             # 各模块算法（归属对应 dev）
config/
  hive/heat_ddl.sql      # F0 建库 + 分层 + Dev-1 供热表
  mysql/heat_init.sql    # F0 建库 + 共享表 + Dev-1 主数据/业务表
  logstash/heat_kafka_to_es.conf  # F0
web/src/
  App.vue                # F0 注册全部懒路由
  services/api.ts        # F0 请求封装（统一 code/message 拦截）
  mock/*.ts              # F0 提供骨架，双方各自补充本模块 mock
  components/StationMap.vue AlarmCard.vue LineChart.vue GaugePanel.vue  # F0 共享，只读
  pages/heat/* twin/* public/*   # Dev-1
  pages/alarm/* workorder/* plan/* sms/*  # Dev-2
```

---

## 4. F0 实施任务（Dev-1 执行，Dev-2 等待）

### F0-T1 基础设施文件
- 创建 `config/settings.py`（读 `DB_URL`、`REDIS_URL`、`KAFKA_BOOTSTRAP`、`SMS_PROVIDER`、`MODEL_DIR`）。
- 创建 `db.py`：`create_engine(DB_URL)`、`SessionLocal`、`redis_client = Redis.from_url(REDIS_URL)`。
- 创建 `kafka_topics.py`、`response.py`（代码见 §2）。

### F0-T2 main.py 骨架（锁定，之后不改）
```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config.settings import settings
from db import init_db_once
from response import fail
from routes_heat import router as heat_router
from routes_alarm import router as alarm_router
from routes_workorder import router as workorder_router
from routes_plan import router as plan_router
from routes_sms import router as sms_router
from routes_twin import router as twin_router
from routes_public import router as public_router

app = FastAPI(title="安塞供暖智慧运行平台", version="2026.08.31")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(Exception)
async def handle(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content=fail(50001, "服务内部错误"))

for r in (heat_router, alarm_router, workorder_router, plan_router,
          sms_router, twin_router, public_router):
    app.include_router(r, prefix="/api")

@app.get("/health")
def health():
    return {"code": 0, "message": "ok", "data": {"status": "healthy"}}
```

### F0-T3 7 个路由空桩（归属标注）
每个形如 `routes_heat.py`：
```python
from fastapi import APIRouter
router = APIRouter()
```
（Dev-1 填 heat/twin/public；Dev-2 填 alarm/workorder/plan/sms）

### F0-T4 数仓与库表（建库 + 共享层）
- `config/hive/heat_ddl.sql`：建 `ods/dwd/dws/ads` 库（沿用现有分层约定），建 `ods.heat_sensor_raw`、`dwd.heat_sensor_detail` 骨架。
- `config/mysql/heat_init.sql`：建库；共享表 `biz_sms_template`、`biz_sms_log`、`biz_alarm`、`biz_work_order`、`biz_plan`（建表语句见各自模块计划，F0 仅建库与 `biz_sms_template`/`biz_sms_log` 由 Dev-2 计划补全，此处建占位）。
- `config/logstash/heat_kafka_to_es.conf`：topic→`heat-sensor-topic`，index→`heat-sensor-%{+YYYY.MM.dd}`。

### F0-T5 前端脚手架与共享组件
- `web/src/services/api.ts`：axios 封装，拦截 `code!=0` 弹错。
- `web/src/App.vue`：懒加载全部模块路由（`pages/heat/Dashboard.vue` 等占位）。
- 共享组件 `StationMap.vue`(GIS 点位)、`AlarmCard.vue`(蓝/黄/橙/红着色)、`LineChart.vue`(ECharts 折线)、`GaugePanel.vue`(仪表盘)。
- `web/src/mock/index.ts`：导出各模块 mock 开关。

### F0-T6 提交与通知
- Dev-1 提交 F0 全部文件，**通知 Dev-2**：`main.py` 已锁定、topic 常量已定、共享组件可用、可开始各自模块。
- Dev-2 自此只读 F0 文件，开始「处置流」计划。

> **契约冻结声明**：F0 之后，《功能开发文档》§3 接口路径/字段为唯一标准。任一开发者改字段须升版本号（v2）并同步对方。

---

## 5. 两计划模块归属一览

| 模块 | 归属 | 关键文件 |
|---|---|---|
| 1.2 数据接入与中台 | Dev-1 | routes_heat / services/master_data / heat_generate_logs / heat_kafka_producer |
| 2.2 供暖管网智慧运行 | Dev-1 | routes_heat / algorithm/{hydraulic_balance,heat_loss,climate_compensation,frost_risk,user_abnormal} |
| 8.x 能效与节能 | Dev-1 | routes_heat / algorithm 复用 + services/energy |
| 10.x 数字孪生仿真 | Dev-1 | routes_twin / algorithm/twin_recovery |
| 11.2 公众服务 | Dev-1 | routes_public（调 POST /api/sms/send） |
| 4.1 预警引擎 | Dev-2 | routes_alarm / services/alarm_engine（消费 heat-alarm-topic） |
| 短信通知 | Dev-2 | routes_sms / services/sms_service / biz_sms_* |
| 4.2 预报与寿命 | Dev-2 | routes_alarm / services/forecast（ML 模型） |
| 9.x 工单巡检 | Dev-2 | routes_workorder / services/workorder |
| 5.1 预案 | Dev-2 | routes_plan / services/plan |

---

## 6. 实施偏离记录（2026-09-01 审查修复后补记）

实际落地与 §4 模板的偏离如下，**双方开发一律以代码现状为准**：

1. **CORS 可配置**：`main.py` 不用硬编码 `allow_origins=["*"]`，改读 `settings.APP_CORS_ORIGINS`（逗号分隔，默认 `*`）。生产环境必须显式配置来源列表（带凭据请求不支持通配符）。
2. **`init_db_once` 已删除**：计划模板中的 `from db import init_db_once` 未启用，且该函数实现有误（引用不存在的 `Base`），审查后直接移除。表结构初始化以 `config/mysql/heat_init.sql`（docker-entrypoint 自动执行）为准。
3. **全局异常处理器带日志**：`main.py` 的 catch-all 会用 `logger.exception` 记录堆栈后再返回 `50001`，便于排障。
4. **`.env` 解析器**：`config/settings.py` 自带解析器支持行内注释与引号；不依赖 `python-dotenv`。
5. **数据库名**：统一为 `warmvein`（原 `heat_platform` 已废弃，见《文档审查报告-20260831》）。
6. **Logstash 管道**：VM compose 挂载 `config/logstash/heat_kafka_to_es.conf`（旧的 `kafka_to_es.conf` 保留为工业模板参考，不再挂载）；ES `document_id` 使用 `sensor_id-event_timestamp` 避免同站多传感器互相覆盖。
7. **前端 mock**：`mock/index.ts` 使用 `export * as` 命名空间导出（各模块 mock 均为命名导出）；已补齐 `public.mock.ts`。
8. **依赖锁版**：`requirements.txt` 恢复精确锁版（`kafka-python==2.1.0`，修复 2.0.2 在 Python 3.12+ 的兼容问题）；前端 `vue-tsc` 升至 `^2.0.0`（1.8 与 TypeScript ≥5.5 不兼容，`npm run build` 会直接崩溃）。
9. **冒烟测试**：`tests/test_scaffold.py` 为契约冻结后的回归基线（5 项：/health、7 路由空桩、统一响应结构、Kafka topic 契约），改动共享文件前必须先跑通。
