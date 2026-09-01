# Task-5 开发记录（角色A）

**PR / Task：** Dev-2 Task 5 故障预报与寿命预测  
**分支：** `dev-2/feature/task5-forecast`  
**需求：** `docs/superpowers/plans/Dev-2-task5-forecast.md`

## 测试用例

| 用例 | 行为 |
|---|---|
| `test_remain_life_linear` | (5.0-3.0)/0.1 → 20.0 |
| `test_remain_life_inf_safe` | v_corr=0 → inf，避免除零 |
| `test_predict_anomaly_rule_low_supply_temp` | 无模型且 supplyTemp<5 → rule 异常 |
| `test_predict_anomaly_rule_high_corrosion` | 无模型且 corrosionRate>0.05 → rule 异常 |
| `test_predict_anomaly_rule_normal` | 无模型且参数正常 → rule 非异常 |
| `test_predict_anomaly_uses_ml_when_model_exists` | 有 pkl 时走 IsolationForest，model=ml |
| `test_forecast_list` | GET /api/forecast/list 返回 camelCase 数组 |
| `test_forecast_list_filters_type` | query `type=lifetime` 绑定 SQL 参数 t |
| `test_forecast_list_rejects_invalid_type` | 非法 type → 40001 |
| `test_train_script_feature_columns_match_predictor` | 训练特征列与预测特征键一致 |
| Task 2 `test_alarm_*` | list/ack 回归，不得破坏 |

## 实现进度

- `services/forecast.py`：`remain_life` 线性估算；`predict_anomaly` 无模型走规则、有 `anomaly_model.pkl` 走 sklearn
- `routes_alarm.py`：仅末尾追加 `GET /forecast/list`（HTTP 参数 `type`），保留 `/alarm/list` `/alarm/ack`；单 `APIRouter()`
- `heat_train_model.py`：IsolationForest，特征 `supplyTemp, returnTemp, pressure, flow, corrosionRate, roomTemp`；无 Hive 用合成样本，输出 `models/anomaly_model.pkl`
- SQL 查 `biz_forecast` F0 列，无 `period_month`；参数化 `:t` / `:limit`

## Commit

| hash | message |
|---|---|
| `d9d74f7` | `feat(4.2): 故障预报/寿命预测模型与接口` |

## 问题与处理

- Task 2 护栏 `test_alarm_router_has_no_forecast` 在追加预报路由后会失败，改为断言 list/ack 仍在；forecast 覆盖放在 `tests/test_forecast.py`
- 列表 `data` 为预报数组 + camelCase，对齐功能开发文档 `forecast[]` 与 Task 2 预警列表，不采用 api-guide 的 `{total, forecasts}` 包一层
- 查询参数按功能开发文档使用 `type`（FastAPI `Query(alias="type")`），不用计划草稿里的 `ftype` 作为对外参数名
- 训练脚本的 `print` 为 CLI 进度（Hive 回退 / 模型已保存），不是调试残留
- 未改 `snapshots` 以外的 F0 冻结文件；独占范围外仅动了上述 Task 2 护栏测试
