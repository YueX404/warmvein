# Dev-2 Task 3 二次审查报告

> **审查日期：** 2026-09-01  
> **审查轮次：** 第 2 轮（对照首轮报告与修复提交）  
> **分支：** `dev-2/feature/task3-sms-core`  
> **对照基线：** `master` `ccaa50c` → 当前 HEAD `038ead0`  
> **首轮审查 HEAD：** `74d361a`  
> **本轮修复提交：** `49d8f96` `fix(task-3): review反馈 - 发送失败不提交 offset 并重试`；`42e3e0c` `fix(task-3): review反馈 - earliest/leaderPhone/网关异常重试`；`038ead0` `docs(task-3): 审查回复，阶段改为待二次审查`  
> **首轮报告：** `docs/审查报告-Dev-2-task3-sms-core.md`  
> **作者回复：** `snapshots/role-a/review-reply-a.md`  
> **审查对象：** `src/python/services/sms_service.py`、`src/python/consumers/sms_consumer.py`、`tests/test_sms_service.py`

审查只读，未改实现代码、未提交。进度快照为「修复完成，待二次审查」，工作区干净。

---

## 一、总体结论

**可以合入。** 首轮 P1 已关闭；P2-1～P2-4 均已按回复落地；P3-1 phone 契约已书面约定。

相对首轮「暂不建议合入」，本轮已经是可运行的短信消费进程：`dispatch_record` 仅在 `skip`/`ok` 提交 offset，`error`（含 `send_sms` 抛错）不提交并重试同一条；`auto_offset_reset="earliest"`；红色模板 `{leaderPhone}` 有报文值或「请登录平台」兜底；`_do_send` 抛错进入三次退避并落 `error_msg`。

当场验证：`pytest tests/ -v` → **44 passed**（本 Task 21 + Task 1 18 + 脚手架 5）。

本轮剩余均为 P3，不构成合入阻断。已知空转（Task 1 报文无 `phone` → skip）按作者书面约定接受，不重开为必须修。

---

## 二、首轮问题关闭表

| ID | 首轮结论 | 本轮状态 | 证据 |
|---|---|---|---|
| P1-1 | 发送失败仍无条件 `commit()`，短信永久丢失 | **已关闭** | `sms_consumer.py:19-20,51-80`：`COMMIT_STATUSES={skip,ok}`；`error` 不提交，`sleep(RETRY_BACKOFF_SEC)` 后重试同一条。毒 JSON skip+commit。测试：`test_dispatch_commits_on_ok_and_skip`、`test_dispatch_retries_error_then_commits`、`test_dispatch_send_raise_does_not_commit_until_ok`、`test_dispatch_commits_undecodable_payload` |
| P2-1 | `auto_offset_reset="latest"` 新消费组丢积压 | **已关闭** | `sms_consumer.py:76` 改为 `"earliest"`；`test_consumer_has_main_guard` 断言该字符串 |
| P2-2 | `ALARM_RED` 的 `{leaderPhone}` 原样发出 | **已关闭** | `handle_notify` vars：`msg.get("leaderPhone") or "请登录平台"`。`test_handle_red_fills_leader_phone_fallback`、`test_handle_red_uses_leader_phone_from_payload` |
| P2-3 | 消费循环 commit/重试无测试 | **已关闭** | 与 P1-1 同一组 `dispatch_record` 四条单测 |
| P2-4 | `_do_send` 抛异常不重试、不写失败日志 | **已关闭** | `sms_service.py:116-133`：try/except 视为 `success=False`，三次仍失败 `status=3` 且 `error_msg=type(exc).__name__`。`test_send_sms_retries_when_do_send_raises`、`test_send_sms_logs_fail_when_do_send_always_raises` |
| P3-1 | Task 1 报文无 phone，消费端全部 skip | **关闭（书面约定）** | 回复：phone 由上游保证，本消费端不查库补号；当前预警→短信空转是已知事实，不是短信服务故障 |
| P3-2 | 缺 `stationName` 回落 `station_id` | **关闭（接受）** | 回复：上游后续补站名 |
| P3-3 | 限流 GET+INCR 非原子、TTL 滑动 24h | **关闭（follow-up）** | 本轮不改 Redis 脚本 |
| P3-4 | `error_msg` 未写等 | **部分关闭** | `error_msg` 已随 P2-4 写入；`batch_id` 同秒混批、`SMS_PROVIDER` 未走 settings、停用模板仍可发、Aliyun stub、冻堵走 `ALARM_RED` 仍接受 |

P1-1 实现要点核对：

- `KafkaConsumer(..., enable_auto_commit=False)` 仍在。
- 仅 `skip`/`ok` 调用 `consumer.commit()`。
- `"error"` 不提交，退避 2s 后重试**同一条** `msg`。
- `handle` 抛 `RuntimeError`（模拟 DB/网关）走 `"error"`，有单测锁住。
- 无法解码的报文当 `skip` 并提交，避免毒消息堵分区。

