# 开发任务拆分 — 角色 A：平台与智能底座（后端 / 数据 / 算法）

> 版本：v2026.08.31-任务拆分-A
> 配对文档：《开发任务拆分 — 角色 B：前端与展现层》
> 对接契约：以《功能开发文档》§3 API 接口清单 为唯一冻结契约

---

## 1. 角色定位与边界

- **你负责**：感知接入、数仓、核心算法、AI 模型、预警/预报/能效/孪生仿真服务、工单与巡检业务服务、短信服务、FastAPI 全部接口、MySQL/Hive/Logstash 配置。
- **你不管**：任何前端页面、Vue 组件、ECharts 图表。这些全部归角色 B。
- **唯一对接面**：对外暴露《功能开发文档》§3 的 REST API。不向前端推送任何 UI 代码。

---

## 2. 代码所有权（目录隔离，避免 PR 冲突）

你独占以下目录，角色 B 不触碰：
```
src/python/                 # 后端全部（改造现有）
  heat_generate_logs.py
  heat_kafka_producer.py
  heat_spark_analysis.py
  heat_train_model.py
  main.py                   # 供热平台 FastAPI 服务
  algorithm/                # 纯函数算法（可单测）
    hydraulic_balance.py  heat_loss.py  climate_compensation.py
    frost_risk.py  user_abnormal.py  lifetime.py  twin_recovery.py
  services/
    sms_service.py  alarm_engine.py  workorder_service.py  plan_service.py
  config/settings.py
config/
  hive/heat_ddl.sql         # 新增供热数仓 DDL
  mysql/heat_init.sql       # 新增 MySQL 主数据/业务表
  logstash/heat_kafka_to_es.conf
```
⚠ 不要修改 `web/`、`docs/功能开发文档.md` 中的 API 契约表。契约变更需双方同步升级版本号。

---

## 3. 技术栈
Python 3.10+ / FastAPI / scikit-learn / joblib；Spark 3.x / Hive；Kafka；MySQL 8；Redis 7；ES。
遵循 `.trae/rules/技术规范.md`：输入校验、参数化查询、敏感信息走环境变量、统一错误码（§功能开发文档 9）。

---

## 4. 并行开发约定（与角色 B 的协作）

1. **契约冻结**：《功能开发文档》§3 接口路径/入参/出参为唯一标准。B 已据此写 Mock。你实现的接口必须与之对齐（路径、字段名、code/message/data 结构）。
2. **Mock 先行**：B 用本地 JSON Mock 开发，不依赖你的服务启动。你无需等 B。
3. **零共享文件**：双方目录无交集，PR 无文件冲突。
4. **契约变更协议**：若必须改字段，升级契约版本（如 v2），在双方文档标注，B 同步改 Mock；旧版本保留兼容期。
5. **联调时机**：各自 M3 结束后再做端到端联调，此前互不阻塞。

---

## 5. 任务拆解（里程碑）

### M1 — 数据接入与监测底座
- [ ] `config/mysql/heat_init.sql`：建主数据/业务表（md_user/md_pipe/md_station/md_heat_source/md_sensor + biz_*，详见功能开发文档 §8）。
- [ ] `config/hive/heat_ddl.sql`：ods/dwd/dws/ads 供热分层表。
- [ ] `config/logstash/heat_kafka_to_es.conf`：topic→`heat-sensor-topic`，index→`heat-sensor-%{+YYYY.MM.dd}`。
- [ ] `heat_generate_logs.py`：由 generate_logs.py 改造，设备类型=热源/换热站/管段/用户，参数=supplyTemp/returnTemp/pressure/flow/heat/corrosionRate/roomTemp，4% 注入异常。
- [ ] `heat_kafka_producer.py`：Topic=`heat-sensor-topic`/`heat-alarm-topic`，key=stationId。
- [ ] `heat_spark_analysis.py`：DWD 展开供热字段；DWS 计算 heat_station_summary/heat_pipe_summary；ADS heat_overview/heat_alarm_stats。
- [ ] `main.py` 改造：挂载 `/heat/stations`、`/heat/station/{id}/realtime`，返回实时参数。
- ✅ 验收：Kafka→Spark→ES→API→（B Mock）全链路跑通；监测接口返回契约字段。

