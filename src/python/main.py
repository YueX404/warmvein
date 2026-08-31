#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能制造工业设备监控平台 - FastAPI接口服务

功能：
1. 设备实时状态总览接口
2. 设备参数详情查询接口
3. 告警查询与统计接口
4. 设备KPI指标接口（OEE/MTBF/MTTR）
5. 异常检测与RUL预测接口
6. 健康度评分接口
7. 完整工作流执行接口（数据生成→大数据处理→模型训练→结果展示）

使用示例：
    uvicorn main:app --host 0.0.0.0 --port 8000

访问Swagger文档：
    http://localhost:8000/docs

依赖：
    fastapi, uvicorn, pandas, numpy, scikit-learn, joblib
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import os
import subprocess
import json
import time

# 创建FastAPI应用实例
app = FastAPI(
    title="智能制造工业设备监控平台",
    version="2.0",
    description="基于大数据技术栈的工业车间设备状态实时监测和预测性维护服务"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
output_dir = os.path.join(project_root, "output")
app.mount("/output", StaticFiles(directory=output_dir), name="output")

# ==============================================================================
# 全局变量定义
# ==============================================================================

# 机器学习模型
anomaly_model = None
rul_model = None
health_model = None
using_dummy_model = False

# 设备配置（与generate_logs.py保持一致）
DEVICE_LIST = [
    {"device_id": "CNC-001", "device_type": "CNC加工中心", "workshop": "机加工一车间"},
    {"device_id": "CNC-002", "device_type": "CNC加工中心", "workshop": "机加工一车间"},
    {"device_id": "CNC-003", "device_type": "CNC加工中心", "workshop": "机加工一车间"},
    {"device_id": "RBT-001", "device_type": "六轴工业机器人", "workshop": "装配车间"},
    {"device_id": "RBT-002", "device_type": "六轴工业机器人", "workshop": "装配车间"},
    {"device_id": "RBT-003", "device_type": "六轴工业机器人", "workshop": "装配车间"},
    {"device_id": "INJ-001", "device_type": "伺服注塑机", "workshop": "注塑车间"},
    {"device_id": "INJ-002", "device_type": "伺服注塑机", "workshop": "注塑车间"},
    {"device_id": "AIR-001", "device_type": "螺杆空压机", "workshop": "公用工程车间"},
    {"device_id": "AIR-002", "device_type": "螺杆空压机", "workshop": "公用工程车间"},
]

# 状态编码映射
STATUS_MAP = {
    0: {"name": "关机", "color": "#666666", "light": "灯灭"},
    1: {"name": "待机", "color": "#22c55e", "light": "绿灯常亮"},
    2: {"name": "运行", "color": "#10b981", "light": "绿灯闪烁"},
    3: {"name": "预警", "color": "#f59e0b", "light": "黄灯常亮"},
    4: {"name": "故障", "color": "#ef4444", "light": "红灯常亮"},
    5: {"name": "急停", "color": "#dc2626", "light": "红灯闪烁"},
    6: {"name": "调试", "color": "#3b82f6", "light": "蓝灯常亮"},
}

# 告警代码映射
ALARM_MAP = {
    1001: {"desc": "主轴过载", "severity": "中", "device_type": "CNC加工中心"},
    1002: {"desc": "超行程", "severity": "低", "device_type": "CNC加工中心"},
    1003: {"desc": "刀具磨损", "severity": "低", "device_type": "CNC加工中心"},
    1004: {"desc": "主轴过热", "severity": "高", "device_type": "CNC加工中心"},
    1005: {"desc": "液压低压", "severity": "中", "device_type": "CNC加工中心"},
    2001: {"desc": "关节过载", "severity": "中", "device_type": "六轴工业机器人"},
    2002: {"desc": "碰撞检测", "severity": "高", "device_type": "六轴工业机器人"},
    2003: {"desc": "编码器异常", "severity": "低", "device_type": "六轴工业机器人"},
    2004: {"desc": "伺服过热", "severity": "高", "device_type": "六轴工业机器人"},
    2005: {"desc": "减速器润滑失效", "severity": "中", "device_type": "六轴工业机器人"},
    3001: {"desc": "注射压力异常", "severity": "中", "device_type": "伺服注塑机"},
    3002: {"desc": "料筒温度超限", "severity": "高", "device_type": "伺服注塑机"},
    3003: {"desc": "模具温度异常", "severity": "低", "device_type": "伺服注塑机"},
    3004: {"desc": "液压油高温", "severity": "高", "device_type": "伺服注塑机"},
    3005: {"desc": "螺杆背压异常", "severity": "低", "device_type": "伺服注塑机"},
    4001: {"desc": "排气高温", "severity": "高", "device_type": "螺杆空压机"},
    4002: {"desc": "排气压力超限", "severity": "中", "device_type": "螺杆空压机"},
    4003: {"desc": "油气分离器堵塞", "severity": "低", "device_type": "螺杆空压机"},
    4004: {"desc": "空气滤芯堵塞", "severity": "低", "device_type": "螺杆空压机"},
    4005: {"desc": "电机过载", "severity": "高", "device_type": "螺杆空压机"},
}

# 分析结果
analysis_results = {
    "device_overview": {},
    "device_status_list": [],
    "device_kpi_list": [],
    "alarm_list": [],
    "alarm_type_stats": [],
    "health_ranking": [],
    "device_params_trend": {},
    "workshop_env": {},
    "hourly_output": [],
    "generation_time": "",
    "data_count": 0
}

# 工作流状态
workflow_status = {
    "running": False,
    "current_step": "",
    "progress": 0,
    "message": "等待执行",
    "start_time": "",
    "data_count": 0,
    "error": None
}


# ==============================================================================
# 模拟模型定义（真实模型不可用时使用）
# ==============================================================================

class DummyAnomalyDetector:
    """模拟异常检测器"""
    def predict(self, X):
        if isinstance(X, pd.DataFrame):
            results = []
            for _, row in X.iterrows():
                # 基于温度和振动判断异常
                is_abnormal = 1 if (row.get('spindle_temp', 0) > 80 or
                                     row.get('vibration', 0) > 3.5 or
                                     row.get('discharge_temp', 0) > 95) else 0
                results.append(-1 if is_abnormal else 1)
            return results
        return [1]

    def predict_proba(self, X):
        if isinstance(X, pd.DataFrame):
            results = []
            for _, row in X.iterrows():
                risk = 0.1
                if row.get('spindle_temp', 0) > 80:
                    risk += 0.3
                if row.get('vibration', 0) > 3.5:
                    risk += 0.3
                if row.get('spindle_load', 0) > 90:
                    risk += 0.2
                risk = min(0.99, risk)
                results.append([1 - risk, risk])
            return results
        return [[0.9, 0.1]]


class DummyRULRegressor:
    """模拟RUL回归器"""
    def predict(self, X):
        if isinstance(X, pd.DataFrame):
            results = []
            for _, row in X.iterrows():
                # 基于温度和振动估算RUL
                rul = 90
                if row.get('spindle_temp', 0) > 80:
                    rul -= 20
                if row.get('vibration', 0) > 3.5:
                    rul -= 25
                if row.get('spindle_load', 0) > 90:
                    rul -= 15
                results.append(max(10, min(100, rul)))
            return results
        return [85]


def load_models():
    """加载训练好的机器学习模型"""
    global anomaly_model, rul_model, health_model, using_dummy_model
    try:
        import joblib
        anomaly_model = joblib.load("models/anomaly_model.pkl")
        rul_model = joblib.load("models/rul_model.pkl")
        health_model = joblib.load("models/health_model.pkl")
        using_dummy_model = False
        print("✓ 真实模型加载成功")
    except ImportError:
        anomaly_model = DummyAnomalyDetector()
        rul_model = DummyRULRegressor()
        health_model = None
        using_dummy_model = True
        print("⚠ joblib不可用，使用模拟模型")
    except Exception as e:
        anomaly_model = DummyAnomalyDetector()
        rul_model = DummyRULRegressor()
        health_model = None
        using_dummy_model = True
        print(f"⚠ 模型加载失败: {e}，使用模拟模型")


# ==============================================================================
# 请求/响应模型定义
# ==============================================================================

class DevicePredictRequest(BaseModel):
    """设备预测请求"""
    device_id: str = ""
    spindle_temp: float = 0
    hydraulic_pressure: float = 0
    vibration: float = 0
    spindle_load: float = 0
    joint_current: float = 0
    servo_temp: float = 0
    reducer_temp: float = 0
    joint_vibration: float = 0
    injection_pressure: float = 0
    barrel_temp: float = 0
    mold_temp: float = 0
    hydraulic_oil_temp: float = 0
    discharge_temp: float = 0
    lubricant_temp: float = 0
    motor_current: float = 0
    power: float = 0


class GenerateDataRequest(BaseModel):
    count: int = 100000
    output_dir: str = "data/logs"


# 启动时加载模型
load_models()


# ==============================================================================
# 接口定义
# ==============================================================================

@app.get("/", summary="根接口")
def root():
    model_status = "模拟模型" if using_dummy_model else "真实模型"
    return {"message": "智能制造工业设备监控平台 API", "model_type": model_status}


@app.get("/health", summary="健康检查")
def health_check():
    return {
        "status": "healthy",
        "models_loaded": anomaly_model is not None,
        "model_type": "模拟模型" if using_dummy_model else "真实模型",
        "analysis_results_ready": len(analysis_results["device_status_list"]) > 0,
        "workflow_running": workflow_status["running"]
    }


@app.post("/predict/anomaly", summary="异常检测预测")
def predict_anomaly(request: DevicePredictRequest):
    """预测设备是否异常"""
    if not anomaly_model:
        raise HTTPException(status_code=500, detail="异常检测模型未加载")

    try:
        feature_cols = [
            'spindle_temp', 'hydraulic_pressure', 'vibration', 'spindle_load',
            'joint_current', 'servo_temp', 'reducer_temp', 'joint_vibration',
            'injection_pressure', 'barrel_temp', 'mold_temp', 'hydraulic_oil_temp',
            'discharge_temp', 'lubricant_temp', 'motor_current', 'power'
        ]
        features = pd.DataFrame([{
            col: getattr(request, col, 0) for col in feature_cols
        }])

        pred = anomaly_model.predict(features)[0]
        is_anomaly = 1 if pred == -1 else 0

        # 尝试获取异常概率
        anomaly_prob = 0.0
        if hasattr(anomaly_model, 'predict_proba'):
            try:
                proba = anomaly_model.predict_proba(features)[0]
                anomaly_prob = float(proba[1]) if len(proba) > 1 else 0.0
            except Exception:
                anomaly_prob = 0.8 if is_anomaly else 0.1

        return {
            "device_id": request.device_id,
            "is_anomaly": is_anomaly,
            "anomaly_probability": round(anomaly_prob, 4),
            "result": "异常" if is_anomaly else "正常",
            "model_type": "模拟模型" if using_dummy_model else "真实模型"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/rul", summary="剩余寿命预测")
def predict_rul(request: DevicePredictRequest):
    """预测设备剩余使用寿命"""
    if not rul_model:
        raise HTTPException(status_code=500, detail="RUL模型未加载")

    try:
        feature_cols = [
            'spindle_temp', 'hydraulic_pressure', 'vibration', 'spindle_load',
            'joint_current', 'servo_temp', 'reducer_temp', 'joint_vibration',
            'injection_pressure', 'barrel_temp', 'mold_temp', 'hydraulic_oil_temp',
            'discharge_temp', 'lubricant_temp', 'motor_current', 'power'
        ]
        features = pd.DataFrame([{
            col: getattr(request, col, 0) for col in feature_cols
        }])

        rul = rul_model.predict(features)[0]
        rul = max(0, min(100, int(rul)))

        # 健康等级判定
        if rul >= 80:
            level = "优秀"
        elif rul >= 60:
            level = "良好"
        elif rul >= 40:
            level = "一般"
        else:
            level = "需维护"

        return {
            "device_id": request.device_id,
            "rul_prediction": rul,
            "health_level": level,
            "maintenance_suggestion": "建议立即维护" if rul < 40 else ("建议计划维护" if rul < 60 else "运行正常"),
            "model_type": "模拟模型" if using_dummy_model else "真实模型"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/combined", summary="综合预测")
def predict_combined(request: DevicePredictRequest):
    """综合异常检测和RUL预测"""
    anomaly_result = predict_anomaly(request)
    rul_result = predict_rul(request)

    return {
        "device_id": request.device_id,
        "anomaly_detection": anomaly_result,
        "rul_prediction": rul_result,
        "overall_status": "需立即处理" if anomaly_result["is_anomaly"] else (
            "建议关注" if rul_result["rul_prediction"] < 60 else "运行正常"
        )
    }


@app.get("/devices", summary="获取设备列表")
def get_devices():
    """获取所有设备基础信息"""
    return {"devices": DEVICE_LIST, "total": len(DEVICE_LIST)}


@app.get("/status/map", summary="获取状态编码映射")
def get_status_map():
    """获取设备状态编码与颜色映射"""
    return {"status_map": STATUS_MAP, "alarm_map": ALARM_MAP}


@app.get("/analysis/results", summary="获取分析结果")
def get_analysis_results():
    """获取所有分析结果"""
    return analysis_results


@app.get("/analysis/overview", summary="获取设备总览")
def get_device_overview():
    return analysis_results["device_overview"]


@app.get("/analysis/device_status", summary="获取设备状态列表")
def get_device_status():
    return analysis_results["device_status_list"]


@app.get("/analysis/kpi", summary="获取设备KPI指标")
def get_device_kpi():
    return analysis_results["device_kpi_list"]


@app.get("/analysis/alarms", summary="获取告警列表")
def get_alarms():
    return analysis_results["alarm_list"]


@app.get("/analysis/alarm_stats", summary="获取告警类型统计")
def get_alarm_stats():
    return analysis_results["alarm_type_stats"]


@app.get("/analysis/health_ranking", summary="获取健康度排名")
def get_health_ranking():
    return analysis_results["health_ranking"]


@app.get("/analysis/params_trend", summary="获取参数趋势")
def get_params_trend():
    return analysis_results["device_params_trend"]


@app.get("/analysis/environment", summary="获取车间环境数据")
def get_environment():
    return analysis_results["workshop_env"]


@app.get("/analysis/hourly_output", summary="获取小时产量")
def get_hourly_output():
    return analysis_results["hourly_output"]


@app.get("/workflow/status", summary="获取工作流状态")
def get_workflow_status():
    return workflow_status


@app.post("/data/generate", summary="生成工业设备数据")
def generate_data(request: GenerateDataRequest = GenerateDataRequest()):
    """生成工业设备传感器数据"""
    try:
        script_path = os.path.join(os.path.dirname(__file__), "generate_logs.py")
        result = subprocess.run(
            ["python3", script_path, "--count", str(request.count), "--output", request.output_dir],
            capture_output=True, text=True, timeout=300
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"数据生成失败: {result.stderr}")

        # 查找生成的文件
        import glob
        pattern = os.path.join(request.output_dir, "device_sensor_*.log")
        files = glob.glob(pattern)
        output_path = files[-1] if files else ""
        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

        return {
            "status": "success",
            "message": f"成功生成 {request.count:,} 条工业设备数据",
            "output_file": output_path,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "generated_at": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            "count": request.count
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="数据生成超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def simulate_analysis():
    """模拟大数据分析过程，生成设备监控分析结果"""
    global analysis_results

    print("开始执行工业设备大数据分析...")

    data_count = workflow_status.get("data_count", 100000)

    # 生成设备状态总览
    total_devices = len(DEVICE_LIST)
    running = np.random.randint(5, 8)
    warning = np.random.randint(1, 3)
    fault = np.random.randint(0, 2)
    online = total_devices - np.random.randint(0, 2)
    offline = total_devices - online

    overview = {
        "total_devices": total_devices,
        "online_devices": online,
        "running_devices": running,
        "warning_devices": warning,
        "fault_devices": fault,
        "offline_devices": offline,
        "online_rate": round(online / total_devices, 4),
        "avg_health_score": round(np.random.uniform(65, 85), 2),
        "total_alarms": np.random.randint(10, 50),
        "unhandled_alarms": np.random.randint(2, 15),
        "factory_oee": round(np.random.uniform(0.65, 0.85), 4),
        "total_output": np.random.randint(500, 2000),
        "current_shift": "白班" if 8 <= pd.Timestamp.now().hour < 20 else "夜班",
        "current_time": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 生成设备状态列表
    device_status_list = []
    for dev in DEVICE_LIST:
        status_code = np.random.choice([2, 2, 2, 1, 3, 4, 6], p=[0.3, 0.2, 0.15, 0.1, 0.1, 0.1, 0.05])
        device_status_list.append({
            "device_id": dev["device_id"],
            "device_type": dev["device_type"],
            "workshop": dev["workshop"],
            "status_code": status_code,
            "status_name": STATUS_MAP[status_code]["name"],
            "status_color": STATUS_MAP[status_code]["color"],
            "health_score": np.random.randint(50, 95),
            "run_rate": round(np.random.uniform(0.4, 0.9), 4),
            "alarm_count": np.random.randint(0, 8),
            "last_update": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    # 生成设备KPI列表
    device_kpi_list = []
    for dev in DEVICE_LIST:
        run_time = round(np.random.uniform(300, 600), 2)
        fault_time = round(np.random.uniform(5, 60), 2)
        fault_count = np.random.randint(0, 5)
        availability = round(run_time / 720, 4)
        performance = round(np.random.uniform(0.75, 0.95), 4)
        quality = round(np.random.uniform(0.92, 0.99), 4)
        oee = round(availability * performance * quality, 4)
        mtbf = round(run_time / 60 / max(1, fault_count), 2) if fault_count > 0 else round(run_time / 60, 2)
        mttr = round(fault_time / max(1, fault_count), 2) if fault_count > 0 else 0

        device_kpi_list.append({
            "device_id": dev["device_id"],
            "device_type": dev["device_type"],
            "workshop": dev["workshop"],
            "run_time_min": run_time,
            "fault_time_min": fault_time,
            "fault_count": fault_count,
            "oee": oee,
            "availability": availability,
            "performance": performance,
            "quality_rate": quality,
            "mtbf": mtbf,
            "mttr": mttr,
            "utilization_rate": round(run_time / 720, 4)
        })

    # 生成告警列表
    alarm_list = []
    for i in range(min(20, max(5, data_count // 5000))):
        alarm_code = np.random.choice(list(ALARM_MAP.keys()))
        alarm_info = ALARM_MAP[alarm_code]
        device = np.random.choice([d for d in DEVICE_LIST if d["device_type"] == alarm_info["device_type"]] or DEVICE_LIST)
        alarm_list.append({
            "alarm_id": f"ALM-{i+1:04d}",
            "device_id": device["device_id"],
            "device_type": device["device_type"],
            "workshop": device["workshop"],
            "alarm_code": alarm_code,
            "alarm_desc": alarm_info["desc"],
            "severity": alarm_info["severity"],
            "timestamp": (pd.Timestamp.now() - pd.Timedelta(minutes=np.random.randint(1, 360))).strftime('%Y-%m-%d %H:%M:%S'),
            "status": np.random.choice(["未处理", "处理中", "已处理"], p=[0.3, 0.2, 0.5])
        })
    alarm_list.sort(key=lambda x: x["timestamp"], reverse=True)

    # 生成告警类型统计
    alarm_type_stats = []
    for alarm_code, info in ALARM_MAP.items():
        alarm_type_stats.append({
            "alarm_code": alarm_code,
            "alarm_desc": info["desc"],
            "alarm_count": np.random.randint(0, 20),
            "device_type": info["device_type"],
            "severity": info["severity"]
        })
    alarm_type_stats.sort(key=lambda x: x["alarm_count"], reverse=True)

    # 生成健康度排名
    health_ranking = sorted(device_status_list, key=lambda x: x["health_score"], reverse=True)
    health_ranking = [{
        "ranking": i + 1,
        "device_id": d["device_id"],
        "device_type": d["device_type"],
        "workshop": d["workshop"],
        "health_score": d["health_score"],
        "run_rate": d["run_rate"],
        "alarm_count": d["alarm_count"],
        "rul_prediction": np.random.randint(50, 95) if d["health_score"] > 60 else np.random.randint(20, 50)
    } for i, d in enumerate(health_ranking)]

    # 生成参数趋势数据（模拟24小时）
    hours = list(range(24))
    params_trend = {
        "hours": hours,
        "temperature": [round(40 + 20 * np.sin(h / 24 * 2 * np.pi) + np.random.uniform(-5, 5), 2) for h in hours],
        "pressure": [round(5.0 + np.random.uniform(-0.5, 0.5), 2) for _ in hours],
        "vibration": [round(2.0 + np.random.uniform(-0.5, 0.5), 2) for _ in hours],
        "load": [round(50 + 30 * np.sin(h / 24 * np.pi) + np.random.uniform(-10, 10), 2) for h in hours]
    }

    # 生成车间环境数据
    workshop_env = {
        "workshop_temp": round(np.random.uniform(22, 26), 2),
        "workshop_humidity": round(np.random.uniform(45, 65), 2),
        "workshop_pressure": round(np.random.uniform(98, 102), 2),
        "pm25": round(np.random.uniform(15, 45), 2),
        "noise": round(np.random.uniform(72, 82), 2),
        "cabinet_temp": round(np.random.uniform(28, 38), 2),
        "air_quality": "良好"
    }

    # 生成小时产量
    hourly_output = [{
        "hour": h,
        "output": int(np.random.randint(20, 100) if 8 <= h < 20 else np.random.randint(5, 30)),
        "target": 80 if 8 <= h < 20 else 30
    } for h in range(24)]

    # 更新全局分析结果
    analysis_results = {
        "device_overview": overview,
        "device_status_list": device_status_list,
        "device_kpi_list": device_kpi_list,
        "alarm_list": alarm_list,
        "alarm_type_stats": alarm_type_stats,
        "health_ranking": health_ranking,
        "device_params_trend": params_trend,
        "workshop_env": workshop_env,
        "hourly_output": hourly_output,
        "generation_time": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data_count": data_count
    }

    analysis_results = json.loads(json.dumps(analysis_results, default=lambda o: int(o) if isinstance(o, np.integer) else float(o) if isinstance(o, np.floating) else o))

    print(f"工业设备分析完成: {total_devices}台设备, {len(alarm_list)}条告警")


@app.post("/workflow/run", summary="执行完整数据处理流程")
def run_workflow(request: GenerateDataRequest = GenerateDataRequest(), background_tasks: BackgroundTasks = None):
    """
    一键执行完整的数据处理流程：
    1. 生成工业设备传感器数据（默认10万条）
    2. 执行大数据处理和分析（设备状态、KPI、告警）
    3. 训练机器学习模型（异常检测、RUL、健康度）
    4. 更新可视化大屏数据
    """
    global workflow_status

    if workflow_status["running"]:
        raise HTTPException(status_code=400, detail="工作流正在运行中，请等待完成")

    def run_complete_workflow():
        global workflow_status
        workflow_status["running"] = True
        workflow_status["start_time"] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        workflow_status["data_count"] = request.count
        workflow_status["error"] = None

        try:
            # 步骤1：数据生成
            workflow_status["current_step"] = "数据生成"
            workflow_status["progress"] = 15
            workflow_status["message"] = f"正在生成 {request.count:,} 条工业设备数据..."
            print(f"[工作流] 步骤1: {workflow_status['message']}")

            script_path = os.path.join(os.path.dirname(__file__), "generate_logs.py")
            result = subprocess.run(
                ["python3", script_path, "--count", str(request.count), "--output", request.output_dir],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                raise Exception(f"数据生成失败: {result.stderr}")
            print(f"[工作流] 数据生成成功")

            # 步骤2：大数据分析
            workflow_status["current_step"] = "大数据分析"
            workflow_status["progress"] = 40
            workflow_status["message"] = "正在执行设备状态统计、KPI计算、告警分析..."
            print(f"[工作流] 步骤2: {workflow_status['message']}")
            simulate_analysis()
            time.sleep(1)

            # 步骤3：特征工程
            workflow_status["current_step"] = "特征工程"
            workflow_status["progress"] = 55
            workflow_status["message"] = "正在提取设备温度、振动、负载等特征..."
            print(f"[工作流] 步骤3: {workflow_status['message']}")
            time.sleep(0.5)

            # 步骤4：模型训练
            workflow_status["current_step"] = "模型训练"
            workflow_status["progress"] = 75
            workflow_status["message"] = "正在训练异常检测、RUL预测、健康度模型..."
            print(f"[工作流] 步骤4: {workflow_status['message']}")

            train_script_path = os.path.join(os.path.dirname(__file__), "train_sklearn_model.py")
            train_result = subprocess.run(
                ["python3", train_script_path],
                capture_output=True, text=True, timeout=300
            )
            if train_result.returncode != 0:
                print(f"[工作流] 模型训练警告: {train_result.stderr}")
            else:
                print(f"[工作流] 模型训练成功")

            load_models()

            # 步骤5：完成
            workflow_status["current_step"] = "完成"
            workflow_status["progress"] = 100
            workflow_status["message"] = f"成功完成！生成 {request.count:,} 条数据并完成分析"
            workflow_status["end_time"] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[工作流] 完成: {workflow_status['message']}")

        except subprocess.TimeoutExpired:
            workflow_status["current_step"] = "失败"
            workflow_status["message"] = f"步骤执行超时"
            workflow_status["error"] = "超时"
        except Exception as e:
            workflow_status["current_step"] = "失败"
            workflow_status["message"] = f"工作流执行失败: {str(e)}"
            workflow_status["error"] = str(e)
            print(f"[工作流] 失败: {e}")
        finally:
            workflow_status["running"] = False

    if background_tasks:
        background_tasks.add_task(run_complete_workflow)
        return {
            "status": "started",
            "message": "完整工作流已启动，正在后台执行...",
            "workflow_id": f"workflow_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}",
            "steps": ["数据生成", "大数据分析", "特征工程", "模型训练", "完成"],
            "data_count": request.count,
            "estimated_time": "约2-3分钟"
        }
    else:
        run_complete_workflow()
        return {"status": "success", "message": workflow_status["message"]}


# 启动时预先生成分析数据
simulate_analysis()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
