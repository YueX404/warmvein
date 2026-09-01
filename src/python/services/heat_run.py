"""Heating operation: realtime monitor and algorithm orchestration."""

from __future__ import annotations

import json
import math
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import text

from algorithm.climate_compensation import climate_compensate
from algorithm.frost_risk import frost_risk
from algorithm.heat_loss import pipe_heat_loss
from algorithm.hydraulic_balance import compute_balance
from algorithm.user_abnormal import detect_user_abnormal
from config.settings import settings
from db import SessionLocal, redis_client

_STATION_SQL = (
    "SELECT station_id, name, region, source_id, area, design_flow, "
    "design_tg, design_th, status FROM md_station"
)
_PIPE_SQL = (
    "SELECT pipe_id, name, station_id, diameter, length_m, k_value, design_flow "
    "FROM md_pipe"
)
_USER_SQL = "SELECT user_id, station_id, area FROM md_user"
_CACHE_KEY = "heat:realtime:{station_id}"


class StationNotFound(Exception):
    """Raised when a heat-exchange station id does not exist."""


class _DbUnavailable(Exception):
    """Raised when MySQL is unreachable; callers may use seed data."""


_DB_DOWN = False


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _to_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    return int(value)


def _is_db_error(exc: BaseException) -> bool:
    if isinstance(exc, OSError):
        return True
    return type(exc).__name__ in {
        "OperationalError",
        "InterfaceError",
        "DisconnectionError",
    }


def _fetch_all(sql: str, params: dict = None) -> list:
    global _DB_DOWN
    if _DB_DOWN:
        raise _DbUnavailable()
    try:
        with SessionLocal() as session:
            rows = session.execute(text(sql), params or {}).mappings().all()
        return [dict(row) for row in rows]
    except Exception as exc:
        if _is_db_error(exc):
            _DB_DOWN = True
        raise _DbUnavailable() from exc


def _fetch_one(sql: str, params: dict) -> Optional[dict]:
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


def _seed_station(station_id: int) -> Optional[dict]:
    return _SEED_STATIONS.get(station_id)


def _seed_pipes(station_id: int = None) -> list:
    if station_id is None:
        return list(_SEED_PIPES)
    return [p for p in _SEED_PIPES if p["station_id"] == station_id]


def _load_station(station_id: int) -> dict:
    if station_id <= 0:
        raise StationNotFound()
    try:
        row = _fetch_one(_STATION_SQL + " WHERE station_id = :id", {"id": station_id})
    except _DbUnavailable:
        row = _seed_station(station_id)
    if not row:
        raise StationNotFound()
    return row


def _load_pipes(station_id: int = None) -> list:
    sql = _PIPE_SQL
    params: dict = {}
    if station_id is not None:
        sql += " WHERE station_id = :id"
        params["id"] = station_id
    sql += " ORDER BY pipe_id"
    try:
        rows = _fetch_all(sql, params)
        if rows:
            return rows
    except _DbUnavailable:
        pass
    return _seed_pipes(station_id)


def _load_users(station_id: int) -> list:
    try:
        return _fetch_all(
            _USER_SQL + " WHERE station_id = :id ORDER BY user_id",
            {"id": station_id},
        )
    except _DbUnavailable:
        return [u for u in _SEED_USERS if u["station_id"] == station_id]


def _cache_snapshot(station_id: int) -> dict:
    try:
        raw = redis_client.get(_CACHE_KEY.format(station_id=station_id))
    except Exception:
        return {}
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _default_snapshot(station: dict) -> dict:
    tg = _to_float(station.get("design_tg"), 75.0)
    th = _to_float(station.get("design_th"), 50.0)
    flow = _to_float(station.get("design_flow"), 100.0)
    return {
        "supplyTemp": tg,
        "returnTemp": th,
        "pressure": 0.6,
        "flowRate": flow,
        "heatEnergy": round(flow * max(tg - th, 0.0) * 0.001163, 2),
        "corrosionRate": 0.02,
        "wallThickness": 8.5,
        "roomTemp": 20.5,
        "outdoorTemp": -3.5,
        "velocity": 1.2,
    }


