# Dev-2 Task 3 代码审查报告

> **审查日期：** 2026-09-01  
> **分支：** `dev-2/feature/task3-sms-core`  
> **对照基线：** `master`（`ccaa50c` → `74d361a`）  
> **需求 / 计划：** `docs/superpowers/plans/Dev-2-task3-sms-core.md`  
> **审查对象：** `src/python/services/sms_service.py`、`src/python/consumers/sms_consumer.py`、`tests/test_sms_service.py`，以及角色 A 快照  
> **交叉核对：** F0 契约（`kafka_topics.py`、`config/settings.py`、`.env.example`）、`config/mysql/heat_init.sql`（`biz_sms_template` / `biz_sms_log`）、已合入的 Task 1 `publish_sms` 报文、`.env.example` 的 `KAFKA_AUTO_OFFSET_RESET=earliest`

审查 commit：

- `e5997b0` `feat(sms): 短信网关适配/模板/脱敏/限流/重试`
- `74d361a` `docs(task-3): 补齐自验证快照，阶段标记为待审查`

阶段校验：工作树进度为「开发完成，待审查」，工作区干净。审查只读，未改实现代码、未提交。

---

## 一、总体结论

**暂不建议合入。**

计划内 3 个独占文件已落地，F0 冻结边界守住了，计划指定的脱敏/渲染单测以及限流、重试、消费映射都有覆盖。当场验证：`pytest tests/test_sms_service.py -v` → **13 passed**；`pytest tests/ -v` → **36 passed**。

合入阻断来自消费循环：已经关掉自动提交，却在 **任何结果（含 Redis/MySQL/网关异常）后都 `commit()`**。这会把本该重试的预警短信永久丢掉。Task 1 二次审查的 P2-R1 已经定过正确模式（仅 skip/ok 提交，error 不提交并重试同一条），本 Task 没有沿用。

**合入建议：先修全部 P1 和下列 P2（latest 丢积压、红色占位符、消费循环测试、`_do_send` 异常重试），P3 / 🔵 可记 follow-up，但 phone 契约必须书面答复。**

---

## 二、审查范围与提交

| 项 | 内容 |
|---|---|
| 相对 `master` 的提交 | `e5997b0` `feat(sms): 短信网关适配/模板/脱敏/限流/重试` |
| | `74d361a` `docs(task-3): 补齐自验证快照，阶段标记为待审查` |
| 新增文件 | `src/python/services/sms_service.py`（126 行） |
| | `src/python/consumers/sms_consumer.py`（65 行） |
| | `tests/test_sms_service.py`（209 行） |
| 快照（覆盖 master 上 Task 1 文案） | `snapshots/role-a/dev-record-a.md`、`snapshots/role-a/progress.md` |
| 未改动（符合 F0 冻结） | `main.py`、`routes_sms.py`、`kafka_topics.py`、`db.py`、`config/settings.py`、`config/mysql/heat_init.sql`、前端 |

---

## 三、做得好的地方

- 改动落在 Task 3 独占文件内，没有 HTTP API / 前端，没有 `ALARM_NOTICE`，没有 import 预警引擎。
- Topic 用 F0 `SMS_NOTIFY_TOPIC`，bootstrap 用 `settings.KAFKA_BOOTSTRAP_SERVERS`，比计划示例的环境变量硬编码更符合单一事实源。
- SQL 参数绑定；落库 `status` 按表注释用 2/3/4，而不是计划草稿里的 0/1。
- 限流用 `>= 20`（计划 `> 20` 会放到 21 条）；缺手机号 skip，而不是发到 `13800000000`。
- `enable_auto_commit=False`、`__main__` 入口、依赖可注入，服务层单测质量明显好于计划的 2 条夹具。
- 毒 JSON 被 `try/except` 接住后仍能前进 offset，不会打挂进程。

---

## 四、问题清单

优先级约定：

- **P0**：合入即导致生产级阻断（本次无）
- **P1**：必须在合入前修复
- **P2**：应修复，否则后续 Task / 联调会踩坑
- **P3**：低影响，可记 follow-up

