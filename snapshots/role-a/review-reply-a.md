# Task-7 审查反馈处理记录

审查来源：`docs/审查报告-Dev-2-task7-patrol.md`、`snapshots/role-a/review-feedback-a.md`  
处理分支：`dev-2/feature/task7-patrol`  
处理时间：2026-09-01

## 🔴 阻断性问题

无。

## 🟡 改进建议

| 编号 | 处理 | 说明 |
|---|---|---|
| P2-1 | 修复 | 开单 `onCreate`、生成计划 `onGenerate` 失败只走拦截器错误提示，不再 Mock 假成功。左侧示例工单/班表点选预览仍用 Mock；查单 GET 在 DEV 断网时仍可读预览数据。删除已无引用的 `mockCreateOrder` / `mockGeneratePatrol`。 |
| P2-2 | 修复 | `_parse_patrol` 按失败项返回短文案（`stationId 非法` / `patrolType 非法` / `assignee 非法` / `planDate 非法` / `planName 非法`），不再一律「缺少字段」。 |
| P2-3 | 修复 | 补 `stationId<=0`、`planName` 超长/非字符串路由测试，并断言日期/空 body 的文案。 |

## 🔵 疑问确认

| 编号 | 结论 |
|---|---|
| P3-1 | **锁定跟子计划走**：请求扁平 `stationId/patrolType/assignee/planDate`，成功体 `{patrolId}`。不包一层 `rule`，不返回 `planId` / `checkPoints` / `estimatedDuration`。后续应改 api-guide / 功能开发文档对齐本契约，角色 B 不要按 api-guide 联调。 |
| P3-2 | **本 Task 只做手工建计划**。用户填站、类型、人、日期后 INSERT，`route_points` 保持 NULL。基于预警/季节生成路线不在 Task 7 范围，留给后续 Task。 |
| P3-3 | 修复：Commit 表补 `6ada516` 及本轮审查修复提交。 |
| P3-4 | 保留。单测 FakeSession 不证明真 MySQL `lastrowid`。合入后需一次真实 INSERT 冒烟。 |
| P3-5 | 保留。`WorkOrderRow` 类型与 `.dot` 样式重复不影响行为，不在本轮抽共享。 |

## 验证

- `pytest tests/test_patrol.py tests/test_workorder.py -v` → 30 passed
- `npx vue-tsc --noEmit`（`web/`）→ exit 0
