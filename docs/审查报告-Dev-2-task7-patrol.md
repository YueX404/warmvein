# Dev-2 Task 7 代码审查报告

> **审查日期：** 2026-09-01  
> **审查轮次：** 第 1 轮  
> **审查角色：** 审查窗口（只读，未改实现、未提交）  
> **分支：** `dev-2/feature/task7-patrol`（worktree：`D:\YY\.worktrees\dev-2-feature-task7-patrol`；主仓库 `D:\YY` 仍在 `master`）  
> **对照基线：** `master`（`d084b59` → `6ada516`）  
> **需求 / 计划：** `docs/superpowers/plans/Dev-2-task7-patrol.md`  
> **冻结契约：** `docs/功能开发文档.md` §3、`docs/api-guide.md` §9  
> **审查对象：** `src/python/services/patrol.py`、`src/python/routes_workorder.py`、`tests/test_patrol.py`、`web/src/pages/workorder/WorkOrder.vue`、`web/src/pages/workorder/Patrol.vue`、`web/src/services/workorder.api.ts`、`web/src/mock/workorder.mock.ts`，以及角色 A 快照  
> **交叉核对：** `config/mysql/heat_init.sql`（`biz_patrol`）、`docs/database-schema.md`、Task 6 已合入的 create/get、F0 冻结边界、`web/src/router/index.ts`

---

## 一、总体结论

**可以合入，无阻断项。建议先处理 2 条 P2。**

计划要求的独占文件均已落地：`generate_plan` 写入 `biz_patrol`；`POST /api/patrol/plan/generate` 返回 `{patrolId}`；Task 6 的 create/get 保留且行为未改；巡检作为 `WorkOrder.vue` 的 Tab，**未改** `router/index.ts`。入参校验（类型/枚举/长度/日期格式）明显强于计划 snippet 的 truthy 判断，并有对应单测。

审查窗口在 worktree 当场执行：

- `pytest tests/test_patrol.py tests/test_workorder.py tests/test_scaffold.py -v` → **31 passed**
- `npx vue-tsc --noEmit`（`web/`）→ **通过**

合入前仍建议改：DEV 写路径在 500/断网时的假成功，以及校验失败文案永远说「缺少字段」。这两条不构成进程级阻断，但联调时会误导操作员。

**合入建议：无 P0/P1。P2 建议在合入前改完；P3 / 疑问可记 follow-up。**

---

## 二、审查范围与提交

| 项 | 内容 |
|---|---|
| 相对 `master` 的提交 | `7bccff1` `feat(9.x): 巡检计划生成与工单页面` |
| | `6ada516` `docs(task-7): 补齐自验证快照，阶段标记为待审查` |
| 新增 | `src/python/services/patrol.py`（24 行） |
| | `tests/test_patrol.py`（180 行） |
| | `web/src/pages/workorder/Patrol.vue`（221 行） |
| | `web/src/services/workorder.api.ts`（45 行） |
| 修改 | `src/python/routes_workorder.py`（仅追加巡检解析与路由；create/get 逻辑与 master 一致） |
| | `web/src/pages/workorder/WorkOrder.vue`、`web/src/mock/workorder.mock.ts` |
| | `snapshots/role-a/dev-record-a.md`、`progress.md` |
| 未改动（符合 F0 / 文件所有权） | `main.py`、`db.py`、`response.py`、`config/mysql/heat_init.sql`、`web/src/router/index.ts`、`services/workorder.py`、`tests/test_scaffold.py`、`tests/test_workorder.py` |
| 阶段快照 | `开发完成，待审查`（与审查前置一致） |
| 远程 | 本地分支，无 `origin/dev-2/feature/task7-patrol`；未对主仓库 `git checkout` / `git pull` 该分支 |

`routes_workorder.py` 相对 master 只多了 `patrol` import 和文件末尾的校验/路由，create/get 及 `_to_api` 与已合入 Task 6 一致。

---

## 三、做得好的地方

- 改动落在 Task 7 独占范围内：新建 `patrol.py` / `test_patrol.py` / 工单前端；`routes_workorder.py` 只追加，没有改 Task 6 的 create/get 行为，也没有改 `workorder.py`。
- F0 冻结守住：未改 `main.py`、`heat_init.sql`、`router/index.ts`、`db.py`。`Patrol.vue` 仅被 `WorkOrder.vue` 引用。
- SQL 使用绑定参数，INSERT 列与 `biz_patrol` 对齐：`station_id` / `plan_name` / `patrol_type` / `assignee` / `plan_date` / `status=0` / `created_at` / `updated_at`。可空列 `route_points` 未硬填，不会撞表结构。
- 入参校验对齐 Task 2/6 的教训：`type(stationId) is not int` 拒绝 `True` 和字符串；`patrolType` 白名单；`assignee` strip 后非空且 ≤32；`planDate` 必须 `YYYY-MM-DD`；`planName` ≤64。`lastrowid` 为空时不 commit，避免 `code=0` 却返回 0。
- 成功响应是 camelCase `patrolId`，并有断言禁止 `plan_id`。前端 `workorder.api.ts` 同时覆盖工单 create/get 与巡检生成，字段与 Task 6 二次审查后的 GET 契约（`orderId` / `trace` / `statusName`）一致。
- 计划指定的失败测试（空 body → 40001、`generate_plan` 返回 id>0）已落地，并补了类型/枚举/空白/超长/日期。Task 6 的 13 条工单测试未破。
- 异常走全局处理器，客户端只看到 `50001 服务内部错误`，不泄漏栈。
- 快照写明了 FakeSession 取舍、扁平契约 vs api-guide 的差异，没有假装联调已通。

