# Task-5 Code Review 反馈（二次审查）

审查分支：`dev-2/feature/task5-forecast`  
审查 commit：`46b451a`（首轮 HEAD `d493e32`；修复 `b2b7649`；回复文档 `46b451a`）  
审查时间：2026-09-01  
对照：`snapshots/role-a/review-reply-a.md`、首轮 `review-feedback-a.md`（commit `d493e32` 时版本）  
审查方式：主仓库保持 `master` 未切换；只读审查 worktree  
单测当场：`pytest tests/test_forecast.py tests/test_alarm_routes.py -v` → **24 passed**；`pytest tests` → **119 passed**

---

## 首轮关闭情况

| 编号 | 本轮判定 | 核对 |
|---|---|---|
| 🟡-1 Hive 列名 | **关闭** | `HIVE_FEATURE_SQL` 使用 F0 `supply_temp AS supplyTemp` 等；回退前缀为 `Hive feature query failed`；`test_hive_sql_aliases_f0_columns` 覆盖 |
| 🟡-2 合成异常叠加 | **关闭** | 低温与高腐蚀分到不同行；`test_synthetic_anomalies_are_split` 断言两因子可单独出现 |
| 🟡-3 ML 单测过弱 | **关闭** | `train_anomaly_model` 产出 Pipeline 后 dump，极端样本 `is_anomaly==1` |
| 🟡-4 列表缺 description/suggestion | **关闭** | SELECT 与 `_to_forecast` 已补；列表单测断言两字段 |
| 🟡-5 MODEL_DIR | **关闭** | 读 `settings.MODEL_DIR`，相对路径按仓库根解析；有绝对路径单测 |
| 🟡-6 演示空表 | **关闭** | 手工 `config/mysql/forecast_seed.sql`（`WHERE NOT EXISTS`，未改 `heat_init.sql`） |
| 🔵-1～6 | **接受** | 见 `review-reply-a.md`：列表不实时算模型、不改 api-guide、本窗口不 rebase、remain_life 不接 HTTP、护栏注释已改、forecast topic 非本 Task |

未改 F0 冻结文件；独占范围外仍只有 Task 2 护栏测试与本次种子 SQL。

---

## 🔴 阻断性问题（必须修改）

无。

---

## 🟡 改进建议

无（首轮 🟡-1～🟡-6 均已关闭）。

---

## 🔵 疑问确认

1. 【`dev-record-a.md`】Commit 表缺 `46b451a`（审查回复文档），无功能影响。
2. 【`forecast.py:21-27` 与 `heat_train_model.py:46-52`】`_resolve_model_dir` 两份拷贝，`parents[3]` / `parents[2]` 依赖文件深度。当前解析正确；以后搬文件时容易漂。可 follow-up 抽到一处。
3. 【`forecast_seed.sql`】按 `type` 去重，重复执行不会堆行；演示执行一次即可。仍不并入 `heat_init.sql`。

🔵-1/2/3/4/6 按回复接受，不要求本 PR 再改。

---

## 审查结论

✅ 通过，建议合入

首轮 🟡 已全部落地且有单测钉住，本轮无新阻断项。可将 `progress.md` 标为审查通过，进入收尾（push / 提 PR）。合入时注意 `snapshots/role-a/*` 与 master 冲突，不要覆盖已合入 Task 的进度说明。
