"""Heat network master-data queries (stations, users, SMS subscribers)."""

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import text

from db import SessionLocal

_STATION_SQL = (
    "SELECT station_id, name, region, source_id, area, design_flow, "
    "design_tg, design_th, address, lng, lat, status FROM md_station"
)


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    return int(value)


def mask_phone(phone: str) -> str:
    """Mask mainland mobile as 138****1234; leave short values unchanged."""
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if len(digits) < 7:
        return phone or ""
    return f"{digits[:3]}****{digits[-4:]}"


def _station_row(row: dict) -> dict:
    design_tg = _to_float(row.get("design_tg"))
    design_th = _to_float(row.get("design_th"))
    return {
        "stationId": _to_int(row["station_id"]),
        "name": row["name"],
        "region": row.get("region"),
        "sourceId": _to_int(row.get("source_id")),
        "area": _to_float(row.get("area")),
        "designFlow": _to_float(row.get("design_flow")),
        "designTg": design_tg,
        "designTh": design_th,
        "address": row.get("address"),
        "lng": _to_float(row.get("lng")),
        "lat": _to_float(row.get("lat")),
        "status": _to_int(row.get("status")),
        "supplyTemp": design_tg,
        "returnTemp": design_th,
        "pressure": None,
    }


def get_stations(region: str = None) -> list:
    sql = _STATION_SQL
    params: dict = {}
    if region:
        sql += " WHERE region = :region"
        params["region"] = region
    sql += " ORDER BY station_id"
    with SessionLocal() as session:
        rows = session.execute(text(sql), params).mappings().all()
    return [_station_row(dict(row)) for row in rows]


def get_user_by_id(uid: int) -> dict:
    sql = (
        "SELECT user_id, house_no, address, phone, station_id, area, sms_subscribe "
        "FROM md_user WHERE user_id = :u"
    )
    with SessionLocal() as session:
        row = session.execute(text(sql), {"u": uid}).mappings().first()
    if not row:
        return {}
    data = dict(row)
    phone = data.get("phone")
    return {
        "userId": _to_int(data.get("user_id")),
        "houseNo": data.get("house_no"),
        "address": data.get("address"),
        "phone": mask_phone(phone) if phone else None,
        "stationId": _to_int(data.get("station_id")),
        "area": _to_float(data.get("area")),
        "smsSubscribe": _to_int(data.get("sms_subscribe")),
    }


def list_subscribed_phones(station_id: int) -> list:
    sql = (
        "SELECT phone FROM md_user "
        "WHERE station_id = :s AND sms_subscribe = 1 AND phone IS NOT NULL"
    )
    with SessionLocal() as session:
        rows = session.execute(text(sql), {"s": station_id}).mappings().all()
    return [row["phone"] for row in rows if row["phone"]]
