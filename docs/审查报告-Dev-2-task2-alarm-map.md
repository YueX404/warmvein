# Dev-2 Task 2 代码审查报告

> **审查日期：** 2026-09-01  
> **审查角色：** 审查窗口（只读，未改实现、未提交）  
> **分支：** `dev-2/feature/task2-alarm-map`（worktree：`D:\YY-task2`，当前 `D:\YY` 仍在 `master`）  
> **对照基线：** `master`（`ccaa50c` → `00c0bd8`）  
> **需求 / 计划：** `docs/superpowers/plans/Dev-2-task2-alarm-map.md`  
> **审查对象：** `src/python/routes_alarm.py`、`tests/test_alarm_routes.py`、`web/src/pages/alarm/AlarmMap.vue`、`web/src/services/alarm.api.ts`、`web/src/mock/alarm.mock.ts`，以及角色 A 快照  
> **交叉核对：** `config/mysql/heat_init.sql`（`biz_alarm`）、`docs/database-schema.md`、`docs/api-guide.md` §3、`docs/功能开发文档.md`、F0 冻结边界、共享组件 `AlarmCard` / `StationMap`

---

## 一、总体结论

**暂不建议合入。**

计划内 5 个独占文件均已落地，F0 冻结文件未动，路由路径正确（`GET /api/alarm/list`、`POST /api/alarm/ack`），列表 SQL 参数化，单测当场验证 **8 passed**。前端用只读 `AlarmCard` 做了蓝/黄/橙/红分级着色，也没有误挂 `/forecast`。

但有两处合入前必须修的正确性问题：

1. 确认按钮的失败/取消路径会把预警**本地改成已确认并弹出成功**，调度员会以为已经 ack。
2. `POST /api/alarm/ack` 无条件 `SET status=1`，已处置 / 已关闭的记录会被打回「已确认」。

单测只 mock 了 Session，**不证明** MySQL 真查、真更新；前端没有单测，错误回落路径也没覆盖。

**合入建议：先修全部 P1；P2（Mock 误当实数、筛选清空、无 LIMIT、站点写死）建议一并改。P3 / 疑问可记 follow-up。**

---

## 二、审查范围与提交

| 项 | 内容 |
|---|---|
| 相对 `master` 的提交 | `33fcacf` `feat(4.1): 预警列表/确认 API 与预警一张图` |
| | `00c0bd8` `docs(task-2): 补齐自验证快照，阶段标记为待审查` |
| 修改 / 新增 | `src/python/routes_alarm.py`（+81） |
| | `tests/test_alarm_routes.py`（+133，新建） |
| | `web/src/pages/alarm/AlarmMap.vue`（+323） |
| | `web/src/services/alarm.api.ts`（+24，新建） |
| | `web/src/mock/alarm.mock.ts`（+82） |
| | `snapshots/role-a/dev-record-a.md`、`snapshots/role-a/progress.md` |
| 未改动（符合 F0 冻结与独占） | `main.py`、`kafka_topics.py`、`response.py`、`db.py`、`config/settings.py`、`config/mysql/heat_init.sql`、`web/src/router/index.ts`、`web/src/components/*`、`tests/test_scaffold.py`、Kafka 消费者、`/forecast` |
| 阶段快照 | `snapshots/role-a/progress.md` 为「开发完成，待审查」，允许审查 |
| 单测（审查当场） | `pytest tests/test_alarm_routes.py -v` → **8 passed** |

---

## 三、做得好的地方

- 改动落在 Task 2 独占文件内，没有触碰 F0 冻结文件，也没有 import `alarm_engine`、没有加 forecast 路由。
- 路由按 F0 约定写完整路径 `@router.get("/alarm/list")`，经 `main.py` 的 `/api` 前缀后正好是契约 URL。
- SQL 全部参数绑定；`status=0` 用 `is not None` 判断，避开了计划 snippet 里 `if status` 把 0 当 falsy 丢掉的坑，并有对应单测。
- 列表输出 camelCase + `levelName`/`statusName`，确认写入 `operator`、`ack_at`，比计划最小 snippet 更贴近 `biz_alarm` 表和 api-guide。
- `operator` 做了类型、空白、32 字符（对齐 `VARCHAR(32)`）校验；`alarmId <= 0` 返回 40001。
- 前端只读使用 `AlarmCard`（分级着色），没有改共享组件；`StationMap` 仍是 F0 空桩，页面用换热站卡片补了可点选能力。
- 开发记录和 progress 已切到 Task 2，自验证项写清楚了 `test_scaffold` 空桩冲突不在本分支改。

---

## 四、问题清单

优先级约定：

- **P0 / 🔴**：合入即导致生产级阻断（本次无）
- **P1 / 🔴**：必须在合入前修复
- **P2 / 🟡**：应修复，否则联调或上线会踩坑
- **P3 / 🔵**：低影响，或需要开发窗口确认意图

### P1 — 必须修复（🔴）

#### P1-1 确认失败或关闭对话框会被当成「已确认成功」