### M2 — 预警 / 预报 / 能效 / 短信
- [ ] `algorithm/hydraulic_balance.py`、`heat_loss.py`、`climate_compensation.py`、`frost_risk.py`、`user_abnormal.py`、`lifetime.py`（纯函数，附 pytest 单测）。
- [ ] `services/alarm_engine.py`：四级预警(蓝1/黄2/橙3/红4)判定、降噪聚合、根因标签、发布 AlarmEvent。
- [ ] `services/sms_service.py`：SMSSender 抽象 + Aliyun/Tencent/LocalMock；模板填充、脱敏(mask_phone)、Redis 限流、失败重试(≤3,指数退避)、落库 biz_sms_log（详见功能开发文档 §6）。
- [ ] `heat_train_model.py`：IsolationForest 异常检测、RF 用热异常三分类、RF 剩余寿命回归；保存到 models/。
- [ ] API：`/api/heat/balance`、`/api/heat/loss`、`/api/heat/energy`、`/api/console/climate-compensate`、`/api/alarm/list`、`/api/alarm/ack`、`/api/forecast/list`、`/api/sms/send`、`/api/sms/log`。
- [ ] 预警引擎联动短信：蓝/黄→责任人；橙/红→责任人+主管+应急；公众停暖→订阅用户批量（见功能开发文档 §6.2）。
- ✅ 验收：四级预警准确率≥95%、误报≤5%；短信 mock 发送成功率 100%、脱敏合规；ML 模型加载成功。

### M3 — 工单 / 巡检 / 预案 / 孪生仿真
- [ ] `services/workorder_service.py`：工单状态机(0待派→1已派→2处置中→3待核验→4销号)、智能派单、超时升级；API `/workorder/create`、`/workorder/{id}`。
- [ ] `services/plan_service.py`：预案结构化+按预警匹配/启动；API `/plan/match`、`/plan/activate`。
- [ ] `algorithm/twin_recovery.py`：停暖恢复热力仿真（离散时间步，收敛判据 用户室温≥18℃）；API `/twin/simulate/recovery`。
- [ ] `/patrol/plan/generate`：基于预警/季节生成巡检计划与路线。
- ✅ 验收：预警→工单→核验闭环；冻堵预案自动提温/加流；恢复仿真返回 tReach 与曲线数据。

### M4 — 合规与收尾
- [ ] 等保三级：TLS、敏感字段加密、手机号脱敏、操作/系统日志审计（biz/log + ES）。
- [ ] 统一错误码全量覆盖（功能开发文档 §9）；参数化查询防注入校验。
- [ ] `src/python/config/settings.py`：短信密钥/DB/Redis 走环境变量。
- [ ] 与角色 B 端到端联调；性能达标（10k 点/5s 采集，实时延迟≤5s，日批≤30min）。
- ✅ 验收：等保自查项逐条通过；联调通过；压测达标。

---

## 6. 验收标准（角色 A）
1. 全部 API 与冻结契约一致（字段名/结构/错误码）。
2. 算法单测通过；ML 模型可加载并产出预测。
3. 短信服务 mock 跑通模板/脱敏/限流/重试/回执。
4. 工单闭环率≥98%，派单≤5min；冻堵预警提前≥24h。
5. 等保三级关键项（加密/脱敏/审计/注入防护）通过。

---

## 7. 风险与解耦点
- **GIS/BIM 数据缺失**：数字孪生二维降级，不阻塞；三维模型由 B 在缺数据时降级为一张图。
- **短信真实网关密钥**：先用 LocalMock，密钥到位后切换环境变量，不影响开发。
- **契约变更**：唯一阻塞点，靠 §4 协议规避——任何字段变更先升版本再改。
