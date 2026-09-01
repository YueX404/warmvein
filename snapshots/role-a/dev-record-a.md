# Task-6 开发记录（角色A）

**PR / Task：** Dev-2 Task 6 工单状态机与智能派单  
**分支：** `dev-2/feature/task6-workorder`  
**需求：** `docs/superpowers/plans/Dev-2-task6-workorder.md`

## 测试用例

| 用例 | 行为 |
|---|---|
| `test_create_and_get` | 由预警创建工单，返回 id>0，查询 status≥0 |
| `test_create_writes_repair_and_pending` | INSERT SQL 含 `order_type=repair`、`status`、`,0,` |
| `test_get_order_missing_returns_empty` | 不存在的工单返回 `{}` |
| `test_workorder_create_validates` | `alarmId=0` 或空 assignee → 40001 |
| `test_workorder_get_not_found` | GET 不存在 → 40002 |
| `test_workorder_create_and_get_via_api` | POST 返回 orderId；GET 为 camelCase + statusName + trace |
| `test_create_writes_trace_row` | 创建后轨迹 `action=create`，`operator=系统` |
| `test_create_rejects_missing_alarm_id` | 缺 alarmId → 40001 |
| `test_create_rejects_missing_assignee` | 缺 assignee → 40001 |
| `test_create_rejects_non_int_alarm_id` | 字符串 alarmId → 40001 |
| `test_create_rejects_bool_alarm_id` | `true` → 40001 |
| `test_create_rejects_blank_assignee` | 空白 assignee → 40001 |
| `test_create_rejects_long_assignee` | 长度 >32 → 40001 |

## 实现进度

- `create_from_alarm`：参数化 INSERT，`order_type='repair'`，`status=0`；同事务写 `biz_work_order_trace`
- `get_order`：主表 + 轨迹；无行返回 `{}`
- 路由：POST 校验正整数 alarmId 与 strip 后 ≤32 的 assignee；GET 映射 camelCase
- 无巡检路由，不 import 预警服务

## Commit

| hash | message |
|---|---|
| `44dbeb4` | `feat(9.x): 工单状态机与智能派单` |
| `8e59df0` | `docs(task-6): 补齐自验证快照，阶段标记为待审查` |
| `76dbac4` | `fix(task-6): review反馈 - GET 详情改为 camelCase 并返回 trace` |
| `19bd4d7` | `fix(task-6): review反馈 - 入参校验与创建写轨迹` |

## 问题与处理

- 计划中的 `test_create_and_get` 会打真实 MySQL；与 Task 1 一致，用 `_FakeSession` 注入。
- `tests/test_scaffold.py` 空桩断言会在填充路由后失败。索引文档要求在 main 上单独 chore，本分支不改该文件。
- 审查 P1-1：GET 不再 dump 表字段；P2-1/2/4 已修；P2-3 留 main chore。
