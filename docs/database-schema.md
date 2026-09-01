# 暖脉 AI 智慧供热平台 — 数据字典

> 版本：v2026.08.31-数据字典
> 覆盖范围：MySQL 主数据/业务表、Hive 数仓分层表、Redis Key、ES Index

---

## 1. MySQL 表（主数据 + 业务）

> 数据库：`warmvein`，字符集 `utf8mb4`，完整建表语句见 `config/mysql/heat_init.sql`

### 1.1 主数据表（Master Data）

#### md_heat_source — 热源

| 字段 | 类型 | 说明 |
|---|---|---|
| source_id | BIGINT PK | 热源 ID（自增） |
| name | VARCHAR(64) | 热源名称 |
| type | VARCHAR(16) | 类型：`boiler`(锅炉) / `heat_pump`(热泵) / `waste`(余热) |
| capacity | DECIMAL(12,2) | 供热能力 MW |
| address | VARCHAR(128) | 地址 |
| lng | DECIMAL(10,7) | 经度 |
| lat | DECIMAL(10,7) | 纬度 |
| status | TINYINT | 0=停用 1=运行 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

---

#### md_station — 换热站

| 字段 | 类型 | 说明 |
|---|---|---|
| station_id | BIGINT PK | 换热站 ID（自增） |
| name | VARCHAR(64) | 站名 |
| source_id | BIGINT | 所属热源 ID |
| area | DECIMAL(10,2) | 供热面积（万㎡） |
| design_flow | DECIMAL(10,2) | 设计流量（m³/h） |
| design_tg | DECIMAL(6,2) | 设计供水温度 ℃ |
| design_th | DECIMAL(6,2) | 设计回水温度 ℃ |
| address | VARCHAR(128) | 地址 |
| lng | DECIMAL(10,7) | 经度 |
| lat | DECIMAL(10,7) | 纬度 |
| status | TINYINT | 0=停用 1=运行 2=检修 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

---

#### md_pipe — 管段

| 字段 | 类型 | 说明 |
|---|---|---|
| pipe_id | BIGINT PK | 管段 ID（自增） |
| name | VARCHAR(64) | 管段名称 |
| station_id | BIGINT | 所属换热站 |
| pipe_type | VARCHAR(16) | `primary`(一次网) / `secondary`(二次网) / `branch`(支干) / `user`(支线) |
| material | VARCHAR(16) | 材质：`steel` / `pe` / `pp` |
| diameter | DECIMAL(8,2) | 管径 mm |
| length_m | DECIMAL(10,2) | 长度 m |
| install_year | INT | 安装年份 |
| insulation | VARCHAR(16) | 保温等级：`good` / `medium` / `poor` / `none` |
| design_flow | DECIMAL(10,2) | 设计流量（m³/h） |
| k_value | DECIMAL(8,4) | 传热系数 W/(m²·℃) |
| min_wall | DECIMAL(6,2) | 最小允许壁厚 mm |
| lng_start / lat_start | DECIMAL(10,7) | 起点经纬度 |
| lng_end / lat_end | DECIMAL(10,7) | 终点经纬度 |
| status | TINYINT | 0=停用 1=运行 2=检修 |
| created_at / updated_at | DATETIME | 时间戳 |

---

#### md_sensor — 传感器

| 字段 | 类型 | 说明 |
|---|---|---|
| sensor_id | BIGINT PK | 传感器 ID（自增） |
| station_id | BIGINT | 所属换热站 |
| pipe_id | BIGINT | 所属管段 |
| sensor_type | VARCHAR(32) | `temp`(温度) / `pressure`(压力) / `flow`(流量) / `heat`(热量) / `corrosion`(腐蚀) / `room_temp`(室温) |
| model | VARCHAR(32) | 型号 |
| install_date | DATE | 安装日期 |
| calibration_due | DATE | 下次校准日期 |
| status | TINYINT | 0=停用 1=正常 2=异常 3=离线 |
| created_at / updated_at | DATETIME | 时间戳 |

---

#### md_user — 供热用户

| 字段 | 类型 | 说明 |
|---|---|---|
| user_id | BIGINT PK | 用户 ID（自增） |
| house_no | VARCHAR(32) | 户号 |
| address | VARCHAR(128) | 地址 |
| phone | VARCHAR(20) | 手机号（明文存储，查询脱敏 `138****1234`） |
| station_id | BIGINT | 所属换热站 |
| area | DECIMAL(8,2) | 建筑面积 ㎡ |
| sms_subscribe | TINYINT | 0=未订阅 1=已订阅短信 |
| created_at / updated_at | DATETIME | 时间戳 |

