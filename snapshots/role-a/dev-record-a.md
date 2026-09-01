# Task-1 开发记录（角色A）

**PR / Task：** Dev-2 Task 1 预警判定与降噪聚合  
**分支：** `dev-2/feature/task1-alarm-engine`  
**需求：** `docs/superpowers/plans/Dev-2-task1-alarm-engine.md`

## 测试用例

计划指定 4 条，均已落地：

| 用例 | 行为 | 结果 |
|---|---|---|
| `test_judge_frost_red` | `judge_level("frost", 4) == 4` | 通过 |
| `test_judge_corrosion_yellow` | `judge_level("corrosion", 2) == 2` | 通过 |
| `test_dedup_key_stable` | 同一站+类型 key 稳定 | 通过 |
| `test_frost_high` | `risk_level_from_frost("high") == 4` | 通过 |

未覆盖（计划未要求，审查可关注）：未知 `alarm_type` 默认 2；`frost` 的 low/medium；5 分钟窗口跳过；`publish_sms`；consumer 入库。

## 实现进度

- `services/alarm_engine.py`：四级判定、降噪 key、向 `sms-notify-topic` 投递
- `consumers/alarm_consumer.py`：消费 `heat-alarm-topic`，Redis 300s 去重，写入 `biz_alarm`
- 不写 HTTP / 前端；不 import 短信服务；不改 `routes_alarm.py`

## Commit

| hash | message |
|---|---|
| `c7a7b42` | `feat(4.1): 预警判定与降噪聚合、Kafka 消费` |

## 问题与处理

- 仓库默认分支是 `master` 不是计划里的 `main`，从 `master` 切出。
- consumer 使用 `kafka_topics.HEAT_ALARM_TOPIC`（Interfaces 要求），未用计划示例里的 `os.getenv("HEAT_ALARM_TOPIC")`。
- `alarm_engine` 按计划 import 了未使用的 `redis_client`（降噪实际在 consumer）。
