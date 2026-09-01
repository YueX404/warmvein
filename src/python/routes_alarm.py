"""Alarm list/ack APIs plus forecast list (Dev-2 Task 5)."""

from datetime import datetime

from fastapi import APIRouter, Query
from sqlalchemy import text

from db import SessionLocal
from response import fail, ok

router = APIRouter()

_LEVEL_NAME = {1: "蓝色", 2: "黄色", 3: "橙色", 4: "红色"}
_STATUS_NAME = {0: "未确认", 1: "已确认", 2: "已处置", 3: "已关闭"}
_LIST_SQL = (
    "SELECT alarm_id, station_id, level, type, root_cause, title, status, created_at "
    "FROM biz_alarm WHERE 1=1"
)
_LIST_LIMIT = 200


def _fmt_time(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def _to_alarm(row: dict) -> dict:
    level = row.get("level")
    status = row.get("status")
    return {
        "alarmId": row.get("alarm_id"),
        "stationId": row.get("station_id"),
        "level": level,
        "levelName": _LEVEL_NAME.get(level, ""),
        "type": row.get("type"),
        "rootCause": row.get("root_cause"),
        "title": row.get("title"),
        "status": status,
        "statusName": _STATUS_NAME.get(status, ""),
        "createdAt": _fmt_time(row.get("created_at")),
    }


@router.get("/alarm/list")
def list_alarms(level: int = None, status: int = None):
    if level is not None and level not in (1, 2, 3, 4):
        return fail(40001, "level 无效")
    if status is not None and status not in (0, 1, 2, 3):
        return fail(40001, "status 无效")
    sql = _LIST_SQL
    params = {}
    if level is not None:
        sql += " AND level=:level"
        params["level"] = level
    if status is not None:
        sql += " AND status=:status"
        params["status"] = status
    sql += " ORDER BY created_at DESC LIMIT :limit"
    params["limit"] = _LIST_LIMIT
    with SessionLocal() as session:
        rows = session.execute(text(sql), params).mappings().all()
    return ok([_to_alarm(dict(item)) for item in rows])


def _apply_ack(session, alarm_id: int, operator: str):
    result = session.execute(
        text(
            "UPDATE biz_alarm SET status=1, operator=:operator, ack_at=NOW() "
            "WHERE alarm_id=:alarm_id AND status=0"
        ),
        {"operator": operator, "alarm_id": alarm_id},
    )
    if result.rowcount > 0:
        session.commit()
        return ok({"ok": True, "alarmId": alarm_id})
    found = session.execute(
        text("SELECT status FROM biz_alarm WHERE alarm_id=:alarm_id"),
        {"alarm_id": alarm_id},
    ).mappings().first()
    session.rollback()
    if found is None:
        return fail(40002, "预警不存在")
    return fail(40001, "已确认或已关闭，不可重复确认")


@router.post("/alarm/ack")
def ack_alarm(body: dict):
    alarm_id = body.get("alarmId")
    operator = body.get("operator")
    if not isinstance(alarm_id, int) or alarm_id <= 0:
        return fail(40001, "缺少 alarmId")
    if not isinstance(operator, str) or not operator.strip():
        return fail(40001, "缺少 operator")
    operator = operator.strip()
    if len(operator) > 32:
        return fail(40001, "operator 超长")
    with SessionLocal() as session:
        return _apply_ack(session, alarm_id, operator)


_FORECAST_TYPES = ("freeze", "lifetime", "fault", "energy")
_FORECAST_TYPE_NAME = {
    "freeze": "冻堵预报",
    "lifetime": "寿命预报",
    "fault": "故障预报",
    "energy": "能效预报",
}
_FORECAST_SQL = (
    "SELECT forecast_id, station_id, type, title, risk_level, forecast_date, "
    "description, suggestion, status, created_at "
    "FROM biz_forecast WHERE (:t IS NULL OR type=:t) "
    "ORDER BY forecast_date DESC LIMIT :limit"
)


def _fmt_date(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _to_forecast(row: dict) -> dict:
    ftype = row.get("type")
    return {
        "forecastId": row.get("forecast_id"),
        "stationId": row.get("station_id"),
        "type": ftype,
        "typeName": _FORECAST_TYPE_NAME.get(ftype, ""),
        "title": row.get("title"),
        "riskLevel": row.get("risk_level"),
        "forecastDate": _fmt_date(row.get("forecast_date")),
        "description": row.get("description"),
        "suggestion": row.get("suggestion"),
        "status": row.get("status"),
        "createdAt": _fmt_time(row.get("created_at")),
    }


@router.get("/forecast/list")
def list_forecasts(ftype: str = Query(default=None, alias="type")):
    if ftype is not None and ftype not in _FORECAST_TYPES:
        return fail(40001, "type 无效")
    with SessionLocal() as session:
        rows = session.execute(
            text(_FORECAST_SQL),
            {"t": ftype, "limit": _LIST_LIMIT},
        ).mappings().all()
    return ok([_to_forecast(dict(item)) for item in rows])
