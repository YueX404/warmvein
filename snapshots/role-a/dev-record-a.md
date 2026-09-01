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
| `test_handle_frost_string_level` | frost + high → 4 |
| `test_handle_non_frost_string_level_uses_type_table` | corrosion + high → 2 |
| `test_dispatch_commits_on_ok_skip_dedup` | 成功状态提交 offset |
| `test_dispatch_retries_error_then_commits` | error 不提交，重试后提交 |
| `test_dispatch_commits_undecodable_payload` | 坏 JSON skip 并提交 |
| `test_consumer_has_main_guard` | `__main__` + `enable_auto_commit=False` |

## 实现进度

- `handle_alarm`：校验、SET NX 占窗、入库失败回滚 key、SMS 失败只记日志
- `dispatch_record`：手动提交 offset；`error` 退避重试同一条
- 启动：`cd src/python && python -m consumers.alarm_consumer`

## Commit

| hash | message |
|---|---|
| `c7a7b42` | `feat(4.1): 预警判定与降噪聚合、Kafka 消费` |
| `eb843b4` | `docs(task-1): 补齐自验证快照，阶段标记为待审查` |
| `8ff6fb3` | `fix(task-1): review反馈 - 消费循环隔离、去重回滚与类型映射` |
| `d550e2c` | `docs(task-1): 审查回复，阶段改为待二次审查` |

## 问题与处理

- SET NX + 入库失败 DELETE，二次审查已接受相对「先 INSERT」的偏差。
- P2-R1：自动提交会在 INSERT 失败后丢消息；改为手动提交。
- kill -9 在 SET NX 与 INSERT 之间最多留下 300s 窗口（P3-R3，接受）。
