# Task-8 开发记录（角色A）

**PR / Task：** Dev-2 Task 8 预案匹配/启动与前端管理  
**分支：** `dev-2/feature/task8-plan`  
**需求：** `docs/superpowers/plans/Dev-2-task8-plan.md`

## 测试用例

| 用例 | 行为 |
|---|---|
| `test_match_frost_high` | frost + 4 → freeze 预案 |
| `test_match_maps_leak_to_burst` | leak → burst |
| `test_match_maps_steal_to_third_party` | steal → third_party |
| `test_match_maps_theft_to_third_party` | theft → third_party |
| `test_match_maps_shutdown` | shutdown → shutdown |
| `test_match_empty_returns_type` | 无启用行时 plan_id=None，保留映射类型 |
| `test_activate_requires_existing` | plan_id=0 → 0 |
| `test_activate_missing_plan` | 库中无该预案 → 0 |
| `test_activate_rejects_disabled_plan` | status≠1 不写执行单 |
| `test_activate_inserts_execution` | 写入 biz_plan_execution，返回 exec_id |
| `test_plan_match_validates` | POST /api/plan/match 缺 alarmType → 40001 |
| `test_plan_match_rejects_non_string_type` | alarmType 非字符串 → 40001 |
| `test_plan_match_rejects_level_out_of_range` | level 越界 → 40001 |
| `test_plan_match_ok` | 匹配成功返回 plan_id/plan_type |
| `test_plan_activate_validates` | POST /api/plan/activate 缺 planId → 40001 |
| `test_plan_activate_rejects_non_positive_id` | planId≤0 → 40001 |
| `test_plan_activate_rejects_long_operator` | operator>32 → 40001 |
| `test_plan_activate_not_found` | 预案不存在 → 40002 |
| `test_plan_activate_ok` | 启动成功返回 execId |

## 实现进度

- `services/plan.py`：`match` / `activate`；映射含 frost/leak/steal/theft/shutdown 及四类自身词
- `activate` 仅允许 `status=1`
- `routes_plan.py`：校验 alarmType/level/planId/operator
- 前端：匹配/启动；Mock 目录预览不可启动；启动前确认
- 种子：`config/mysql/plan_seed.sql`（手工，不改 `heat_init.sql`）

## Commit

| hash | message |
|---|---|
| `2db07a3` | `feat(5.1): 预案匹配/启动与前端管理` |
| `3d31721` | `fix(task-8): 补齐停暖映射与启动 40002 测试` |
| `8ea5e67` | `docs(task-8): 补齐自验证快照，阶段标记为待审查` |
| `5ecbb75` | `fix(task-8): review反馈 - 停用不可启动、入参校验与theft映射` |
| `1df300a` | `fix(task-8): review反馈 - Mock目录标注、种子SQL与启动确认` |

## 问题与处理

- 匹配/启动单测用 FakeSession，并对 SQL 表名/列名/`status=1` 做断言；HTTP 成功路径 mock 服务层。
- `tests/test_scaffold.py` 空路由断言会在本 Task 合入后失败，按索引要求不在本分支改脚手架。
- 演示闭环需手工执行 `config/mysql/plan_seed.sql`。
- 审查 P3-1：契约锁定 snake_case 单对象；P3-2：级别精确匹配。
