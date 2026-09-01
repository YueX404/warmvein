# Dev-2 Task 6 代码审查报告

> **审查日期：** 2026-09-01  
> **审查轮次：** 第 1 轮  
> **分支：** `dev-2/feature/task6-workorder`  
> **对照基线：** `master`（`ccaa50c` → `8e59df0`）  
> **需求 / 计划：** `docs/superpowers/plans/Dev-2-task6-workorder.md`  
> **冻结契约：** `docs/功能开发文档.md` §3  
> **审查对象：** `src/python/services/workorder.py`、`src/python/routes_workorder.py`、`tests/test_workorder.py`，以及角色 A 快照  
> **交叉核对：** `config/mysql/heat_init.sql`（`biz_work_order` / `biz_work_order_trace`）、`docs/api-guide.md` §5、`web/src/mock/workorder.mock.ts`、并行 Task 2 的路由校验与 camelCase 映射、Dev-2 文件所有权

---

## 一、总体结论

**暂不建议合入。**

计划内 3 个独占文件和 create/get 两条 API 已经落地，F0 冻结边界守住了，SQL 也是参数化的。当场验证：`pytest tests/test_workorder.py -v` → **6 passed**。

但合入后会把两个问题带给 Task 7 / 角色 B：

1. **GET 详情把表字段原样吐出**（`order_id` / `alarm_id` / `created_at`，且没有 `trace`），与冻结契约、前端 mock、同一文件里 POST 的 `orderId` 不一致。
2. **外部输入只做 truthy 判断**，没有类型/长度校验；超长 `assignee` 会撞上 `VARCHAR(32)`，变成 50001。

单测全部走 `_FakeSession`，**不证明** 真 MySQL 的 `lastrowid` / 列约束可用。这与 Task 1 一样可接受为本地无库的折中，但不能当作联调已通。

**合入建议：先修全部 🔴 和下列 🟡（校验、合入前 scaffold chore），🔵 可记 follow-up。**

---

## 二、审查范围与提交

| 项 | 内容 |
|---|---|
| 相对 `master` 的提交 | `44dbeb4` `feat(9.x): 工单状态机与智能派单` |
| | `8e59df0` `docs(task-6): 补齐自验证快照，阶段标记为待审查` |
| 新增 | `src/python/services/workorder.py`（22 行） |
| | `tests/test_workorder.py`（112 行） |
| 修改 | `src/python/routes_workorder.py`（空桩 → create/get） |
| | `snapshots/role-a/dev-record-a.md`、`progress.md` |
| 未改动（符合 F0 / 文件所有权） | `main.py`、`db.py`、`response.py`、`config/mysql/heat_init.sql`、`tests/test_scaffold.py`、巡检与前端 |
| 阶段快照 | `开发完成，待审查`（与审查前置一致） |
| 全量测试 | `pytest tests/ -v` → **28 passed，1 failed**（`test_all_seven_module_routers_exist`，作者已记录） |

---

## 三、做得好的地方

- 改动落在 Task 6 独占文件内，没有巡检路由，没有 import 预警服务。
- `order_type` 插入写死 `'repair'`、`status=0`，与计划和表注释「待派」一致。
- SQL 使用绑定参数，无字符串拼接。
- INSERT 列与 `biz_work_order` 兼容：`order_type` 有值，`priority`/`title` 可走默认或 NULL。
- 计划指定的 `test_create_and_get`、`test_workorder_create_validates` 已落地，并补了缺失查询、写库字段、API 往返。
- 快照如实写了 scaffold 失败和 FakeSession 的取舍，没有假装全量绿。

---

## 四、问题清单

优先级：

- **P0**：合入即生产级阻断（本次无）
- **P1 / 🔴**：必须在合入前修复
- **P2 / 🟡**：应修，否则后续 Task / 联调会踩坑
- **P3 / 🔵**：低影响，或需要确认是否为计划有意切片

### 🔴 阻断性问题（必须修改）

#### P1-1 GET 详情字段与冻结契约、前端 mock 不一致

- **位置：** `src/python/routes_workorder.py:16-19`，`src/python/services/workorder.py:16-22`，`tests/test_workorder.py:108-112`

```python
@router.get("/workorder/{order_id}")
def api_get(order_id: int):
    o = workorder.get_order(order_id)
    return ok(o) if o else fail(40002, "工单不存在")
```

- **问题：** `get_order` 直接 `dict(row)`，响应是 `order_id` / `alarm_id` / `created_at` / `updated_at`，没有 `trace`。
  - 功能开发文档 §3（冻结契约）GET 出参是 `{status, trace}`。
  - `web/src/mock/workorder.mock.ts` 是 `orderId` / `alarmId` / `createdAt`。
  - 同一文件 POST 成功体已经是 `orderId`。
  - 并行 Task 2 的 `/alarm/list` 已做 snake_case → camelCase 和时间格式化。
  - `test_workorder_create_and_get_via_api` 还把 `alarm_id` 写进断言，等于把错误契约冻住了。
- **影响：** Task 7 的 `getWorkOrder()` 会按 mock/camelCase 读字段，详情页会空值；`trace` 缺失则「工单详情/状态」契约不完整。计划 snippet 的 `return ok(o)` 不能压过冻结契约。
- **修复：** 在路由层做映射，至少输出 `orderId`、`alarmId`、`assignee`、`status`、`statusName`、`createdAt`、`updatedAt`、`trace`（暂无轨迹可先 `[]`）。同步改测试，不要再断言 `alarm_id`。

---

### 🟡 改进建议

#### P2-1 入参只做 truthy，没有类型/长度/格式校验