---

## 四、问题清单

优先级：

- **P0**：合入即生产级阻断（本次无）
- **P1 / 🔴**：必须在合入前修复（本次无）
- **P2 / 🟡**：应修，否则联调会踩坑
- **P3 / 🔵**：低影响，或需要确认是否为计划有意切片

### 🔴 阻断性问题（必须修改）

无。

### 🟡 改进建议

#### P2-1 DEV 写路径在 500/断网时仍提示成功

- **位置：** `web/src/pages/workorder/Patrol.vue:120-132`，`web/src/pages/workorder/WorkOrder.vue:137-144`
- **问题：** `catch` 里若 `import.meta.env.DEV && isWorkorderBackendUnreachable(err)`，则本地 `mockGeneratePatrol` / `mockCreateOrder`，再 `ElMessage.success("已本地生成（Mock）")`。`isWorkorderBackendUnreachable` 把 **无 response** 和 **HTTP ≥500** 都当成不可达。
  - `api.ts` 拦截器对网络/500 已经 `ElMessage.error`，这里再弹 success，用户先看到失败再看到成功。
  - `generate_plan` 抛 `RuntimeError`（无 lastrowid）或 MySQL 失败时，全局处理器返回 **HTTP 500 / 50001**，DEV 下会被当成「后端未就绪」并假写入。
  - 40001（HTTP 200 + `code≠0`）不会走这条：拦截器 `reject(new Error(...))` 不是 AxiosError。这条比 Task 2 首轮 P1 收敛，但仍是写操作假成功。
- **对照：** Task 2 二次审查要求写路径失败即失败；Task 8 启动失败不假成功，审查时作为优点写下。列表/预览用 Mock 可以，开单/生成计划不行。
- **修复：** 写操作（`onCreate` / `onGenerate`）失败只保留拦截器错误提示，不要 mock 成功。左侧「示例工单 / 示例班表」点选预览可以继续用 Mock。

#### P2-2 校验失败文案永远是「缺少字段」

- **位置：** `src/python/routes_workorder.py:123-128`
- **问题：** `_parse_patrol` 失败原因包括：`stationId` 非正整数、`patrolType` 不在枚举、`assignee` 空白/超长、`planDate` 格式错、`planName` 非字符串/超长。返回却一律：

  `缺少 stationId/patrolType/assignee/planDate`

  工单创建同文件已用「参数校验失败」（与错误码表一致）。前端拦截器会把 `message` 直接 `ElMessage.error` 给用户。
- **影响：** 四个字段都填了只是日期写成 `09-02` 时，界面仍说「缺少 …」，排障成本高。
- **修复：** 与 `api_create` 对齐改为「参数校验失败」；或按失败项给短文案（非法 stationId / 非法巡检类型 / 日期格式等）。

#### P2-3 校验单测未覆盖已实现的 planName / stationId≤0

- **位置：** `tests/test_patrol.py`
- **问题：** 已有空 body、错误类型、bool/字符串 stationId、空白/超长 assignee、坏日期。没有：
  - `stationId: 0` / 负数
  - `planName` 长度 >64、非字符串
- **影响：** 这几条校验现在没有回归网，以后改 `_parse_patrol` 容易 silently 放宽。
- **修复：** 各补 1～2 条路由测试即可。

### 🔵 疑问确认

#### P3-1 请求/响应形态与冻结文档、api-guide 不一致

- **位置：** `routes_workorder.py:123-128`，`Patrol.vue:103-109` vs `docs/功能开发文档.md` §3、`docs/api-guide.md` §9.1
- **内容：** 子计划 snippet 是扁平 `stationId/patrolType/assignee/planDate`，成功体 `{patrolId}`。实现与测试按此冻结。功能开发文档是入参 `{rule}`、出参 `{planId}`；api-guide 还有嵌套 `rule.checkPoints` 和响应 `estimatedDuration`。
- **疑问：** 开发记录已写「按子计划，非 api-guide」。请在回复里确认后续联调以子计划为准，避免角色 B 按 api-guide 包一层 `rule` 或读 `planId` 读空。

#### P3-2 未生成巡检路线，也未按预警/季节出计划