对应角色 A 审查窗口标记：🔴 阻断 / 🟡 建议修 / 🔵 需确认。

### P1 — 必须修复（🔴）

#### P1-1 发送失败仍提交 offset，预警短信被永久丢弃

- **位置：** `src/python/consumers/sms_consumer.py:54-60`

```python
    for msg in consumer:
        try:
            payload = json.loads(msg.value.decode())
            handle_notify(payload)
        except Exception:
            logger.exception("sms notify failed")
        consumer.commit()
```

- **问题：** `commit()` 在 `try/except` 之外，无条件执行。`handle_notify` → `send_sms` 在下列情况会抛错：模板查询失败（MySQL 抖动）、Redis `get`/`incr` 失败、`_write_log` 失败、`_do_send` 抛异常。异常只打日志，offset 照样前进，这条 `sms-notify-topic` 记录不会再投递。
- **对比：** 已合入的 Task 1 用 `dispatch_record`：仅 `skip`/`dedup`/`ok` 提交；`error` 退避后重试同一条；只有无法解码的毒消息才 skip+commit。`.env.example` 也按 earliest 保留积压，说明管道设计是「可重试」而不是「失败即丢」。
- **影响：** 供热红色/橙色预警短信在依赖抖动时静默丢失，且无法从 Kafka 恢复。`enable_auto_commit=False` 在这里没有起到保护作用。
- **修复：** 抽出类似 `dispatch_record` 的分派：解码失败 → `skip` 并提交；`handle_notify` 区分 `skip`/`ok`/`error`；`error` 不提交、短退避后重试同一条。`send_sms` 的基础设施异常不要在消费循环里被吃掉后当成功。补测试：`ok`/`skip` 会 commit；`send_sms` 抛错不 commit。

### P2 — 应修复（🟡）

#### P2-1 `auto_offset_reset="latest"` 使新消费组丢掉启动前的短信请求

- **位置：** `src/python/consumers/sms_consumer.py:51`
- **问题：** 新 `group_id=sms_consumer` 没有提交位点时从 latest 起读。短信消费进程晚于预警引擎启动、或重建消费组时，积压的 `sms-notify-topic` 全部跳过。Task 1 已改为 `earliest`；`.env.example` 写的是 `KAFKA_AUTO_OFFSET_RESET=earliest`。计划示例虽是 latest，但与已合入管道和仓库约定不一致。
- **修复：** 改为 `earliest`（或读配置且默认 earliest）。与 P1-1 一起，才能在重启后补发失败短信。

#### P2-2 红色模板 `{leaderPhone}` 从未填充，用户会收到字面占位符

- **位置：** `src/python/consumers/sms_consumer.py:34-42`；种子模板 `config/mysql/heat_init.sql:303`
- **问题：** F0 种子 `ALARM_RED` 为 `…需立即到场！联系人:{leaderPhone}`。`handle_notify` 只传 `level` / `type` / `stationName`。`build_content` 用字符串替换，缺键时原样保留，红色短信会变成「联系人:{leaderPhone}」。
- **修复：** vars 增加 `leaderPhone`（报文字段或按站查 `md_organization.phone`）；没有号码时填「平台」或「请登录平台」，不要把占位符发出去。补一条用真实 `ALARM_RED` 文案的渲染测试。

#### P2-3 消费循环的 commit/重试路径没有测试

- **位置：** `tests/test_sms_service.py:170-209`
- **问题：** 现有测试覆盖 `handle_notify` 的映射与 skip，以及 `sms_service` 的假 Redis/假 Session。`consume()` 的「失败仍 commit」完全测不到。`test_consumer_has_main_guard` 只是读源文件字符串。Task 1 在同类缺陷后补了 `dispatch` 单测才把回归锁住。
- **修复：** 用假 consumer 测：合法报文 commit；`send_sms` 抛错不 commit；坏 JSON skip 并 commit。

#### P2-4 `_do_send` 抛异常时既不重试也不写失败日志

