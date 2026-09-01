# Dev-2 Task 1 代码审查报告

> **审查日期：** 2026-09-01  
> **分支：** `dev-2/feature/task1-alarm-engine`  
> **对照基线：** `master`（`d1c7f15` → `eb843b4`）  
> **需求 / 计划：** `docs/superpowers/plans/Dev-2-task1-alarm-engine.md`  
> **审查对象：** `src/python/services/alarm_engine.py`、`src/python/consumers/alarm_consumer.py`、`tests/test_alarm_engine.py`，以及角色 A 快照  
> **交叉核对：** F0 契约（`kafka_topics.py`、`config/settings.py`、`.env.example`）、`config/mysql/heat_init.sql`（`biz_alarm`）、`docs/database-schema.md`、系统设计文档 §5.2、Dev-1 告警报文约定、Dev-2 Task 3 短信消费约定

---

## 一、总体结论

**暂不建议合入。**

计划内 3 个独占文件和 4 条单测都已落地，Topic 契约与 F0 冻结边界也守住了。但消费循环还不能按生产标准运行：

1. 一条坏消息会打挂整个预警引擎进程。
2. Redis 去重占坑发生在入库成功之前，失败告警会被静默丢掉 5 分钟。
3. `consume()` 没有进程入口，合入后管道实际上是死代码。

单测已当场验证：`pytest tests/test_alarm_engine.py -v` → **4 passed**。这只证明查表函数符合计划夹具，**不证明** 4.1 消费路径可用。

**合入建议：先修全部 P1 和下列 P2（Kafka 环境变量、Producer 复用、类型词表映射），P3 可记 follow-up。**

---

## 二、审查范围与提交

| 项 | 内容 |
|---|---|
| 相对 `master` 的提交 | `c7a7b42` `feat(4.1): 预警判定与降噪聚合、Kafka 消费` |
| | `eb843b4` `docs(task-1): 补齐自验证快照，阶段标记为待审查` |
| 新增文件 | `src/python/services/alarm_engine.py`（28 行） |
| | `src/python/consumers/alarm_consumer.py`（30 行） |
| | `tests/test_alarm_engine.py`（17 行） |
| | `snapshots/role-a/dev-record-a.md`、`snapshots/role-a/progress.md` |
| 未改动（符合 F0 冻结） | `main.py`、`routes_alarm.py`、`kafka_topics.py`、`db.py`、`config/settings.py`、`config/mysql/heat_init.sql` |

---

## 三、做得好的地方

- 改动落在 Task 1 独占文件内，没有触碰 F0 冻结文件。
- Kafka 契约用法正确：消费 `HEAT_ALARM_TOPIC`（`heat-alarm-topic`），投递 `SMS_NOTIFY_TOPIC`（`sms-notify-topic`），没有 import 短信服务。
- Consumer 使用 `kafka_topics.HEAT_ALARM_TOPIC`，比计划示例里的 `os.getenv("HEAT_ALARM_TOPIC")` 更符合 F0 单一事实源。
- SQL 使用参数绑定，无字符串拼接。
- 降噪 key 形状 `alarm:{station_id}:{alarm_type}`、窗口 300 秒，与系统设计文档 §5.2「同 station+同类告警 5min 窗口聚合」一致。
- 计划指定的 4 条单测均已落地并通过。

---

## 四、问题清单

优先级约定：

- **P0**：合入即导致生产级阻断（本次无）
- **P1**：必须在合入前修复
- **P2**：应修复，否则后续 Task / 联调会踩坑
- **P3**：低影响，可记 follow-up

### P1 — 必须修复

#### P1-1 单条坏消息会停掉整个预警引擎

- **位置：** `src/python/consumers/alarm_consumer.py:14-30`
- **问题：** `for msg in c` 没有 `try/except`。JSON 反序列化失败、缺 `station_id`、Redis/MySQL 不可用、`publish_sms` 抛错，都会让 `consume()` 退出。kafka-python 默认自动提交下，毒消息还可能卡在分区头，重启即再次崩溃。
- **影响：** 对 4.1 是进程级停摆，不是漏一条告警。
- **修复：** 逐条捕获异常、打日志、跳过畸形报文；不要让单条记录杀死循环。

#### P1-2 Redis 先占坑、入库失败后告警被静默丢 300 秒

- **位置：** `src/python/consumers/alarm_consumer.py:19-29`

```python
last = int(redis_client.get(key) or 0)
if now - last < 300:
    continue
redis_client.set(key, now, ex=300)   # 先占坑
with SessionLocal() as s:
    s.execute(...)                   # 后入库
    s.commit()
```

