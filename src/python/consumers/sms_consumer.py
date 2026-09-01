"""SMS Kafka consumer.

Start from src/python:
    python -m consumers.sms_consumer
"""

import json
import logging
import time

from kafka import KafkaConsumer

from config.settings import settings
from kafka_topics import SMS_NOTIFY_TOPIC
from services import sms_service

logger = logging.getLogger(__name__)

COMMIT_STATUSES = frozenset({"skip", "ok"})
RETRY_BACKOFF_SEC = 2

_LEVEL_TPL = {1: "ALARM_BLUE", 2: "ALARM_YELLOW", 3: "ALARM_ORANGE", 4: "ALARM_RED"}


def handle_notify(msg, send=None):
    send = send or sms_service.send_sms
    if not isinstance(msg, dict):
        return "skip"
    phone = msg.get("phone")
    if not sms_service.is_mobile(phone):
        logger.warning("skip sms notify without valid phone")
        return "skip"
    try:
        level = int(msg.get("level") or 2)
    except (TypeError, ValueError):
        level = 2
    template_code = _LEVEL_TPL.get(level, "ALARM_YELLOW")
    send(
        template_code,
        phones=[phone],
        vars={
            "level": msg.get("level"),
            "type": msg.get("alarmType"),
            "stationName": msg.get("stationName", msg.get("station_id", "")),
        },
    )
    return "ok"


def dispatch_record(msg, consumer, handle=None, sleep=None):
    handle = handle or handle_notify
    sleep = sleep or time.sleep
    while True:
        try:
            payload = json.loads(msg.value.decode())
            result = handle(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
            logger.exception("skip undecodable sms notify")
            result = "skip"
        except Exception:
            logger.exception("sms notify handle failed")
            result = "error"
        if result in COMMIT_STATUSES:
            consumer.commit()
            return result
        logger.warning("sms notify error, retry without commit")
        sleep(RETRY_BACKOFF_SEC)


def consume():
    consumer = KafkaConsumer(
        SMS_NOTIFY_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="sms_consumer",
        auto_offset_reset="latest",
        enable_auto_commit=False,
    )
    for msg in consumer:
        dispatch_record(msg, consumer)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    consume()
