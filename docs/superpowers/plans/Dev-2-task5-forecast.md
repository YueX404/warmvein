# Dev-2 Task 5: 故障预报与寿命预测 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **分支：** `dev-2/feature/task5-forecast`
> **基线：** Task 2（`dev-2/feature/task2-alarm-map`）已合入 `main`，或叠在该分支上。禁止与 Task 2 同时改 `routes_alarm.py`。
> **索引：** [Dev-2-处置流.md](./Dev-2-处置流.md)

**Goal:** 提供剩余寿命线性估算与异常预报（sklearn + 规则兜底），并在 `routes_alarm.py` 追加 `GET /api/forecast/list`。

**Architecture:** 新建 `forecast.py` 与 `heat_train_model.py`。只在 `routes_alarm.py` **末尾追加** `/forecast/list`，保留 Task 2 的 list/ack。

**Tech Stack:** Python 3.10+ / FastAPI / scikit-learn / joblib。

## Global Constraints

- 见索引文档 Global Constraints。
- 独占：`services/forecast.py`、`heat_train_model.py`、`tests/test_forecast.py`；`routes_alarm.py` 仅追加预报路由。
- `biz_forecast` 列以 F0 为准，不要用 `period_month`。

---

### Task 5: 寿命/预报模型训练与预测接口

**Files:**
- Create: `src/python/heat_train_model.py`
- Create: `src/python/services/forecast.py`
- Modify: `src/python/routes_alarm.py`（仅追加）
- Create: `tests/test_forecast.py`

**Interfaces:**
- Produces: `remain_life(W_current, W_min, v_corr) -> float`、`predict_anomaly(features) -> dict`、`GET /api/forecast/list`

- [ ] **Step 1: 确认基线**

`routes_alarm.py` 中应已有 `/alarm/list` 与 `/alarm/ack`。没有则先合入 Task 2。

- [ ] **Step 2: 写失败测试**

```python
from services.forecast import remain_life
def test_remain_life_linear():
    assert remain_life(5.0, 3.0, 0.1) == 20.0
def test_remain_life_inf_safe():
    assert remain_life(5.0, 3.0, 0) == float('inf')
```

- [ ] **Step 3: 运行失败**

Run: `pytest tests/test_forecast.py -v`
Expected: FAIL with "cannot import" 或 "function not defined"

- [ ] **Step 4: 实现 services/forecast.py**

```python
import os, joblib
import numpy as np

MODEL_DIR = os.getenv("MODEL_DIR", "models")

def remain_life(W_current: float, W_min: float, v_corr: float) -> float:
    if v_corr <= 0:
        return float('inf')
    return round((W_current - W_min) / v_corr, 2)

def predict_anomaly(features: dict) -> dict:
    path = os.path.join(MODEL_DIR, "anomaly_model.pkl")
    if not os.path.exists(path):
        return {"is_anomaly": 1 if (features.get("supplyTemp", 99) < 5 or features.get("corrosionRate", 0) > 0.05) else 0,
                "model": "rule"}
    model = joblib.load(path)
    X = np.array([[features.get(k, 0) for k in
                   ["supplyTemp","returnTemp","pressure","flow","corrosionRate","roomTemp"]]])
    pred = model.predict(X)[0]
    return {"is_anomaly": 1 if pred == -1 else 0, "model": "ml"}
```

- [ ] **Step 5: 在 routes_alarm.py 末尾追加（保留 list/ack）**

```python
@router.get("/forecast/list")
def api_forecast(ftype: str = None):
    with SessionLocal() as s:
        rows = [dict(r) for r in s.execute(text(
            "SELECT forecast_id, station_id, type, title, risk_level, forecast_date, status, created_at "
            "FROM biz_forecast WHERE (:t IS NULL OR type=:t)"),
            {"t": ftype}).mappings().all()]
    return ok(rows)
```

复用已有 import，不要再建第二个 `APIRouter()`。

- [ ] **Step 6: 改造 heat_train_model.py**

沿用 `train_sklearn_model.py` 的 IsolationForest，特征改为 `supplyTemp, returnTemp, pressure, flow, corrosionRate, roomTemp`；输出 `models/anomaly_model.pkl`。无 Hive 时用合成样本，保证本地可跑。

- [ ] **Step 7: 补路由测试并跑通**

```python
from fastapi.testclient import TestClient
from main import app

def test_forecast_list():
    c = TestClient(app)
    r = c.get("/api/forecast/list")
    assert r.status_code == 200 and r.json()["code"] == 0
```

Run: `pytest tests/test_forecast.py tests/test_alarm_routes.py -v`
Expected: PASS（不得破坏 Task 2 测试）

- [ ] **Step 8: 提交** `git commit -m "feat(4.2): 故障预报/寿命预测模型与接口"`