- **问题：** `SET` 在 `INSERT` 之前。MySQL 宕机、`type` 为 `NULL`（列是 `NOT NULL`）、commit 失败时，key 已占满 300 秒。重试会走 `now - last < 300` 直接 `continue`：库里没有记录，短信也不会发。
- **说明：** 计划 snippet 顺序相同，但仍然不安全。
- **修复：** 先写入成功，再用 `SET key NX EX 300` 占窗口。SMS 失败应打日志，不要用 Redis 挡住后续补发/修复任务。

#### P1-3 `consume()` 没有进程入口，合入后管道是死代码

- **位置：** `src/python/consumers/alarm_consumer.py:9`
- **问题：** 没有 `if __name__ == "__main__"`，Docker Compose 也没有对应服务。`main.py` 按 F0 冻结不能挂后台循环。当前没有可执行的启动方式，预警引擎实际上跑不起来。
- **修复：** 增加 `__main__` 守卫，并在任务说明中写明启动命令（例如在 `src/python` 下 `python -m consumers.alarm_consumer`）。

---

### P2 — 应修复

#### P2-1 Kafka 地址读了错误的环境变量

- **位置：** `src/python/consumers/alarm_consumer.py:11`、`src/python/services/alarm_engine.py:25`
- **对照：** `src/python/config/settings.py:65`、`.env.example:38` 均为 `KAFKA_BOOTSTRAP_SERVERS`
- **问题：** 代码读 `KAFKA_BOOTSTRAP`。两边默认都是 `localhost:9092`，本地测不出来。一旦 `.env` 改了真实 broker，consumer/producer 仍连 localhost。
- **修复：** 使用 `settings.KAFKA_BOOTSTRAP_SERVERS`（与 `db.py` 同一模式）。

#### P2-2 每条告警新建 KafkaProducer 且不 close

- **位置：** `src/python/services/alarm_engine.py:22-28`
- **问题：** 每次 `publish_sms` 建连接、`flush`、不关闭。突发告警会堆线程和 FD，并给每条短信加上连接开销。
- **修复：** 复用一个 producer（模块级或 consumer 持有），关闭时 `close()`，并对 `send` 的 future 做失败日志。

#### P2-3 去重 GET+SET 非原子

- **位置：** `src/python/consumers/alarm_consumer.py:19-22`
- **问题：** 两个 worker 都可能看到 `last=0` 并各插一条。Dev-1 计划虽写了 `key=stationId`，本仓库里生产者尚未落地，分区也未保证。
- **修复：** 门闩改为 `SET NX EX 300`。

#### P2-4 写入 `biz_alarm.type` 的词表与数据字典不一致

- **位置：** `src/python/services/alarm_engine.py:4-6`
- **对照：** `config/mysql/heat_init.sql:136`、`docs/database-schema.md:129`

| 引擎写入 | Schema / 数据字典 |
|---|---|
| `frost` | `freeze` |
| `imbalance` | `balance` |
| `steal` | `theft` |
| `loss` / `blocked` / `water` | 无对应；schema 为 `pressure` / `other` 等 |

- **影响：** Task 2 按 schema 枚举筛选列表时会漏数据。Task 8 虽有 `frost→freeze` 映射，那是预案匹配层，救不了 `biz_alarm.type` 存错词。
- **修复：** Kafka 侧可继续用 `frost`（与 Dev-1 约定一致），入库时映射到 schema 枚举。

#### P2-5 报文未校验

- **位置：** `src/python/consumers/alarm_consumer.py:15-17`
- **问题：** `station_id` 用 `[]` 取值，缺字段即 `KeyError`（叠加 P1-1 会打挂进程）。`alarmType` 用 `.get()`，可为 `None`，插入 `NOT NULL` 的 `type` 会失败，再叠加 P1-2 后 5 分钟内无法重试。
- **修复：** 校验 `station_id` 存在且可转为整数、`alarmType` 为非空已知字符串；非法报文打日志并 skip。

#### P2-6 测试只覆盖查表函数，没覆盖本 Task 的运行路径

- **位置：** `tests/test_alarm_engine.py:1-17`
- **问题：** `test_judge_frost_red` 能过，是因为 `"frost"` 被写死为 4，不是因为用了 `value=4`。5 分钟跳过、入库、SMS、缺字段、未知类型均无测试。作者在 `snapshots/role-a/dev-record-a.md` 已写明缺口。
- **修复：** 抽出 `handle_alarm(msg)`，用假 Redis / Session / Producer 覆盖真实规格。

---

### P3 — 低影响

#### P3-1 未使用的 `redis_client` 导入

- **位置：** `src/python/services/alarm_engine.py:2`
- **问题：** 计划 Interfaces 要求 import，降噪实际在 consumer。模块 import 时会连带拉起 `db.py` 的 Redis 客户端，属于无效耦合。
- **修复：** 从 engine 中删除该 import。

