# 安塞区城市安全生命线管网 AI 智慧平台

> 城市供暖管网智慧运行核心闭环 · 天信管业科技集团城市生命线项目

---

## 项目简介

本平台针对城市供暖管网热量损耗大、管道腐蚀泄漏、冻堵、温度失衡、运维低效等痛点，构建**「全时段感知 → 分级预警 → 超前预报 → 事前预案 → 工单闭环 → 运营运维」**的供暖安全管控闭环，实现从"事后抢险"向"事前防控"的转变。

- 投资规模（典型地级市，人口 30 万）：建设期约 500 万元
- 年减少事故损失约 3,000～8,000 万元，投资回收期 3～5 年
- 符合国家城市生命线安全工程、应急管理体系建设战略方向

---

## 核心功能

### 主模块 — 2.2 供暖管网智慧运行

| 能力 | 说明 |
|---|---|
| 运行参数实时监测 | 供回水温度/压力/流量/热量损耗/腐蚀速率，GIS 点位精准定位 |
| 热网水力平衡分析 | 各支路平衡度 β 实时计算，失衡预警与调节建议 |
| 换热站智能控制（气候补偿） | 依据室外气温自动调节二次供水温度，节能降耗 |
| 热损耗精准核算 | 按管段计算散热损失，量化保温层失效带来的热量损失 |
| 分户用热异常识别 | 偷热/私自放水/室温不达标智能诊断 |
| 冻堵风险预判 | 结合气温预测，提前预判冻堵风险，自动启动防冻预案 |
| 停暖恢复仿真 | 复暖时间预测与升温策略优化 |

### 配套模块

- **数据治理与中台**：供热主数据、统一 API
- **分级分类预警引擎**：蓝/黄/橙/红四级，根因分析，多源聚合降噪
- **故障预报与寿命预测**：腐蚀剩余寿命、周期故障预报、ML 异常检测
- **供暖能效与节能优化**：热效对标、AI 优化运行策略
- **工单与巡检管理**：预警自动派单，全流程可视化，巡检路线优化
- **数字孪生与热力仿真**：三维管网、温度场仿真、停暖恢复仿真
- **数字化预案管理**：冻堵/爆管/停暖/第三方破坏专项预案
- **公众服务**：停暖通知、线上报修
- **短信通知**：多渠道预警/停暖推送，脱敏合规
- **系统支撑**：多租户权限、运行监控、审计日志、等保三级

---

## 技术架构

```
感知层    供热传感器 · 换热站PLC · 气象 · GIS/BIM
          ↓ Kafka
接入层    Kafka（heat-sensor-topic / heat-alarm-topic）
          ↓ Logstash + Spark
存储层    Elasticsearch · Hive 数仓（ODS→DWD→DWS→ADS）· MySQL · Redis
          ↓
计算层    Spark 离线分析 · FastAPI 实时接口
          ↓
AI层      sklearn 异常检测 · 寿命预测 · 冻堵预报
          ↓
服务层    FastAPI（REST API，/api 前缀，统一响应）
          ↓
展现层    Vue3 + ECharts 指挥大屏 · 运维移动端 · 管理后台
```

| 层 | 技术 |
|---|---|
| 后端 | Python 3.10+ / FastAPI / scikit-learn / joblib |
| 实时 | Kafka（kafka-python） |
| 离线 | PySpark 3.x + Hive |
| 搜索 | Elasticsearch + Logstash |
| 业务库 | MySQL 8 / Redis 7 |
| 前端 | Vue3 + TypeScript + Vite + Element Plus + ECharts |
| 部署 | Docker Compose |

---

## 项目结构

```
├── src/python/                # 后端服务
│   ├── main.py               # FastAPI 入口（7 模块路由挂载）
│   ├── algorithm/            # 核心算法（水力平衡/热损耗/气候补偿/冻堵/仿真）
│   ├── services/             # 业务服务层
│   ├── consumers/            # Kafka 消费者（预警/短信）
│   ├── routes_*.py           # 各模块 API 路由
│   ├── heat_*.py             # 数据生成/Kafka生产/Spark分析/模型训练（改造模板）
│   └── config/db/kafka_topics/response.py  # 基础设施
├── web/                      # Vue3 前端
│   └── src/pages/            # 各模块页面（heat/alarm/workorder/plan/sms/twin/public）
├── config/
│   ├── hive/heat_ddl.sql     # 数仓分层 DDL
│   ├── mysql/heat_init.sql   # MySQL 建表脚本
│   └── logstash/             # Kafka→ES 配置
├── docker/                   # Docker Compose 编排
├── docs/                     # 文档与实现计划
│   ├── 需求分析文档.md
│   ├── 系统设计文档.md
│   ├── 功能开发文档.md
│   └── superpowers/plans/    # 双人实现计划（F0 + Dev-1 + Dev-2）
└── models/                   # 训练模型文件
```

