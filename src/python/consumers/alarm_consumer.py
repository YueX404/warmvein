"""Alarm Kafka consumer.

Start from src/python:
    python -m consumers.alarm_consumer
"""

import json
import logging
import time

from kafka import KafkaConsumer
from sqlalchemy import text

from config.settings import settings
from db import SessionLocal, redis_client as default_redis
from kafka_topics import HEAT_ALARM_TOPIC
from services import alarm_engine

logger = logging.getLogger(__name__)


def _parse_alarm(msg):
    if not isinstance(msg, dict):
        return None
    try:
        station_id = int(msg.get("station_id"))
    except (TypeError, ValueError):
        return None
    alarm_type = msg.get("alarmType")
    if not isinstance(alarm_type, str) or alarm_type not in alarm_engine.KNOWN_ALARM_TYPES:
        return None
    raw_level = msg.get("level")
    if isinstance(raw_level, str):
        level = alarm_engine.risk_level_from_frost(raw_level)
    else:
        level = alarm_engine.judge_level(alarm_type, raw_level)
    return {
        "station_id": station_id,
        "alarm_type": alarm_type,
        "level": level,
        "schema_type": alarm_engine.to_schema_type(alarm_type),
        "raw": msg,
    }


def _insert_alarm(session_factory, parsed):
    with session_factory() as session:
        session.execute(text(
            "INSERT INTO biz_alarm(station_id, level, type, root_cause, status, created_at) "
            "VALUES(:s,:l,:t,:rc,0,NOW())"),
            {"s": parsed["station_id"], "l": parsed["level"],
             "t": parsed["schema_type"], "rc": parsed["alarm_type"]})
        session.commit()


def handle_alarm(msg, redis_client=None, session_factory=None, publish=None):
    cache = redis_client if redis_client is not None else default_redis
    session_factory = session_factory or SessionLocal
    publish = publish or alarm_engine.publish_sms
    parsed = _parse_alarm(msg)
    if parsed is None:
        logger.warning("skip malformed alarm: %s", msg)
        return "skip"
    key = alarm_engine.dedup_key(parsed["station_id"], parsed["alarm_type"])
    now = str(int(time.time()))
    if not cache.set(key, now, nx=True, ex=alarm_engine.DEDUP_WINDOW_SEC):
        logger.info("dedup skip %s", key)
        return "dedup"
    try:
        _insert_alarm(session_factory, parsed)
    except Exception:
        cache.delete(key)
        logger.exception("insert failed, released %s", key)
        return "error"
    try:
        publish({**parsed["raw"], "level": parsed["level"],
                 "station_id": parsed["station_id"]})
    except Exception:
        logger.exception("sms publish failed station=%s", parsed["station_id"])
    return "ok"


def consume():
    consumer = KafkaConsumer(
        HEAT_ALARM_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        group_id="alarm_engine",
    )
    for msg in consumer:
        try:
            payload = json.loads(msg.value.decode())
            handle_alarm(payload)
        except Exception:
            logger.exception("alarm handle failed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        consume()
    finally:
        alarm_engine.close_producer()
