#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业设备机器学习模型训练脚本

功能：
1. 从Hive读取设备传感器特征数据
2. 训练孤立森林异常检测模型
3. 训练剩余使用寿命(RUL)回归预测模型
4. 训练设备健康度评分分类模型
5. 保存模型为pickle格式供FastAPI使用

使用示例：
    python train_sklearn_model.py

依赖：
    pyspark, pandas, scikit-learn, joblib
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest, RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    classification_report, mean_squared_error, accuracy_score
)


def create_spark_session():
    """创建SparkSession用于读取Hive数据"""
    from pyspark.sql import SparkSession
    spark = SparkSession.builder \
        .appName("TrainDeviceModels") \
        .enableHiveSupport() \
        .getOrCreate()
    return spark


def load_data(spark):
    """
    从Hive加载设备传感器特征数据

    Returns:
        pd.DataFrame: 特征数据
    """
    try:
        df = spark.sql("""
            SELECT
                device_id,
                device_type,
                workshop,
                status_code,
                spindle_temp,
                hydraulic_pressure,
                vibration,
                spindle_load,
                joint_current,
                servo_temp,
                reducer_temp,
                joint_vibration,
                injection_pressure,
                barrel_temp,
                mold_temp,
                hydraulic_oil_temp,
                discharge_temp,
                lubricant_temp,
                motor_current,
                power,
                health_score,
                alarm_code,
                CASE WHEN alarm_code != 0 OR status_code IN (4, 5) THEN 1 ELSE 0 END AS is_abnormal
            FROM dwd.device_sensor_detail
            WHERE spindle_temp IS NOT NULL OR servo_temp IS NOT NULL
                 OR discharge_temp IS NOT NULL
        """).toPandas()
        print(f"从Hive加载 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"Hive加载失败: {e}")
        print("生成模拟训练数据...")
        return generate_sample_data()


def generate_sample_data():
    """
    生成模拟设备传感器训练数据

    Returns:
        pd.DataFrame: 模拟数据
    """
    np.random.seed(42)
    n_samples = 10000

    device_types = ['CNC加工中心', '六轴工业机器人', '伺服注塑机', '螺杆空压机']
    workshops = ['机加工一车间', '装配车间', '注塑车间', '公用工程车间']

    data = {
        'device_id': [f'DEV-{i:04d}' for i in range(n_samples)],
        'device_type': np.random.choice(device_types, n_samples),
        'workshop': np.random.choice(workshops, n_samples),
        'status_code': np.random.choice([0, 1, 2, 3, 4, 5, 6], n_samples,
                                        p=[0.05, 0.1, 0.65, 0.08, 0.07, 0.02, 0.03]),
    }

    # 生成温度类参数（25~90℃）
    for col in ['spindle_temp', 'servo_temp', 'reducer_temp', 'barrel_temp',
                'mold_temp', 'hydraulic_oil_temp', 'discharge_temp', 'lubricant_temp']:
        data[col] = np.random.uniform(25, 90, n_samples)

    # 生成压力类参数
    for col in ['hydraulic_pressure', 'injection_pressure']:
        data[col] = np.random.uniform(4, 145, n_samples)

    # 生成振动类参数
    for col in ['vibration', 'joint_vibration']:
        data[col] = np.random.uniform(0.3, 4.5, n_samples)

    # 生成电气类参数
    data['spindle_load'] = np.random.uniform(20, 95, n_samples)
    data['joint_current'] = np.random.uniform(2, 7.5, n_samples)
    data['motor_current'] = np.random.uniform(40, 90, n_samples)
    data['power'] = np.random.uniform(15, 50, n_samples)

    # 生成健康度评分（基于参数综合计算）
    health_scores = []
    for i in range(n_samples):
        base = 95
        # 温度过高扣分
        for temp_col in ['spindle_temp', 'servo_temp', 'discharge_temp']:
            if data[temp_col][i] > 80:
                base -= (data[temp_col][i] - 80) * 1.5
        # 振动过大扣分
        if data['vibration'][i] > 3.5:
            base -= (data['vibration'][i] - 3.5) * 10
        # 负载过高扣分
        if data['spindle_load'][i] > 90:
            base -= (data['spindle_load'][i] - 90) * 2
        health_scores.append(max(10, min(100, int(base))))

    data['health_score'] = health_scores

    # 生成告警标签（健康度<50或状态为故障/急停视为异常）
    data['alarm_code'] = 0
    for i in range(n_samples):
        if data['status_code'][i] in (4, 5) or health_scores[i] < 50:
            data['alarm_code'][i] = np.random.randint(1001, 4006)
        elif data['status_code'][i] == 3 and np.random.random() < 0.3:
            data['alarm_code'][i] = np.random.randint(1001, 4006)

    data['is_abnormal'] = (data['alarm_code'] != 0).astype(int)

    return pd.DataFrame(data)


def preprocess_data(df):
    """
    数据预处理：特征工程

    Args:
        df (pd.DataFrame): 原始数据

    Returns:
        tuple: (特征X, 异常标签y_anomaly, RUL标签y_rul, 健康度标签y_health, 特征列名)
    """
    # 数值特征列
    numeric_features = [
        'spindle_temp', 'hydraulic_pressure', 'vibration', 'spindle_load',
        'joint_current', 'servo_temp', 'reducer_temp', 'joint_vibration',
        'injection_pressure', 'barrel_temp', 'mold_temp', 'hydraulic_oil_temp',
        'discharge_temp', 'lubricant_temp', 'motor_current', 'power'
    ]

    # 填充缺失值为0
    for col in numeric_features:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    X = df[numeric_features].copy()

    # 异常检测标签
    y_anomaly = df['is_abnormal'].copy()

    # RUL标签：基于健康度映射剩余寿命百分比
    # 健康度越高，RUL越大
    y_rul = df['health_score'].apply(lambda h: max(10, min(100, h))).copy()

    # 健康度分类标签（0=差, 1=中, 2=良, 3=优）
    y_health = df['health_score'].apply(
        lambda h: 3 if h >= 80 else (2 if h >= 60 else (1 if h >= 40 else 0))
    ).copy()

    return X, y_anomaly, y_rul, y_health, numeric_features


def train_anomaly_detection_model(X_train, y_train, numeric_features):
    """
    训练孤立森林异常检测模型

    Args:
        X_train: 训练特征
        y_train: 训练标签
        numeric_features: 特征列名

    Returns:
        Pipeline: 训练好的模型管道
    """
    print("训练异常检测模型（孤立森林）...")

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('detector', IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1
        ))
    ])

    # 孤立森林是无监督学习，只使用正常数据训练
    normal_mask = y_train == 0
    pipeline.fit(X_train[normal_mask])

    # 评估
    y_pred = pipeline.predict(X_train)
    y_pred_binary = [1 if p == -1 else 0 for p in y_pred]
    accuracy = accuracy_score(y_train, y_pred_binary)
    print(f"异常检测准确率: {accuracy:.4f}")

    return pipeline


