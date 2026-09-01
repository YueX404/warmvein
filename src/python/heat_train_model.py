#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Train heating-network IsolationForest anomaly model.

Usage:
    python heat_train_model.py

Hive is optional: if Spark/Hive is unavailable, synthetic samples are used
so the script can run locally and write models/anomaly_model.pkl.
"""

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_COLS = [
    "supplyTemp",
    "returnTemp",
    "pressure",
    "flow",
    "corrosionRate",
    "roomTemp",
]
MODEL_DIR = os.getenv("MODEL_DIR", "models")


def generate_sample_data(n_samples=2000, seed=42):
    rng = np.random.default_rng(seed)
    n_anom = max(1, n_samples // 20)
    data = {
        "supplyTemp": rng.uniform(40, 90, n_samples),
        "returnTemp": rng.uniform(30, 60, n_samples),
        "pressure": rng.uniform(0.2, 0.8, n_samples),
        "flow": rng.uniform(10, 80, n_samples),
        "corrosionRate": rng.uniform(0.001, 0.04, n_samples),
        "roomTemp": rng.uniform(16, 24, n_samples),
    }
    data["supplyTemp"][:n_anom] = rng.uniform(0, 4, n_anom)
    data["corrosionRate"][:n_anom] = rng.uniform(0.06, 0.12, n_anom)
    return pd.DataFrame(data)


def load_hive_frame():
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder.appName("TrainHeatAnomaly")
        .enableHiveSupport()
        .getOrCreate()
    )
    try:
        return spark.sql(
            """
            SELECT supplyTemp, returnTemp, pressure, flow, corrosionRate, roomTemp
            FROM dwd.heat_sensor_detail
            WHERE supplyTemp IS NOT NULL
            """
        ).toPandas()
    finally:
        spark.stop()


def load_data():
    try:
        df = load_hive_frame()
        if df is not None and not df.empty:
            return df
    except Exception as exc:
        print(f"Hive unavailable, using synthetic samples: {exc}")
    return generate_sample_data()


def train_anomaly_model(df):
    X = df[FEATURE_COLS].fillna(0).to_numpy()
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "detector",
                IsolationForest(
                    n_estimators=100,
                    contamination=0.05,
                    random_state=42,
                ),
            ),
        ]
    )
    pipeline.fit(X)
    return pipeline


def save_model(model):
    os.makedirs(MODEL_DIR, exist_ok=True)
    path = os.path.join(MODEL_DIR, "anomaly_model.pkl")
    joblib.dump(model, path)
    print(f"model saved: {path}")
    return path


def main():
    df = load_data()
    model = train_anomaly_model(df)
    save_model(model)


if __name__ == "__main__":
    main()
