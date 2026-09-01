# Task-5 Code Review 反馈

审查分支：`dev-2/feature/task5-forecast`  
审查 commit：`d493e32`（功能 `d9d74f7`；快照 `d493e32`）  
审查时间：2026-09-01  
对照基线：worktree merge-base `d084b59`（当时 `master`）；当前 `origin/master` 已前进到 `ef27e96`  
需求 / 计划：`docs/superpowers/plans/Dev-2-task5-forecast.md`  
交叉核对：`docs/功能开发文档.md` §3/§5.5、`docs/api-guide.md` §4、`config/mysql/heat_init.sql`（`biz_forecast`）、`config/hive/heat_ddl.sql`（`dwd.heat_sensor_detail`）、Task 2 `routes_alarm.py` 既有 list/ack  
审查方式：主仓库 `D:\YY` 保持 `master` 未切换；只读审查 worktree `D:\YY\.worktrees\dev-2-feature-task5-forecast`  
单测当场：`pytest tests` → **116 passed**；`test_forecast.py` + `test_alarm_routes.py` → **21 passed**

---

## 一、总体结论

计划要求的三件套都已落地：`remain_life`、`predict_anomaly`（无 pkl 走规则 / 有 pkl 走 IsolationForest）、`GET /api/forecast/list` 仅追加在 `routes_alarm.py` 末尾，Task 2 的 list/ack 行为保留。SQL 参数化，列表 camelCase，`type` 白名单，F0 冻结文件未动。

未发现合入即错的 API/算法阻断项。有几处联调/训练会踩坑，建议开发窗口处理后再合，但不把审查结论打成不通过。

---

## 二、审查范围与提交

| 项 | 内容 |
|---|---|
| 相对基线的提交 | `d9d74f7` `feat(4.2): 故障预报/寿命预测模型与接口` |
| | `d493e32` `docs(task-5): 补齐自验证快照，阶段标记为待审查` |
| 新增 | `src/python/services/forecast.py`、`src/python/heat_train_model.py`、`tests/test_forecast.py` |
| 修改 | `src/python/routes_alarm.py`（末尾追加 forecast）、`tests/test_alarm_routes.py`（护栏从「禁止 forecast」改为「保留 list/ack」） |
| 快照 | `snapshots/role-a/dev-record-a.md`、`progress.md` |
| 未改动（符合 F0 / 独占） | `main.py`、`db.py`、`response.py`、`kafka_topics.py`、`config/mysql/heat_init.sql`、`config/hive/heat_ddl.sql`、前端、Kafka 消费者 |
| 阶段快照 | `开发完成，待审查`，允许本轮审查 |
| 工作区 | 干净；分支无 upstream，未执行会改动 HEAD 的 pull |

---

## 三、做得好的地方

- 独占范围清楚：新建三个文件，路由只追加，没有第二个 `APIRouter()`，没有改 Task 2 的 list/ack 逻辑。
- 查询参数按功能开发文档用 `type`（`Query(alias="type")`），并在开发记录里写明不采用计划草稿的对外名 `ftype`。
- `type` 做了 `freeze/lifetime/fault/energy` 白名单，非法值 40001；SQL 绑定 `:t` / `:limit`，无拼接。
- 列表输出 camelCase + `typeName`，日期/时间格式与 Task 2 预警列表一致；`data` 直接给数组，对齐功能开发文档 `forecast[]`，并在快照里说明了不跟 api-guide 的 `{total, forecasts}`。
- `remain_life` 与功能开发文档 §5.5 / 计划公式一致，`v_corr<=0` 返回 `inf`，有对应单测。
- 规则兜底与计划 snippet 一致（`supplyTemp<5` 或 `corrosionRate>0.05`）；训练特征列与预测 `FEATURE_KEYS` 有对等断言。
- `models/*.pkl` 已在 `.gitignore`，模型未入库。
- 自验证声明的 116 passed 当场复核成立；Task 2 回归 11 项仍绿。

---

## 🔴 阻断性问题（必须修改）

无。

---

## 🟡 改进建议