- **位置：** `web/src/pages/alarm/AlarmMap.vue:205-225`
- **问题：** `onAck` 的 `catch` 只把 `err === "cancel"` 当取消。其余一律：
  - 把当前卡片 `status` 改成 1、文案改成「已确认」
  - `usingMock = true`
  - `ElMessage.success("已本地确认（后端未就绪）")`
- **会误伤的路径：**
  1. 点对话框右上角关闭：Element Plus 的 reject 值是 `"close"`，不是 `"cancel"`，会走「本地确认成功」。
  2. 后端返回 40001 / 40002 / 50001，或网络失败：拦截器已经 `ElMessage.error`，这里再弹 success，按钮消失，库里的预警仍是未确认。
  3. 操作人超过 32 字符：后端拒了，前端仍显示已确认。
- **影响：** 调度员以为 ack 已完成，真实未确认预警会漏处置。这是写操作上的假成功，不是展示问题。
- **修复：**
  - 取消/关闭（`"cancel"` / `"close"`）直接 return，不要改数据。
  - `ackAlarm` 失败只保留错误提示，不要改 `item.status`，不要 `success`。
  - 若仍要 Mock 确认，必须显式判断「当前本来就在用 Mock」再改本地夹具，不能把任意 API 失败都当成 Mock。

#### P1-2 ack 无条件把任意状态写成「已确认」

- **位置：** `src/python/routes_alarm.py:75-84`
- **问题：**

```sql
UPDATE biz_alarm SET status=1, operator=:operator, ack_at=NOW()
WHERE alarm_id=:alarm_id
```

没有 `AND status=0`。对 `status=2`（已处置）或 `3`（已关闭）再调一次 ack，记录会被打回「已确认」，并覆盖 `operator` / `ack_at`。

- **影响：** 前端按钮虽然只在 `status===0` 显示，但 API 没有状态机。工单/预案后续只要误调或重放请求，就会把已关闭预警重新打开。`rowcount==0` 也不能当「不存在」：MySQL 默认统计的是 **changed** 行，重复确认且字段无变化时可能误报 40002。
- **修复：** `WHERE alarm_id=:id AND status=0`。`rowcount==0` 时先按主键查：没有行 → 40002；已是终态 → 40001（或明确「已确认/已关闭，不可重复确认」）。不要用无条件 `status=1` 覆盖 2/3。

---

### P2 — 应修复（🟡）

#### P2-1 列表接口一旦失败就展示 Mock 实况

- **位置：** `web/src/pages/alarm/AlarmMap.vue:191-203`
- **问题：** `loadAlarms` 对任何异常（后端 500、校验失败、超时、筛选参数不合法）都 `filterAlarms(...)` 填入安塞区四个假预警，只靠一行「后端未就绪」区分。
- **影响：** MySQL 挂了或过滤参数发错时，页面仍显示冻堵/泄漏等红色预警。安全生命线场景下，假告警和真告警混在同一张图上。
- **修复：** 仅在明确的开发回落（例如 `import.meta.env.DEV` 且后端不可达）才用 Mock；生产路径应 `ElMessage.error` + 空列表，不要用夹具冒充实时数据。

#### P2-2 清空筛选可能把 `null` 传给后端，再掉进 Mock

- **位置：** `web/src/services/alarm.api.ts:16-20`，`AlarmMap.vue` 的 `el-select` `clearable`
- **问题：** Element Plus 清空后 `v-model` 常见值是 `null`。`if (level !== undefined)` 对 `null` 为真，请求会带 `level=null`。FastAPI `level: int` 校验失败走 422，于是触发 P2-1 的 Mock。
- **影响：** 用户点「清空级别」后，页面从真实列表变成四条假数据，还提示后端未就绪。
- **修复：** 只在 `typeof level === "number"`（status 同理）时写入 params；或把 `v-model` 规范成 `undefined`。

#### P2-3 列表无 LIMIT，全表一次返回

- **位置：** `src/python/routes_alarm.py:15-61`
- **问题：** `SELECT ... FROM biz_alarm WHERE 1=1 ORDER BY created_at DESC` 没有上限。api-guide 写了 `page`/`pageSize`（默认 20），本 Task 计划返回数组，但至少应有硬顶。
- **影响：** 供暖季告警堆积后，一张图一次拉全表，接口和前端渲染都会拖死。
- **修复：** 本 Task 可以不实现完整分页，但应加 `LIMIT`（如 200）或默认 `status=0`。完整 `{total, alarms}` 可留给后续，不必一次对齐 api-guide。

#### P2-4 地图与站点卡片写死 3 个 Mock 换热站

- **位置：** `web/src/pages/alarm/AlarmMap.vue:147-172`，`web/src/mock/alarm.mock.ts:67-71`
- **问题：** `mapStations` / `stationCards` 只遍历 mock 里的 station 1/2/3。真实 `biz_alarm.station_id` 不在这三个里时，列表能看到「换热站 #N」，地图和左侧卡片没有对应点。
- **影响：** 「预警一张图」的空间视图与列表脱节；联调 Task 1 写入的站号只要不是 1/2/3，看起来像没告警。
- **修复：** 站点集合改为「mock 站点 ∪ 当前告警里出现的 stationId」；没有经纬度的用占位卡片，不要丢点。

