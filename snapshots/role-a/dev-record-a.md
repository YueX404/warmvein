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
| `test_match_maps_shutdown` | shutdown → shutdown |
| `test_match_empty_returns_type` | 无启用行时 plan_id=None，保留映射类型 |
| `test_activate_requires_existing` | plan_id=0 → 0 |
| `test_activate_missing_plan` | 库中无该预案 → 0 |
| `test_activate_inserts_execution` | 写入 biz_plan_execution，返回 exec_id |
| `test_plan_match_validates` | POST /api/plan/match 缺 alarmType → 40001 |
| `test_plan_activate_validates` | POST /api/plan/activate 缺 planId → 40001 |
| `test_plan_activate_not_found` | 预案不存在 → 40002 |

## 实现进度

- `services/plan.py`：`match` / `activate`；类型映射 frost→freeze、leak→burst、steal→third_party；列名对齐 `biz_plan` / `biz_plan_execution`
- `routes_plan.py`：`POST /api/plan/match`、`POST /api/plan/activate`；不 import 预警服务
- 前端：`plan.api.ts` + `PlanManage.vue` 匹配/启动；`steps` 解析 JSON 展示动作/责任主体/资源
- 未改 `heat_init.sql`、`main.py` 及其他 Task 独占文件

## Commit

| hash | message |
|---|---|
| `2db07a3` | `feat(5.1): 预案匹配/启动与前端管理` |
| `3d31721` | `fix(task-8): 补齐停暖映射与启动 40002 测试` |

## 问题与处理

- 匹配/启动单测用 FakeSession，避免并行开发时依赖本机 MySQL。
- `tests/test_scaffold.py` 空路由断言会在本 Task 合入后失败，按索引要求不在本分支改脚手架。
- 浏览器核对了 `/plan` 页面与匹配按钮；未起 FastAPI/MySQL 时匹配走失败路径，启动闭环靠 API 单测覆盖。
