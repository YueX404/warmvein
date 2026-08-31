#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kafka工业设备数据生产者脚本

功能：将设备传感器时序数据发送到Kafka消息队列
支持JSON格式消息序列化，按设备类型分发到不同Topic

使用示例：
    python kafka_producer.py
    python kafka_producer.py --input data/logs/device_sensor_20260720.log

依赖：
    pip install kafka-python
"""

import json
import os
import time
import argparse
from datetime import datetime


# Kafka Topic配置
SENSOR_TOPIC = "device-sensor-topic"
ALARM_TOPIC = "device-alarm-topic"


def create_producer(bootstrap_servers='localhost:9092'):
    """
    创建Kafka生产者实例

    Args:
        bootstrap_servers (str): Kafka服务器地址

    Returns:
        KafkaProducer: 配置好的生产者实例
    """
    from kafka import KafkaProducer

    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        retries=3,
        acks='all',
        linger_ms=10,
        batch_size=16384
    )
    return producer


def send_to_kafka(producer, topic, message, key=None):
    """
    发送消息到Kafka指定Topic

    Args:
        producer (KafkaProducer): 生产者实例
        topic (str): 目标Topic名称
        message (dict): 消息内容
        key (str): 分区键（通常为device_id）

    Returns:
        bool: 是否发送成功
    """
    try:
        future = producer.send(topic, value=message, key=key)
        result = future.get(timeout=10)
        return True
    except Exception as e:
        print(f"消息发送失败: {e}")
        return False


def load_and_send_logs(log_file, producer, speed=1.0):
    """
    从日志文件读取数据并发送到Kafka

    Args:
        log_file (str): 日志文件路径
        producer (KafkaProducer): 生产者实例
        speed (float): 发送速度倍率（1.0=实时，10.0=10倍速）
    """
    if not os.path.exists(log_file):
        print(f"日志文件不存在: {log_file}")
        return

    total_sent = 0
    alarm_sent = 0
    interval = 5.0 / speed  # 基于5秒采集间隔

    print(f"开始读取日志文件: {log_file}")
    print(f"发送速度: {speed}x (间隔{interval:.2f}秒)")

    with open(log_file, 'r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"第{line_no}行JSON解析失败，跳过")
                continue

            device_id = record.get("device_id", "unknown")

            # 传感器数据发送到sensor topic
            if send_to_kafka(producer, SENSOR_TOPIC, record, key=device_id):
                total_sent += 1

            # 告警数据额外发送到alarm topic
            if record.get("alarm_code", 0) != 0:
                alarm_record = {
                    "device_id": device_id,
                    "device_type": record.get("device_type"),
                    "workshop": record.get("workshop"),
                    "event_timestamp": record.get("event_timestamp"),
                    "alarm_code": record["alarm_code"],
                    "alarm_desc": record.get("alarm_desc"),
                    "status_code": record.get("status_code"),
                    "health_score": record.get("health_score")
                }
                if send_to_kafka(producer, ALARM_TOPIC, alarm_record, key=device_id):
                    alarm_sent += 1

            # 按速度控制发送频率
            if line_no % 100 == 0:
                print(f"已发送 {total_sent} 条传感器数据, {alarm_sent} 条告警数据")
                time.sleep(interval * 0.01)  # 批量发送时减少等待

    print(f"\n✓ 数据发送完成")
    print(f"  传感器数据: {total_sent} 条 -> Topic: {SENSOR_TOPIC}")
    print(f"  告警数据: {alarm_sent} 条 -> Topic: {ALARM_TOPIC}")


def send_realtime_data(producer, device_configs, duration=60):
    """
    实时生成并发送设备数据（模拟实时采集）

    Args:
        producer (KafkaProducer): 生产者实例
        device_configs (list): 设备配置列表
        duration (int): 运行时长（秒）
    """
    from generate_logs import generate_device_list, generate_log_entry

    devices = generate_device_list()
    device_count = len(devices)
    print(f"实时模式：{device_count}台设备，运行{duration}秒")

    start_time = time.time()
    sent_count = 0
    idx = 0

    while time.time() - start_time < duration:
        device = devices[idx % device_count]
        record = generate_log_entry(device, datetime.now(), idx // device_count)

        device_id = record["device_id"]
        if send_to_kafka(producer, SENSOR_TOPIC, record, key=device_id):
            sent_count += 1

        if record.get("alarm_code", 0) != 0:
            send_to_kafka(producer, ALARM_TOPIC, record, key=device_id)

        idx += 1
        time.sleep(5.0)  # 5秒采集间隔

    print(f"✓ 实时发送完成: {sent_count} 条数据")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Kafka工业设备数据生产者")
    parser.add_argument("--input", type=str, default=None,
                        help="日志文件路径，不指定则使用实时模式")
    parser.add_argument("--bootstrap", type=str, default="localhost:9092",
                        help="Kafka服务器地址，默认 localhost:9092")
    parser.add_argument("--speed", type=float, default=10.0,
                        help="文件回放速度倍率，默认10倍速")
    parser.add_argument("--duration", type=int, default=60,
                        help="实时模式运行时长（秒），默认60秒")

    args = parser.parse_args()

    try:
        producer = create_producer(args.bootstrap)
        print(f"✓ Kafka连接成功: {args.bootstrap}")
    except Exception as e:
        print(f"✗ Kafka连接失败: {e}")
        return

    try:
        if args.input:
            # 文件回放模式
            load_and_send_logs(args.input, producer, args.speed)
        else:
            # 实时模式
            send_realtime_data(producer, None, args.duration)
    finally:
        producer.close()
        print("Producer已关闭")


if __name__ == "__main__":
    main()
