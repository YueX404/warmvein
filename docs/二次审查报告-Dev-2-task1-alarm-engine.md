# Dev-2 Task 1 二次审查报告

> **审查日期：** 2026-09-01  
> **审查轮次：** 第 2 轮（对照首轮报告与修复提交）  
> **分支：** `dev-2/feature/task1-alarm-engine`  
> **对照基线：** `master` `d1c7f15` → 当前 HEAD `d550e2c`  
> **首轮审查 HEAD：** `eb843b4`  
> **本轮修复提交：** `8ff6fb3` `fix(task-1): review反馈 - 消费循环隔离、去重回滚与类型映射`；`d550e2c` `docs(task-1): 审查回复，阶段改为待二次审查`  
> **首轮报告：** `docs/审查报告-Dev-2-task1-alarm-engine.md`  
> **作者回复：** `snapshots/role-a/review-reply-a.md`  
> **审查对象：** `src/python/services/alarm_engine.py`、`src/python/consumers/alarm_consumer.py`、`tests/test_alarm_engine.py`

---

## 一、总体结论

**首轮 P1 全部关闭，P2/P3 均已按回复落地。建议修复 1 个新暴露的 P2 后再合入。**

相对首轮「暂不建议合入」，本轮代码已经可以作为一个可运行的预警消费进程：异常隔离、`SET NX` 原子占窗、入库失败释锁、schema 类型映射、`settings.KAFKA_BOOTSTRAP_SERVERS`、Producer 复用、`__main__` 入口、handle 路径单测均已具备。

本轮新问题来自「不崩溃」与「默认自动提交」的组合：INSERT 失败时 Redis 锁已释放，但 Kafka offset 仍会前进，**原消息不会被再投递**。这不是首轮 P1-2 的残留黑洞，而是修复 P1-1 后新露出的丢数路径。

当场验证：`pytest tests/ -v` → **19 passed**（14 条本 Task + 5 条脚手架）。  
模块导入：在 `src/python` 下 `from consumers.alarm_consumer import consume` 成功。

---

## 二、首轮问题关闭表

| ID | 首轮结论 | 本轮状态 | 证据 |
|---|---|---|---|
| P1-1 | 单条坏消息打挂进程 | **已关闭** | `alarm_consumer.py:90-95`：JSON 解码与 `handle_alarm` 包在 try/except |
| P1-2 | Redis 先 SET 再 INSERT，失败静默丢 300s | **已关闭（接受偏差）** | `alarm_consumer.py:66-74`：`SET NX EX 300` 占窗，INSERT 失败 `DELETE` key。并发下比「先 INSERT 再 SET」更安全，且关掉了 300s 黑洞 |
| P1-3 | 无进程入口 | **已关闭** | `alarm_consumer.py:98-103`；文档约定 `cd src/python && python -m consumers.alarm_consumer` |
| P2-1 | 读 `KAFKA_BOOTSTRAP` | **已关闭** | consumer / producer 均用 `settings.KAFKA_BOOTSTRAP_SERVERS` |
| P2-2 | 每条告警新建 Producer | **已关闭** | 模块级 `_sms_producer`；`__main__` 的 `finally` 调用 `close_producer()`；`send().get(timeout=10)` |
| P2-3 | GET+SET 非原子 | **已关闭** | `cache.set(..., nx=True, ex=DEDUP_WINDOW_SEC)`。redis-py 在 NX 未命中时返回 `None`；`if not cache.set(...)` 把 `None`/`False` 都当未占到锁，行为正确 |
| P2-4 | `biz_alarm.type` 词表不一致 | **已关闭** | `to_schema_type`：frost→freeze、imbalance→balance、steal→theft；入库写 `schema_type` |
| P2-5 | 报文未校验 | **已关闭** | `_parse_alarm`：`station_id` 可转 int，`alarmType` 必须在 `KNOWN_ALARM_TYPES` |
| P2-6 | 测试不覆盖运行路径 | **已关闭** | skip / dedup / 入库映射 / DB 失败释锁 / SMS 失败 / 字符串 level |
| P3-1 | 未使用的 `redis_client` import | **已关闭** | `alarm_engine.py` 已删除 |
| P3-2 | `auto_offset_reset="latest"` | **已关闭** | 改为 `"earliest"` |
| P3-3 | 魔法 300、无日志 | **已关闭** | `DEDUP_WINDOW_SEC`；skip / dedup / insert 失败 / SMS 失败均有日志 |
| P3-4 | 快照与 HEAD 不一致 | **部分关闭** | `progress.md` 已改为待二次审查；`dev-record-a.md` 的 commit 表仍停在 `eb843b4`，未列 `8ff6fb3` / `d550e2c` |

### 关于 P1-2 偏差

作者未按首轮「先 INSERT 再 SET」字面实现，改为 **SET NX 占窗 + INSERT 失败 DELETE**。二次审查同意该偏差：先写库无法原子互斥，两个 worker 仍会插出重复行。当前方案同时解决 P1-2 与 P2-3。