#### P2-5 工具栏下拉改筛选不会自动刷新

- **位置：** `web/src/pages/alarm/AlarmMap.vue:23-30`、`182-185`
- **问题：** 图例芯片会 `toggleLevel` → `loadAlarms()`；`el-select` 只改 `levelFilter`/`statusFilter`，必须再点「刷新」。
- **影响：** 下拉已显示「红色」，列表仍是上一次结果，筛选状态和数据不一致。
- **修复：** `watch([levelFilter, statusFilter], loadAlarms)`，或 `@change` 里拉数。

---

### P3 — 低影响 / 疑问确认（🔵）

#### P3-1 开发记录未登记自验证文档 commit

- **位置：** `snapshots/role-a/dev-record-a.md` Commit 表
- **问题：** 表里只有 `33fcacf`，没有 `00c0bd8`。Task 1 二次审查 P3-R2 已要求过补齐。
- **修复：** 补一行 `00c0bd8 docs(task-2): 补齐自验证快照...`。

#### P3-2 Task 1 的 `review-reply-a.md` 会随本 PR 残留

- **位置：** 本分支未改 `snapshots/role-a/review-reply-a.md`
- **问题：** 合入后 `progress.md` 是 Task 2，回复文档仍是 Task 1 的 P1/P2 对照表。
- **修复：** 本 Task 可新建空的回复占位，或在合入说明里注明快照以 progress/dev-record 为准。

#### P3-3 缺 `status` 非法值单测；ack 的 id 断言过宽

- **位置：** `tests/test_alarm_routes.py:91-100`
- **问题：** 有 `level=9 → 40001`，没有 `status=9`。`test_alarm_ack_validates_id` 仍按计划写成 `40002 or 40001`，实现已固定为 40001。
- **修复：** 补非法 status；ack id 断言收成 `== 40001`。

#### P3-4 FastAPI 类型错误仍是 HTTP 422，不是 40001

- **位置：** `list_alarms(level: int = None, status: int = None)`，`ack_alarm(body: dict)`
- **问题：** `level=abc` 或 body 不是对象时走框架 422，与统一错误码表不完全一致。`main.py` 的全局 handler 只管未捕获 Exception，压不住 `RequestValidationError`。
- **修复：** 可记 follow-up（全站共性）；本 Task 若要自洽，可对 query 自己解析并 `fail(40001)`。

#### P3-5 列表响应形状与 api-guide 不完全一致（计划内偏差）

- **对照：** 计划 snippet 返回 `ok(rows)` 数组；api-guide 是 `{total, alarms[]}`，并含 `stationName`/`typeName`/`page`。
- **判断：** 这是**跟计划走、没跟 api-guide 走**。功能开发文档表格也写的是 `alarm[]`。不按 P1 开，但 Task 5 / 前端其它页如果按 api-guide 接 `data.alarms` 会接空。
- **请开发窗口确认：** 本 Task 是否锁定「数组」作为 4.1 列表契约，并在 api-guide 里改掉分页包装。

---

## 五、计划对齐与范围

| 计划项 | 结果 |
|---|---|
| `GET /api/alarm/list`、`POST /api/alarm/ack` | 已实现 |
| 不写 Kafka 消费者、不写 `/forecast/list` | 遵守；有 `test_alarm_router_has_no_forecast` |
| 不 import `alarm_engine` | 遵守 |
| 独占 5 文件 | 遵守；另改了角色 A 快照（合理） |
| 计划夹具 `test_alarm_list` / `test_alarm_ack_validates_id` | 已落地，并多了 status=0、非法 level、缺 operator、404、成功路径 |
| 前端 `alarm.api.ts` + AlarmMap + AlarmCard 分级着色 | 已落地 |
| `test_scaffold.py::test_all_seven_module_routers_exist` | 本分支填充路由后会失败；索引要求在 **main 单独 chore** 放宽，本分支不改 — 接受，但合入后 main 的 F0 空桩测试会红，需另开 chore |

相对计划 snippet 的**合理增强**（保留）：`title` 字段、camelCase 映射、`operator`/`ack_at`、level/status 枚举校验。这些不是问题。

---

## 六、测试与残留风险

- 路由单测 **8 passed**（审查窗口在 `D:\YY-task2` 当场执行）。全部通过 mock `SessionLocal`，没有打到真实 `biz_alarm`。
- 前端无组件/页面测试；P1-1、P2-1、P2-2 都在 catch 路径上，当前测试网扫不到。
- `StationMap` 仍是灰色占位，点选靠自绘卡片，GIS 不在本 Task 范围。
- 合入后 `tests/test_scaffold.py` 的「七个路由必须为空桩」会失败，需要 main 上单独放宽，不要 8 条功能分支一起改。

---

## 七、审查结论

❌ **需要修改后再审**

必须处理 P1-1、P1-2。建议同期处理 P2-1～P2-4（尤其不要把接口失败显示成真预警）。修复后请更新 `review-reply-a.md` 与 `progress.md`（阶段改为「修复完成，待二次审查」），再交审查窗口复审。
