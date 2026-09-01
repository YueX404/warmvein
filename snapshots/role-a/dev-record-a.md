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
| `test_consumer_has_main_guard` | `__main__` + `SMS_NOTIFY_TOPIC` + 手动提交，无 `ALARM_NOTICE` |

## 实现进度

- `sms_service`：`LocalMockSender` / `AliyunSMSSender`、模板渲染、脱敏、日限流 20、指数退避重试 3 次、写 `biz_sms_log`
- `sms_consumer`：消费 `SMS_NOTIFY_TOPIC`，蓝/黄/橙/红模板映射；缺手机号跳过
- 启动：`cd src/python && python -m consumers.sms_consumer`
- 本 Task 不写 HTTP API / 前端（Task 4）

## Commit

| hash | message |
|---|---|
| `e5997b0` | `feat(sms): 短信网关适配/模板/脱敏/限流/重试` |

## 问题与处理

- 计划示例落库 status 用 0/1；表结构与 API 约定是 2=成功 / 3=失败 / 4=限流跳过，按 `heat_init.sql`。
- 计划限流条件 `> 20` 实际会放到 21 条；改为 `>= 20`。
- 计划缺 phone 时发到 `13800000000`；改为 skip，避免污染发送记录。
- Topic 用 F0 `SMS_NOTIFY_TOPIC`，不用环境变量硬编码。
- 未改 `snapshots` 以外的共享文件；独占文件仅 3 个实现/测试文件。
