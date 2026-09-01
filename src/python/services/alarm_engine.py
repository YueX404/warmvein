import json

from kafka_topics import SMS_NOTIFY_TOPIC

DEDUP_WINDOW_SEC = 300

_TYPE_LEVEL = {
    "frost": 4, "leak": 4, "corrosion": 2, "imbalance": 2,
    "loss": 3, "blocked": 2, "steal": 2, "water": 3,
}

_TYPE_TO_SCHEMA = {
    "frost": "freeze",
    "leak": "leak",
    "corrosion": "corrosion",
    "imbalance": "balance",
    "steal": "theft",
    "loss": "other",
    "blocked": "other",
    "water": "other",
}

KNOWN_ALARM_TYPES = frozenset(_TYPE_LEVEL)

_sms_producer = None


def judge_level(alarm_type: str, value: int = None) -> int:
    return _TYPE_LEVEL.get(alarm_type, 2)


def risk_level_from_frost(level: str) -> int:
    return {"low": 2, "medium": 3, "high": 4}.get(level, 2)


def dedup_key(station_id: int, alarm_type: str) -> str:
    return f"alarm:{station_id}:{alarm_type}"


def to_schema_type(alarm_type: str) -> str:
    return _TYPE_TO_SCHEMA.get(alarm_type, "other")


def _get_producer():
    global _sms_producer
    if _sms_producer is None:
        from kafka import KafkaProducer
        from config.settings import settings
        _sms_producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode(),
        )
    return _sms_producer


def close_producer():
    global _sms_producer
    if _sms_producer is not None:
        _sms_producer.close()
        _sms_producer = None


def publish_sms(alarm: dict, producer=None):
    p = producer if producer is not None else _get_producer()
    future = p.send(SMS_NOTIFY_TOPIC, value=alarm)
    future.get(timeout=10)
