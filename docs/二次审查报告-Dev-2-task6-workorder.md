# Dev-2 Task 6 二次审查报告

> **审查日期：** 2026-09-01  
> **审查轮次：** 第 2 轮（对照首轮报告与修复提交）  
> **分支：** `dev-2/feature/task6-workorder`  
> **对照基线：** `master` `ccaa50c` → 当前 HEAD `9ee53e7`  
> **首轮审查 HEAD：** `8e59df0`  
> **本轮修复提交：** `76dbac4` `fix(task-6): review反馈 - GET 详情改为 camelCase 并返回 trace`；`19bd4d7` `fix(task-6): review反馈 - 入参校验与创建写轨迹`；`9ee53e7` `docs(task-6): 审查回复，阶段改为待二次审查`  
> **首轮报告：** `docs/审查报告-Dev-2-task6-workorder.md`  
> **作者回复：** `snapshots/role-a/review-reply-a.md`  
> **审查对象：** `src/python/services/workorder.py`、`src/python/routes_workorder.py`、`tests/test_workorder.py`

---

## 一、总体结论

**首轮 P1 已关闭，本分支内的 P2 均已落地。建议合入。**

相对首轮「暂不建议合入」，本轮 GET 已按冻结契约和前端 mock 输出 camelCase + `trace`；创建与轨迹在同一事务；入参校验对齐 Task 2。当场验证：`pytest tests/test_workorder.py -v` → **13 passed**。

残留只有合入流程项 P2-3：`tests/test_scaffold.py` 空桩断言仍会让 `pytest tests/` 红灯。作者按文件所有权未改该文件，处理方式正确。合入前在 **main 上单独 chore** 放宽即可，不构成本分支再改一轮代码的理由。

---

## 二、首轮问题关闭表

| ID | 首轮结论 | 本轮状态 | 证据 |
|---|---|---|---|
| P1-1 | GET dump 表字段、无 `trace`、snake_case | **已关闭** | `routes_workorder.py:27-44` `_to_api` 输出 `orderId`/`alarmId`/`statusName`/`createdAt`/`trace`；`test_workorder_create_and_get_via_api` 断言 camelCase 且不含 `alarm_id`/`order_id` |
| P2-1 | 入参只做 truthy | **已关闭** | `_parse_create`：`type(alarm_id) is int` 且 `> 0`（排除 `bool`）；`assignee` strip 后非空且 ≤32。6 条拆分校验单测均过 |
| P2-2 | 创建不写轨迹表 | **已关闭** | `create_from_alarm` 先取 `lastrowid` 再 `INSERT biz_work_order_trace`，同一 session 内 `commit`；`get_order` 联查轨迹 |
| P2-3 | scaffold 空桩导致全量 pytest 失败 | **保留（正确）** | 本分支未改 `test_scaffold.py`。当场复现：`pytest tests/ -v` → 35 passed，1 failed。合入依赖 main chore |
| P2-4 | 校验/SQL 断言不足 | **已关闭** | 缺字段 / 非 int / bool / 空白 / 超长均有用例；INSERT SQL 断言含 `status`、`'repair'`、`,0,` |
| P3-1 | 标题 vs 只做 create/get | **已关闭（接受切片）** | 回复写明：状态机流转与智能派单不在本 PR；Task 7 只追加巡检与前端，流转需另开任务 |
| P3-2 | GET 是否只保证 §3 最小集 | **已关闭（接受）** | 本轮保证 `{status, trace}` + mock 所需 camelCase；不返回 `title`/`orderType`/`priority`/`stationId` |
| P3-3 | 开发记录缺 commit | **部分关闭** | 已补 `8e59df0`/`76dbac4`/`19bd4d7`；HEAD `9ee53e7`（审查回复文档）仍未进 commit 表 |
| P3-4 | `lastrowid` 未经真库验证 | **部分关闭（接受）** | `if not oid: raise RuntimeError(...)`，避免 `orderId` 为 `None` 仍 `code=0`。单测仍走 FakeSession，真 MySQL 冒烟合入后做 |

### 关于 P2-2 实现细节

轨迹 `operator` 写 `"系统"` 而非 `assignee`，与首轮「assignee 或系统」一致，采纳。  
`lastrowid` 在第二条 INSERT **之前**取出，避免 trace 行的 id 覆盖工单 id，这一点是对的。  
工单行与轨迹行同事务提交：轨迹失败会连工单一起回滚，不会留下无轨迹的工单。

---

## 三、本轮新问题

无新的 P0 / P1 / P2。

### 🔵 P3-R1 开发记录仍缺当前 HEAD

- **位置：** `snapshots/role-a/dev-record-a.md` Commit 表
- **内容：** 表止于 `19bd4d7`，未列 `9ee53e7` `docs(task-6): 审查回复，阶段改为待二次审查`。不阻塞合入，收尾时补一行即可。

---

## 四、当场验证

| 命令 | 结果 |
|---|---|
| `pytest tests/test_workorder.py -v` | **13 passed** |
| `pytest tests/ -v` | **35 passed，1 failed**（`test_all_seven_module_routers_exist`，P2-3） |

工作区干净，阶段快照为「修复完成，待二次审查」，与二次审查前置一致。

---

## 五、审查结论

**✅ 通过**

本分支代码可以合入。请开发窗口在收尾时：

1. 合入前确认 main 上的 `test_scaffold.py` chore 已做或与本 PR 捆绑说明。
2. （可选）开发记录补上 `9ee53e7`。
