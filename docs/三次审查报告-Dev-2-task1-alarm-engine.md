# Dev-2 Task 1 三次审查报告

> **审查日期：** 2026-09-01  
> **审查轮次：** 第 3 轮（对照二次审查报告与后续修复）  
> **分支：** `dev-2/feature/task1-alarm-engine`  
> **对照基线：** `master` `d1c7f15` → 当前 HEAD `9a86c0f`  
> **二次审查 HEAD：** `d550e2c`  
> **本轮修复提交：** `8bafbed` `fix(task-1): review反馈 - 入库失败不提交 offset 并重试`；`9a86c0f` `docs(task-1): 二次审查回复，阶段改为待复审`  
> **二次审查报告：** `docs/二次审查报告-Dev-2-task1-alarm-engine.md`  
> **作者回复：** `snapshots/role-a/review-reply-a.md`（二次审查一节）

---

## 一、总体结论

**可以合入。** 二次审查的阻断项 P2-R1 已按约定落地；P3-R1 已修；P3-R3 已书面接受。首轮 P1 仍全部关闭。

本轮剩余均为 P3：`dispatch_record` 把 `handle()` 抛出的 `TypeError` 误判为 skip 并提交；开发记录 commit 表仍落后 HEAD。不构成合入阻断。计划缺口（数字 `level` 被覆盖、无蓝色、根因标签）继续按约定不重开。

当场验证：`pytest tests/ -v` → **23 passed**。

---

## 二、关闭表（首轮 P1 + 二轮项）

| ID | 要求 | 本轮状态 | 证据 |
|---|---|---|---|
| P1-1 | 单条坏消息不打挂进程 | **仍关闭** | `dispatch_record` 逐条捕获；毒 JSON 当 skip |
| P1-2 | 入库失败不黑洞 300s | **仍关闭（偏差已接受）** | SET NX + INSERT 失败 DELETE |
| P1-3 | 进程入口 | **仍关闭** | `__main__`；`python -m consumers.alarm_consumer` |
| P2-R1 | `enable_auto_commit=False`；仅 skip/dedup/ok 提交；error 不提交并重试同一条 | **已关闭** | `alarm_consumer.py:21-22,86-115`；`test_dispatch_commits_on_ok_skip_dedup`、`test_dispatch_retries_error_then_commits` |
| P3-R1 | 非 frost 字符串 level 不走 `risk_level_from_frost` | **已关闭** | `alarm_consumer.py:36-39`；`test_handle_non_frost_string_level_uses_type_table`：`corrosion` + `"high"` → 2 |
| P3-R2 | 开发记录 commit 表跟上 HEAD | **仍开放** | 表补到 `d550e2c`，缺本轮 `8bafbed` / `9a86c0f` |
| P3-R3 | kill -9 留下最多 300s 窗口 | **关闭（接受）** | 作者二次审查回复明确接受 |

P2-R1 实现要点核对：

- `KafkaConsumer(..., enable_auto_commit=False)` 已设置。
- `COMMIT_STATUSES = {skip, dedup, ok}`，仅这些状态调用 `consumer.commit()`。
- `"error"` 不提交，`sleep(RETRY_BACKOFF_SEC)` 后重试**同一条** `msg`。
- 无法解码的报文当 `skip` 并提交，避免毒消息堵分区。

**kafka-python 预取批次不会被一次 `commit()` 整批确认。** 迭代器 `_message_generator_v2` 以 `poll(..., update_offsets=False)` 取批，每 yield 一条才把该分区 position 设为 `record.offset + 1`。无参 `commit()` 提交的是 `all_consumed_offsets()`（当前已 yield 的 position）。`for msg in consumer` 一次处理一条时，提交的是这一条的下一 offset，不是内存里剩余的预取记录。

---

## 三、本轮问题

### P3 — 不阻断合入

#### P3-T1 `handle()` 的 `TypeError` 被当成 skip 并提交