- **位置：** `src/python/routes_workorder.py:9-13`
- **问题：** `if not body.get("alarmId") or not body.get("assignee")` 会把 `0`、`""` 拦掉（符合计划夹具），但：
  - `"assignee": "  "`、非字符串、长度 > 32 都会放行；`assignee VARCHAR(32)` 超长会变成 MySQL 错 → 全局 50001。
  - `"alarmId": true` / `"3"` / `3.14` 也会进 INSERT。
- **对照：** Task 2 `ack_alarm` 已校验 `isinstance(alarm_id, int) and > 0`、字符串 strip、长度 ≤ 32。技术规范和 Dev-2 Global Constraints 都要求类型/长度/合法性校验。
- **修复：** 对齐 Task 2：`alarmId` 必须是正整数；`assignee` 必须是非空字符串并 `strip()`，长度 ≤ 32；非法一律 40001。建议补单测。

#### P2-2 创建工单不写 `biz_work_order_trace`

- **位置：** `src/python/services/workorder.py:6-13`
- **问题：** 表结构有独立轨迹表，契约 GET 需要 `trace`。当前 INSERT 只写主表，查询也不读轨迹。即使 P1-1 先返回 `[]`，创建动作本身仍没有 `create` 记录。
- **影响：** 后续若要做状态机/核验闭环，轨迹从一开始就是空的。
- **修复：** 创建成功后插入 `action=create, operator=assignee`（或 `"系统"`），GET 再按 `order_id` 查出 `trace`。

#### P2-3 合入前 `tests/test_scaffold.py` 会红灯

- **位置：** `tests/test_scaffold.py:35`（本分支按所有权未改，正确）
- **问题：** 当场复现 `test_all_seven_module_routers_exist` 失败。索引文档要求在 **main 上单独 chore** 放宽，不要在本分支改。
- **影响：** 若 CI 跑 `pytest tests/`，本 PR 无法绿。
- **修复：** 合入前先在 main 做 chore（或本 PR 说明依赖该 chore 先合）。不要在 Task 6 分支改 `test_scaffold.py`。

#### P2-4 校验单测只覆盖「0 + 空字符串」这一条组合

- **位置：** `tests/test_workorder.py:82-85`
- **问题：** 缺字段、缺 body、仅缺 `assignee`、非 int `alarmId`、超长 `assignee` 都没有覆盖。`_FakeSession` 还把 `status=0` 写死，`test_create_writes_repair_and_pending` 并不能证明 INSERT SQL 真的写了 `status=0`。
- **修复：** 拆开校验用例；断言 INSERT SQL 文本含 `status` 与 `0`；P1-1 的字段名断言改成 camelCase。

---

### 🔵 疑问确认

#### P3-1 标题是「状态机与智能派单」，实现只有创建 + 查询

- **位置：** 计划 Goal vs `docs/开发任务拆分-角色A-平台与智能底座.md` M3
- **疑问：** M3 要求状态机 `0→1→2→3→4`、智能派单、超时升级。子计划把本 Task 收成 `create_from_alarm(alarm_id, assignee)`，派单人完全由调用方传入，没有流转 API。这是有意切片还是漏做？若是切片，请在回复里写明后续 Task 承接，避免角色 B 按标题理解成已可接单/核验。

#### P3-2 GET 未返回 `orderType` / `title` / `priority` / `stationId`

- **位置：** `workorder.py:18-20` vs `docs/api-guide.md` §5.2
- **疑问：** api-guide 比功能开发文档 §3 更全。本 Task 计划 SELECT 只有 6 列。Task 7 前端若按 api-guide 画详情，这些字段会空。是否本轮只保证 §3 最小集（`status` + `trace`）？

#### P3-3 开发记录未登记第二笔 commit

- **位置：** `snapshots/role-a/dev-record-a.md` 的 Commit 表
- **内容：** 表里只有 `44dbeb4`，HEAD 实际是 `8e59df0` `docs(task-6): 补齐自验证快照...`。二次审查时补一行即可。

#### P3-4 假会话无法证明 `lastrowid` 在真 MySQL + SQLAlchemy 2.0 上可用

- **位置：** `workorder.py:13`
- **内容：** 计划与 Task 7 巡检都用 `r.lastrowid`。本地无库可以理解，合入后需要一次真实 INSERT 冒烟（或集成测试），避免 `orderId` 为 `None`/`0` 仍返回 `code=0`。

---

## 五、审查维度核对

| 维度 | 结论 |
|---|---|
| 功能正确性 | create/get 路径按子计划能跑通；相对冻结契约，GET 形态不对；状态机/智能派单未做（见 P3-1） |
| 测试质量 | 6 条均过，但 FakeSession 不碰真库，且把 snake_case 和写死 `status=0` 冻进断言 |
| 代码质量 | 函数短、分层清晰、无重复、无新依赖 |
| 范围控制 | 合格，未改 F0 冻结文件，未加巡检 |
| 文档同步 | 快照已切到 Task 6 且阶段正确；commit 表少一行 |
| 潜在风险 | 无密钥硬编码；超长 assignee → 500；CI 全量 pytest 红灯 |

---

## 六、审查结论

**❌ 需要修改后再审**

请开发窗口优先处理：

1. 🔴 P1-1 GET 响应改为 camelCase，并带上 `trace`
2. 🟡 P2-1 入参类型/长度校验
3. 🟡 P2-2 创建时写轨迹（若 P1-1 先返回 `[]`，轨迹写入仍建议本轮做完）
4. 🟡 P2-3 合入路径上处理 scaffold chore（main，不在本分支改）
5. 🟡 P2-4 补校验与契约断言

🔵 三项在 `snapshots/role-a/review-reply-a.md` 里说明采纳或保留即可。
