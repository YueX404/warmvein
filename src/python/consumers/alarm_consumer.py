from kafka import KafkaConsumer
import json, os, time
from db import SessionLocal, redis_client
from sqlalchemy import text
from services import alarm_engine
from kafka_topics import HEAT_ALARM_TOPIC


def consume():
    c = KafkaConsumer(HEAT_ALARM_TOPIC,
                      bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "localhost:9092"),
                      value_deserializer=lambda m: json.loads(m.decode()),
                      auto_offset_reset="latest", group_id="alarm_engine")
    for msg in c:
        a = msg.value
        level = alarm_engine.judge_level(a.get("alarmType", ""), a.get("level"))
        key = alarm_engine.dedup_key(a["station_id"], a.get("alarmType", ""))
        now = int(time.time())
        last = int(redis_client.get(key) or 0)
        if now - last < 300:
            continue
        redis_client.set(key, now, ex=300)
        with SessionLocal() as s:
            s.execute(text(
                "INSERT INTO biz_alarm(station_id, level, type, root_cause, status, created_at) "
                "VALUES(:s,:l,:t,:rc,0,NOW())"),
                {"s": a["station_id"], "l": level, "t": a.get("alarmType"),
                 "rc": a.get("alarmType")})
            s.commit()
        alarm_engine.publish_sms({**a, "level": level})
