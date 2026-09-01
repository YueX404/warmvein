"""SMS send and log APIs. Gateway / template internals belong to Task 3."""

from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import text

from db import SessionLocal
from response import fail, ok
from services import sms_service

router = APIRouter()

_TEMPLATE_MAX = 32
_PHONE_MAX = 11
_BATCH_MAX = 32
_LIST_LIMIT = 200
_LIST_SQL = (
    "SELECT id, batch_id, phone_masked, template_code, status, receipt, created_at "
    "FROM biz_sms_log WHERE 1=1"
)


def _fmt_time(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def _parse_send(body: dict):
    code = body.get("templateCode")
    if not isinstance(code, str) or not code.strip():
        return None, "缺少 templateCode 或 phones"
    code = code.strip()
    if len(code) > _TEMPLATE_MAX:
        return None, "templateCode 非法"
    phones = body.get("phones")
    if not isinstance(phones, list) or not phones:
        return None, "缺少 templateCode 或 phones"
    cleaned = []
    for phone in phones:
        if not isinstance(phone, str) or not phone.strip() or len(phone.strip()) > _PHONE_MAX:
            return None, "phones 非法"
        cleaned.append(phone.strip())
    vars_map = body.get("vars", {})
    if vars_map is None:
        vars_map = {}
    if not isinstance(vars_map, dict):
        return None, "vars 非法"
    return {"templateCode": code, "phones": cleaned, "vars": vars_map}, None


def _to_log(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "batchId": row.get("batch_id"),
        "phoneMasked": row.get("phone_masked"),
        "templateCode": row.get("template_code"),
        "status": row.get("status"),
        "receipt": row.get("receipt"),
        "createdAt": _fmt_time(row.get("created_at")),
    }


@router.post("/sms/send")
def api_send(body: dict):
    parsed, err = _parse_send(body)
    if err:
        return fail(40001, err)
    try:
        batch_id = sms_service.send_sms(
            parsed["templateCode"], parsed["phones"], parsed["vars"]
        )
    except ValueError:
        return fail(40002, "短信模板不存在")
    return ok({"batchId": batch_id})


@router.get("/sms/log")
def api_log(batch_id: str = None, batchId: str = None):
    bid = batch_id or batchId
    if bid is not None:
        if not isinstance(bid, str) or not bid.strip() or len(bid.strip()) > _BATCH_MAX:
            return fail(40001, "batchId 非法")
        bid = bid.strip()
    sql = _LIST_SQL
    params = {}
    if bid:
        sql += " AND batch_id=:b"
        params["b"] = bid
    sql += " ORDER BY created_at DESC LIMIT :limit"
    params["limit"] = _LIST_LIMIT
    with SessionLocal() as session:
        rows = session.execute(text(sql), params).mappings().all()
    return ok([_to_log(dict(item)) for item in rows])
