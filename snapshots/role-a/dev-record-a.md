# Task-2 开发记录（角色A）

**PR / Task：** Dev-2 Task 2 预警列表/确认 API 与前端预警一张图  
**分支：** `dev-2/feature/task2-alarm-map`  
**需求：** `docs/superpowers/plans/Dev-2-task2-alarm-map.md`  
**工作区：** `D:\YY-task2`（worktree，未切换 `D:\YY` 的 master）

## 测试用例

| 用例 | 行为 |
|---|---|
| `test_alarm_list` | `GET /api/alarm/list?level=3` → `code=0`，camelCase 字段，SQL 带 level |
| `test_alarm_list_filters_status` | `status=0` 作为合法过滤条件传入（避免把 0 当 falsy 丢掉） |
| `test_alarm_list_rejects_invalid_level` | `level=9` → `40001` |
| `test_alarm_ack_validates_id` | `alarmId=0` → `40001` |
| `test_alarm_ack_requires_operator` | 缺 operator → `40001` |
| `test_alarm_ack_not_found` | `rowcount=0` → `40002` |
| `test_alarm_ack_success` | 更新 status/operator 并 `code=0` |
| `test_alarm_router_has_no_forecast` | 本 Task 不挂 `/forecast` |

## 实现进度

- `GET /api/alarm/list`：查 `biz_alarm`，参数化过滤，不 import `alarm_engine`
- `POST /api/alarm/ack`：校验 alarmId/operator，写入 `status=1`、`operator`、`ack_at`
- 前端 `alarm.api.ts` + `AlarmMap.vue`（AlarmCard 分级着色）+ mock 回落

## Commit

| hash | message |
|---|---|
| `33fcacf` | `feat(4.1): 预警列表/确认 API 与预警一张图` |

## 问题与处理

- `tests/test_scaffold.py::test_all_seven_module_routers_exist` 会因本 Task 填充路由失败。索引要求在 **main 单独 chore** 放宽，本分支不改该文件。
- 列表/确认单测 mock `SessionLocal`，不依赖真实 MySQL。
- 前端无独立单测；`vue-tsc && vite build` 作为类型与打包校验。