def train_rul_model(X_train, y_train, X_test, y_test, numeric_features):
    """
    训练剩余使用寿命(RUL)预测模型

    Args:
        X_train: 训练特征
        y_train: 训练标签
        X_test: 测试特征
        y_test: 测试标签
        numeric_features: 特征列名

    Returns:
        Pipeline: 训练好的回归模型
    """
    print("训练RUL预测模型（随机森林回归）...")

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        ))
    ])

    pipeline.fit(X_train, y_train)

    # 评估
    y_pred = pipeline.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"RUL预测MSE: {mse:.4f}")
    print(f"RUL预测RMSE: {np.sqrt(mse):.4f}")

    return pipeline


def train_health_classification_model(X_train, y_train, X_test, y_test, numeric_features):
    """
    训练设备健康度分类模型

    Args:
        X_train: 训练特征
        y_train: 训练标签
        X_test: 测试特征
        y_test: 测试标签
        numeric_features: 特征列名

    Returns:
        Pipeline: 训练好的分类模型
    """
    print("训练健康度分类模型（随机森林分类）...")

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        ))
    ])

    pipeline.fit(X_train, y_train)

    # 评估
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"健康度分类准确率: {accuracy:.4f}")
    print("\n分类报告:")
    print(classification_report(y_test, y_pred,
                                target_names=['差(0-40)', '中(40-60)', '良(60-80)', '优(80-100)']))

    return pipeline


def save_model(model, model_name):
    """保存模型到文件"""
    os.makedirs("models", exist_ok=True)
    filepath = f"models/{model_name}.pkl"
    joblib.dump(model, filepath)
    print(f"模型已保存: {filepath}")


def main():
    """主函数"""
    print("=" * 60)
    print("工业设备机器学习模型训练")
    print("=" * 60)

    os.makedirs("models", exist_ok=True)

    # 加载数据
    try:
        print("\n尝试连接Spark...")
        spark = create_spark_session()
        df = load_data(spark)
        spark.stop()
        print("✓ 从Spark加载数据成功")
    except Exception as e:
        print(f"⚠ Spark不可用，使用模拟数据: {e}")
        df = generate_sample_data()

    # 数据预处理
    print("\n开始数据预处理...")
    X, y_anomaly, y_rul, y_health, numeric_features = preprocess_data(df)
    print(f"✓ 预处理完成，样本数: {len(X)}")
    print(f"  异常样本: {y_anomaly.sum()} ({y_anomaly.sum() / len(y_anomaly) * 100:.1f}%)")

    # 划分数据集
    X_train, X_test, y_anomaly_train, y_anomaly_test = train_test_split(
        X, y_anomaly, test_size=0.2, random_state=42
    )
    _, _, y_rul_train, y_rul_test = train_test_split(
        X, y_rul, test_size=0.2, random_state=42
    )
    _, _, y_health_train, y_health_test = train_test_split(
        X, y_health, test_size=0.2, random_state=42
    )

    # 训练异常检测模型
    print("\n" + "=" * 60)
    print("训练异常检测模型")
    print("=" * 60)
    anomaly_model = train_anomaly_detection_model(X_train, y_anomaly_train, numeric_features)
    save_model(anomaly_model, 'anomaly_model')

    # 训练RUL预测模型
    print("\n" + "=" * 60)
    print("训练RUL预测模型")
    print("=" * 60)
    rul_model = train_rul_model(X_train, y_rul_train, X_test, y_rul_test, numeric_features)
    save_model(rul_model, 'rul_model')

    # 训练健康度分类模型
    print("\n" + "=" * 60)
    print("训练健康度分类模型")
    print("=" * 60)
    health_model = train_health_classification_model(
        X_train, y_health_train, X_test, y_health_test, numeric_features
    )
    save_model(health_model, 'health_model')

    print("\n" + "=" * 60)
    print("✓ 所有模型训练完成并保存成功！")
    print("=" * 60)
    print("模型文件位置:")
    print("  - models/anomaly_model.pkl (异常检测)")
    print("  - models/rul_model.pkl (RUL剩余寿命预测)")
    print("  - models/health_model.pkl (健康度分类)")
    print("=" * 60)


if __name__ == "__main__":
    main()
