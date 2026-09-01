# 暖脉 AI 智慧供热平台 — API 接口文档

> ⚠ **规划态契约**：以下 17 个端点为《功能开发文档》§3 冻结的接口契约，当前路由均为 F0 空桩，由各模块开发计划（Dev-1/Dev-2）实现。

> 版本：v2026.08.31-API
> Base URL：`http://localhost:8000`
> 认证：当前开发环境无鉴权；生产环境通过 Header `Authorization: Bearer <token>` 传递

---

## 通用说明

### 统一响应格式

```json
{
  "code": 0,
  "message": "ok",
  "data": { ... }
}
```

### 错误码

| code | 含义 | 说明 |
|---|---|---|
| `0` | 成功 | 正常响应 |
| `40001` | 参数校验失败 | 请求参数类型/长度/格式不合法 |
| `40002` | 资源不存在 | 查询的 ID 或资源未找到 |
| `40003` | 权限不足 | 当前用户无权访问 |
| `50001` | 服务内部错误 | 服务端异常，不暴露栈信息 |
| `50002` | 模型未加载 | ML 模型文件缺失，预测接口不可用 |
| `50003` | 短信网关失败 | 短信发送失败（网关超时/余额不足等） |

### 分页约定

列表接口支持以下 query 参数：
- `page`：页码，默认 `1`
- `pageSize`：每页条数，默认 `20`，最大 `100`

分页响应在 `data` 中包含 `total` 字段表示总条数。

---

## 1. 供暖管网运行（/api/heat）

### 1.1 GET /api/heat/stations — 换热站列表

**说明**：查询换热站列表，支持按区域筛选。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| region | query | string | 否 | 区域名称筛选 |

**响应 data**：
```json
{
  "stations": [
    {
      "stationId": 1,
      "name": "安塞区第一换热站",
      "sourceId": 1,
      "area": 12.5,
      "address": "安塞区XX路",
      "lng": 109.32,
      "lat": 36.86,
      "status": 1,
      "supplyTemp": 65.2,
      "returnTemp": 45.1,
      "pressure": 0.62
    }
  ]
}
```

---

### 1.2 GET /api/heat/station/{id}/realtime — 换热站实时参数

**说明**：查询指定换热站的实时运行参数。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| id | path | integer | 是 | 换热站 ID |

**响应 data**：
```json
{
  "stationId": 1,
  "stationName": "安塞区第一换热站",
  "supplyTemp": 65.2,
  "returnTemp": 45.1,
  "tempDiff": 20.1,
  "pressure": 0.62,
  "flowRate": 120.5,
  "heatEnergy": 3.25,
  "corrosionRate": 0.02,
  "wallThickness": 8.5,
  "roomTemp": 21.3,
  "outdoorTemp": -3.5,
  "velocity": 1.2,
  "healthScore": 87,
  "eventTime": "2026-08-31 14:30:00"
}
```

**错误码**：`40002` — 换热站不存在

---

### 1.3 GET /api/heat/balance — 水力平衡分析

**说明**：计算各支路平衡度 β，标识失衡支路并给出调节建议。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| stationId | query | integer | 是 | 换热站 ID |

**响应 data**：
```json
{
  "stationId": 1,
  "branches": [
    {
      "branchId": "B001",
      "branchName": "北区支路",
      "actualFlow": 45.2,
      "designFlow": 48.0,
      "beta": 0.942,
      "unbalanced": false,
      "suggestOpen": 5.8
    },
    {
      "branchId": "B002",
      "branchName": "南区支路",
      "actualFlow": 30.1,
      "designFlow": 40.0,
      "beta": 0.753,
      "unbalanced": true,
      "suggestOpen": 24.7
    }
  ],
  "unbalancedCount": 1
}
```

**失衡判定**：β < 0.9 或 β > 1.1 为失衡。

---

### 1.4 GET /api/heat/loss — 热损耗核算

**说明**：按管段计算散热损失。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| date | query | string | 是 | 日期（yyyy-MM-dd） |

**响应 data**：
```json
{
  "date": "2026-08-31",
  "pipeLoss": [
    {
      "pipeId": 1,
      "pipeName": "一次网主管",
      "kValue": 0.5,
      "diameter": 0.3,
      "length": 500,
      "supplyTemp": 65.2,
      "returnTemp": 45.1,
      "outdoorTemp": -3.5,
      "heatLossW": 5423.8,
      "totalLossKwh": 130.2
    }
  ],
  "totalLossW": 12580.3
}
```

