# Task-4 Code Review 反馈（二次审查）

审查分支：`dev-2/feature/task4-sms-api`  
审查 commit：`f48a753`（首轮 HEAD `e4b5860`；修复 `86727da`；回复文档 `9176680` `f48a753`）  
审查时间：2026-09-01  
对照：首轮 `snapshots/role-a/review-feedback-a.md`（审查前版本）、`snapshots/role-a/review-reply-a.md`  
工作区：`D:\YY\.worktrees\dev-2-feature-task4-sms-api`

审查只读，未改实现代码、未提交。

当场验证：

- `python -m pytest tests/test_sms_routes.py tests/test_sms_service.py tests/test_scaffold.py -v` → **43 passed**
- `npx vue-tsc --noEmit`（`web/`）→ **exit 0**

阶段校验：`progress.md` 为「修复完成，待二次审查」，工作区审查前干净。

---

## 一、总体结论

**通过，建议合入。**

首轮 6 条 🟡 均已落地，🔵 书面答复可接受。本轮无新阻断项。相对 `master` 仍只动 Task 4 独占文件与角色 A 快照，未改 `sms_service.py` / `main.py` / `heat_init.sql`。

---

## 二、首轮意见关闭情况

| 编号 | 首轮 | 二次结论 | 证据 |
|---|---|---|---|
| 🟡1 | 非法号仍 200 + batchId | **关闭** | `_parse_send` 用 `sms_service.is_mobile`；`test_sms_send_rejects_short_phone` / `non_digit_phone` PASSED |
| 🟡2 | Mock 与种子不一致 | **关闭** | 7 条模板文案/变量与 `heat_init.sql` 种子逐字对齐 |
| 🟡3 | phones 无上限 | **关闭** | `_PHONE_BATCH_MAX = 20`；21 个合法号 → 40001 |
| 🟡4 | 手改编码仍用旧 vars | **关闭** | `watch(templateCode)` 按编码匹配目录并清空变量 |
| 🟡5 | 记录无失败原因 | **关闭** | SELECT `error_msg`/`content`；响应 `errorMsg`；表格「失败原因」 |
| 🟡6 | 缺边界单测 | **关闭** | 路由测试由 10 条增至 17 条，当场全绿 |
| 🔵1 | 是否只做 Mock 目录 | **接受** | 本阶段发送台，不加 `GET /templates` |
| 🔵2 | camelCase 契约 | **接受** | 锁定 `batchId` / `phoneMasked` / `createdAt` |
| 🔵3 | 提交成功 ≠ 送达 | **接受** | HTTP `ok` = 批次受理；送达看 log；不滥用 50003 |
| 🔵4 | 快照 HEAD 滞后 | **关闭** | 已补到修复提交；后续又多一次文档 commit，见下 |
| 🔵5 | 快照合入冲突 | **保留** | 与 Task 2/3/6/8 相同，合入时以本分支为准 |

---

## 🔴 阻断性问题（必须修改）

无。

---

## 🟡 改进建议

无（首轮 P2 已关闭）。

---

## 🔵 疑问确认

1. 【`dev-record-a.md`】Commit 表缺最后一次 `f48a753`（补齐审查修复记录），无功能影响。
2. 【`TemplateManage.vue:322-324`】蓝/黄/橙/公众目录圆点仍走默认灰色，仅红/停暖/冻堵有配色。纯展示，可 follow-up。
3. 【`TemplateManage.vue:190-207`】发送前前端仍不拦非法号/超过 20 个；后端会 40001，拦截器报错，不再假成功。可保留。

---

## 审查结论

✅ 通过，建议合入

首轮 🟡 已关闭，本轮无新阻断项。可将 `progress.md` 标为审查通过，进入收尾：手动 push 分支、提 PR。
