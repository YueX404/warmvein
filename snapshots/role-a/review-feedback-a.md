# Task-6 Code Review 反馈

审查分支：`dev-2/feature/task6-workorder`  
审查 commit：`8e59df0`（相对 `master` `ccaa50c`：`44dbeb4` + `8e59df0`）  
审查时间：2026-09-01  
完整报告：`docs/审查报告-Dev-2-task6-workorder.md`

## 🔴 阻断性问题（必须修改）

1. 【`src/python/routes_workorder.py:16-19` / `services/workorder.py:16-22` / `tests/test_workorder.py:108-112`】GET 详情直接 dump 表字段（`order_id` / `alarm_id` / `created_at`，无 `trace`）。冻结契约是 `{status, trace}`，前端 mock 与 POST 已用 camelCase（`orderId`）。需在路由层映射，并改测试断言。

## 🟡 改进建议

1. 【`routes_workorder.py:9-13`】入参只做 truthy。应对齐 Task 2：`alarmId` 正整数，`assignee` strip 后非空且 ≤32，否则 40001。
2. 【`services/workorder.py:6-13`】创建不写 `biz_work_order_trace`。创建后插入 `action=create`，GET 查出 `trace`。
3. 【`tests/test_scaffold.py:35`】全量 pytest 会因空桩断言失败。在 **main 上 chore** 放宽，本分支不要改该文件。
4. 【`tests/test_workorder.py:82-85`】校验只覆盖 `alarmId=0` + 空 assignee；FakeSession 写死 `status=0`。拆开用例，断言 SQL 与 camelCase 字段。

## 🔵 疑问确认

1. 【计划 vs M3】标题是状态机与智能派单，实现只有 create/get。是否有意切片？请在回复里写明后续承接。
2. 【`workorder.py:18-20` vs api-guide §5.2】GET 是否本轮只保证 §3 最小集（`status` + `trace`），不返回 `orderType`/`title`/`priority`/`stationId`？
3. 【`snapshots/role-a/dev-record-a.md`】Commit 表缺 `8e59df0`。
4. 【`workorder.py:13`】`lastrowid` 未经真 MySQL 验证。

## 审查结论

❌ 需要修改后再审