与 Task 1 相同：kafka-python 预取批次不会被一次无参 `commit()` 整批确认；`for msg in consumer` 一次处理一条时，提交的是当前条的下一 offset。

---

## 三、本轮问题

### P3 — 不阻断合入

#### P3-R1 `handle()` 的 `TypeError` 被当成 skip 并提交

- **位置：** `src/python/consumers/sms_consumer.py:55-60`

```python
        try:
            payload = json.loads(msg.value.decode())
            result = handle(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            logger.exception("skip undecodable sms notify")
            result = "skip"
```

- **问题：** 与已合入 Task 1 `dispatch_record`（三次审查 P3-T1）同一写法。`TypeError` 与解码异常写在同一个 `except`，且包住了 `handle()`。`.decode()` 之后 `json.loads` 吃的是 `str`，几乎不会再抛 `TypeError`；该分支实际接到的是 `handle()` / `send_sms` 冒出来的 `TypeError`（例如 Redis 返回不可 `int()` 的类型）。随后进入 `COMMIT_STATUSES` → `commit()`，offset 前进，原短信请求不再投递。
- **为何不升 P2：** 当前 `_do_send` 异常已在服务层吃掉；模板缺失是 `ValueError` → `"error"` 重试。现网路径上 `TypeError` 冒到 `dispatch_record` 的概率低。但这是分类错误，后续改 `handle`/`send_sms` 时会变成静默丢数。
- **修复（可选）：** 解码与 `handle` 分开 try。解码失败仍 skip+commit；`handle` 的任意异常（含 `TypeError`）走 `"error"` 不提交。可补一条「`handle` 抛 `TypeError` → 不 commit」。不修也可合入，与 Task 1 已接受的残留一致。

#### P3-R2 开发记录 commit 表仍落后 HEAD

- **位置：** `snapshots/role-a/dev-record-a.md`、`snapshots/role-a/review-reply-a.md` 提交表
- **问题：** 两表都列到 `42e3e0c`，缺本轮文档提交 `038ead0`。无运行影响。

#### P3-R3 网关已成功但落库失败时，Kafka 重试会导致重复短信

- **位置：** `sms_service.py:121-133` + `dispatch_record` 的 `"error"` 重试
- **问题：** `_do_send` 成功后先 `incr`，再 `_write_log`。若 INSERT 抛错，异常冒到 `dispatch_record` → 不提交 → 重试同一条 → 用户可能再收到一条。这是 P1-1「失败不丢 Kafka」换成 at-least-once 后的代价。
- **处理：** 接受。不要为了去重改回失败也 commit。后续若要幂等，用网关回执 / `batch_id+phone` 去重，不在本轮改。

---

## 四、已核对、不作为缺陷重开

| 项 | 结论 |
|---|---|
| P3-1 phone 契约 | 作者明确：缺合法 11 位号 skip；补号不在本 Task。合入后预警→短信空转，直到上游带 `phone`。联调时不要据此判短信服务故障。 |
| 网关三次失败后 commit | `_send_one` 穷尽重试后写 `status=3` 并返回，`handle_notify` 仍 `"ok"`。这是「最多重试 3 次」而不是「网关宕机堵死分区」。与计划一致，正确。 |
| 持久 DB 宕机 HOL | 模板查询 / 落库抛错走 `"error"` + 2s 退避，单分区会堵住直到库恢复。与 Task 1 P2-R1 同一选择，不要用「失败也 commit」回退。 |
| F0 边界 | vs `master` 仅独占三文件 + 角色 A 快照 + 本审查报告；未改 `heat_init.sql` / `main.py` / `kafka_topics.py` / 前端。无 `ALARM_NOTICE`。 |
| `leaderPhone` 不查 `md_organization` | 回复已说明。兜底文案「请登录平台」满足「不要把占位符发给用户」。 |

---

## 五、测试核对

| 首轮要求 | 本轮 |
|---|---|
| ok/skip 提交 | `test_dispatch_commits_on_ok_and_skip` |
| error 不提交、重试后提交 | `test_dispatch_retries_error_then_commits` |
| `send_sms` 抛错不提交 | `test_dispatch_send_raise_does_not_commit_until_ok`（`RuntimeError`） |
| 坏 JSON skip+commit | `test_dispatch_commits_undecodable_payload` |
| 红色模板无 `{leaderPhone}` | `test_handle_red_fills_leader_phone_fallback` |
| `_do_send` 抛错重试/失败落库 | `test_send_sms_retries_when_do_send_raises`、`test_send_sms_logs_fail_when_do_send_always_raises` |
| `handle` 抛 `TypeError` 不 commit | **无（P3-R1）** |

---

## 审查结论

**✅ 通过，可以合入。**

不要求再开一轮修复。P3-R1 与 Task 1 已合入代码同源，可在后续 chore 里与预警消费一并拆开解码/`handle` 的 try。P3-R2 补一行 commit 即可。P3-R3 与 P3-1 空转保持文档约定即可。