1. 【`src/python/heat_train_model.py:57-63`】Hive 训练 SQL 列名与 F0 `dwd.heat_sensor_detail` 对不上。DDL 是 `supply_temp` / `return_temp` / `flow_rate` / `corrosion_rate` / `room_temp`，脚本写的是 `supplyTemp` / `returnTemp` / `flow` / `corrosionRate` / `roomTemp`。Spark/Hive 一旦可用，查询会失败，被 `load_data` 的宽 `except` 打成「Hive unavailable」，随后用合成样本写出 `anomaly_model.pkl`。这不是「无 Hive 回退」，而是「有数仓也训不到」。建议 `SELECT supply_temp AS supplyTemp, ... flow_rate AS flow, ...`，失败日志不要写「Hive unavailable」。

2. 【`src/python/heat_train_model.py:43-44`】合成异常把低供水温度和高腐蚀打在同一批行上。规则路径是「或」，模型路径容易学成「且」。有 pkl 之后，只低温或只高腐蚀的样本可能漏检。建议两因子分开注入，或各注入一部分单因子异常。

3. 【`tests/test_forecast.py:46-66`】ML 用例 dump 的是裸 `IsolationForest`，生产训练存的是 `Pipeline(StandardScaler + IsolationForest)`；断言只是 `model==ml` 且 `is_anomaly in (0,1)`，等于没验证生产产物能检出异常。建议用 `train_anomaly_model` 出模，并对构造的异常样本断言 `is_anomaly==1`。

4. 【`src/python/routes_alarm.py:109-137`】`biz_forecast` 有 `description` / `suggestion` / `pipe_id`，api-guide 列表也有前两项；本 Task 没有详情接口，列表又不返回，角色 B 只能拿到标题。计划 SELECT 确实没写这些列，但建议至少补 `description`、`suggestion`。

5. 【`heat_train_model.py` / `forecast.py` 的 `MODEL_DIR`】相对路径 `"models"`，未走 `config.settings.settings.MODEL_DIR`。从 `src/python` 跑训练/服务会找不到仓库根下的 `models/`。建议与 settings 对齐，或按文件位置解析绝对路径。

6. 【演示数据】`heat_init.sql` 无 `biz_forecast` 种子，本分支也无写入逻辑。联调 `GET /api/forecast/list` 恒为空数组，容易被当成接口坏了。可加独立 seed SQL（不要改 F0 `heat_init.sql`），或在开发记录里写明「表空是预期」。

---

## 🔵 疑问确认

1. 【`services/forecast.py` vs `routes_alarm.py`】`remain_life` / `predict_anomaly` 没有被列表（或任何路由/消费者）调用，`biz_forecast` 本 Task 也无人写入。这是计划把「公式+模型」和「读表 API」并排放进同一切片，还是后续还要有预报落库任务？请在回复里确认，避免角色 B 以为列表会按模型实时计算。

2. 【`docs/api-guide.md` vs 功能开发文档】列表 `data` 用数组而不是 `{total, forecasts}`，且无 `page/pageSize`。开发记录已说明取舍，本审查接受；合入后请同步 api-guide，避免前端按 guide 解包失败。

3. 【合入前 rebase】`origin/master` 自基线后又合入 Dev-1 监测/能效/孪生/公众等（`d084b59..ef27e96`）。与 `routes_alarm.py` 无文件重叠，但 `snapshots/role-a/*` 几乎必冲突。合入时按各分支自带快照处理，不要盖掉 master 上已合入 Task 的进度说明。

4. 【`remain_life`】`W_current < W_min` 会返回负数；`inf` 目前不进 JSON。若后续把该函数接到 API，需要先定义序列化与下限（夹成 0 还是保持负数）。

5. 【`tests/test_alarm_routes.py:1`】文件头仍写 “forecast are out of scope”，与本 Task 已追加 `/forecast/list` 不符，改注释即可。

6. 【`HEAT_FORECAST_TOPIC`】F0 已有 topic，本 Task 未生产/消费。按计划可接受，确认不是漏做。

---

## 审查结论

✅ 通过

计划范围内实现完整，F0 边界守住，Task 2 回归仍绿，当场 116 passed。无 🔴。建议优先处理 🟡-1（Hive 列名静默训假数据），其余 🟡 可与回复一并决定采纳或保留。
