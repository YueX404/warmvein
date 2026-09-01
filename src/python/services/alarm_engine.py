from kafka_topics import SMS_NOTIFY_TOPIC
from db import redis_client

_TYPE_LEVEL = {
    "frost": 4, "leak": 4, "corrosion": 2, "imbalance": 2,
    "loss": 3, "blocked": 2, "steal": 2, "water": 3,
}


def judge_level(alarm_type: str, value: int = None) -> int:
    return _TYPE_LEVEL.get(alarm_type, 2)


def risk_level_from_frost(level: str) -> int:
    return {"low": 2, "medium": 3, "high": 4}.get(level, 2)


def dedup_key(station_id: int, alarm_type: str) -> str:
    return f"alarm:{station_id}:{alarm_type}"


def publish_sms(alarm: dict):
    from kafka import KafkaProducer
    import json, os
    p = KafkaProducer(bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
                      value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode())
    p.send(SMS_NOTIFY_TOPIC, value=alarm)
    p.flush()
