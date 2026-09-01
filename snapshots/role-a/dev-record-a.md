# Task-3 开发记录（角色A）

**PR / Task：** Dev-2 Task 3 短信服务（网关/模板/脱敏/限流/重试）  
**分支：** `dev-2/feature/task3-sms-core`  
**需求：** `docs/superpowers/plans/Dev-2-task3-sms-core.md`

## 测试用例

| 用例 | 行为 |
|---|---|
| `test_mask_phone` | `13812341234` → `138****1234` |
| `test_mask_phone_keeps_non_mobile` | 非 11 位原样返回 |
| `test_build_content_fills_vars` | `{planTime}` 替换为 `09-01` |
| `test_send_sms_missing_template_raises` | 模板不存在 → `ValueError` |
| `test_send_sms_success_masks_and_logs` | 发送成功，脱敏入库 status=2，日计数 +1 TTL=86400 |
| `test_send_sms_skips_invalid_phone` | 非法号码不发送、不落库 |
| `test_send_sms_rate_limit_skips_and_logs` | 计数 ≥20 跳过，status=4 |
| `test_send_sms_retries_then_succeeds` | 失败 1 次后成功，退避 sleep=[1] |
| `test_send_sms_retries_three_times_then_fails` | 3 次失败 status=3，不占限额 |
| `test_handle_maps_red_and_sends` | level=4 → `ALARM_RED` |
| `test_handle_defaults_to_yellow` | 缺 level → `ALARM_YELLOW`，站名回落到 station_id |
| `test_handle_skips_missing_phone` | 无合法手机号 skip |
| `test_consumer_has_main_guard` | `__main__` + `SMS_NOTIFY_TOPIC` + 手动提交 + earliest，无 `ALARM_NOTICE` |
| `test_dispatch_commits_on_ok_and_skip` | ok/skip 提交 offset |
| `test_dispatch_retries_error_then_commits` | error 不提交，重试后提交 |
| `test_dispatch_send_raise_does_not_commit_until_ok` | `send_sms` 抛错不提交，重试后提交 |
| `test_dispatch_commits_undecodable_payload` | 坏 JSON skip 并提交 |
| `test_handle_red_fills_leader_phone_fallback` | 缺 leaderPhone 填「请登录平台」，红色文案无占位符 |
| `test_handle_red_uses_leader_phone_from_payload` | 报文带 leaderPhone 则原样填充 |
| `test_send_sms_retries_when_do_send_raises` | `_do_send` 抛错计入重试，第三次成功 |
| `test_send_sms_logs_fail_when_do_send_always_raises` | 三次抛错落 status=3，error_msg=RuntimeError |

## 实现进度

- `sms_service`：网关适配、模板渲染、脱敏、日限流 20、指数退避重试 3 次（含 `_do_send` 抛错）、写 `biz_sms_log`
- `sms_consumer`：`dispatch_record` 仅 ok/skip 提交；`earliest`；红色 vars 含 `leaderPhone`
- 启动：`cd src/python && python -m consumers.sms_consumer`
- 本 Task 不写 HTTP API / 前端（Task 4）

## Commit

| hash | message |
|---|---|
| `e5997b0` | `feat(sms): 短信网关适配/模板/脱敏/限流/重试` |
| `74d361a` | `docs(task-3): 补齐自验证快照，阶段标记为待审查` |
| `49d8f96` | `fix(task-3): review反馈 - 发送失败不提交 offset 并重试` |
| `42e3e0c` | `fix(task-3): review反馈 - earliest/leaderPhone/网关异常重试` |

## 问题与处理

- 计划示例落库 status 用 0/1；表结构是 2/3/4，按 `heat_init.sql`。
- 计划限流 `> 20` 会放到 21 条；改为 `>= 20`。
- 缺 phone skip，不发 `13800000000`。phone 由上游保证（P3-1 书面约定）。
- Topic 用 F0 `SMS_NOTIFY_TOPIC`。
- P1-1：无条件 commit 会丢失败短信；改为 `dispatch_record` 与 Task 1 一致。
- P2-2：红色 `{leaderPhone}` 缺省「请登录平台」，不查组织表。
