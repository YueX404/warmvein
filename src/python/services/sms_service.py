import os
import time
from abc import ABC, abstractmethod

from sqlalchemy import text

DAILY_LIMIT = 20
RETRY_TIMES = 3
LIMIT_TTL_SEC = 86400
STATUS_SUCCESS = 2
STATUS_FAIL = 3
STATUS_RATE_LIMITED = 4


class SMSSender(ABC):
    @abstractmethod
    def _do_send(self, phone: str, content: str) -> dict:
        ...


class LocalMockSender(SMSSender):
    def _do_send(self, phone, content):
        return {"success": True, "bizId": f"mock-{int(time.time())}"}


class AliyunSMSSender(SMSSender):
    def _do_send(self, phone, content):
        return {"success": True, "bizId": f"ali-{int(time.time())}"}


def get_sender() -> SMSSender:
    mapping = {"local": LocalMockSender, "aliyun": AliyunSMSSender}
    return mapping.get(os.getenv("SMS_PROVIDER", "local"), LocalMockSender)()


def mask_phone(phone: str) -> str:
    if not isinstance(phone, str) or len(phone) != 11:
        return phone
    return phone[:3] + "****" + phone[-4:]


def build_content(tpl: str, vars: dict) -> str:
    out = tpl
    for key, value in (vars or {}).items():
        out = out.replace("{" + key + "}", str(value))
    return out


def is_mobile(phone) -> bool:
    return isinstance(phone, str) and len(phone) == 11 and phone.isdigit()


def _write_log(session_factory, batch_id, phone, template_code, content, status, receipt, retry_count, error_msg=""):
    with session_factory() as session:
        session.execute(text(
            "INSERT INTO biz_sms_log(batch_id, phone_masked, template_code, content, "
            "status, receipt, error_msg, retry_count, created_at) "
            "VALUES(:b,:pm,:t,:c,:st,:r,:e,:rc,NOW())"
        ), {
            "b": batch_id,
            "pm": mask_phone(phone),
            "t": template_code,
            "c": content,
            "st": status,
            "r": receipt,
            "e": error_msg,
            "rc": retry_count,
        })
        session.commit()


def _load_template(session_factory, template_code: str):
    with session_factory() as session:
        return session.execute(
            text("SELECT content FROM biz_sms_template WHERE template_code=:c"),
            {"c": template_code},
        ).mappings().first()


def send_sms(
    template_code: str,
    phones: list,
    vars: dict,
    redis_client=None,
    session_factory=None,
    sender=None,
    sleep=None,
) -> str:
    if session_factory is None or redis_client is None:
        from db import SessionLocal, redis_client as default_redis
        session_factory = session_factory or SessionLocal
        redis_client = redis_client if redis_client is not None else default_redis
    sender = sender or get_sender()
    sleep = sleep or time.sleep
    tpl_row = _load_template(session_factory, template_code)
    if not tpl_row:
        raise ValueError("template not found")
    content = build_content(tpl_row["content"], vars)
    batch_id = f"b{int(time.time())}"
    for phone in phones:
        _send_one(phone, content, template_code, batch_id, redis_client, session_factory, sender, sleep)
    return batch_id


def _send_one(phone, content, template_code, batch_id, cache, session_factory, sender, sleep):
    if not is_mobile(phone):
        return
    key = f"sms:limit:{phone}"
    if int(cache.get(key) or 0) >= DAILY_LIMIT:
        _write_log(session_factory, batch_id, phone, template_code, content, STATUS_RATE_LIMITED, "", 0)
        return
    result = {"success": False}
    retry_count = 0
    error_msg = ""
    for attempt in range(RETRY_TIMES):
        try:
            result = sender._do_send(phone, content)
        except Exception as exc:
            result = {"success": False}
            error_msg = type(exc).__name__
        if result.get("success"):
            cache.incr(key)
            cache.expire(key, LIMIT_TTL_SEC)
            error_msg = ""
            break
        retry_count = attempt + 1
        if attempt < RETRY_TIMES - 1:
            sleep(2 ** attempt)
    status = STATUS_SUCCESS if result.get("success") else STATUS_FAIL
    _write_log(
        session_factory, batch_id, phone, template_code, content,
        status, result.get("bizId", ""), retry_count, error_msg,
    )
