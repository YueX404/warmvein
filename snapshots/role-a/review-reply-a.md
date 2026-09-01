# Task-4 审查反馈处理记录

审查来源：`snapshots/role-a/review-feedback-a.md`  
处理分支：`dev-2/feature/task4-sms-api`  
处理时间：2026-09-01

## 🔴 阻断性问题

无。

## 🟡 改进建议

| 编号 | 处理 | 说明 |
|---|---|---|
| 1 | 修复 | `_parse_send` 用 `sms_service.is_mobile`（11 位数字）。短号、非数字、混入非法号一律 40001，不再 `ok` 后被服务层 skip。 |
| 2 | 修复 | Mock 模板与 `heat_init.sql` 种子对齐：补齐 BLUE/YELLOW/ORANGE/PUBLIC；RED 含 `{leaderPhone}`；SHUTDOWN 含 `{endTime}`；FROST 含 `{stationName}` `{tgSet}`。 |
| 3 | 修复 | 单次 `phones` 上限 20，超限 40001，避免同步重试顶满 15s。 |
| 4 | 修复 | `watch(templateCode)`：按当前编码匹配目录并切换 `selected` / 变量区，避免旧 vars 发到新模板。 |
| 5 | 修复 | 日志 SELECT 增加 `error_msg`、`content`；响应 `errorMsg`/`content`；表格增加「失败原因」。 |
| 6 | 修复 | 补单测：短号、非数字、超量、templateCode 超长、vars 非 dict、batchId 超长、errorMsg。 |

## 🔵 疑问确认

| 编号 | 结论 |
|---|---|
| 1 | **本阶段模板列表只走 Mock，不加 `GET /api/sms/templates`。** 页面是发送台：目录点选填变量、手动发送、查记录。模板 CRUD / 库内目录接口不在本 Task 计划 Step 6。Mock 文案已与种子对齐。 |
| 2 | **锁定 camelCase。** Dev-1 公众服务按 `batchId` / `phoneMasked` / `createdAt` 解析。与预警列表一致。`POST /sms/send` 成功体本来就是 `{batchId}`。 |
| 3 | **接受「提交成功 ≠ 送达」。** `send_sms` 对单号失败仍返回 `batchId`（Task 3 契约）。HTTP 层 `ok` 表示批次已受理；网关/限流看 `/sms/log` 的 `status`/`errorMsg`。50003 留给网关适配器抛错且整批无法受理时用，本层不把部分失败升成 50003。 |
| 4 | 修复：进度与 commit 表补到当前 HEAD。 |
| 5 | 保留。合入时 `snapshots/role-a/*` 以本分支 Task 4 记录为准，或以 `docs/` 审查报告为准，与 Task 2/3/6/8 相同。 |

## 验证

- `pytest tests/test_sms_routes.py tests/test_sms_service.py tests/test_scaffold.py -v` → 43 passed
- `npx vue-tsc --noEmit`（`web/`）→ exit 0

审查修复提交：`86727da`。文档提交：`9176680`、`f48a753`。

## 二次审查（2026-09-01）

来源：`snapshots/role-a/review-feedback-a.md`（二次）。结论：✅ 通过，建议合入。首轮 🟡 1–6 全部关闭。

| 编号 | 处理 | 说明 |
|---|---|---|
| 🔵1 | 修复 | Commit 表补 `f48a753`。 |
| 🔵2 | 保留 | 蓝/黄/橙/公众目录圆点配色 follow-up，不在合入前改。 |
| 🔵3 | 保留 | 发送前前端不预拦非法号/超量；后端 40001 + 拦截器，不假成功。 |

