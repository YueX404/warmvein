# Task-8 Code Review 反馈

审查分支：`dev-2/feature/task8-plan`  
审查 commit：`8ea5e67`（相对 `master` `ccaa50c`：`2db07a3`、`3d31721`、`8ea5e67`）  
审查时间：2026-09-01  
对照计划：`docs/superpowers/plans/Dev-2-task8-plan.md`  
完整报告：`docs/审查报告-Dev-2-task8-plan.md`  
单测当场：`pytest tests/test_plan.py -v` → 11 passed

## 🔴 阻断性问题（必须修改）

无。

## 🟡 改进建议

1. 【`src/python/services/plan.py:29-33`】`activate` 只查 `plan_id` 是否存在，不要求 `status=1`。停用预案也能写入 `biz_plan_execution`。应加上启用过滤。
2. 【`src/python/routes_plan.py:8-22`】`alarmType`/`level`/`planId`/`operator` 几乎未校验。`level` 应限制 1–4；`operator` 对齐 `VARCHAR(32)`；非字符串 `alarmType` 会 `TypeError` → 50001。非法入参应统一 40001。
3. 【`src/python/services/plan.py:5-11`】`_TYPE_MAP` 有 `steal→third_party`，没有 Task 1 / `biz_alarm.type` 的 `theft`。按预警记录匹配会永远空。补 `"theft": "third_party"`。
4. 【`web/src/pages/plan/PlanManage.vue:38-44`】左侧目录是 mock，匹配打真实 API；`heat_init.sql` 无预案种子。目录有预案、匹配结果为空。目录需标明 Mock 或可点选；测试/运维补 INSERT 夹具（不要改 `heat_init.sql`）。
5. 【`tests/test_plan.py`】无 match/activate HTTP 成功路径；FakeSession 复刻 SQL 语义，测不出语句错误。补 200 用例，并对 SQL 做表名/列名断言。

## 🔵 疑问确认

1. 【响应形状】实现是 snake_case 单对象，api-guide 是 `{plans:[{planId,...}]}`。是否锁定跟计划走，后续改文档？
2. 【`plan.py:19-21`】级别是精确匹配。只有 L4 冻堵预案时，L2/L3 匹配为空。是否应为「同级或以上」？
3. 【`PlanManage.vue:173-184`】启动不传 `alarmId`，也无确认框。管理页手工启动是否接受？
4. 【`dev-record-a.md`】Commit 表缺 `8ea5e67` 自验证文档提交，请补一行。

## 审查结论

✅ 通过（无阻断项）

计划内 6 个独占文件已落地，F0 边界守住，映射与路由正确，启动失败不会假成功。建议合入前处理 🟡 P2-1～P2-4；P3 可在 `review-reply-a.md` 说明。若改了代码，将 `progress.md` 改为「修复完成，待二次审查」后再审；若只回复不改，可进入收尾。