**算法**：`Q_loss = K × π × D × L × (T_avg - T_ambient)`

---

### 1.5 GET /api/heat/energy — 能效指标

**说明**：查询指定日期的能效 KPI。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| date | query | string | 是 | 日期（yyyy-MM-dd） |
| region | query | string | 否 | 区域筛选 |

**响应 data**：
```json
{
  "date": "2026-08-31",
  "totalHeatEnergy": 1250.5,
  "totalHeatLoss": 150.3,
  "heatLossRate": 12.0,
  "unitEnergy": 0.42,
  "avgRoomTemp": 21.5,
  "energySavingRate": 8.3,
  "carbonReduction": 2.1
}
```

---

## 2. 气候补偿控制（/api/console）

### 2.1 POST /api/console/climate-compensate — 气候补偿调节

**说明**：根据室外温度计算二次供水温度设定值，生成控制指令。

**请求体**：
```json
{
  "stationId": 1,
  "tw": -5.0
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| stationId | integer | 是 | 换热站 ID |
| tw | number | 是 | 当前室外温度 ℃ |

**响应 data**：
```json
{
  "stationId": 1,
  "tw": -5.0,
  "TgSet": 62.5,
  "thSet": 37.5,
  "actionId": 1001,
  "status": 0
}
```

**算法**：`Tg_set = tn + (Tg_d - tn) × (tw - tn) / (tw_d - tn)`

**错误码**：`40001` — 参数缺失；`40002` — 换热站不存在

---

## 3. 预警管理（/api/alarm）

### 3.1 GET /api/alarm/list — 预警列表

**说明**：分页查询预警记录。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| level | query | integer | 否 | 预警级别 1-4 |
| status | query | integer | 否 | 0=未确认 1=已确认 2=已处置 3=已关闭 |
| page | query | integer | 否 | 页码，默认 1 |
| pageSize | query | integer | 否 | 每页条数，默认 20 |

**响应 data**：
```json
{
  "total": 156,
  "alarms": [
    {
      "alarmId": 1001,
      "stationId": 1,
      "stationName": "安塞区第一换热站",
      "level": 3,
      "levelName": "橙色",
      "type": "freeze",
      "typeName": "冻堵",
      "rootCause": "供水温度过低",
      "title": "安塞区第一换热站冻堵预警",
      "status": 0,
      "statusName": "未确认",
      "createdAt": "2026-08-31 14:30:00"
    }
  ]
}
```

**预警级别**：1=蓝(轻微)、2=黄(1-3月)、3=橙(1月内)、4=红(72h内)

---

### 3.2 POST /api/alarm/ack — 预警确认

**说明**：确认预警，记录操作人。

**请求体**：
```json
{
  "alarmId": 1001,
  "operator": "张三"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| alarmId | integer | 是 | 预警 ID |
| operator | string | 是 | 确认人 |

**响应 data**：
```json
{
  "ok": true,
  "alarmId": 1001
}
```

**错误码**：`40002` — 预警不存在

---

## 4. 预报管理（/api/forecast）

### 4.1 GET /api/forecast/list — 预报列表

**说明**：查询预报记录。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| type | query | string | 否 | freeze / lifetime / fault / energy |
| page | query | integer | 否 | 页码 |
| pageSize | query | integer | 否 | 每页条数 |

**响应 data**：
```json
{
  "total": 42,
  "forecasts": [
    {
      "forecastId": 201,
      "stationId": 1,
      "type": "freeze",
      "typeName": "冻堵预报",
      "title": "未来3天冻堵风险",
      "riskLevel": "high",
      "forecastDate": "2026-09-02",
      "description": "预计9月2日最低气温-12℃，供水温度5℃以下，有冻堵风险",
      "suggestion": "建议提前提升供水温度至50℃以上，增加循环泵频率",
      "status": 0,
      "createdAt": "2026-08-31 14:30:00"
    }
  ]
}
```

---

## 5. 工单管理（/api/workorder）

### 5.1 POST /api/workorder/create — 创建工单

**说明**：由预警触发或手动创建工单。

**请求体**：
```json
{
  "alarmId": 1001,
  "title": "第一换热站冻堵处置",
  "description": "供水温度异常偏低，需到场检查",
  "orderType": "emergency",
  "priority": 1,
  "assignee": "李四",
  "stationId": 1,
  "dueAt": "2026-08-31 18:00:00"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| alarmId | integer | 否 | 关联预警 ID |
| title | string | 是 | 工单标题 |
| description | string | 否 | 描述 |
| orderType | string | 是 | repair / patrol / emergency |
| priority | integer | 否 | 1=高 2=中 3=低，默认 2 |
| assignee | string | 否 | 指派人 |
| stationId | integer | 否 | 关联换热站 |
| dueAt | string | 否 | 截止时间（yyyy-MM-dd HH:mm:ss） |

**响应 data**：
```json
{
  "orderId": 3001
}
```

---

### 5.2 GET /api/workorder/{id} — 工单详情

**说明**：查询工单详情和操作轨迹。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| id | path | integer | 是 | 工单 ID |

**响应 data**：
```json
{
  "orderId": 3001,
  "alarmId": 1001,
  "title": "第一换热站冻堵处置",
  "orderType": "emergency",
  "priority": 1,
  "assignee": "李四",
  "status": 2,
  "statusName": "处置中",
  "createdAt": "2026-08-31 14:35:00",
  "updatedAt": "2026-08-31 15:00:00",
  "trace": [
    { "action": "create", "operator": "系统", "time": "2026-08-31 14:35:00" },
    { "action": "assign", "operator": "调度员", "time": "2026-08-31 14:36:00" },
    { "action": "accept", "operator": "李四", "time": "2026-08-31 14:40:00" },
    { "action": "process", "operator": "李四", "time": "2026-08-31 15:00:00", "remark": "已到场检查" }
  ]
}
```

**工单状态机**：`待派(0) → 已派(1) → 处置中(2) → 待核验(3) → 已销号(4)`

---

## 6. 预案管理（/api/plan）

### 6.1 POST /api/plan/match — 匹配预案

**说明**：根据预警类型和级别自动匹配适用预案。

**请求体**：
```json
{
  "alarmType": "freeze",
  "level": 4
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| alarmType | string | 是 | freeze / burst / shutdown / third_party |
| level | integer | 是 | 预警级别 1-4 |

**响应 data**：
```json
{
  "plans": [
    {
      "planId": 101,
      "name": "冻堵应急处置预案(红色)",
      "planType": "freeze",
      "alarmLevel": 4,
      "steps": [
        { "step": 1, "action": "立即提升供水温度至60℃以上", "role": "调度员", "resource": "气候补偿系统" },
        { "step": 2, "action": "关闭故障段阀门", "role": "巡检员", "resource": "阀门控制器" },
        { "step": 3, "action": "通知受影响用户", "role": "客服", "resource": "短信服务" }
      ]
    }
  ]
}
```

---

### 6.2 POST /api/plan/activate — 启动预案

**说明**：启动指定预案，创建执行记录。

**请求体**：
```json
{
  "planId": 101,
  "alarmId": 1001,
  "operator": "调度员"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| planId | integer | 是 | 预案 ID |
| alarmId | integer | 否 | 关联预警 ID |
| operator | string | 否 | 操作人 |

**响应 data**：
```json
{
  "ok": true,
  "execId": 5001
}
```

---

## 7. 短信服务（/api/sms）

### 7.1 POST /api/sms/send — 发送短信

**说明**：通过模板发送短信，支持批量发送。

**请求体**：
```json
{
  "templateCode": "ALARM_ORANGE",
  "phones": ["13812345678", "13900001111"],
  "vars": {
    "stationName": "安塞区第一换热站",
    "leaderPhone": "135****6789"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| templateCode | string | 是 | 模板编码（见 biz_sms_template） |
| phones | string[] | 是 | 手机号列表 |
| vars | object | 是 | 模板变量（键值对） |

**响应 data**：
```json
{
  "batchId": "b1725111800",
  "totalCount": 2,
  "sentCount": 2,
  "skippedCount": 0
}
```

**错误码**：`50003` — 短信网关失败

---

### 7.2 GET /api/sms/log — 短信记录

**说明**：查询短信发送记录。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| batchId | query | string | 否 | 批次 ID |
| page | query | integer | 否 | 页码 |
| pageSize | query | integer | 否 | 每页条数 |

**响应 data**：
```json
{
  "total": 2,
  "logs": [
    {
      "id": 1,
      "batchId": "b1725111800",
      "phoneMasked": "138****5678",
      "templateCode": "ALARM_ORANGE",
      "status": 2,
      "statusName": "成功",
      "receipt": "ali-biz-123456",
      "retryCount": 0,
      "createdAt": "2026-08-31 14:30:00"
    }
  ]
}
```

**短信状态**：0=待发送 1=发送中 2=成功 3=失败 4=限流跳过

---

## 8. 数字孪生（/api/twin）

### 8.1 POST /api/twin/simulate/recovery — 停暖恢复仿真

**说明**：模拟停暖后复暖过程，预测达标时间与温度曲线。

**请求体**：
```json
{
  "stationId": 1,
  "curve": {
    "startTime": "2026-08-31 08:00:00",
    "targetSupplyTemp": 65.0,
    "rampRate": 2.0,
    "steps": 24
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| stationId | integer | 是 | 换热站 ID |
| curve | object | 是 | 升温曲线参数 |
| curve.startTime | string | 是 | 开始时间 |
| curve.targetSupplyTemp | number | 是 | 目标供水温度 ℃ |
| curve.rampRate | number | 否 | 升温速率 ℃/h，默认 2.0 |
| curve.steps | integer | 否 | 仿真步数，默认 24 |

**响应 data**：
```json
{
  "stationId": 1,
  "tReach": "2026-08-31 14:30:00",
  "hoursToReach": 6.5,
  "converged": true,
  "chart": {
    "timestamps": ["08:00", "09:00", "10:00", "..."],
    "supplyTemp": [20.0, 22.0, 24.0, "..."],
    "returnTemp": [18.0, 19.5, 21.0, "..."],
    "roomTemp": [16.0, 16.5, 17.2, "...", 18.0]
  }
}
```

**收敛判据**：所有用户室温 ≥ 18℃

---

## 9. 巡检管理（/api/patrol）

### 9.1 POST /api/patrol/plan/generate — 生成巡检计划

**说明**：根据规则自动生成巡检计划。

**请求体**：
```json
{
  "rule": {
    "stationId": 1,
    "patrolType": "daily",
    "assignee": "王五",
    "planDate": "2026-09-01",
    "checkPoints": ["阀门", "压力表", "温度计", "补偿器"]
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| rule | object | 是 | 巡检规则 |
| rule.stationId | integer | 否 | 关联换热站 |
| rule.patrolType | string | 是 | daily / special / emergency |
| rule.assignee | string | 否 | 巡检人 |
| rule.planDate | string | 是 | 计划日期 |
| rule.checkPoints | string[] | 否 | 巡检点位 |

**响应 data**：
```json
{
  "planId": 6001,
  "stationId": 1,
  "planDate": "2026-09-01",
  "checkPoints": ["阀门", "压力表", "温度计", "补偿器"],
  "estimatedDuration": 60
}
```

---

## 附录：接口总览

| # | 方法 | 路径 | 模块 |
|---|---|---|---|
| 1 | GET | /api/heat/stations | 供暖运行 |
| 2 | GET | /api/heat/station/{id}/realtime | 供暖运行 |
| 3 | GET | /api/heat/balance | 水力平衡 |
| 4 | GET | /api/heat/loss | 热损耗 |
| 5 | GET | /api/heat/energy | 能效 |
| 6 | POST | /api/console/climate-compensate | 气候补偿 |
| 7 | GET | /api/alarm/list | 预警 |
| 8 | POST | /api/alarm/ack | 预警 |
| 9 | GET | /api/forecast/list | 预报 |
| 10 | POST | /api/workorder/create | 工单 |
| 11 | GET | /api/workorder/{id} | 工单 |
| 12 | POST | /api/plan/match | 预案 |
| 13 | POST | /api/plan/activate | 预案 |
| 14 | POST | /api/sms/send | 短信 |
| 15 | GET | /api/sms/log | 短信 |
| 16 | POST | /api/twin/simulate/recovery | 数字孪生 |
| 17 | POST | /api/patrol/plan/generate | 巡检 |
