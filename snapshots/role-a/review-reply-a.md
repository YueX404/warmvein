# Task-3 Code Review 回复

审查来源：`docs/审查报告-Dev-2-task3-sms-core.md`  
处理分支：`dev-2/feature/task3-sms-core`

## P1 阻断（已修）

| 编号 | 处理 |
|---|---|
| P1-1 | 抽出 `dispatch_record`：仅 `skip`/`ok` 时 `commit()`；`error`（含 `send_sms` 抛错）不提交，退避 2s 后重试同一条。无法解码的报文当 `skip` 提交，避免毒消息堵分区。测试覆盖 ok/skip 提交、error 重试、抛错不提交、坏 JSON skip+commit。 |

## P2（已修）

| 编号 | 处理 |
|---|---|
| P2-1 | `auto_offset_reset="earliest"`，与 Task 1 和 `.env.example` 对齐。 |
| P2-2 | `handle_notify` 的 vars 增加 `leaderPhone`：报文字段优先，缺省填「请登录平台」，红色模板不再留下 `{leaderPhone}`。不在本 Task 查 `md_organization`。 |
| P2-3 | 与 P1-1 同一组 `dispatch_record` 单测。 |
| P2-4 | `_do_send` 包在 try 中，异常视为 `success=False` 进入指数退避；三次仍失败落 `status=3`，`error_msg` 记异常类型。 |

## P3 / 🔵

| 编号 | 处理 |
|---|---|
| P3-1 **phone 契约** | **缺合法 11 位手机号则 skip。phone 由上游保证，本消费端不查库补号。** 已合入的 Task 1 `publish_sms` 当前不带 `phone`，本 Task 合入后预警→短信会 skip，这是已知空转，不是短信服务故障。补号属于 Task 1 follow-up 或后续按 `station_id` 查责任人/订阅的独立任务。 |
| P3-2 | 接受：缺 `stationName` 时回落 `station_id`。上游后续补站名。 |
| P3-3 | 接受 follow-up：限流非原子、TTL 滑动 24h。本轮不改 Redis 脚本。 |
| P3-4 | `error_msg` 已随 P2-4 写入。`batch_id` 同秒混批、`get_sender` 未走 `settings.SMS_PROVIDER`、停用模板仍可发、Aliyun stub、冻堵走 `ALARM_RED` 而非 `FROST`：接受或记 follow-up，本轮不改。 |

---

## 二次审查（`docs/二次审查报告-Dev-2-task3-sms-core.md`）

结论：**✅ 通过，可以合入。** 首轮 P1/P2 全部关闭。本轮剩余 P3 不改代码。

| 编号 | 处理 |
|---|---|
| P3-R1 | **接受。** 与已合入 Task 1 `dispatch_record` 同源：`TypeError` 与解码写在同一 `except`。现网 `_do_send` 异常已在服务层消化，模板缺失是 `ValueError`→error 重试。后续 chore 与预警消费一并拆开解码/`handle` 的 try。 |
| P3-R2 | 提交表补 `038ead0`。 |
| P3-R3 | **接受。** 网关成功后落库失败会 at-least-once 重发。不去重、不改回失败也 commit。后续若要幂等，用回执或 `batch_id+phone`。 |

---

## Commit

| hash | message |
|---|---|
| `e5997b0` | `feat(sms): 短信网关适配/模板/脱敏/限流/重试` |
| `74d361a` | `docs(task-3): 补齐自验证快照，阶段标记为待审查` |
| `49d8f96` | `fix(task-3): review反馈 - 发送失败不提交 offset 并重试` |
| `42e3e0c` | `fix(task-3): review反馈 - earliest/leaderPhone/网关异常重试` |
| `038ead0` | `docs(task-3): 审查回复，阶段改为待二次审查` |