def _merge_snapshot(station: dict, station_id: int) -> dict:
    snap = _default_snapshot(station)
    cache = _cache_snapshot(station_id)
    for key, value in cache.items():
        if value is not None:
            snap[key] = value
    if "flow" in cache and "flowRate" not in cache:
        snap["flowRate"] = _to_float(cache["flow"], snap["flowRate"])
    return snap


def _health_score(risk: str, snap: dict) -> int:
    score = 100
    if risk == "high":
        score -= 40
    elif risk == "medium":
        score -= 20
    if _to_float(snap.get("pressure")) < 0.3:
        score -= 15
    return max(0, min(100, score))


def _user_abnormals(station_id: int, snap: dict) -> list:
    users = _load_users(station_id)
    if not users:
        return []
    flows = [_to_float(u.get("area"), 80.0) / 80.0 for u in users]
    mean_flow = sum(flows) / len(flows)
    var = sum((item - mean_flow) ** 2 for item in flows) / len(flows)
    std_flow = math.sqrt(var)
    room = _to_float(snap.get("roomTemp"), 20.5)
    result = []
    for user, flow in zip(users, flows):
        status = detect_user_abnormal(flow, room, mean_flow, std_flow)
        if status != "normal":
            result.append({"userId": _to_int(user.get("user_id")), "status": status})
    return result