---

#### md_organization — 组织架构

| 字段 | 类型 | 说明 |
|---|---|---|
| org_id | BIGINT PK | 组织 ID（自增） |
| name | VARCHAR(64) | 组织名称 |
| parent_id | BIGINT | 上级组织 ID |
| org_type | VARCHAR(16) | `company`(公司) / `dept`(部门) / `team`(班组) |
| leader | VARCHAR(32) | 负责人 |
| phone | VARCHAR(20) | 联系电话 |
| created_at | DATETIME | 创建时间 |

---

### 1.2 业务表（Business）

#### biz_alarm — 预警记录

| 字段 | 类型 | 说明 |
|---|---|---|
| alarm_id | BIGINT PK | 预警 ID（自增） |
| station_id | BIGINT | 关联换热站 |
| pipe_id | BIGINT | 关联管段（可选） |
| level | TINYINT | 级别：1=蓝(轻微) 2=黄(1-3月) 3=橙(1月内) 4=红(72h内) |
| type | VARCHAR(32) | 类型：`freeze`/`leak`/`corrosion`/`pressure`/`balance`/`theft`/`other` |
| root_cause | VARCHAR(32) | 根因标签 |
| title | VARCHAR(128) | 预警标题 |
| description | TEXT | 预警描述 |
| status | TINYINT | 0=未确认 1=已确认 2=已处置 3=已关闭 |
| operator | VARCHAR(32) | 确认人 |
| ack_at | DATETIME | 确认时间 |
| created_at | DATETIME | 创建时间 |

**预警级别枚举**：

| level | 颜色 | 含义 | 时间窗口 |
|---|---|---|---|
| 1 | 蓝 | 轻微偏差 | 3 个月内可能发展 |
| 2 | 黄 | 需关注 | 1-3 月内需处理 |
| 3 | 橙 | 严重 | 1 月内需处理 |
| 4 | 红 | 紧急 | 72 小时内需到场 |

---

#### biz_forecast — 预报记录

| 字段 | 类型 | 说明 |
|---|---|---|
| forecast_id | BIGINT PK | 预报 ID |
| station_id | BIGINT | 关联换热站 |
| pipe_id | BIGINT | 关联管段 |
| type | VARCHAR(32) | `freeze`(冻堵) / `lifetime`(寿命) / `fault`(故障) / `energy`(能效) |
| title | VARCHAR(128) | 预报标题 |
| risk_level | VARCHAR(16) | `high` / `medium` / `low` |
| forecast_date | DATE | 预报目标日期 |
| description | TEXT | 预报内容 |
| suggestion | TEXT | 建议措施 |
| status | TINYINT | 0=待查看 1=已查看 2=已处置 |
| created_at | DATETIME | 创建时间 |

---

#### biz_work_order — 工单

| 字段 | 类型 | 说明 |
|---|---|---|
| order_id | BIGINT PK | 工单 ID |
| alarm_id | BIGINT | 触发预警 ID |
| title | VARCHAR(128) | 工单标题 |
| description | TEXT | 工单描述 |
| order_type | VARCHAR(16) | `repair`(维修) / `patrol`(巡检) / `emergency`(应急) |
| priority | TINYINT | 优先级：1=高 2=中 3=低 |
| assignee | VARCHAR(32) | 负责人 |
| station_id | BIGINT | 关联换热站 |
| status | TINYINT | 0=待派 1=已派 2=处置中 3=待核验 4=已销号 |
| due_at | DATETIME | 截止时间 |
| closed_at | DATETIME | 关闭时间 |
| created_at / updated_at | DATETIME | 时间戳 |

**工单状态机**：

```
待派(0) ──派单──▶ 已派(1) ──接单──▶ 处置中(2) ──提交──▶ 待核验(3) ──核验通过──▶ 已销号(4)
   │                 │                   │                    │
   └─ 超时升级        └─ 超时升级          └─ 超时升级           └─ 核验驳回 → 处置中(2)
```

---

#### biz_work_order_trace — 工单轨迹

| 字段 | 类型 | 说明 |
|---|---|---|
| trace_id | BIGINT PK | 轨迹 ID |
| order_id | BIGINT | 工单 ID |
| action | VARCHAR(32) | `create` / `assign` / `accept` / `process` / `review` / `close` / `escalate` |
| operator | VARCHAR(32) | 操作人 |
| remark | TEXT | 备注 |
| created_at | DATETIME | 操作时间 |

---

#### biz_patrol — 巡检计划

