# Task-2 开发记录（角色A）

**PR / Task：** Dev-2 Task 2 预警列表/确认 API 与前端预警一张图  
**分支：** `dev-2/feature/task2-alarm-map`  
**需求：** `docs/superpowers/plans/Dev-2-task2-alarm-map.md`  
**工作区：** `D:\YY-task2`（worktree，未切换 `D:\YY` 的 master）

## 测试用例

| 用例 | 行为 |
|---|---|
| `test_alarm_list` | `GET /api/alarm/list?level=3` → `code=0`，camelCase |
| `test_alarm_list_filters_status` | `status=0` 作为合法过滤 |
| `test_alarm_list_rejects_invalid_level` | `level=9` → `40001` |
| `test_alarm_list_rejects_invalid_status` | `status=9` → `40001` |
| `test_alarm_list_caps_result_size` | SQL 带 `LIMIT 200` |
| `test_alarm_ack_validates_id` | `alarmId=0` → `40001` |
| `test_alarm_ack_requires_operator` | 缺 operator → `40001` |
| `test_alarm_ack_not_found` | 无行 → `40002`，不 commit |
| `test_alarm_ack_rejects_non_open_status` | 终态 → `40001` |
| `test_alarm_ack_success` | `status=0` 更新成功 |
| `test_alarm_router_has_no_forecast` | 不挂 `/forecast` |

## 实现进度

- 列表查 `biz_alarm`，`LIMIT 200`，失败不在生产灌 Mock
- ack 仅 `status=0`；失败/关闭对话框不假成功
- 站点卡片 = mock ∪ 告警 stationId

## Commit

| hash | message |
|---|---|
| `33fcacf` | `feat(4.1): 预警列表/确认 API 与预警一张图` |
| `00c0bd8` | `docs(task-2): 补齐自验证快照，阶段标记为待审查` |
| `3eeea88` | `fix(task-2): review反馈 - ack失败或关闭不再假成功` |
| `9a2f8e9` | `fix(task-2): review反馈 - ack仅未确认可确认` |
| `1fec805` | `fix(task-2): review反馈 - 列表失败不灌Mock与筛选站点上限` |

## 问题与处理

- `test_scaffold.py` 空桩断言仍失败，本分支不改。
- P3-4 HTTP 422 需改冻结的 `main.py`，follow-up。
