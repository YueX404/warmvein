# Dev-2 Task 8 二次审查报告

> **审查日期：** 2026-09-01  
> **审查轮次：** 第 2 轮（对照首轮报告与修复提交）  
> **审查角色：** 审查窗口（只读，未改实现、未提交）  
> **分支：** `dev-2/feature/task8-plan`（worktree：`D:\YY\.worktrees\dev-2-feature-task8-plan`，HEAD `c0e5191`）  
> **对照基线：** `master` `ccaa50c` → 当前 HEAD `c0e5191`  
> **首轮审查 HEAD：** `8ea5e67`  
> **本轮修复提交：** `5ecbb75` `1df300a`；`c0e5191` 文档/快照  
> **首轮报告：** `docs/审查报告-Dev-2-task8-plan.md`  
> **作者回复：** `snapshots/role-a/review-reply-a.md`  
> **阶段快照：** `修复完成，待二次审查`

---

## 一、总体结论

**首轮无 P1。P2 均已落地，P3 已按回复修复或书面锁定。建议合入。**

相对首轮「可以合入，建议先处理 P2」，本轮已经把停用预案启动、入参校验、`theft` 映射、Mock 目录假数据、HTTP 成功路径测试补齐。种子 SQL 独立文件，未改 `heat_init.sql`。

当场验证：`pytest tests/test_plan.py -v` → **19 passed**。

本轮没有新的 P1/P2。P3 可记 follow-up，不阻塞合入。P3-1（snake_case 单对象）、P3-2（级别精确匹配）、P3-3（管理页不传 alarmId）、P3-6（框架 422）按回复接受。

---

## 二、首轮问题关闭表

| ID | 首轮结论 | 本轮状态 | 证据 |
|---|---|---|---|
| P2-1 | `activate` 不看 `status=1`，停用也能启动 | **已关闭** | `plan.py:33-35`：`WHERE plan_id=:p AND status=1`。`test_activate_rejects_disabled_plan` 断言不 INSERT |
| P2-2 | alarmType/level/planId/operator 几乎未校验 | **已关闭** | `routes_plan.py` `_parse_match` / `_parse_activate`：字符串且 ≤32；`type(x) is int` 排除 bool；level 1–4；planId ≥1；operator strip 且 ≤32。单测覆盖非字符串类型、level 越界、非正 id、超长 operator |
| P2-3 | 缺 `theft→third_party` | **已关闭** | `_TYPE_MAP` 含 theft，并显式 freeze/burst/third_party。`test_match_maps_theft_to_third_party` |
| P2-4 | 左侧目录是 mock，匹配打空库，两边矛盾 | **已关闭** | 目录标注「Mock，非库内数据」；点选仅预览；`fromMock` 时 `canActivate=false` 且 `onActivate` 直接 return。`config/mysql/plan_seed.sql` 手工种子，第三方破坏级别改为 2 |
| P2-5 | 无 HTTP 成功路径；FakeSession 复刻 SQL | **已关闭** | `test_plan_match_ok` / `test_plan_activate_ok`。FakeSession 断言表名、匹配列、`status=1` |
| P3-1 | 响应形状与 api-guide 不一致 | **接受** | 锁定跟计划走：snake_case 单对象。后续改 api-guide |
| P3-2 | 级别精确匹配 | **接受** | 与计划 SQL 一致；种子冻堵/爆管 L4、停暖/第三方 L2 |
| P3-3 | 启动不带 alarmId、无确认框 | **部分关闭** | 不传 alarmId **接受**。已加 `ElMessageBox.confirm` |
| P3-4 | `onActivate` 无 catch | **已关闭** | `PlanManage.vue:215-216` 空 catch |
| P3-5 | 开发记录缺自验证 commit | **已关闭** | 已列 `8ea5e67`、`5ecbb75`、`1df300a`。本轮文档 commit `c0e5191` 仍未入表，见 P3-R1 |
| P3-6 | 非对象 body 走 422 | **接受** | 全站共性，不在本 Task 包一层 |

---

## 三、本轮新问题

### P3 — 可记 follow-up，不阻塞合入

#### P3-R1 开发记录仍未登记本轮文档 commit

- **位置：** `snapshots/role-a/dev-record-a.md` Commit 表
- **问题：** 有 `1df300a`，没有 `c0e5191 docs(task-8): 审查回复，阶段改为待二次审查`。无功能影响。

#### P3-R2 `plan_seed.sql` 重复执行会插出重复预案

- **位置：** `config/mysql/plan_seed.sql`
- **问题：** 纯 `INSERT`，无去重。跑两遍会有两套四类预案。匹配 `LIMIT 1` 仍能工作，目录会乱。
- **处理：** 演示前执行一次即可；或后续改成 `INSERT ... WHERE NOT EXISTS`。不要并进 `heat_init.sql`。

#### P3-R3 启动人输入框无 maxlength

- **位置：** `PlanManage.vue:97`
- **问题：** 后端已拒 >32 字符（40001），输入框仍可键入更长，确认后才失败。
- **处理：** `maxlength="32"` 即可，非必须。

---

## 四、修复质量（本轮）

- `_as_int` 用 `type(value) is not int`，避开 Python `bool` 是 `int` 子类的坑。`level: true` / `planId: true` 会 40001，这是对的。
- `fromMock` 与 `canActivate` 双保险：预览即使带了 mock 的 `plan_id`，也不会对库发启动。
- 种子与 mock 的第三方破坏都改成 L2，和 Task 1 `steal` 默认级对齐，精确匹配语义下联调能对上。
- 范围仍在预案模块 + 角色 A 快照 + 首轮要求的 `plan_seed.sql`。未改 `heat_init.sql`、`main.py` 及其它 Task 独占文件。

---

## 五、残留风险（与首轮相同，非本轮引入）

- HTTP 成功路径 mock 的是 `plan.match` / `plan.activate`，不经过 FakeSession；SQL 列名断言只在服务层单测。没有打到真实 MySQL。
- 前端无组件测试；Mock 预览不可启动、确认框取消，靠读代码确认。
- 合入后 `tests/test_scaffold.py::test_all_seven_module_routers_exist` 仍会红，需 main 上单独 chore 放宽空桩断言。
- 演示闭环必须手工执行 `config/mysql/plan_seed.sql`，新库默认仍无预案行。

---

## 六、审查结论

✅ **通过，建议合入**

首轮 P2 已关闭，本轮无新阻断项。P3-R1～R3 不挡合入。开发窗口可将 `progress.md` 标为审查通过，按收尾流程 push / 提 PR。
