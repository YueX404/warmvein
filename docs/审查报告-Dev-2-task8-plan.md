# Dev-2 Task 8 代码审查报告

> **审查日期：** 2026-09-01  
> **审查角色：** 审查窗口（只读，未改实现、未提交）  
> **分支：** `dev-2/feature/task8-plan`（worktree：`D:\YY\.worktrees\dev-2-feature-task8-plan`，当前 `D:\YY` 仍在 `master`）  
> **对照基线：** `master`（`ccaa50c` → `8ea5e67`）  
> **需求 / 计划：** `docs/superpowers/plans/Dev-2-task8-plan.md`  
> **审查对象：** `src/python/services/plan.py`、`src/python/routes_plan.py`、`tests/test_plan.py`、`web/src/pages/plan/PlanManage.vue`、`web/src/services/plan.api.ts`、`web/src/mock/plan.mock.ts`，以及角色 A 快照  
> **交叉核对：** `config/mysql/heat_init.sql`（`biz_plan` / `biz_plan_execution`）、`docs/database-schema.md`、`docs/api-guide.md` §6、`docs/功能开发文档.md`、F0 冻结边界、Task 1 预警词表（`frost`/`steal`/`theft`）

---

## 一、总体结论

**可以合入，建议先处理 P2。**

计划内 6 个独占文件均已落地，F0 冻结文件未动，未 import 预警服务，列名对齐 `biz_plan` / `biz_plan_execution`，也没有误用 `plan_code` / `activated`。类型映射 `frost→freeze`、`leak→burst`、`steal→third_party`、停暖 `shutdown` 都在。路由路径正确（`POST /api/plan/match`、`POST /api/plan/activate`）。

前端启动路径是失败即失败，没有 Task 2 那种「接口失败却提示成功」的写路径假成功。审查窗口当场执行 `pytest tests/test_plan.py -v` → **11 passed**。

合入前仍建议修：停用预案也能启动、入参几乎未校验、`theft` 词表缺口、左侧目录是 mock 而匹配打空库。这些不构成进程级阻断，但联调时会直接踩坑。

**合入建议：无 P0/P1。P2 建议在合入前改完；P3 / 疑问可记 follow-up。**

---

## 二、审查范围与提交

| 项 | 内容 |
|---|---|
| 相对 `master` 的提交 | `2db07a3` `feat(5.1): 预案匹配/启动与前端管理` |
| | `3d31721` `fix(task-8): 补齐停暖映射与启动 40002 测试` |
| | `8ea5e67` `docs(task-8): 补齐自验证快照，阶段标记为待审查` |
| 新增 | `src/python/services/plan.py`（+39） |
| | `tests/test_plan.py`（+150） |
| | `web/src/services/plan.api.ts`（+23） |
| 修改 | `src/python/routes_plan.py`（+19） |
| | `web/src/pages/plan/PlanManage.vue`（+338） |
| | `web/src/mock/plan.mock.ts`（+66） |
| | `snapshots/role-a/dev-record-a.md`、`snapshots/role-a/progress.md` |
| 未改动（符合 F0 冻结与独占） | `main.py`、`kafka_topics.py`、`response.py`、`db.py`、`config/settings.py`、`config/mysql/heat_init.sql`、`web/src/router/index.ts`、`web/src/components/*`、`tests/test_scaffold.py`、预警/工单/短信模块 |
| 阶段快照 | worktree `snapshots/role-a/progress.md` 为「开发完成，待审查」，允许审查 |
| 单测（审查当场） | `pytest tests/test_plan.py -v` → **11 passed** |

---

## 三、做得好的地方

- 改动落在 Task 8 独占文件内，没有触碰 F0 冻结文件，也没有 import `alarm_engine` / 预警路由。
- 路由按 F0 约定写完整路径 `@router.post("/plan/match")`，经 `main.py` 的 `/api` 前缀后正好是契约 URL。
- SQL 全部参数绑定；`SELECT` / `INSERT` 列名与 `heat_init.sql` 的 `biz_plan`、`biz_plan_execution` 一致；启动写 `status=0`（启动中），没用 `plan_code` / `activated`。
- `_TYPE_MAP` 覆盖计划要求的 frost/leak/steal/shutdown；`freeze`/`burst`/`third_party` 因 `.get(x, x)` 直通，api-guide 那套词也能匹配。
- `plan_id=0` 启动直接返回 0；库中无行返回 40002。前端无 `plan_id` 时启动按钮 disabled，接口失败不会再弹 success。
- `steps` 同时兼容 JSON 字符串和数组，按动作 / 责任主体 / 资源展开，符合「结构化节点」要求。
- 补提交 `3d31721` 把停暖映射和 40002 测补上了，比第一版完整。
- 开发记录写明了 FakeSession 原因、以及 `test_scaffold` 空桩冲突不在本分支改，和索引约定一致。

---

## 四、问题清单

优先级约定：

- **P0 / 🔴**：合入即导致生产级阻断（本次无）
- **P1 / 🔴**：必须在合入前修复（本次无）
- **P2 / 🟡**：应修复，否则联调或上线会踩坑
- **P3 / 🔵**：低影响，或需要开发窗口确认意图

