#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kafka 供热时序数据生产者。

向 HEAT_SENSOR_TOPIC 发送换热站/分户传感 JSON；
向 HEAT_ALARM_TOPIC 发送告警（供 Dev-2 预警引擎消费）。

使用示例：
    python heat_kafka_producer.py --bootstrap localhost:9092 --duration 300
    python heat_kafka_producer.py --input data/logs/heat_sensor_20260831.log
"""

import argparse
import json
import os
import time
from datetime import datetime

from kafka_topics import HEAT_ALARM_TOPIC, HEAT_SENSOR_TOPIC


def build_sensor_record(station_id, supply_temp, return_temp, pressure, flow, heat,
                        corrosion, room_temp, outdoor_temp, ts) -> dict:
    return {
        "station_id": station_id,
        "supplyTemp": supply_temp,
        "returnTemp": return_temp,
        "pressure": pressure,
        "flow": flow,
        "heat": heat,
        "corrosionRate": corrosion,
        "roomTemp": room_temp,
        "outdoorTemp": outdoor_temp,
        "event_timestamp": ts,
    }


def build_alarm_record(station_id, alarm_type, level, ts) -> dict:
    return {
        "station_id": station_id,
        "alarmType": alarm_type,
        "level": level,
        "event_timestamp": ts,
    }


def create_producer(bootstrap_servers="localhost:9092"):
    from kafka import KafkaProducer

    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        retries=3,
        acks="all",
        linger_ms=10,
        batch_size=16384,
    )


def send_to_kafka(producer, topic, message, key=None) -> bool:
    try:
        future = producer.send(topic, value=message, key=key)
        future.get(timeout=10)
        return True
    except Exception as exc:
        print(f"消息发送失败: {exc}")
        return False


def _record_key(record: dict) -> str:
    return str(record.get("device_id") or record.get("station_id") or "unknown")


def _maybe_send_alarm(producer, record: dict, key: str) -> bool:
    alarm_type = record.get("alarmType")
    if not alarm_type:
        return False
    alarm = build_alarm_record(
        station_id=record.get("station_id"),
        alarm_type=alarm_type,
        level=record.get("level", 1),
        ts=record.get("event_timestamp"),
    )
    return send_to_kafka(producer, HEAT_ALARM_TOPIC, alarm, key=key)


def load_and_send_logs(log_file, producer, speed=1.0):
    if not os.path.exists(log_file):
        print(f"日志文件不存在: {log_file}")
        return

    total_sent = 0
    alarm_sent = 0
    interval = 5.0 / speed

    print(f"开始读取日志文件: {log_file}")
    print(f"发送速度: {speed}x (间隔{interval:.2f}秒)")

    with open(log_file, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"第{line_no}行JSON解析失败，跳过")
                continue

            key = _record_key(record)
            if send_to_kafka(producer, HEAT_SENSOR_TOPIC, record, key=key):
                total_sent += 1
            if _maybe_send_alarm(producer, record, key):
                alarm_sent += 1
            if line_no % 100 == 0:
                print(f"已发送 {total_sent} 条传感器数据, {alarm_sent} 条告警数据")
                time.sleep(interval * 0.01)

    print(f"\n数据发送完成")
    print(f"  传感器数据: {total_sent} 条 -> Topic: {HEAT_SENSOR_TOPIC}")
    print(f"  告警数据: {alarm_sent} 条 -> Topic: {HEAT_ALARM_TOPIC}")


def send_realtime_data(producer, duration=60):
    from heat_generate_logs import generate_entity_list, generate_log_entry

    entities = generate_entity_list()
    entity_count = len(entities)
    print(f"实时模式：{entity_count}个采集点，运行{duration}秒")

    start_time = time.time()
    sent_count = 0
    idx = 0

    while time.time() - start_time < duration:
        entity = entities[idx % entity_count]
        record = generate_log_entry(entity, datetime.now(), idx // entity_count)
        key = _record_key(record)
        if send_to_kafka(producer, HEAT_SENSOR_TOPIC, record, key=key):
            sent_count += 1
        _maybe_send_alarm(producer, record, key)
        idx += 1
        time.sleep(5.0)

    print(f"实时发送完成: {sent_count} 条数据")


def main():
    parser = argparse.ArgumentParser(description="Kafka 供热时序数据生产者")
    parser.add_argument("--input", type=str, default=None,
                        help="日志文件路径，不指定则使用实时模式")
    parser.add_argument("--bootstrap", type=str, default="localhost:9092",
                        help="Kafka 服务器地址，默认 localhost:9092")
    parser.add_argument("--speed", type=float, default=10.0,
                        help="文件回放速度倍率，默认 10 倍速")
    parser.add_argument("--duration", type=int, default=60,
                        help="实时模式运行时长（秒），默认 60 秒")
    args = parser.parse_args()

    try:
        producer = create_producer(args.bootstrap)
        print(f"Kafka 连接成功: {args.bootstrap}")
    except Exception as exc:
        print(f"Kafka 连接失败: {exc}")
        return

    try:
        if args.input:
            load_and_send_logs(args.input, producer, args.speed)
        else:
            send_realtime_data(producer, args.duration)
    finally:
        producer.close()
        print("Producer 已关闭")


if __name__ == "__main__":
    main()
