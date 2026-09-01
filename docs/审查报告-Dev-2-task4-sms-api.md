# Task-4 Code Review 反馈

审查分支：`dev-2/feature/task4-sms-api`  
审查 commit：`e4b5860`（功能 `54d4e17`；文档 `beb2dc1` `e4b5860`）  
审查时间：2026-09-01  
对照基线：`master`（`d084b59` → `e4b5860`）  
需求 / 计划：`docs/superpowers/plans/Dev-2-task4-sms-api.md`  
审查对象：`src/python/routes_sms.py`、`tests/test_sms_routes.py`、`web/src/pages/sms/TemplateManage.vue`、`web/src/services/sms.api.ts`、`web/src/mock/sms.mock.ts`，以及角色 A 快照  
交叉核对：`src/python/services/sms_service.py`（只读）、`config/mysql/heat_init.sql`（`biz_sms_template` / `biz_sms_log`）、`docs/功能开发文档.md` §3/§9、F0 冻结边界、Task 3 已合入契约  
工作区：`D:\YY\.worktrees\dev-2-feature-task4-sms-api`（审查窗口未切换 `D:\YY` 的 `master`）

审查只读，未改实现代码、未提交。

当场验证：

- `python -m pytest tests/test_sms_routes.py tests/test_sms_service.py tests/test_scaffold.py -v` → **36 passed**
- `npx vue-tsc --noEmit`（`web/`）→ **exit 0**

阶段校验：`snapshots/role-a/progress.md` 为「开发完成，待审查」，工作区审查前干净。

---

## 一、总体结论

**可以合入。** 无阻断项。

计划内 5 个独占文件均已落地，F0 冻结文件未动，未改 `sms_service.py` / `main.py` / `heat_init.sql`。路由路径正确（`POST /api/sms/send`、`GET /api/sms/log`），发送走 Task 3 `send_sms`，模板不存在映射 40002，SQL 参数化，列表 camelCase + `LIMIT 200`，手机号展示脱敏。前端拦截器能把非 0 `code` 当成失败，没有 Task 2 那种「接口失败却提示成功」。

合入前仍建议处理下面的 🟡：HTTP 层未按 11 位数字校验手机号（会返回成功但实际 0 条发送）、Mock 模板与种子数据变量不一致、同步重试可能顶满 15s 超时。这些不构成进程级阻断，联调时会踩坑。

**合入建议：无 🔴。🟡 建议在合入前改完；🔵 书面答复即可。**

---

## 二、审查范围与提交

| 项 | 内容 |
|---|---|
| 相对 `master` 的提交 | `54d4e17` `feat(sms): 短信发送/记录 API 与模板管理页面` |
| | `beb2dc1` `docs(task-4): 补齐开发记录中的 commit hash` |
| | `e4b5860` `docs(task-4): 自验证通过，阶段标记为待审查` |
| 修改 | `src/python/routes_sms.py`（+92） |
| | `web/src/pages/sms/TemplateManage.vue`（+365） |
| | `web/src/mock/sms.mock.ts`（+75） |
| 新增 | `tests/test_sms_routes.py`（+140） |
| | `web/src/services/sms.api.ts`（+35） |
| 快照 | `snapshots/role-a/dev-record-a.md`、`snapshots/role-a/progress.md` |
| 未改动（符合 F0 冻结与独占） | `main.py`、`sms_service.py`、`sms_consumer.py`、`kafka_topics.py`、`response.py`、`db.py`、`config/settings.py`、`config/mysql/heat_init.sql`、`web/src/router/index.ts`、`web/src/services/api.ts`、`web/src/components/*`、`tests/test_scaffold.py` |
| 范围 | `git diff --name-only master...HEAD` 仅上述 7 个文件 |

---

## 三、做得好的地方

- 改动落在 Task 4 独占文件内，没有碰短信网关实现，也没有改 F0 锁定的 `main.py` / 路由表。
- 路由按约定写完整路径 `@router.post("/sms/send")`，经 `/api` 前缀后正好是契约 URL。
- 校验比计划 snippet 更严：`templateCode` 去空白/超长、`phones` 非列表/空/非字符串、`vars` 非 dict、`batchId` 超长；SQL 用 `:b` / `:limit` 绑定。
- 列表输出 camelCase（`phoneMasked` / `batchId` / `createdAt`），与预警列表和本页前端一致；`ORDER BY created_at DESC LIMIT 200` 对齐 Task 2，避免无界扫描。
- `GET /sms/log` 同时接受 `batch_id` 与 `batchId`，兼容计划用例和 `sms.api.ts` 的 `batch_id`。
- 前端走共享 `http` 拦截器：`code !== 0` 会 `reject`，发送失败不会再弹成功；DEV 下仅日志查询回落 Mock，发送路径不假成功。
- `maskPhone` 与 Task 3 `mask_phone` 规则一致（11 位 → `138****1234`）；发送区预览脱敏，记录列不再展示明文号。
- 单测覆盖计划两条夹具，并补了缺参、类型错误、40002、过滤、脱敏字段、LIMIT；`test_sms_service.py` 回归仍绿。

