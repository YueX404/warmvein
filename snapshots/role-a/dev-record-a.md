# Task-4 开发记录（角色A）

**PR / Task：** Dev-2 Task 4 短信 API 与前端模板管理  
**分支：** `dev-2/feature/task4-sms-api`  
**工作区：** `D:\YY\.worktrees\dev-2-feature-task4-sms-api`（独立 worktree，未切换 `D:\YY` 的 `master`）  
**需求：** `docs/superpowers/plans/Dev-2-task4-sms-api.md`

## 测试用例

| 用例 | 行为 |
|---|---|
| `test_sms_send_validates` | 空 templateCode + 空 phones → 40001 |
| `test_sms_send_rejects_missing_phones` | 缺 phones → 40001 |
| `test_sms_send_rejects_non_list_phones` | phones 非列表 → 40001 |
| `test_sms_send_rejects_non_string_phone` | phones 含非字符串 → 40001 |
| `test_sms_send_rejects_short_phone` | 不足 11 位 → 40001 |
| `test_sms_send_rejects_non_digit_phone` | 11 位非数字 → 40001 |
| `test_sms_send_rejects_too_many_phones` | 超过 20 个 → 40001 |
| `test_sms_send_rejects_long_template_code` | templateCode>32 → 40001 |
| `test_sms_send_rejects_non_dict_vars` | vars 非 dict → 40001 |
| `test_sms_send_template_not_found` | send_sms 抛 ValueError → 40002 |
| `test_sms_send_ok` | 返回 data.batchId |
| `test_sms_log_list` | GET /api/sms/log?batchId= 返回 200 |
| `test_sms_log_filters_batch_id` | 参数化 WHERE batch_id=:b |
| `test_sms_log_returns_masked_phone` | 返回 phoneMasked / camelCase / 格式化时间 |
| `test_sms_log_caps_result_size` | LIMIT 200 |
| `test_sms_log_rejects_long_batch_id` | batchId>32 → 40001 |
| `test_sms_log_returns_error_msg` | 返回 errorMsg / content |

## 实现进度

- `routes_sms.py`：`POST /sms/send`、`GET /sms/log`；校验 templateCode/phones/vars；模板不存在 40002
- 查询兼容 `batch_id` 与 `batchId`；SQL 参数化；不改 `sms_service.py`
- 前端：模板目录、手动发送、发送记录；号码展示走 `maskPhone`
- `routes_sms.py`：非法号按 `is_mobile` 拒收；单次最多 20 个号；日志带 `errorMsg`/`content`
- Mock 模板与 `heat_init.sql` 种子对齐；编码输入同步目录变量区

## Commit

| hash | message |
|---|---|
| `54d4e17` | `feat(sms): 短信发送/记录 API 与模板管理页面` |
| `beb2dc1` | `docs(task-4): 补齐开发记录中的 commit hash` |
| `e4b5860` | `docs(task-4): 自验证通过，阶段标记为待审查` |
| `86727da` | `fix(task-4): review反馈 - 非法号40001、单次20上限、Mock对齐种子` |
| `9176680` | `docs(task-4): 审查回复，阶段改为待二次审查` |

## 问题与处理

- 计划测试用 `batchId`，前端契约用 `batch_id`，路由同时接受两者。
- 发送成功路径 mock `sms_service.send_sms`，记录查询用 FakeSession，避免依赖 MySQL/Redis。
- 列表加 `LIMIT 200`，与预警列表一致，防止无界扫描。
- 审查 🟡：HTTP 层拒非法号与超量号；Mock 对齐种子；记录展示失败原因。