- **位置：** `services/patrol.py` vs `docs/开发任务拆分-角色A-平台与智能底座.md`（「基于预警/季节生成巡检计划与路线」）、表字段 `route_points`
- **疑问：** 当前是用户填站、类型、人、日期后 INSERT，`route_points` 为 NULL。这是子计划有意切片，还是漏做？若是切片，请写明后续 Task 承接。

#### P3-3 进度快照 HEAD 与 Commit 表落后一笔

- **位置：** `snapshots/role-a/progress.md`、`dev-record-a.md`
- **内容：** 进度写 HEAD `7bccff1`；实际分支 HEAD 是 `6ada516` `docs(task-7): 补齐自验证快照…`。Commit 表只有第一笔。二次审查或回复时补一行即可。

#### P3-4 FakeSession 不能证明真 MySQL 的 `lastrowid`

- **位置：** `services/patrol.py:20-24`，`tests/test_patrol.py` 的 `_FakeSession`
- **内容：** 与 Task 6 相同折中。实现已对空 id 拒绝 commit，方向正确，但仍不证明 SQLAlchemy 2.0 + MySQL 驱动返回的 `CursorResult.lastrowid` 可用。合入后需要一次真实 INSERT 冒烟。

#### P3-5 类型与样式重复

- **位置：** `workorder.api.ts` 与 `workorder.mock.ts` 各定义一份 `WorkOrderRow` / `WorkOrderTrace`；`WorkOrder.vue` 里有一套 `.dot[data-type]` 样式，父页工单列表用不到。
- **内容：** 不影响行为。可后续抽共享类型、删死样式。

---

## 五、审查维度核对

| 维度 | 结论 |
|---|---|
| 功能正确性 | 子计划 API + 工单 Tab 已落地；相对冻结文档是扁平 `{patrolId}`（见 P3-1）；路线/季节生成未做（见 P3-2） |
| 测试质量 | 13 条 patrol + 13 条 workorder + 5 条 scaffold 当场全绿；FakeSession 不碰真库；planName/stationId≤0 缺测 |
| 代码质量 | 函数未超 50 行；分层清晰；SQL 参数化；无新依赖；无 `print` / `console.log` / `TODO` / `pdb` |
| 范围控制 | 合格。未改 F0 冻结文件，未改 `workorder.py` / `test_workorder.py` / `heat_init.sql` / 路由表 |
| 文档同步 | 阶段正确（开发完成，待审查）；HEAD/Commit 表少一笔 docs 提交 |
| 潜在风险 | 无密钥硬编码；DEV 写路径假成功；超长 planName 已被挡，不会撞 `VARCHAR(64)` 变 50001 |

---

## 六、与计划步骤对照

| 计划步骤 | 结果 |
|---|---|
| Step 1 基线已有 create/get | 是，master 上 Task 6 已合入 |
| Step 2–3 失败测试 | 已有 `test_generate_plan_returns_id`、`test_patrol_generate_validates` |
| Step 4 `generate_plan` 写 `biz_patrol` | 已落地，并增加 lastrowid 守卫 |
| Step 5 追加 `POST /patrol/plan/generate` | 已落地，校验强于 snippet |
| Step 6 路由测试且不破坏 workorder | 13+13 当场通过 |
| Step 7 前端 api + WorkOrder Tab，不改 router | 已落地；可选 `Patrol.vue` 仅被 WorkOrder 引用 |
| Step 8 commit `feat(9.x): 巡检计划生成与工单页面` | `7bccff1` |

相对 snippet 的合理增强（保留）：bool/字符串 stationId 拒绝、日期格式、planName 长度、lastrowid 空则不 commit、工单页完整开单/查单/流转。

---

## 七、测试与残留风险

- 审查窗口在 worktree 当场：`31 passed`；`vue-tsc --noEmit` 通过。
- 全部服务测试走 FakeSession，**不证明** 真库 INSERT / `lastrowid`。
- 前端无组件测试；写路径 Mock、校验文案只能靠代码阅读确认。
- 未起 FastAPI/MySQL，也未用浏览器点 `/workorder`。
- `test_scaffold.py` 在本分支已绿（master 已 chore 放宽空桩断言）。
- 分支尚未 push 到 origin。

---

## 八、审查结论

✅ **通过（无阻断项）**

没有必须拦合入的 P0/P1。建议开发窗口在合入前处理：

1. 🟡 P2-1 去掉开单/生成计划的写路径假成功
2. 🟡 P2-2 校验失败文案改为「参数校验失败」或按原因区分
3. 🟡 P2-3 补 `stationId<=0` 与 `planName` 校验测试（可与 P2-2 一起做）

🔵 五项在 `snapshots/role-a/review-reply-a.md` 说明采纳或保留即可。

处理完成后请更新 `review-reply-a.md` 与 `progress.md`。若改了 P2，阶段改为「修复完成，待二次审查」再交复审；若只回复不改代码，可保持待合入。