---

## 三、本轮新问题

### P2 — 建议合入前修复

#### P2-R1 入库失败返回 `"error"` 且不抛，Kafka 自动提交会丢掉该条告警

- **位置：** `src/python/consumers/alarm_consumer.py:69-75`、`:83-95`
- **问题：** `handle_alarm` 在 INSERT 失败时释放 Redis key 并 `return "error"`，不向上抛。`consume()` 不检查返回值。`KafkaConsumer` 未设置 `enable_auto_commit=False`，kafka-python 默认为 `True`（约 5s / 下次 poll 提交上一批 offset）。
- **为何是新问题：** 首轮 P1-1 要求「单条失败不要打挂进程」。修完之后进程会继续跑，offset 一定前进。P1-2 的 DELETE 本意是让**同一条**告警能重试；Kafka 侧却已经确认消费。MySQL 短暂不可用时：锁释放了，消息也没了。后续只有 Dev-1 再发同站同类型才会入库，原事件丢失。
- **对比首轮：** 当时 INSERT 失败会把 `consume()` 打挂；若自动提交尚未刷出，重启反而可能重投。可用性修上去之后，至少一次投递语义变差。
- **修复：** `enable_auto_commit=False`；仅当 `handle_alarm` 返回 `skip` / `dedup` / `ok` 时 `consumer.commit()`；返回 `error` 时不提交，可短暂退避后重试同一条。不要把 `"error"` 当成循环成功。

### P3 — 可记 follow-up

#### P3-R1 非 frost 的字符串 `level` 一律走 `risk_level_from_frost`

- **位置：** `src/python/consumers/alarm_consumer.py:33-36`
- **问题：** `isinstance(raw_level, str)` 时不看 `alarm_type`。`corrosion` + `"high"` 会变成 4，而不是类型表的 2。数字 `level` 仍被 `judge_level` 忽略（计划缺口，不重开为必须修）。
- **处理：** 若约定只有冻堵发 `low|medium|high`，书面确认即可；否则仅在 `alarm_type == "frost"` 时走该映射。

#### P3-R2 开发记录 commit 表未跟上 HEAD

- **位置：** `snapshots/role-a/dev-record-a.md` 提交表
- **问题：** 仍只列 `c7a7b42`、`eb843b4`。无功能影响。

#### P3-R3 进程被 kill -9 时 SET NX 后、INSERT 前会留下最多 300s 窗口

- **位置：** `alarm_consumer.py:66-70`
- **问题：** 正常异常路径已 DELETE；硬杀进程无法执行 DELETE。可接受的残留，比原 300s 黑洞 + 无法区分成败要好。

---

## 四、计划缺口（仍接受，不作为本轮阻断）

作者在回复中明确保留，二次审查不再列为必须修复：

| 项 | 现状 |
|---|---|
| `judge_level` 忽略数字 `value` | Dev-1 的 `frost` + `level=3` 仍会被写成 4 |
| 蓝色（level=1） | 静态表最小为 2 |
| `root_cause` | 仍存 Kafka `alarmType`，不是根因标签 |
| FR-4.1.1 阈值/规则引擎 | 另开任务 |

---

## 五、做得好的地方（本轮修复）

- 独占文件边界仍守住，F0 冻结文件未动。
- 抽出可注入的 `handle_alarm`，单测真正打到降噪、映射和失败回滚，而不是只测查表。
- Kafka 契约未变：消费 `HEAT_ALARM_TOPIC`，投递 `SMS_NOTIFY_TOPIC`，不 import 短信服务。
- SMS 失败只记日志、保留行和窗口，符合首轮「不要用 Redis 挡住补发」的要求。
- `if not cache.set(nx=True)` 与 redis-py「NX 失败返回 `None`」兼容，假 Redis 返回 `False` 时同样正确。

---

## 六、测试证据

```
pytest tests/ -v
======================== 19 passed, 1 warning in 0.84s ========================
```

本 Task 新增/保留用例：查表 4 条、schema 映射、缺站号/缺类型/未知类型 skip、SET NX 去重、入库 freeze 并投递、DB 失败释锁、SMS 失败保留、字符串 `high`、`__main__` 守卫。

未覆盖（非阻断）：Kafka offset 在 `"error"` 时是否提交；非 frost 字符串 level；TTL 到期后 NX 可再次占窗。

---

## 七、评估

| 项 | 结论 |
|---|---|
| **是否可合入** | 建议先修 P2-R1 再合；若书面接受「DB 抖动丢单条、靠上游重发」可合入并开 follow-up |
| **首轮 P1** | 全部关闭 |
| **P1-2 偏差** | 接受 |
| **生产就绪** | 接近。缺手动提交策略时，瞬时 DB 故障会丢告警 |

**理由：** 首轮阻断项已落地，消费进程可启动、可测、词表与配置契约已对齐。合入前应补上「入库失败不提交 Kafka offset」，否则释锁没有对应的重投，P1-2 的重试意图在 Kafka 侧落空。
