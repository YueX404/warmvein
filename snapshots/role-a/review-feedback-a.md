# Task-7 Code Review 反馈

审查分支：`dev-2/feature/task7-patrol`  
审查 commit：`6ada516`（功能 `7bccff1`；快照 `6ada516`）  
审查时间：2026-09-01  
对照：`docs/superpowers/plans/Dev-2-task7-patrol.md`  
完整报告：`docs/审查报告-Dev-2-task7-patrol.md`  
单测当场：`pytest tests/test_patrol.py tests/test_workorder.py tests/test_scaffold.py -v` → 31 passed  
前端当场：`web` 目录 `npx vue-tsc --noEmit` → 通过

主仓库 `D:\YY` 保持 `master`，审查只读 worktree，未切主仓库分支、未改实现、未提交。

## 🔴 阻断性问题（必须修改）

无。

## 🟡 改进建议

1. 【`web/src/pages/workorder/Patrol.vue:120-132`、`WorkOrder.vue:137-144`】DEV 下后端 500/断网时写路径仍 `ElMessage.success` 并写入本地 Mock。拦截器已先弹 error，再弹成功。与 Task 2 二次审查「写路径不假成功」、Task 8 启动失败即失败不一致。建议写操作失败就失败；Mock 只用于点选预览。
2. 【`src/python/routes_workorder.py:123-128`】校验失败一律返回「缺少 stationId/patrolType/assignee/planDate」。类型错误、超长、日期格式错时字段其实都在，前端拦截器会把这句直接展示给用户。建议与工单创建对齐，改为「参数校验失败」，或按失败原因给短文案。
3. 【`tests/test_patrol.py`】缺 `stationId<=0`、`planName` 超长/非字符串 的路由用例。校验代码已写，补测可防止回退。

## 🔵 疑问确认

1. 【契约】子计划与实现是扁平 body + `{patrolId}`；`docs/功能开发文档.md` §3 是 `{rule}` / `{planId}`，`docs/api-guide.md` §9.1 还有 `checkPoints` / `estimatedDuration`。开发记录已写明按子计划。请确认后续以子计划为准，避免角色 B 按 api-guide 联调。
2. 【`snapshots/role-a/progress.md` / `dev-record-a.md`】进度 HEAD 仍写 `7bccff1`，Commit 表未登记 `6ada516`。
3. 【`services/patrol.py`】未写 `route_points`，也没有按预警/季节自动生成路线。是否本 Task 只做手工建计划，路线留给后续？
4. 【FakeSession】`lastrowid` 未打到真 MySQL。合入后需要一次真实 INSERT 冒烟。

## 审查结论

✅ 通过（无阻断项）

计划内文件均已落地，F0 冻结守住，Task 6 create/get 未改行为，校验比计划 snippet 更完整。建议合入前处理 P2-1、P2-2；P2-3 与 🔵 在 `review-reply-a.md` 说明即可。

若改 P2，将 `progress.md` 标为「修复完成，待二次审查」再交复审；若只回复不改代码，可保持待合入。
