# Task-6 开发记录（角色A）

**PR / Task：** Dev-2 Task 6 工单状态机与智能派单  
**分支：** `dev-2/feature/task6-workorder`  
**需求：** `docs/superpowers/plans/Dev-2-task6-workorder.md`

## 测试用例

| 用例 | 行为 |
|---|---|
| `test_create_and_get` | 由预警创建工单，返回 id>0，查询 status≥0 |
| `test_create_writes_repair_and_pending` | INSERT 写 `order_type=repair`、`status=0` |
| `test_get_order_missing_returns_empty` | 不存在的工单返回 `{}` |
| `test_workorder_create_validates` | `alarmId=0` 或空 assignee → 40001 |
| `test_workorder_get_not_found` | GET 不存在 → 40002 |
| `test_workorder_create_and_get_via_api` | POST 成功返回 orderId，GET 返回 status/alarm_id/assignee |

## 实现进度

- `create_from_alarm`：参数化 INSERT，`order_type='repair'`，`status=0`
- `get_order`：按 `order_id` 查询，无行返回 `{}`
- `POST /api/workorder/create`、`GET /api/workorder/{order_id}`；无巡检路由，不 import 预警服务

## Commit

| hash | message |
|---|---|
| `44dbeb4` | `feat(9.x): 工单状态机与智能派单` |

## 问题与处理

- 计划中的 `test_create_and_get` 会打真实 MySQL；与 Task 1 一致，用 `_FakeSession` 注入，避免本机无库时无法红绿。
- `tests/test_scaffold.py` 空桩断言会在填充路由后失败。索引文档要求在 main 上单独 chore，本分支不改该文件。