---

## 快速开始

**前置条件**：Python 3.10+、Node.js 18+、Docker + Docker Compose

```bash
# 1. 启动基础集群（Kafka/Hive/Spark/ES/Redis/MySQL）
cd docker && docker-compose up -d && cd ..

# 2. 生成供热模拟数据（1 万条）
python src/python/heat_generate_logs.py --count 10000 --output data/logs

# 3. 启动 Kafka 生产者（实时模拟，300秒）
python src/python/heat_kafka_producer.py --bootstrap localhost:9092 --duration 300

# 4. Spark 离线分析（ODS→DWD→DWS→ADS）
spark-submit --master spark://spark-master:7077 src/python/heat_spark_analysis.py 2026-08-31

# 5. 训练 ML 模型
python src/python/heat_train_model.py

# 6. 启动后端服务
uvicorn src.python.main:app --host 0.0.0.0 --port 8000

# 7. 启动前端（另开终端）
cd web && npm install && npm run dev
```

启动后访问：
- API 文档（Swagger）：`http://localhost:8000/docs`
- 前端大屏：`http://localhost:5173`（Vite 默认端口）

---

## 文档索引

| 文档 | 内容 |
|---|---|
| [需求分析文档](docs/需求分析文档.md) | 切片范围、功能需求 FR、非功能需求 NFR、验收标准 |
| [系统设计文档](docs/系统设计文档.md) | 分层架构、数据模型、核心算法、安全等保三级 |
| [功能开发文档](docs/功能开发文档.md) | API 接口清单、MySQL DDL、错误码、迭代里程碑 |
| [开发任务-运行流](docs/开发任务拆分-角色A-平台与智能底座.md) | 双人拆分：Dev-1 负责 1.2/2.2/8.x/10.x/11.2 |
| [开发任务-处置流](docs/开发任务拆分-角色B-前端与展现层.md) | 双人拆分：Dev-2 负责 4.1/短信/4.2/9.x/5.1 |
| [Dev-1 实现计划](docs/superpowers/plans/Dev-1-运行流.md) | TDD 细粒度任务（含完整代码与测试） |
| [Dev-2 实现计划](docs/superpowers/plans/Dev-2-处置流.md) | TDD 细粒度任务（含完整代码与测试） |

---

## 开发规范

- 命名：类大驼峰，函数/变量小驼峰，常量全大写下划线，标识符英文
- 后端 4 空格缩进，前端 2 空格缩进；函数≤50行，嵌套≤3层
- 所有输入类型/长度/格式/合法性校验；SQL 参数化查询
- 敏感信息（密钥/密码）走环境变量，禁止硬编码；手机号脱敏
- 统一响应：`{"code":0,"message":"ok","data":{...}}`
- 详细规范见 `.trae/rules/技术规范.md`

---

## 开发团队分工

采用**模块垂直拆分**（非前后端拆分）实现双人并行开发，以共享脚手架 F0 为解耦基础：

| 开发者 | 负责模块 | 关键目录 |
|---|---|---|
| Dev-1（运行流） | 数据接入、2.2 供暖运行、8.x 能效、10.x 数字孪生、11.2 公众服务 | `routes_heat`、`routes_twin`、`routes_public`、`algorithm/*`（大部分）、`web/pages/heat/twin/public` |
| Dev-2（处置流） | 4.1 预警、短信、4.2 预报、9.x 工单/巡检、5.1 预案 | `routes_alarm`、`routes_sms`、`routes_workorder`、`routes_plan`、`services/sms_service`、`web/pages/alarm/workorder/plan/sms` |

---

## License

待定（天信管业科技集团所有）