| 字段 | 类型 | 说明 |
|---|---|---|
| patrol_id | BIGINT PK | 巡检 ID |
| station_id | BIGINT | 关联换热站 |
| plan_name | VARCHAR(64) | 计划名称 |
| patrol_type | VARCHAR(16) | `daily`(日常) / `special`(专项) / `emergency`(应急) |
| assignee | VARCHAR(32) | 巡检人 |
| plan_date | DATE | 计划日期 |
| status | TINYINT | 0=待执行 1=执行中 2=已完成 3=已取消 |
| route_points | TEXT | 巡检路线点位（JSON 数组） |
| created_at / updated_at | DATETIME | 时间戳 |

---

#### biz_plan — 应急预案

| 字段 | 类型 | 说明 |
|---|---|---|
| plan_id | BIGINT PK | 预案 ID |
| name | VARCHAR(64) | 预案名称 |
| plan_type | VARCHAR(32) | `freeze`(冻堵) / `burst`(爆管) / `shutdown`(停暖) / `third_party`(第三方破坏) |
| alarm_level | TINYINT | 匹配预警级别 |
| trigger_condition | TEXT | 触发条件描述 |
| steps | TEXT | 处置步骤（JSON：`[{step, action, role, resource}]`） |
| resource_list | TEXT | 所需资源（JSON） |
| status | TINYINT | 0=停用 1=启用 |
| created_at / updated_at | DATETIME | 时间戳 |

---

#### biz_plan_execution — 预案执行记录

| 字段 | 类型 | 说明 |
|---|---|---|
| exec_id | BIGINT PK | 执行 ID |
| plan_id | BIGINT | 预案 ID |
| alarm_id | BIGINT | 触发预警 ID |
| operator | VARCHAR(32) | 启动人 |
| status | TINYINT | 0=启动中 1=执行中 2=已完成 3=已终止 |
| started_at | DATETIME | 启动时间 |
| finished_at | DATETIME | 完成时间 |
| remark | TEXT | 执行备注 |

---

#### biz_sms_template — 短信模板

| 字段 | 类型 | 说明 |
|---|---|---|
| template_code | VARCHAR(32) PK | 模板编码 |
| content | VARCHAR(256) | 模板内容（支持 `{var}` 占位符） |
| scene | VARCHAR(32) | 场景：`alarm_blue`/`alarm_yellow`/`alarm_orange`/`alarm_red`/`shutdown`/`frost`/`public`/`custom` |
| status | TINYINT | 0=停用 1=启用 |
| created_at / updated_at | DATETIME | 时间戳 |

**预置模板**：

| 编码 | 场景 | 内容 |
|---|---|---|
| ALARM_BLUE | 蓝色预警 | 【暖脉供热】{stationName}水力失衡预警(蓝色)… |
| ALARM_YELLOW | 黄色预警 | 【暖脉供热】{stationName}设备异常预警(黄色)… |
| ALARM_ORANGE | 橙色预警 | 【暖脉供热】{stationName}严重预警(橙色)… |
| ALARM_RED | 红色预警 | 【暖脉供热】{stationName}紧急预警(红色)… |
| SHUTDOWN | 停暖通知 | 【暖脉供热】尊敬的用户，{area}将于… |
| FROST | 冻堵通知 | 【暖脉供热】寒潮预警，{stationName}已启动防冻模式… |
| PUBLIC | 公众通知 | 【暖脉供热】{message} |

---

#### biz_sms_log — 短信发送记录

| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK | 记录 ID |
| batch_id | VARCHAR(32) | 批次 ID |
| phone_masked | VARCHAR(20) | 手机号（脱敏：`138****1234`） |
| template_code | VARCHAR(32) | 使用的模板编码 |
| content | VARCHAR(256) | 实际发送内容 |
| status | TINYINT | 0=待发送 1=发送中 2=成功 3=失败 4=限流跳过 |
| receipt | VARCHAR(64) | 网关回执 ID |
| error_msg | VARCHAR(128) | 失败原因 |
| retry_count | TINYINT | 重试次数 |
| created_at | DATETIME | 发送时间 |

---

#### biz_console_action — 换热站控制指令