#### P3-2 `auto_offset_reset="latest"` 与项目默认不一致

- **位置：** `src/python/consumers/alarm_consumer.py:13`
- **对照：** `.env.example` 为 `KAFKA_AUTO_OFFSET_RESET=earliest`
- **问题：** 新消费组会丢掉它不在线期间的告警；更换 `group_id` 上线时同样丢数据。
- **修复：** 与项目默认对齐，或明确文档说明首次部署丢积压是有意行为。

#### P3-3 魔法数字、无日志、命名不透明

- **位置：** `alarm_consumer.py` 全文
- **问题：** `300` 未命名；无 skip/insert/SMS 日志；变量名 `a` / `c` / `s` 不利于运维排障。
- **修复：** `DEDUP_WINDOW_SEC` 常量 + 关键路径日志。

#### P3-4 快照与 HEAD 不一致

- **位置：** `snapshots/role-a/progress.md`
- **问题：** 写的是相对 master 仅 1 个 commit `c7a7b42`；实际 HEAD 是 `eb843b4`。无功能影响。

---

## 五、计划本身的缺口

实现基本是按计划 snippet 誊写。下列问题**不是「没按计划写」**，而是计划把 4.1 简化过头。合入前需要产品 / 角色 A 拍板：算法丰富度可以跟进，但不要把「snippet 能跑」当成「FR-4.1 做完」。

| 现象 | 说明 |
|---|---|
| `judge_level` 忽略 `value` | 签名有第二参数，实现只查 `_TYPE_LEVEL`。Dev-1 约定 `frost` + `level=3` 会被改写成 4。 |
| `risk_level_from_frost` 只存在于单测 | consumer 从未调用；冻堵 `low` / `medium` / `high` 不会进四级。 |
| 蓝色（level=1）永不出现 | 静态表最小是 2，不满足系统设计文档 §5.2 / FR-4.1.1 的四级映射。 |
| `root_cause` 填的是 `alarmType` | 不是根因标签（腐蚀 / 压力 / 冻堵 / 偷热）。 |
| 计划用 `KAFKA_BOOTSTRAP` | 与已落地的 `KAFKA_BOOTSTRAP_SERVERS` 冲突（Task 3 计划同样复制了这个错误）。 |
| 无 `__main__`、无日志、无 consumer 测试 | 计划未要求，但缺少它们则 4.1 无法运行、无法观测、无法回归。 |

Kafka 报文约定按本 Task 计划为 `{station_id, alarmType, level, phone?}`。Dev-1 的 `heat_kafka_producer.py` 尚未在本仓库落地。

---

## 六、测试与残留风险

| 项 | 结论 |
|---|---|
| 计划指定 4 条单测 | 通过（2026-09-01 当场执行） |
| 未知 `alarm_type` 默认 2 | 未覆盖 |
| 冻堵 `low` / `medium` | 未覆盖 |
| 5 分钟窗口跳过 | 未覆盖 |
| `publish_sms` | 未覆盖 |
| consumer 入库 / 缺字段 / Redis 抢锁 | 未覆盖 |
| 与 Dev-1 生产者联调 | 生产者未合入，无法验证 |
| 与 Task 3 短信消费联调 | 未做；短信侧缺 `phone` 时会落到 Task 3 的默认号 |

**残留风险：** 即使修完 P1，静态类型→级别表仍不是真正的「规则/阈值四级判定」。若产品要求 FR-4.1.1 准确率验收，需要单独跟进算法，而不是把当前查表实现当成完成态。

---

## 七、修复建议（优先顺序）

1. 从 Kafka 循环抽出 `handle_alarm(msg: dict)`，循环内 try/except，便于单测。
2. 先成功写入 `biz_alarm`，再用 `SET NX EX 300` 占窗口；SMS 失败只打日志。
3. 增加 `__main__` 与启动说明；Kafka bootstrap 改读 `settings.KAFKA_BOOTSTRAP_SERVERS`。
4. 复用单个 `KafkaProducer`。
5. 确定一套类型枚举：Kafka 可用 `frost`，入库映射为 `freeze` 等 schema 值。
6. 若冻堵风险是字符串，consumer 调用 `risk_level_from_frost`；若 Dev-1 已给数字 `level`，明确是信任还是覆盖，并写进约定。

---

## 八、评估

| 项 | 结论 |
|---|---|
| **是否可合入** | 需要先修再合 |
| **计划对齐** | 文件边界、Topic、4 条单测合格；运行时安全与可运行性不合格 |
| **F0 冻结** | 遵守 |
| **生产就绪** | 否 |

**理由：** 计划文件、契约和 4 条单测已就位。消费路径目前不安全：异常未隔离、去重抢锁早于入库、没有启动入口、Kafka 配置键与项目不一致。P1 不修不得合入。