### P1 — 必须修复（🔴）

无。

---

### P2 — 应修复（🟡）

#### P2-1 停用预案也能启动

- **位置：** `src/python/services/plan.py:29-33`
- **问题：** `activate` 只按 `plan_id` 查是否存在，不看 `status=1`。匹配侧已经过滤了 `status=1`，但只要拿得到 id（旧匹配结果、手工 POST、目录里抄编号），就能给停用预案写 `biz_plan_execution`。
- **影响：** 调度员可以启动已退役预案，执行单是真写入，不是前端展示问题。
- **修复：** `SELECT plan_id FROM biz_plan WHERE plan_id=:p AND status=1`。停用视为不存在（40002），或单独返回 40001「预案已停用」。

#### P2-2 外部入参几乎未做类型 / 范围 / 长度校验

- **位置：** `src/python/routes_plan.py:8-22`，`src/python/services/plan.py:14-39`
- **问题：** 项目规范要求外部输入做类型、长度、格式、合法性校验。当前只有「缺 alarmType / 缺 planId」：
  - `level` 不限制 1–4，非 int 原样进 SQL。
  - `alarmType` 非字符串（list/dict）会在 `_TYPE_MAP.get` 上 `TypeError` → 全局 50001，不是 40001。
  - `operator` 无长度限制，`biz_plan_execution.operator` 是 `VARCHAR(32)`，超长在 MySQL 严格模式会 `DataError` → 50001。
  - `planId` 不校验正整数。
- **影响：** 畸形请求打出 500 而不是 40001；超长启动人让一次合法启动变成内部错误。Task 2 已对 `operator` 做了 32 字符校验，这里应看齐。
- **修复：** `alarmType` 必须是非空字符串；`level` 缺省 2，且必须是 1–4 的 int；`planId` 必须是正整数；`operator` 去空白并截断/拒绝 >32。非法一律 `fail(40001, ...)`。

#### P2-3 词表没覆盖 Task 1 / schema 入库值 `theft`

- **位置：** `src/python/services/plan.py:5-11`
- **对照：** Task 1 `to_schema_type("steal") == "theft"`；`biz_alarm.type` 枚举含 `theft`。本模块只映射 `steal → third_party`。
- **问题：** 页面下拉发 `steal` 能命中。一旦按预警记录的 `type=theft` 来匹配（后续工单/预警页联调是大概率），会去查 `plan_type=theft`，四类预案里没有这个值，永远 `plan_id=None`。
- **修复：** `_TYPE_MAP` 增加 `"theft": "third_party"`。建议同时显式写入 `freeze`/`burst`/`third_party` 自身映射，避免只靠直通。

#### P2-4 左侧目录是 mock，匹配打真实 API；新库无种子时两边矛盾

- **位置：** `web/src/pages/plan/PlanManage.vue:38-44`、`:110`；`web/src/mock/plan.mock.ts:10-67`；`config/mysql/heat_init.sql:218-231`（无 INSERT）
- **问题：** 左侧四条预案来自 mock，不可点选，也没有「示例数据」标注。匹配/启动走 `/api/plan/*`。`heat_init.sql` 只建表不插预案（计划禁止改该文件）。结果是：目录里明明有「冻堵应急处置预案」，匹配 frost / L4 却得到「库中暂无对应启用预案」。
- **影响：** 联调或演示时会以为匹配逻辑坏了。计划允许测试里 INSERT 一条 `freeze`，但单测用 FakeSession 把这条路径绕开了。
- **修复：**
  1. 测试按计划对 FakeSession 以外补一条真实 SQL 夹具（或至少用可执行 SQL 断言列名/表名），不要只复刻 Python 过滤。
  2. 给运维一份手工 INSERT 四类预案的 SQL（独立文件或 dev-record），仍不要改 `heat_init.sql`。
  3. 前端目录要么标明 Mock，要么可点选后走匹配结果；不要让「看起来已有预案」和「匹配为空」同时出现。

#### P2-5 匹配 / 启动成功路径没有 HTTP 单测；FakeSession 复刻了 SQL 语义

- **位置：** `tests/test_plan.py:21-55`、`:134-150`
- **问题：** 路由测只覆盖 40001 / 40002（40002 还是直接 mock 掉 `plan.activate`）。没有 `POST /api/plan/match` 成功、没有 `POST /api/plan/activate` 成功。`_FakeSession` 自己实现了一遍 `plan_type + status + alarm_level` 过滤，SQL 写错表名/列名/条件也测不红。
- **影响：** 计划 Step 3 写的是测试里 INSERT 夹具，当前测试不证明语句能在 MySQL 上跑通。
- **修复：** 至少加：match 200 返回 `plan_type/plan_id`；activate 200 返回 `execId`。FakeSession 对 SQL 字符串做列名/表名断言，或改用内存库执行真实 `text()`。

---

### P3 — 低影响 / 疑问确认（🔵）

#### P3-1 响应形状跟 api-guide 不一致（跟计划走）