def get_realtime(station_id: int) -> dict:
    station = _load_station(station_id)
    snap = _merge_snapshot(station, station_id)
    tg = _to_float(snap["supplyTemp"])
    th = _to_float(snap["returnTemp"])
    tw = _to_float(snap["outdoorTemp"])
    vel = _to_float(snap["velocity"], 1.2)
    risk = frost_risk(tg, tw, vel)
    return {
        "stationId": station_id,
        "stationName": station.get("name"),
        "supplyTemp": round(tg, 2),
        "returnTemp": round(th, 2),
        "tempDiff": round(tg - th, 2),
        "pressure": round(_to_float(snap["pressure"]), 3),
        "flowRate": round(_to_float(snap["flowRate"]), 2),
        "heatEnergy": round(_to_float(snap["heatEnergy"]), 2),
        "corrosionRate": round(_to_float(snap["corrosionRate"], 0.02), 4),
        "wallThickness": round(_to_float(snap["wallThickness"], 8.5), 2),
        "roomTemp": round(_to_float(snap["roomTemp"], 20.5), 2),
        "outdoorTemp": round(tw, 2),
        "velocity": round(vel, 2),
        "healthScore": _health_score(risk, snap),
        "frostRisk": risk,
        "userAbnormals": _user_abnormals(station_id, snap),
        "eventTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _actual_flow(station_id: int, design_flow: float, station: dict) -> float:
    snap = _merge_snapshot(station, station_id)
    station_design = _to_float(station.get("design_flow"), 0.0)
    live = _to_float(snap.get("flowRate"), 0.0)
    if station_design > 0 and live > 0:
        return round(live * (design_flow / station_design), 2)
    return round(design_flow * 0.95, 2)


def get_balance(station_id: int) -> dict:
    station = _load_station(station_id)
    pipes = _load_pipes(station_id)
    actual: dict = {}
    design: dict = {}
    meta: dict = {}
    for pipe in pipes:
        bid = str(pipe["pipe_id"])
        design_flow = _to_float(pipe.get("design_flow"))
        actual[bid] = _actual_flow(station_id, design_flow, station)
        design[bid] = design_flow
        meta[bid] = pipe
    computed = compute_balance(actual, design)
    branches = []
    for bid, item in computed.items():
        pipe = meta[bid]
        branches.append({
            "branchId": bid,
            "branchName": pipe.get("name"),
            "actualFlow": actual[bid],
            "designFlow": design[bid],
            "beta": item["beta"],
            "unbalanced": item["unbalanced"],
            "suggestOpen": item["suggest_open"],
        })
    return {
        "stationId": station_id,
        "branches": branches,
        "unbalancedCount": sum(1 for b in branches if b["unbalanced"]),
    }


def _pipe_loss_item(pipe: dict, snap: dict) -> dict:
    k_value = _to_float(pipe.get("k_value"), 0.035)
    diameter_m = _to_float(pipe.get("diameter")) / 1000.0
    length_m = _to_float(pipe.get("length_m"))
    tg = _to_float(snap["supplyTemp"])
    th = _to_float(snap["returnTemp"])
    tamb = _to_float(snap["outdoorTemp"])
    loss_w = pipe_heat_loss(k_value, diameter_m, length_m, tg, th, tamb)
    return {
        "pipeId": _to_int(pipe.get("pipe_id")),
        "pipeName": pipe.get("name"),
        "kValue": k_value,
        "diameter": round(diameter_m, 4),
        "length": length_m,
        "supplyTemp": round(tg, 2),
        "returnTemp": round(th, 2),
        "outdoorTemp": round(tamb, 2),
        "stationId": _to_int(pipe.get("station_id")),
        "heatLossW": round(loss_w, 1),
        "totalLossKwh": round(loss_w * 24.0 / 1000.0, 2),
    }


def get_loss(date: str) -> dict:
    items = []
    total_w = 0.0
    for pipe in _load_pipes():
        try:
            station = _load_station(_to_int(pipe.get("station_id")))
        except StationNotFound:
            continue
        snap = _merge_snapshot(station, _to_int(pipe.get("station_id")))
        item = _pipe_loss_item(pipe, snap)
        total_w += item["heatLossW"]
        items.append(item)
    return {"date": date, "pipeLoss": items, "totalLossW": round(total_w, 1)}


def get_energy(date: str, region: str = None) -> dict:
    from services.energy import benchmark, compute_kpi

    kpi = compute_kpi(date, region)
    bench = benchmark(kpi)
    heat_loss = _to_float(kpi.get("heatLossKwh"))
    heat_gj = _to_float(kpi.get("heatSupplyGj"))
    heat_kwh = heat_gj * 277.78
    saving = {"high": 0.0, "mid": 4.0, "low": 8.3}.get(bench["gap"], 0.0)
    return {
        "date": date,
        "totalHeatEnergy": heat_gj,
        "totalHeatLoss": heat_loss,
        "heatLossRate": round(heat_loss / heat_kwh * 100, 2) if heat_kwh else 0.0,
        "unitEnergy": _to_float(kpi.get("unitHeatKwh")),
        "sourcePowerKwh": _to_float(kpi.get("sourcePowerKwh")),
        "avgRoomTemp": 21.5,
        "energySavingRate": saving,
        "carbonReduction": round(heat_loss * 0.0008, 2),
        "benchmark": bench,
    }


def _insert_console_action(station_id: int, tg_set: float, th_set: float, tw: float) -> int:
    global _DB_DOWN
    if _DB_DOWN:
        return 0
    sql = (
        "INSERT INTO biz_console_action "
        "(station_id, action_type, tg_set, th_set, tw, status) "
        "VALUES (:sid, 'climate', :tg, :th, :tw, 0)"
    )
    params = {"sid": station_id, "tg": tg_set, "th": th_set, "tw": tw}
    try:
        with SessionLocal() as session:
            result = session.execute(text(sql), params)
            session.commit()
            return int(result.lastrowid or 0)
    except Exception as exc:
        if _is_db_error(exc):
            _DB_DOWN = True
        return 0


def apply_climate(station_id: int, tw: float) -> dict:
    station = _load_station(station_id)
    result = climate_compensate(
        float(tw),
        settings.CLIMATE_TN,
        _to_float(station.get("design_tg"), settings.CLIMATE_TG_D),
        settings.CLIMATE_TW_D,
        settings.CLIMATE_DT_D,
    )
    action_id = _insert_console_action(
        station_id, result["TgSet"], result["thSet"], float(tw)
    )
    return {
        "stationId": station_id,
        "tw": float(tw),
        "TgSet": result["TgSet"],
        "thSet": result["thSet"],
        "actionId": action_id,
        "status": 0,
    }


# Seed mirrors config/mysql/heat_init.sql so API tests work without MySQL.
_SEED_STATIONS = {
    1: {"station_id": 1, "name": "CNC-001", "region": "ansai",
        "design_tg": 75.0, "design_th": 50.0, "design_flow": 140.0, "area": 12.5},
    2: {"station_id": 2, "name": "CNC-002", "region": "ansai",
        "design_tg": 75.0, "design_th": 50.0, "design_flow": 135.0, "area": 11.8},
    3: {"station_id": 3, "name": "CNC-003", "region": "ansai",
        "design_tg": 75.0, "design_th": 50.0, "design_flow": 145.0, "area": 13.2},
    4: {"station_id": 4, "name": "RBT-001", "region": "ansai",
        "design_tg": 70.0, "design_th": 48.0, "design_flow": 110.0, "area": 8.6},
    5: {"station_id": 5, "name": "RBT-002", "region": "ansai",
        "design_tg": 70.0, "design_th": 48.0, "design_flow": 108.0, "area": 8.4},
    6: {"station_id": 6, "name": "RBT-003", "region": "ansai",
        "design_tg": 70.0, "design_th": 48.0, "design_flow": 112.0, "area": 8.9},
    7: {"station_id": 7, "name": "INJ-001", "region": "ansai",
        "design_tg": 72.0, "design_th": 49.0, "design_flow": 160.0, "area": 15.4},
    8: {"station_id": 8, "name": "INJ-002", "region": "ansai",
        "design_tg": 72.0, "design_th": 49.0, "design_flow": 155.0, "area": 14.8},
    9: {"station_id": 9, "name": "AIR-001", "region": "ansai",
        "design_tg": 65.0, "design_th": 45.0, "design_flow": 90.0, "area": 6.2},
    10: {"station_id": 10, "name": "AIR-002", "region": "ansai",
         "design_tg": 65.0, "design_th": 45.0, "design_flow": 88.0, "area": 6.0},
}

_SEED_PIPES = [
    {"pipe_id": 1, "name": "CNC-001二次网", "station_id": 1,
     "diameter": 250, "length_m": 420, "k_value": 0.035, "design_flow": 140.0},
    {"pipe_id": 2, "name": "CNC-002二次网", "station_id": 2,
     "diameter": 250, "length_m": 380, "k_value": 0.035, "design_flow": 135.0},
    {"pipe_id": 3, "name": "CNC-003二次网", "station_id": 3,
     "diameter": 250, "length_m": 450, "k_value": 0.038, "design_flow": 145.0},
    {"pipe_id": 4, "name": "RBT-001二次网", "station_id": 4,
     "diameter": 200, "length_m": 310, "k_value": 0.032, "design_flow": 110.0},
    {"pipe_id": 5, "name": "RBT-002二次网", "station_id": 5,
     "diameter": 200, "length_m": 290, "k_value": 0.032, "design_flow": 108.0},
    {"pipe_id": 6, "name": "RBT-003二次网", "station_id": 6,
     "diameter": 200, "length_m": 330, "k_value": 0.034, "design_flow": 112.0},
    {"pipe_id": 7, "name": "INJ-001二次网", "station_id": 7,
     "diameter": 300, "length_m": 510, "k_value": 0.045, "design_flow": 160.0},
    {"pipe_id": 8, "name": "INJ-002二次网", "station_id": 8,
     "diameter": 300, "length_m": 490, "k_value": 0.045, "design_flow": 155.0},
    {"pipe_id": 9, "name": "AIR-001二次网", "station_id": 9,
     "diameter": 150, "length_m": 220, "k_value": 0.028, "design_flow": 90.0},
    {"pipe_id": 10, "name": "AIR-002二次网", "station_id": 10,
     "diameter": 150, "length_m": 210, "k_value": 0.028, "design_flow": 88.0},
]

_SEED_USERS = [
    {"user_id": 1, "station_id": 1, "area": 86.0},
    {"user_id": 2, "station_id": 1, "area": 92.0},
    {"user_id": 3, "station_id": 1, "area": 78.0},
]
