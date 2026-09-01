#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供热管网模拟采集数据生成脚本。

生成换热站与分户用热时序记录，按 4% 概率注入异常
（冻堵前兆 / 室温不热 / 流量异常高=偷热），可写入文件或供 Kafka 实时发送。

使用示例：
    python heat_generate_logs.py --count 10000 --output data/logs
"""

import argparse
import json
import os
import random
from datetime import datetime, timedelta

from heat_kafka_producer import build_sensor_record

HEAT_CONFIGS = [
    {
        "kind": "station",
        "prefix": "ST",
        "count": 5,
        "params": {
            "supplyTemp": (60, 80, "℃"),
            "returnTemp": (40, 55, "℃"),
            "pressure": (0.4, 0.8, "MPa"),
            "flow": (80, 160, "t/h"),
            "heat": (50, 120, "GJ"),
            "corrosionRate": (0.0, 0.05, "mm/yr"),
            "roomTemp": (16, 22, "℃"),
            "outdoorTemp": (-15, 5, "℃"),
        },
    },
    {
        "kind": "user",
        "prefix": "U",
        "count": 200,
        "params": {
            "roomTemp": (14, 24, "℃"),
            "flow": (0.2, 1.5, "t/h"),
        },
    },
]

ANOMALY_RATE = 0.04
ALARM_LEVELS = {"frost": 3, "underheat": 2, "theft": 2}


def generate_entity_list():
    entities = []
    station_ids = []
    for config in HEAT_CONFIGS:
        for seq in range(1, config["count"] + 1):
            entity_id = f"{config['prefix']}-{seq:03d}"
            if config["kind"] == "station":
                station_ids.append(seq)
                entities.append({
                    "kind": "station",
                    "entity_id": entity_id,
                    "station_id": seq,
                    "params_config": config["params"],
                })
            else:
                station_id = station_ids[(seq - 1) % len(station_ids)] if station_ids else 1
                entities.append({
                    "kind": "user",
                    "entity_id": entity_id,
                    "station_id": station_id,
                    "user_id": seq,
                    "params_config": config["params"],
                })
    return entities


def pick_anomaly_type(kind):
    if random.random() >= ANOMALY_RATE:
        return None
    if kind == "station":
        return random.choice(["frost", "underheat", "theft"])
    return random.choice(["underheat", "theft"])


def generate_params(params_config, anomaly_type=None):
    params = {}
    for name, (min_val, max_val, _unit) in params_config.items():
        params[name] = round(random.uniform(min_val, max_val), 2)

    if anomaly_type == "frost" and "supplyTemp" in params:
        params["supplyTemp"] = round(random.uniform(30.0, 45.0), 2)
    elif anomaly_type == "underheat" and "roomTemp" in params:
        params["roomTemp"] = round(random.uniform(8.0, 15.5), 2)
    elif anomaly_type == "theft" and "flow" in params:
        max_flow = params_config["flow"][1]
        params["flow"] = round(max_flow * random.uniform(1.5, 2.5), 2)
    return params


def generate_log_entry(entity, base_time, index):
    timestamp = base_time + timedelta(seconds=index * 5)
    ts = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    anomaly_type = pick_anomaly_type(entity["kind"])
    params = generate_params(entity["params_config"], anomaly_type)

    if entity["kind"] == "station":
        rec = build_sensor_record(
            station_id=entity["station_id"],
            supply_temp=params["supplyTemp"],
            return_temp=params["returnTemp"],
            pressure=params["pressure"],
            flow=params["flow"],
            heat=params["heat"],
            corrosion=params["corrosionRate"],
            room_temp=params["roomTemp"],
            outdoor_temp=params["outdoorTemp"],
            ts=ts,
        )
    else:
        rec = {
            "user_id": entity["user_id"],
            "station_id": entity["station_id"],
            "roomTemp": params["roomTemp"],
            "flow": params["flow"],
            "event_timestamp": ts,
        }

    rec["kind"] = entity["kind"]
    rec["device_id"] = entity["entity_id"]
    if anomaly_type:
        rec["alarmType"] = anomaly_type
        rec["level"] = ALARM_LEVELS[anomaly_type]
    return rec


def generate_logs(count, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    entities = generate_entity_list()
    entity_count = len(entities)
    print(f"采集点清单：共 {entity_count} 个（5 座换热站 + 200 户）")

    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    filename = f"heat_sensor_{base_time.strftime('%Y%m%d')}.log"
    filepath = os.path.join(output_dir, filename)
    print(f"\n开始生成 {count:,} 条供热采集数据...")
    print(f"输出文件: {filepath}")

    batch_size = 1000
    batches = (count + batch_size - 1) // batch_size
    with open(filepath, "w", encoding="utf-8") as handle:
        for batch in range(batches):
            start_idx = batch * batch_size
            end_idx = min((batch + 1) * batch_size, count)
            batch_logs = []
            for i in range(end_idx - start_idx):
                global_idx = start_idx + i
                entity = entities[global_idx % entity_count]
                entry = generate_log_entry(entity, base_time, global_idx // entity_count)
                batch_logs.append(json.dumps(entry, ensure_ascii=False))
            handle.write("\n".join(batch_logs) + "\n")
            if (batch + 1) % 10 == 0 or batch == batches - 1:
                progress = ((batch + 1) / batches) * 100
                print(f"进度: {progress:.1f}% ({end_idx:,}/{count:,} 条记录)")

    file_size = os.path.getsize(filepath)
    print("数据生成完成")
    print(f"  文件路径: {filepath}")
    print(f"  文件大小: {file_size / 1024 / 1024:.2f} MB")
    print(f"  记录数量: {count:,}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="供热管网模拟采集数据生成器")
    parser.add_argument("--count", type=int, default=100000, help="生成记录数量，默认 100000")
    parser.add_argument("--output", type=str, default="data/logs", help="输出目录，默认为 data/logs")
    args = parser.parse_args()
    generate_logs(args.count, args.output)


if __name__ == "__main__":
    main()
