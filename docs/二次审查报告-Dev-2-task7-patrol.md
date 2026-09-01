# Dev-2 Task 7 二次审查报告

> **审查日期：** 2026-09-01  
> **审查轮次：** 第 2 轮（对照首轮报告与修复提交）  
> **审查角色：** 审查窗口（只读，未改实现、未提交）  
> **分支：** `dev-2/feature/task7-patrol`（worktree：`D:\YY\.worktrees\dev-2-feature-task7-patrol`，HEAD `84eef37`）  
> **对照基线：** `master` `d084b59` → 当前 HEAD `84eef37`  
> **首轮审查 HEAD：** `6ada516`  
> **本轮修复提交：** `1a0103b`；文档 `4778db8` `84eef37`  
> **首轮报告：** `docs/审查报告-Dev-2-task7-patrol.md`  
> **作者回复：** `snapshots/role-a/review-reply-a.md`  
> **阶段快照：** `修复完成，待二次审查`

---

## 一、总体结论

**首轮无 P1。P2 均已落地，P3 已按回复修复或书面锁定。建议合入。**

相对首轮「可以合入，建议先处理 P2」，本轮已经去掉开单/生成计划的写路径假成功，校验失败按字段返回短文案，并补上 `stationId<=0` 与 `planName` 路由测试。`mockCreateOrder` / `mockGeneratePatrol` 已删除。

当场验证：`pytest tests/test_patrol.py tests/test_workorder.py tests/test_scaffold.py -v` → **35 passed**。

本轮没有新的 P1/P2。P3 可记 follow-up，不阻塞合入。P3-1（扁平 `{patrolId}`）、P3-2（手工建计划、不写路线）、P3-4（FakeSession）、P3-5（类型/样式重复）按回复接受。

---

## 二、首轮问题关闭表

| ID | 首轮结论 | 本轮状态 | 证据 |
|---|---|---|---|
| P2-1 | DEV 写路径 500/断网仍 `success` 并写入 Mock | **已关闭** | `Patrol.vue:120-123`、`WorkOrder.vue:137-140`：`catch` 只注释拦截器已提示。`workorder.mock.ts` 已删 `mockCreateOrder` / `mockGeneratePatrol`。仓库内无「已本地开单/生成」文案 |
| P2-2 | 校验失败一律「缺少字段」 | **已关闭** | `_parse_patrol` 返回 `(parsed, err)`；`stationId 非法` / `patrolType 非法` / `assignee 非法` / `planDate 非法` / `planName 非法`。空 body 与坏日期单测断言了文案 |
| P2-3 | 缺 `stationId<=0`、`planName` 超长/非字符串测试 | **已关闭** | `test_patrol_generate_rejects_zero_station`、`_negative_station`、`_long_plan_name`、`_non_string_plan_name` |
| P3-1 | 扁平 `{patrolId}` vs 文档 `{rule}`/`{planId}` | **接受** | 回复锁定跟子计划走；不包 `rule`，不返回 `planId` / `checkPoints` / `estimatedDuration`。后续改 api-guide |
| P3-2 | 未写 `route_points`、无预警/季节路线 | **接受** | 本 Task 只做手工建计划；路线留给后续 Task |
| P3-3 | 进度 HEAD / Commit 表缺 `6ada516` | **已关闭** | Commit 表已有 `6ada516`、`1a0103b`。后续文档 commit 见 P3-R1 |
| P3-4 | FakeSession 不证明真 MySQL `lastrowid` | **接受** | 合入后真实 INSERT 冒烟 |
| P3-5 | 类型与 `.dot` 样式重复 | **接受** | 不影响行为，本轮不抽共享 |

---

## 三、本轮新问题

### P3 — 可记 follow-up，不阻塞合入

#### P3-R1 开发记录未登记本轮文档 commit

- **位置：** `snapshots/role-a/dev-record-a.md` Commit 表
- **问题：** 有 `1a0103b`，没有 `4778db8 docs(task-7): 审查回复…`、`84eef37 docs(task-7): 补登记审查修复 commit hash`。无功能影响。

#### P3-R2 空 body 文案是「stationId 非法」

- **位置：** `routes_workorder.py:90-93`，`test_patrol_generate_validates`
- **问题：** 缺字段按检查顺序失败，空 `{}` 得到 `stationId 非法`，不是「缺少」。与「按失败项短文案」一致，比首轮「缺少四个字段」清楚。可接受，不必再改。

#### P3-R3 查单 GET 在 DEV 断网时仍走 Mock

- **位置：** `WorkOrder.vue:154-158`
- **问题：** 写路径已不再假成功；查单仍 `isWorkorderBackendUnreachable` 时 `findOrder`。回复明确保留为只读预览。与 Task 2 二次审查「列表失败 Mock 仅限 DEV 且后端不可达」同类，**接受**。

---

## 四、修复质量（本轮）

- 写失败即失败：拦截器 `ElMessage.error` 后页面不再弹 success，也不把本地夹具写成「已生成」。点选示例工单/班表仍可预览。
- `_parse_patrol` 仍用 `type(station_id) is not int`，bool / 字符串 / 0 / 负数都会 40001。
- 补测覆盖了首轮点名的边界；空 body、坏日期、0 号站、超长 planName 还断言了 `message`。
- 范围仍在巡检/工单前端 + `routes_workorder.py` 追加段 + 角色 A 快照。未改 `workorder.py`、`heat_init.sql`、`main.py`、`router/index.ts`。

---

## 五、残留风险（与首轮相同，非本轮引入）

- HTTP 成功路径仍 patch `SessionLocal`，不打真实 `biz_patrol`。
- 前端无组件测试；写路径不假成功只能靠代码阅读确认。
- 审查窗口未起 FastAPI/MySQL，也未用浏览器点 `/workorder`。
- 分支尚未 push 到 origin。

---

## 六、审查结论

✅ **通过，建议合入**

首轮 P2 已关闭，本轮无新阻断项。可将 `snapshots/role-a/progress.md` 标为审查通过，进入收尾（push / 提 PR / 合并）。P3-R1 补 Commit 表一行即可，不挡合入。
