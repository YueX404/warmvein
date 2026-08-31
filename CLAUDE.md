# CLAUDE.md

本文件为 Claude Code 每次会话自动加载的项目记忆，包含项目概况、技术栈、目录结构、运行方式与开发规范。

---

## 项目概况

**安塞区城市安全生命线管网 AI 智慧平台**

- 行业：城市供暖管网智慧运行（Phase 1 核心闭环）
- 定位：从"事后抢险"转向"事前预警-预报-预案"的主动防控平台
- 投资规模（典型地级市）：建设期一次性投入约 500 万元

**当前状态（2026-08）**
- `src/python/` 存在一套「工业设备监控」模板（FastAPI + Kafka + Spark + Hive + ES + sklearn + ECharts），是本项目的脚手架起点，供热改造在其基础上进行。
- 设计文档与实现计划已生成（`docs/`），待开发启动。

**Phase 1 切片范围（本次开发）**
主模块：2.2 供暖管网智慧运行（7 项能力完整）；配套：1.2 数据中台、4.1 预警引擎、4.2 预报/寿命、8.x 能效节能、9.x 工单/巡检、10.x 数字孪生/仿真、5.1 预案、11.2 公众服务、14.x 系统支撑；新增短信通知。

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.10+ / FastAPI / scikit-learn / joblib |
| 实时计算 | Kafka（kafka-python） |
| 离线计算 | PySpark 3.x + Hive |
| 搜索/时序检索 | Elasticsearch（Logstash 采集） |
| 数据库 | MySQL 8（主数据/业务）/ Redis 7（缓存/会话/限流）/ Hive（数仓） |
| 前端 | Vue3 + TypeScript + Vite + Element Plus + ECharts |
| 部署 | Docker Compose |
| 规范 | `.trae/rules/技术规范.md` |

---

## 目录结构

```
D:\YY\
├── src/python/
│   ├── main.py                    # FastAPI 服务（F0 已锁定，含 7 路由挂载）
│   ├── config/settings.py         # 环境变量配置
│   ├── db.py                      # MySQL 引擎 + Redis 客户端
│   ├── kafka_topics.py            # Topic 常量
│   ├── response.py                # 统一响应 ok/fail
│   ├── routes_heat.py             # 2.2+8.x 供暖运行路由（Dev-1）
│   ├── routes_alarm.py            # 4.1 预警+4.2 预报路由（Dev-2）
│   ├── routes_workorder.py        # 9.x 工单/巡检路由（Dev-2）
│   ├── routes_plan.py             # 5.1 预案路由（Dev-2）
│   ├── routes_sms.py              # 短信路由（Dev-2）
│   ├── routes_twin.py             # 10.x 数字孪生路由（Dev-1）
│   ├── routes_public.py           # 11.2 公众服务路由（Dev-1）
│   ├── algorithm/                 # 核心算法（纯函数）
│   │   ├── hydraulic_balance.py   # 水力平衡（Dev-1）
│   │   ├── heat_loss.py           # 热损耗核算（Dev-1）
│   │   ├── climate_compensation.py# 气候补偿（Dev-1）
│   │   ├── frost_risk.py          # 冻堵风险（Dev-1）
│   │   ├── user_abnormal.py       # 分户异常（Dev-1）
│   │   └── twin_recovery.py       # 停暖恢复仿真（Dev-1）
│   ├── services/                  # 业务服务层
│   ├── consumers/                 # Kafka 后台消费者
│   ├── heat_generate_logs.py      # 供热模拟数据生成（改造自 generate_logs.py）
│   ├── heat_kafka_producer.py     # 供热 Kafka 生产者（改造自 kafka_producer.py）
│   ├── heat_spark_analysis.py     # 供热 Spark 分析（改造自 spark_analysis.py）
│   └── heat_train_model.py        # 供热 ML 模型训练（改造自 train_sklearn_model.py）
├── web/                           # Vue3 前端（新增）
│   └── src/
│       ├── pages/                 # 各模块页面（heat/alarm/workorder/plan/sms/twin/public）
│       ├── components/            # 共享组件（StationMap/AlarmCard/LineChart/GaugePanel）
│       ├── services/              # API 请求层（按模块拆分 .api.ts）
│       └── mock/                  # Mock 夹具
├── config/
│   ├── hive/heat_ddl.sql          # 供热数仓分层 DDL
│   ├── mysql/heat_init.sql        # MySQL 主数据/业务表建表脚本
│   └── logstash/heat_kafka_to_es.conf
├── models/                        # sklearn 模型文件（*.pkl）
├── docker/docker-compose.yml      # Docker 编排
├── scripts/                       # ETL/运维脚本
├── docs/                          # 文档与实现计划
│   ├── 需求分析文档.md
│   ├── 系统设计文档.md
│   ├── 功能开发文档.md
│   ├── 开发任务拆分-角色A-平台与智能底座.md
│   ├── 开发任务拆分-角色B-前端与展现层.md
│   └── superpowers/plans/
│       ├── F0-shared-scaffold.md
│       ├── Dev-1-运行流.md
│       └── Dev-2-处置流.md
└── data/                          # 日志/数据文件
```

