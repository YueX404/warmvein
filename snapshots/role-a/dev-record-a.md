# Task-1 开发记录（角色A）

**PR / Task：** Dev-2 Task 1 预警判定与降噪聚合  
**分支：** `dev-2/feature/task1-alarm-engine`  
**需求：** `docs/superpowers/plans/Dev-2-task1-alarm-engine.md`

## 测试用例

| 用例 | 行为 |
|---|---|
| `test_judge_frost_red` | frost → 4 |
| `test_judge_corrosion_yellow` | corrosion → 2 |
| `test_dedup_key_stable` | key 稳定 |
| `test_frost_high` | high → 4 |
| `test_schema_type_frost_maps_freeze` | frost/imbalance/steal 入库词表 |
| `test_handle_skips_missing_station_id` | 缺站号 skip |
| `test_handle_skips_blank_alarm_type` | 缺类型 skip |
| `test_handle_skips_unknown_alarm_type` | 未知类型 skip |
| `test_handle_dedup_when_nx_fails` | SET NX 失败则跳过 |
| `test_handle_inserts_schema_type_and_publishes` | 入库 freeze 并投递短信 |
| `test_handle_db_failure_releases_dedup_key` | 入库失败释放锁 |
| `test_handle_sms_failure_keeps_row_and_key` | 短信失败保留行和窗口 |
| `test_handle_frost_string_level` | level=high → 4 |
| `test_consumer_has_main_guard` | 进程入口存在 |

## 实现进度

- `handle_alarm`：校验、SET NX 占窗、入库失败回滚 key、SMS 失败只记日志
- `to_schema_type`：Kafka 词 → schema 枚举
- 启动：`cd src/python && python -m consumers.alarm_consumer`
- Kafka 地址：`settings.KAFKA_BOOTSTRAP_SERVERS`；Producer 复用

## Commit

| hash | message |
|---|---|
| `c7a7b42` | `feat(4.1): 预警判定与降噪聚合、Kafka 消费` |
| `eb843b4` | `docs(task-1): 补齐自验证快照，阶段标记为待审查` |

## 问题与处理

- 仓库默认分支是 `master`，从 `master` 切出。
- 审查 P1-2 要求先入库再 SET；为同时满足 P2-3 原子门闩，改为 SET NX + 入库失败 DELETE。
- `judge_level` 仍忽略数字 value；蓝色等级与根因标签留给后续算法任务。
