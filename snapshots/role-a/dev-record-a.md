# Task-7 开发记录（角色A）

**PR / Task：** Dev-2 Task 7 巡检计划生成与工单页面  
**分支：** `dev-2/feature/task7-patrol`  
**工作区：** `D:\YY\.worktrees\dev-2-feature-task7-patrol`（独立 worktree，未切换主仓库 `master`）  
**需求：** `docs/superpowers/plans/Dev-2-task7-patrol.md`

## 测试用例

| 用例 | 行为 |
|---|---|
| `test_generate_plan_returns_id` | FakeSession 插入后返回 id>0 且 commit |
| `test_generate_plan_writes_biz_patrol` | SQL 写入 `biz_patrol` 必填列，参数映射正确 |
| `test_generate_plan_defaults_plan_name` | 缺 planName 时写入 `auto` |
| `test_generate_plan_rejects_missing_id` | lastrowid 为空则抛错且不 commit |
| `test_patrol_generate_validates` | POST 空 body → 40001 |
| `test_patrol_generate_ok` | 成功返回 camelCase `patrolId` |
| `test_patrol_generate_rejects_invalid_type` | patrolType 非 daily/special/emergency → 40001 |
| `test_patrol_generate_rejects_bool_station` | stationId=True → 40001 |
| `test_patrol_generate_rejects_string_station` | stationId 字符串 → 40001 |
| `test_patrol_generate_rejects_blank_assignee` | 空白巡检人 → 40001 |
| `test_patrol_generate_rejects_long_assignee` | 超过 32 字 → 40001 |
| `test_patrol_generate_rejects_bad_date` | 日期非 YYYY-MM-DD → 40001 |
| `test_patrol_generate_accepts_date_object_via_service` | 服务层可接受 date 对象 |

## 实现进度

- `services/patrol.py`：`generate_plan(rule) -> int`，插入 `biz_patrol`，status=0
- `routes_workorder.py`：仅追加 `POST /api/patrol/plan/generate`，保留 Task 6 create/get
- 前端：工单创建/查询 + 巡检 Tab（`WorkOrder.vue` 引用 `Patrol.vue`），未改 `router/index.ts`
- `workorder.api.ts`：create / get / generatePatrolPlan
- Mock：工单票根 + 巡检班表，后端不可达时 DEV 回退

## Commit

| hash | message |
|---|---|
| `7bccff1` | `feat(9.x): 巡检计划生成与工单页面` |

## 问题与处理

- 计划 snippet 直连 MySQL；单测沿用 Task 6 FakeSession，避免无库时误报。
- 契约按子计划：请求扁平 `stationId/patrolType/assignee/planDate`，响应 `{patrolId}`（非 api-guide 的嵌套 `rule` / `planId`）。
- lastrowid 为空时拒绝 commit，避免返回 0 仍 `code=0`。
- 主仓库 `D:\YY` 保持 `master`，本 Task 只在 worktree 分支上改文件。
