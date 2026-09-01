"""Remaining-life estimate and anomaly forecast (sklearn with rule fallback)."""

import os
from pathlib import Path

import joblib
import numpy as np

from config.settings import settings

FEATURE_KEYS = (
    "supplyTemp",
    "returnTemp",
    "pressure",
    "flow",
    "corrosionRate",
    "roomTemp",
)


def _resolve_model_dir() -> str:
    raw = settings.MODEL_DIR
    path = Path(raw)
    if path.is_absolute():
        return str(path)
    repo_root = Path(__file__).resolve().parents[3]
    return str((repo_root / raw).resolve())


MODEL_DIR = _resolve_model_dir()


def remain_life(W_current: float, W_min: float, v_corr: float) -> float:
    if v_corr <= 0:
        return float("inf")
    return round((W_current - W_min) / v_corr, 2)


def predict_anomaly(features: dict) -> dict:
    path = os.path.join(MODEL_DIR, "anomaly_model.pkl")
    if not os.path.exists(path):
        is_anomaly = 1 if (
            features.get("supplyTemp", 99) < 5 or features.get("corrosionRate", 0) > 0.05
        ) else 0
        return {"is_anomaly": is_anomaly, "model": "rule"}
    model = joblib.load(path)
    X = np.array([[features.get(k, 0) for k in FEATURE_KEYS]])
    pred = model.predict(X)[0]
    return {"is_anomaly": 1 if pred == -1 else 0, "model": "ml"}