| 字段 | 类型 | 说明 |
|---|---|---|
| action_id | BIGINT PK | 指令 ID |
| station_id | BIGINT | 目标换热站 |
| action_type | VARCHAR(16) | `climate`(气候补偿) / `manual`(手动调节) |
| tg_set | DECIMAL(6,2) | 供水温度设定 ℃ |
| th_set | DECIMAL(6,2) | 回水温度设定 ℃ |
| tw | DECIMAL(5,2) | 室外温度 ℃ |
| pump_speed | DECIMAL(5,2) | 循环泵频率 Hz |
| valve_opening | DECIMAL(5,2) | 阀门开度 % |
| status | TINYINT | 0=待下发 1=已下发 2=执行成功 3=执行失败 |
| operator | VARCHAR(32) | 操作人 |
| created_at | DATETIME | 创建时间 |
| executed_at | DATETIME | 执行时间 |

---

## 2. Hive 数仓表（ODS/DWD/DWS/ADS）

> 完整 DDL 见 `config/hive/heat_ddl.sql`

### 2.1 ODS 层 — 贴源

| 表名 | 存储 | 说明 |
|---|---|---|
| `ods.heat_sensor_raw` | TEXTFILE, raw_json STRING, 按 dt 分区 | 供热传感器原始 JSON |

### 2.2 DWD 层 — 明细

| 表名 | 存储 | 说明 |
|---|---|---|
| `dwd.heat_sensor_detail` | ORC/SNAPPY, 按 dt 分区 | 展开后的传感器明细（温度/压力/流量/热量/腐蚀/健康/告警） |

**关键字段**：sensor_id, station_id, supply_temp, return_temp, pressure, flow_rate, heat_energy, corrosion_rate, wall_thickness, velocity, health_score, alarm_code, is_abnormal

### 2.3 DWS 层 — 汇总

| 表名 | 说明 |
|---|---|
| `dws.heat_station_summary` | 换热站日汇总：平衡度、热损耗、能耗、告警数 |
| `dws.heat_pipe_summary` | 管段日汇总：腐蚀速率、壁厚、热损、剩余寿命 |

### 2.4 ADS 层 — 应用

| 表名 | 说明 |
|---|---|
| `ads.heat_overview` | 大屏总览：站/管/用户数、全网温压流、能效KPI、告警分布 |
| `ads.heat_alarm_stats` | 告警统计：按类型+级别聚合，平均处置时长 |

---

## 3. Redis Key 规范

| Key 模式 | 说明 | TTL |
|---|---|---|
| `alarm:latest:{stationId}` | 换热站最新告警缓存 | 30 分钟 |
| `sms:limit:{phone}` | 短信日发送计数器 | 24 小时（当天结束） |
| `dict:{dictType}` | 数据字典缓存 | 1 小时 |
| `session:{token}` | 用户会话 | 30 分钟（滑动） |
| `rate_limit:{ip}:{api}` | API 限流计数 | 1 分钟 |
| `sms_circuit:{provider}` | 短信熔断器状态 | — |

> 所有 Key 统一加前缀 `warmvein:`（可通过 `REDIS_KEY_PREFIX` 环境变量配置）

---

## 4. Elasticsearch Index

| Index 模式 | 说明 |
|---|---|
| `heat-sensor-{YYYY.MM.dd}` | 供热传感器时序数据（Logstash 从 Kafka 写入） |

**Document 结构**：
```json
{
  "sensor_id": "S001",
  "station_id": "1",
  "event_timestamp": "2026-08-31 14:30:00.000",
  "supply_temp": 65.2,
  "return_temp": 45.1,
  "pressure": 0.62,
  "flow_rate": 120.5,
  "heat_energy": 3.25,
  "corrosion_rate": 0.02,
  "health_score": 87,
  "alarm_code": 0,
  "dt": "2026-08-31",
  "hour": 14
}
```

**Document ID 格式**：`{sensor_id}-{event_timestamp}`

---

## 5. Kafka Topic

| Topic | 分区策略 | 说明 |
|---|---|---|
| `heat-sensor-topic` | key=stationId | 供热传感器数据流（JSON） |
| `heat-alarm-topic` | key=stationId | 告警事件流（JSON） |

**传感器消息格式**：
```json
{
  "sensor_id": "S001",
  "station_id": "1",
  "station_name": "安塞区第一换热站",
  "device_type": "station",
  "event_timestamp": "2026-08-31 14:30:00",
  "ts": 1725111000000,
  "params": {
    "supplyTemp": 65.2,
    "returnTemp": 45.1,
    "pressure": 0.62,
    "flowRate": 120.5,
    "heatEnergy": 3.25,
    "corrosionRate": 0.02,
    "wallThickness": 8.5,
    "roomTemp": 21.3,
    "outdoorTemp": -3.5,
    "velocity": 1.2
  },
  "alarm_code": 0,
  "alarm_desc": "",
  "health_score": 87
}
```
