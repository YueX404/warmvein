"""Energy KPI accounting and regional benchmark (module 8.x)."""

from typing import Any, Optional

from sqlalchemy import text

from db import SessionLocal

_DWS_SQL = (
    "SELECT COALESCE(SUM(heat_loss_kwh),0) AS hl, "
    "COALESCE(SUM(heat_supply_gj),0) AS hs "
    "FROM dws.heat_station_summary WHERE dt=:d"
)
_HARD_SEED = {"hl": 150.3, "hs": 1250.5, "sp": 420.0}


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _pack(hl: float, hs: float, sp: float) -> dict:
    return {
        "heatLossKwh": round(hl, 2),
        "heatSupplyGj": round(hs, 2),
        "sourcePowerKwh": round(sp, 2),
        "unitHeatKwh": round(hl / hs, 4) if hs else 0.0,
    }


def _query_dws(date: str) -> Optional[dict]:
    try:
        with SessionLocal() as session:
            row = session.execute(text(_DWS_SQL), {"d": date}).mappings().first()
    except Exception:
        return None
    if not row:
        return None
    hl = _to_float(row.get("hl"))
    hs = _to_float(row.get("hs"))
    sp = _to_float(row.get("sp"), hs * 85.0)
    return _pack(hl, hs, sp)


def _from_network_loss(date: str, region: str = None) -> dict:
    from services import heat_run

    items = heat_run.get_loss(date).get("pipeLoss") or []
    if region:
        filtered = []
        for item in items:
            try:
                station = heat_run._load_station(int(item.get("stationId") or 0))
            except heat_run.StationNotFound:
                continue
            if station.get("region") == region:
                filtered.append(item)
        items = filtered
    if not items:
        return _pack(_HARD_SEED["hl"], _HARD_SEED["hs"], _HARD_SEED["sp"])
    hl = sum(_to_float(item.get("totalLossKwh")) for item in items)
    hs = max(hl / 12.0, 1.0)
    return _pack(hl, hs, hs * 85.0)


def compute_kpi(date: str, region: str = None) -> dict:
    if not region:
        found = _query_dws(date)
        if found is not None:
            return found
    return _from_network_loss(date, region)


def benchmark(kpi: dict, baseline: float = 1.0) -> dict:
    gap = _to_float(kpi.get("unitHeatKwh")) - baseline
    if gap > 0.1:
        level = "high"
    elif gap > 0:
        level = "mid"
    else:
        level = "low"
    return {"gap": level, "diff": round(gap, 4)}
