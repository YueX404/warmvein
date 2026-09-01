"""Public service: stop-heating SMS notify and online repair reports."""

import os

import requests
from sqlalchemy import text

from db import SessionLocal
from services import master_data

SMS_URL = os.getenv("SMS_URL", "http://localhost:8000/api/sms/send")
SMS_TIMEOUT = 5
DESC_MAX_LEN = 255


def notify_stop_heating(station_id: int, plan_time: str) -> dict:
    """Notify subscribed users via Dev-2 SMS API. Does not implement SMS itself."""
    phones = master_data.list_subscribed_phones(station_id)
    if not phones:
        return {"sent": False, "reason": "no_subscriber", "count": 0}
    payload = {
        "templateCode": "STOP_HEATING",
        "phones": phones,
        "vars": {"planTime": plan_time, "stationId": station_id},
    }
    try:
        resp = requests.post(SMS_URL, json=payload, timeout=SMS_TIMEOUT)
        body = resp.json() if resp.content else {}
        ok_send = resp.status_code == 200 and body.get("code") == 0
    except (requests.RequestException, ValueError):
        return {"sent": False, "reason": "sms_gateway", "count": len(phones)}
    result = {"sent": ok_send, "count": len(phones)}
    if not ok_send:
        result["reason"] = "sms_gateway"
    return result


def create_repair_report(user_id: int, desc: str) -> dict:
    """Insert a public repair report and return the new order id."""
    with SessionLocal() as session:
        result = session.execute(
            text(
                "INSERT INTO biz_repair_report(user_id, description, status, created_at) "
                "VALUES(:u,:d,0,NOW())"
            ),
            {"u": user_id, "d": desc},
        )
        session.commit()
        return {"order_id": int(result.lastrowid)}