- **对照：** 计划 snippet 直接 `ok(plan.match(...))`，列名是 snake_case 单对象。api-guide §6.1 是 `{ plans: [{ planId, planType, alarmLevel, steps: 数组 }] }`。功能开发文档表格写的是 `{plan}`。
- **判断：** 这是跟计划走、没跟 api-guide 走。前端 `PlanRow` 已按 snake_case 对接，页内自洽。其它客户端若按 api-guide 读 `data.plans[0].planId` 会接空。
- **请开发窗口确认：** 本 Task 是否锁定「单对象 + 库列名」作为 5.1 契约，并在后续改 api-guide；还是要在路由层做成 camelCase / `plans[]`。

#### P3-2 级别是精确匹配，不是「≥ 该级别」

- **位置：** `src/python/services/plan.py:19-21`
- **问题：** `(alarm_level IS NULL OR alarm_level=:lv)`。库里只有冻堵 L4 时，frost/L2、L3 匹配为空。Task 1 里 `steal` 默认级别是 2，mock 里第三方破坏是 L3，对不上。
- **请确认：** 产品语义是「同级预案」还是「该级别及以上 / 最接近」？若是后者，条件要改，并补单测。

#### P3-3 启动不带 `alarmId`，也无二次确认

- **位置：** `web/src/pages/plan/PlanManage.vue:88-96`、`:173-184`
- **问题：** 页面没有预警 ID 输入，`activatePlan(planId, undefined, operator)`。危险按钮无 `ElMessageBox.confirm`。重复点击会写多条执行单（可能是有意的）。
- **请确认：** 管理页手工启动不关联预警是否接受；是否需要确认框。

#### P3-4 `onActivate` 无 `catch`，失败靠拦截器

- **位置：** `web/src/pages/plan/PlanManage.vue:173-184`
- **问题：** 失败时拦截器已 `ElMessage.error`，不会误报成功，但未捕获的 Promise 会在控制台抛 unhandled rejection。
- **修复：** 加空 `catch` 或 `catch { /* 拦截器已提示 */ }`。

#### P3-5 开发记录未登记自验证文档 commit

- **位置：** `snapshots/role-a/dev-record-a.md` Commit 表
- **问题：** 表里只有 `2db07a3`、`3d31721`，没有 `8ea5e67 docs(task-8): 补齐自验证快照...`。Task 1/2 审查已要求过补齐。
- **修复：** 补一行。

#### P3-6 FastAPI 非对象 body 仍是 HTTP 422

- **位置：** `api_match(body: dict)` / `api_activate(body: dict)`
- **问题：** body 不是对象时走框架 422，与统一错误码表不完全一致。全站共性，可记 follow-up。

---

## 五、计划对齐与范围

| 计划项 | 结果 |
|---|---|
| `plan.match` / `plan.activate` | 已实现 |
| `POST /api/plan/match`、`POST /api/plan/activate` | 已实现 |
| 映射 frost→freeze、leak→burst、停暖→shutdown、steal→third_party | 已实现；缺 schema 侧 `theft` |
| 不 import 预警服务；列名以 F0 表为准 | 遵守 |
| 独占 6 文件 | 遵守；另改了角色 A 快照（合理） |
| 计划夹具 `test_match_frost_high` / `test_activate_requires_existing` / 路由 40001 | 已落地，并多了 leak/steal/shutdown/空匹配/缺失预案/40002 |
| 前端 match/activate + steps JSON 展示 | 已落地 |
| 测试里 INSERT freeze 夹具 | **未做**，改用 FakeSession |
| `test_scaffold.py::test_all_seven_module_routers_exist` | 本分支填充路由后会失败（审查当场已确认）；索引要求在 **main 单独 chore** 放宽 — 接受 |

相对计划 snippet 的合理增强（保留）：前端匹配台布局、四类 mock 步骤、`parseSteps`、启动人输入、执行单号回显。

---

## 六、测试与残留风险

- 服务/路由单测 **11 passed**（审查窗口在 worktree 当场执行）。全部通过 FakeSession / mock `activate`，没有打到真实 `biz_plan`。
- 前端无组件测试；匹配失败清空结果、启动失败不假成功，这两条只能靠代码阅读确认。
- 审查窗口未起 FastAPI/MySQL，也未再走浏览器。开发记录写了 `/plan` 在后端未就绪时走失败路径。
- 合入后 `tests/test_scaffold.py` 的「七个路由必须为空桩」会失败，需要 main 上单独放宽，不要 8 条功能分支一起改。
- 新库无预案行时，匹配恒为 `plan_id=None`，启动只能 40002。这是数据问题，不是匹配函数崩溃，但演示闭环过不去。

---

## 七、审查结论

✅ **通过（无阻断项）**

没有必须拦合入的 P0/P1。建议开发窗口在合入前处理 P2-1～P2-4（启用状态、入参校验、`theft` 映射、目录/种子脱节），P2-5 和 P3 可与回复一并说明。

处理完成后请更新 `snapshots/role-a/review-reply-a.md` 与 `progress.md`。若只回复不改代码，阶段可保持待合入；若改了 P2，阶段改为「修复完成，待二次审查」再交复审。
