# Task-8 审查反馈处理记录

审查来源：`docs/审查报告-Dev-2-task8-plan.md`  
处理分支：`dev-2/feature/task8-plan`  
处理时间：2026-09-01

## 🔴 阻断性问题

无。

## 🟡 改进建议

| 编号 | 处理 | 说明 |
|---|---|---|
| P2-1 | 修复 | `activate` 改为 `WHERE plan_id=:p AND status=1`。停用视为不存在，路由仍返回 40002。新增 `test_activate_rejects_disabled_plan`。 |
| P2-2 | 修复 | 路由层校验：`alarmType` 非空字符串且 ≤32；`level` 缺省 2，必须是 1–4 的 int（排除 bool）；`planId` 正整数；`operator` 去空白且 ≤32。非法一律 40001。 |
| P2-3 | 修复 | `_TYPE_MAP` 增加 `theft→third_party`，并显式写入 `freeze`/`burst`/`third_party` 自身映射。 |
| P2-4 | 修复 | 目录标注「Mock，非库内数据」；点选仅预览步骤，启动按钮禁用。新增手工种子 `config/mysql/plan_seed.sql`（未改 `heat_init.sql`）。第三方破坏种子级别改为 2，与 Task 1 `steal` 默认级对齐。 |
| P2-5 | 修复 | 补 `POST /api/plan/match`、`POST /api/plan/activate` 成功路径。FakeSession 对 `biz_plan` / `biz_plan_execution` 表名和列名、以及存在性查询的 `status=1` 做断言。 |

## 🔵 疑问确认

| 编号 | 结论 |
|---|---|
| P3-1 | **锁定跟计划走**：响应为 snake_case 单对象（`ok(plan.match(...))`）。不在本 Task 改成 api-guide 的 `{plans:[{planId}]}`。后续改 api-guide 对齐本契约。 |
| P3-2 | **保持精确匹配**（同级或 `alarm_level IS NULL`）。与计划 SQL 一致。级别覆盖靠种子数据（冻堵 L4、爆管 L4、停暖 L2、第三方 L2），不做「≥ 该级别」。 |
| P3-3 | **接受管理页不传 alarmId**。已加 `ElMessageBox.confirm`。重复启动仍会写多条执行单（有意：一次启动一条记录）。 |
| P3-4 | 修复：`onActivate` 增加 `catch`，避免 unhandled rejection。 |
| P3-5 | 修复：Commit 表补 `8ea5e67` 及后续审查修复提交。 |
| P3-6 | 保留。非对象 body 走 FastAPI 422 是全站共性，不在本 Task 单独包一层。 |

## 验证

- `pytest tests/test_plan.py -v` → 19 passed
- `npx vue-tsc --noEmit`（`web/`）→ exit 0

审查修复提交：`5ecbb75`、`1df300a`。文档提交：`c0e5191`。

## 二次审查（2026-09-01）

来源：`docs/二次审查报告-Dev-2-task8-plan.md`。结论：通过，建议合入。首轮 P2 全部关闭。

| 编号 | 处理 | 说明 |
|---|---|---|
| P3-R1 | 修复 | Commit 表补 `c0e5191`。 |
| P3-R2 | 修复 | `plan_seed.sql` 改为按 `plan_type` `WHERE NOT EXISTS`，可重复执行。仍不并入 `heat_init.sql`。 |
| P3-R3 | 修复 | 启动人输入框 `maxlength="32"`。 |