- **位置：** `src/python/consumers/alarm_consumer.py:90-95`

```python
        try:
            payload = json.loads(msg.value.decode())
            result = handle(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            logger.exception("skip undecodable alarm")
            result = "skip"
```

- **问题：** `TypeError` 与解码异常写在同一个 `except`，且包住了 `handle()`。`.decode()` 之后 `json.loads` 吃的是 `str`，几乎不会再抛 `TypeError`；该分支实际接到的是 `handle()` 冒出来的 `TypeError`。随后进入 `COMMIT_STATUSES` → `commit()`，offset 前进，原记录不再投递。
- **为何不升 P2：** 当前 `handle_alarm` 对 INSERT / SMS 已有 `except Exception`；Redis 宕机走 `ConnectionError` → `"error"` 重试。现网路径上 `TypeError` 冒到 `dispatch_record` 的概率低。但这是 `dispatch_record` 的分类错误，后续改 `handle` 时会变成静默丢数。
- **修复：** 解码与 `handle` 分开 try。解码失败仍 skip+commit；`handle` 的任意异常（含 `TypeError`）走 `"error"` 不提交。可补一条「`handle` 抛 `TypeError` → 不 commit」的测试。

#### P3-T2 开发记录 commit 表仍落后 HEAD（P3-R2 未关）

- **位置：** `snapshots/role-a/dev-record-a.md` 提交表
- **问题：** 仍只列到 `d550e2c`。本轮 `8bafbed`、`9a86c0f` 未入表。无运行影响。

---

## 四、已核对、不作为缺陷重开

| 项 | 结论 |
|---|---|
| 持久 DB 宕机 HOL | `"error"` 上 `while True` + 2s 退避，是 P2-R1 要求的「同一条重试」。单分区会堵住，直到库恢复。不要用「失败也 commit」来解。 |
| 心跳 / 离组 | 长时间不返回 `consume()` 的 poll 时，超过 `max_poll_interval_ms`（默认 300s）可能被踢出组。恢复后 `commit()` 若因已离组失败，该调用在 try 外会打挂进程；重启后 SET NX 走 dedup，一般不会重复行。可记运维 follow-up。 |
| 计划缺口 | `judge_level` 忽略数字 `value`、无蓝色 1、`root_cause` 存 Kafka 类型、FR-4.1.1 规则引擎 — 仍按约定保留。 |

---

## 五、做得好的地方（本轮）

- P2-R1 按二次审查字面落地，且抽出 `dispatch_record` 后 offset 策略可单测。
- 测试覆盖：ok/skip/dedup 提交、error 先不提交再提交、坏 JSON skip 并提交、非 frost 字符串 level 走类型表。
- 毒消息（无法解码）选择 skip+commit，与「入库失败不提交」区分正确。
- F0 冻结边界仍守住。

---

## 六、测试证据

```
pytest tests/ -v
======================== 23 passed, 1 warning in 0.84s ========================
```

本 Task 18 条 + 脚手架 5 条。与 `progress.md` 声称的 23 passed 一致。

未覆盖（P3-T1）：`handle` 抛 `TypeError` 时不得 `commit()`。

---

## 七、评估

| 项 | 结论 |
|---|---|
| **是否可合入** | **可以合入** |
| **首轮 P1** | 全部关闭 |
| **二轮 P2-R1** | 已关闭 |
| **剩余** | P3-T1（TypeError 分类）、P3-T2（快照 commit 表） |
| **生产就绪** | 对本 Task 范围：是。算法级四级判定仍属计划外 follow-up |

**理由：** 二次审查要求的「入库失败不推进 offset、同一条退避重试」已实现并有单测。kafka-python 迭代器下手动 `commit()` 不会误提交预取整批。剩余 TypeError 分类是防御性缺口，当前 `handle_alarm` 主路径被内层 except 兜住，不阻断合入；建议合入前顺手拆开 try，或记 follow-up。
