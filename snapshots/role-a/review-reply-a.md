# Task-5 审查反馈处理记录

审查来源：`snapshots/role-a/review-feedback-a.md`  
处理分支：`dev-2/feature/task5-forecast`  
处理时间：2026-09-01

## 🔴 阻断性问题

无。

## 🟡 改进建议

| 编号 | 处理 | 说明 |
|---|---|---|
| 🟡-1 | 采纳 | Hive SQL 改为 `supply_temp AS supplyTemp` 等 F0 列别名；回退日志改为 `Hive feature query failed`，不再写「Hive unavailable」。 |
| 🟡-2 | 采纳 | 合成样本把低供水温度与高腐蚀分到不同行（各约一半异常配额）。 |
| 🟡-3 | 采纳 | ML 用例改为 `train_anomaly_model` 产出 `Pipeline`，对极端样本断言 `is_anomaly==1`。 |
| 🟡-4 | 采纳 | 列表 SELECT/映射补 `description`、`suggestion`。未加 `pipe_id`（审查只要求至少前两项）。 |
| 🟡-5 | 采纳 | `MODEL_DIR` 读 `settings.MODEL_DIR`，相对路径按仓库根解析为绝对路径。未改冻结的 `config/settings.py`。 |
| 🟡-6 | 采纳 | 新增手工种子 `config/mysql/forecast_seed.sql`（未改 `heat_init.sql`）。空表是未执行种子时的预期。 |

## 🔵 疑问确认

| 编号 | 结论 |
|---|---|
| 🔵-1 | **按计划并排放进同一切片**。`remain_life` / `predict_anomaly` 是可调用纯函数与训练产物；`GET /api/forecast/list` 只读 `biz_forecast`。本 Task **没有**预报落库/消费者，列表 **不会**按模型实时计算。角色 B 应按表记录渲染。 |
| 🔵-2 | **本 PR 不改 api-guide**。契约维持功能开发文档：`data` 为 `forecast[]`，无 `page/pageSize`。合入后另开 chore 同步 api-guide，避免前端按 `{total, forecasts}` 解包失败。 |
| 🔵-3 | **本窗口不 rebase**（并行多分支）。合入时 `snapshots/role-a/*` 以各分支自带快照为准，不要覆盖 master 上已合入 Task 的进度说明。 |
| 🔵-4 | **本 Task 不把 `remain_life` 接到 HTTP**。负数（`W_current < W_min`）与 `inf` 的序列化待接入 API 时再定（建议下限夹 0，`inf` 用 null 或独立字段）。当前保持公式原样。 |
| 🔵-5 | 已改 `tests/test_alarm_routes.py` 文件头，去掉「forecast out of scope」。 |
| 🔵-6 | **不是漏做**。`HEAT_FORECAST_TOPIC` 由 F0 提供，本 Task 计划不生产/消费。 |

## 验证

- `pytest tests/test_forecast.py tests/test_alarm_routes.py -v` → 24 passed
- `pytest tests` → 119 passed

审查修复提交：`b2b7649`。

## 二次审查（2026-09-01）

来源：`snapshots/role-a/review-feedback-a.md`（二次）。结论：✅ 通过，建议合入。首轮 🟡-1～🟡-6 全部关闭。

| 编号 | 处理 | 说明 |
|---|---|---|
| 🔵1 | 修复 | Commit 表补 `46b451a`。 |
| 🔵2 | 保留 | `_resolve_model_dir` 两处拷贝 follow-up 再抽。 |
| 🔵3 | 接受 | `forecast_seed.sql` 按 type 去重，不并入 `heat_init.sql`。 |