---

## 🔴 阻断性问题（必须修改）

无。

---

## 🟡 改进建议

1. 【`src/python/routes_sms.py:41-44`】手机号只拦了「非字符串 / 空 / 长度 > 11」，没有按 `sms_service.is_mobile`（11 位数字）做格式校验。`"1381234"`、`"abcdefghijk"` 会 200 + `batchId`，服务层静默 skip，调用方（含 Dev-1 公众服务）会以为发出去了。建议在 `_parse_send` 拒绝非法号，返回 40001；至少当清洗后号码全非法时不要 `ok`。

2. 【`web/src/mock/sms.mock.ts:20-39`】模板目录仍是 Mock，且与 `heat_init.sql` 种子不一致：
   - 缺 `ALARM_BLUE` / `ALARM_YELLOW` / `ALARM_ORANGE` / `PUBLIC`
   - `ALARM_RED` 种子还有 `{leaderPhone}`，Mock 没有
   - `SHUTDOWN` 种子有 `{endTime}`，`FROST` 种子有 `{stationName}` `{tgSet}`，Mock 文案都少了
   点选目录填变量再发送，真实模板占位符会原样发出。计划允许 Mock 目录，但内容应与种子对齐，否则「模板管理页」联调必踩坑。

3. 【`src/python/routes_sms.py:37-44` + `api_send:71-73`】`phones` 无数量上限。`send_sms` 对失败号同步重试（最多 3 次，间隔 1s+2s），前端 `http` 超时 15s。5 个失败号就可能把 HTTP 拖死，大批量时更明显。建议限制单次号码数（例如 20，对齐日限额语义），超限 40001。

4. 【`web/src/pages/sms/TemplateManage.vue:36` / `:167-183`】模板编码是自由输入，变量区绑定的是 `selected` 目录项。改编码不点选时，会用旧模板的 `vars` 去发新 `templateCode`（例如目录停在 `ALARM_RED`，输入改成 `PUBLIC`）。建议输入变更时同步 `selected`，或发送前按当前编码匹配目录。

5. 【`src/python/routes_sms.py:18-20` / `web/src/pages/sms/TemplateManage.vue:82-94`】记录查询未带 `error_msg` / `content`。状态=失败/限流时，页面只有空回执，调度看不到原因。计划 SELECT 可扩一列 `error_msg`，成本低。

6. 【`tests/test_sms_routes.py`】`templateCode` 超长、`vars` 非 dict、`batchId` 超长、非法手机号仍 200——代码有分支，无独立单测（自验证已承认前三项）。建议补这几条，避免回归时校验被改松。

---

## 🔵 疑问确认

1. 【`web/src/mock/sms.mock.ts` / 计划 Step 6】模板列表有意只走 Mock、不做 `GET /api/sms/templates`？`routes_sms.py` 是本 Task 独占文件，加只读目录接口并不越界。若确认本阶段只做发送台，请在回复里写明，避免被当成漏做「模板管理」。

2. 【`src/python/routes_sms.py:53-62`】日志字段用 camelCase，计划 snippet 是 raw 列名。与预警列表一致，前端也对。确认 Dev-1 公众服务按 `phoneMasked`/`batchId` 解析，而不是 `phone_masked`。

3. 【`src/python/routes_sms.py:74-76`】`send_sms` 对单号失败仍返回 `batchId`（Task 3 契约），HTTP 一律 `ok`。网关/限流失败要调用方再查 `/sms/log`。是否接受「提交成功 ≠ 送达」？错误码表有 50003，本层未用。

4. 【`snapshots/role-a/progress.md:10`】自验证正文写 HEAD `beb2dc1`，实际分支 HEAD 是随后的 `e4b5860`。`dev-record-a.md` commit 表也没记 `e4b5860`。无功能影响，合入前可补一行。

5. 【合入过程】`snapshots/role-a/*` 与 `master` 上已合入分支的快照会冲突。与 Task 2/3/6/8 相同，合入时保留本分支 Task 4 记录或以 `docs/` 审查报告为准。

---

## 审查结论

✅ 通过（建议处理 🟡 后再合入，不强制二次审查；若开发窗口改了 🟡 中的 1–3，可再走一轮快速确认）

计划功能已齐，边界守住，测试与类型检查当场通过。剩余是校验完整性和 Mock/种子一致性，不是契约缺失或假成功。
