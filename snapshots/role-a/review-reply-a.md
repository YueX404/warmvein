# Task-1 Code Review 回复

审查来源：`docs/审查报告-Dev-2-task1-alarm-engine.md`  
处理分支：`dev-2/feature/task1-alarm-engine`

## P1 阻断（已修）

| 编号 | 处理 |
|---|---|
| P1-1 | 抽出 `handle_alarm`；`consume()` 内 JSON 解码与处理包在 try/except，单条失败只打日志。 |
| P1-2 | **未按「先 INSERT 再 SET」字面实现。** 并发下先写库会产生重复行。改为 `SET NX EX 300` 占窗，INSERT 失败则 `DELETE` key，避免 300 秒黑洞。 |
| P1-3 | 增加 `__main__`。启动：在 `src/python` 下执行 `python -m consumers.alarm_consumer`。 |

## P2（已修）

| 编号 | 处理 |
|---|---|
| P2-1 | bootstrap 改为 `settings.KAFKA_BOOTSTRAP_SERVERS`。 |
| P2-2 | 模块级复用 `_sms_producer`，进程退出 `close_producer()`；`send().get(timeout=10)` 失败由 `handle_alarm` 记日志。 |
| P2-3 | 与 P1-2 同一门闩：`SET NX EX 300`。 |
| P2-4 | Kafka 词表保持 `frost` 等；入库 `to_schema_type`：frost→freeze、imbalance→balance、steal→theft，其余无 schema 对应的进 `other`。 |
| P2-5 | `_parse_alarm` 校验 `station_id` 可转 int、`alarmType` 为已知非空字符串。 |
| P2-6 | `handle_alarm` 可注入 Redis / Session / publish；单测覆盖 skip / dedup / 入库映射 / DB 失败释放锁 / SMS 失败。 |

## P3

| 编号 | 处理 |
|---|---|
| P3-1 | 已从 `alarm_engine` 删除未使用的 `redis_client` import。 |
| P3-2 | `auto_offset_reset="earliest"`，与 `.env.example` 对齐。 |
| P3-3 | 增加 `DEDUP_WINDOW_SEC` 与 skip/dedup/insert/sms 日志。 |
| P3-4 | 进度快照改为当前 HEAD。 |

## 计划缺口（保留，不在本轮改算法）

- `judge_level` 仍按类型表覆盖数字 `level`（计划 snippet 如此）。冻堵字符串 `low/medium/high` 走 `risk_level_from_frost`。
- 类型表最小为 2，蓝色（1）不会从查表产生。
- `root_cause` 仍存 Kafka `alarmType`。
- FR-4.1.1 阈值/规则引擎另开任务。

---

## 二次审查（`docs/二次审查报告-Dev-2-task1-alarm-engine.md`）

| 编号 | 处理 |
|---|---|
| P2-R1 | `enable_auto_commit=False`。抽出 `dispatch_record`：仅 `skip`/`dedup`/`ok` 时 `commit()`；`error` 不提交，退避 2s 后重试同一条。无法解码的报文当 `skip` 提交，避免毒消息堵分区。 |
| P3-R1 | 仅 `alarm_type == "frost"` 且 `level` 为字符串时走 `risk_level_from_frost`。 |
| P3-R2 | 开发记录 commit 表补齐。 |
| P3-R3 | 接受：kill -9 可能留下最多 300s 窗口。 |