---

## 运行命令

```bash
# 启动 Docker 集群（Kafka/Hive/Spark/ES/Redis/MySQL）
cd docker && docker-compose up -d

# 生成供热模拟数据
python src/python/heat_generate_logs.py --count 10000 --output data/logs

# 启动 Kafka 生产者（实时模式）
python src/python/heat_kafka_producer.py --bootstrap localhost:9092 --duration 300

# 启动 Spark 分析（ODS→DWD→DWS→ADS）
spark-submit --master spark://spark-master:7077 src/python/heat_spark_analysis.py 2026-08-31

# 训练 ML 模型
python src/python/heat_train_model.py

# 启动 FastAPI 服务
uvicorn src.python.main:app --host 0.0.0.0 --port 8000

# 前端开发
cd web && npm install && npm run dev
```

---

## 开发规范（摘自 .trae/rules/技术规范.md）

- 命名：类大驼峰，函数/变量小驼峰，常量全大写下划线；标识符英文，无拼音缩写
- 后端 4 空格缩进，前端 2 空格缩进；函数≤50行，嵌套≤3层
- 所有外部输入类型/长度/格式/合法性校验；SQL 参数化，禁止字符串拼接
- 敏感信息（密钥/密码/Token）走环境变量，禁止硬编码；手机号脱敏 `138****1234`
- 统一响应：`{"code":0,"message":"ok","data":{...}}`，错误码见功能开发文档 §9
- 异常处理：捕获但不暴露栈信息，返回统一错误码+友好提示
- 中文沟通，英文代码/注释说明意图不冗余

---

## 关键设计决策

- **混合栈复用**：沿用现有 Python 大数据栈（FastAPI+Kafka+Spark+Hive+ES+sklearn），新增 Vue3 前端；不引入 Java 重写
- **F0 共享脚手架**：main.py 一次性挂载 7 个空路由后锁定，之后无人再改，消除 PR 冲突
- **消息总线解耦**：Dev-1 采集→Kafka `heat-alarm-topic`→Dev-2 预警引擎消费；双方不共享业务代码
- **短信归属 Dev-2**：Dev-1 的公众服务只调 `POST /api/sms/send`，不碰短信实现

---

## 核心文件快速索引

| 需求 | 查看文件 |
|---|---|
| 算法接口（水力平衡/热损/气候补偿/冻堵/仿真） | `src/python/algorithm/*.py` |
| 实时数据接入 | `src/python/heat_generate_logs.py` + `heat_kafka_producer.py` |
| Spark 数仓分层 | `src/python/heat_spark_analysis.py` + `config/hive/heat_ddl.sql` |
| ML 模型 | `src/python/heat_train_model.py`（异常/寿命/健康度） |
| API 入口 | `src/python/main.py`（路由挂载）、`src/python/routes_*.py` |
| MySQL 建表 | `config/mysql/heat_init.sql` |
| 实现计划（双人） | `docs/superpowers/plans/Dev-1-运行流.md`、`Dev-2-处置流.md` |