- **位置：** `src/python/services/sms_service.py:113-126`
- **问题：** 重试循环假定 `_do_send` 返回 `{success: False}`。网关 SDK 一抛异常，循环中断，不会写 `status=3` 的 `biz_sms_log`，再被 P1-1 的 `commit()` 吃掉。计划里的 3 次指数退避对「抛错」无效。
- **修复：** `_do_send` 包在 try 中，异常视为 `success=False` 并进入退避；三次仍失败再落失败日志（`error_msg` 可记异常类型）。

### P3 — 低影响 / 需确认（🔵）

#### P3-1 与 Task 1 联调：报文通常没有 `phone`，消费端会全部 skip

- **位置：** `sms_consumer.py:25-28`；Task 1 `alarm_consumer.py:79-80` 只转发 `{**raw, level, station_id}`
- **说明：** Kafka 约定 `phone?` 为可选。缺号 skip 比计划里的 `13800000000` 更正确，已在开发记录写明。结果是：当前已合入的预警引擎 **不会往短信管道填手机号**，Task 3 合入后预警→短信闭环仍是空转。请确认：phone 由上游保证，还是本消费端按 `station_id` 查责任人/订阅用户？本轮可以不改代码，但必须书面约定，否则 Task 4 联调会误判「短信服务坏了」。

#### P3-2 `stationName` 回落到 `station_id`，短信正文会变成站点数字

Task 1 转发的是 `station_id` 不是站名。`ALARM_*` 模板是 `{stationName}`。缺站名时会发出「【暖脉供热】1紧急预警」。是否接受，或后续由上游补 `stationName`？

#### P3-3 限流 `GET` + `INCR` 非原子，TTL 是滑动 24h

并发下可超过 20 条/号。`incr` 与 `expire` 不是同一事务，进程若在两步之间退出，key 可能没有 TTL。`database-schema.md` 写的是「当天结束」，实现是「距上次成功发送 86400 秒」。建议后续改为 `INCR` 后若值为 1 再 `EXPIRE`，或 Lua/管道。

#### P3-4 其它低影响项

- `biz_sms_log.error_msg` 失败原因从未写入。
- `batch_id = f"b{int(time.time())}"` 同一秒两次发送会混批，Task 4 按 `batch_id` 查询会串单。
- `get_sender()` 读 `os.getenv("SMS_PROVIDER")`，未走已有的 `settings.SMS_PROVIDER`；`AliyunSMSSender` 仍是恒成功 stub（计划如此）。生产环境把 `.env` 设成 `aliyun` 会记成功却不发真短信。
- 加载模板未过滤 `status=1`，停用模板仍可发送。
- `FROST` / `SHUTDOWN` / `PUBLIC` 消费端不用，只按 level 映射 `ALARM_*`——与计划 snippet 一致，冻堵红色会走 `ALARM_RED` 而不是 `FROST`。
- 开发记录 commit 表只列了 `e5997b0`，缺当前 HEAD `74d361a`。

---

## 五、测试缺口与残余风险

| 路径 | 现状 |
|---|---|
| mask / build_content / 限流 / 重试 / 脱敏入库 | 有，且通过 |
| `handle_notify` 模板映射与缺号 skip | 有 |
| `consume()` commit / 失败重试 | **无（P1-1 / P2-3）** |
| 真实 `ALARM_RED` 文案含 `{leaderPhone}` | **无（P2-2）** |
| 与 Task 1 实报文（无 phone、无 stationName）联调 | **未做（P3-1）** |
| Aliyun 真网关 | 不在本 Task 范围 |

---

## 审查结论

**❌ 需要修改后再审**

合入前至少关闭 **P1-1**。建议一并修 **P2-1～P2-4**（latest 丢积压、红色占位符、消费循环测试、`_do_send` 异常重试），否则修复 P1 后仍容易在下一轮被打回。P3 / 🔵 可书面接受或记 follow-up，但 **phone 契约必须有一句明确答复**。

开发窗口处理时：优先改 `sms_consumer.py` 的分派/提交策略并补测试；不要改 F0 冻结文件。处理记录写入 `snapshots/role-a/review-reply-a.md` 后，再回到审查窗口做二次审查。
