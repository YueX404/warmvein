from datetime import datetime

from fastapi import APIRouter, Query

from response import fail, ok
from services import heat_run, master_data
from services.heat_run import StationNotFound

router = APIRouter()
heat_router = APIRouter(prefix="/heat")


def _valid_region(region: str) -> bool:
    if len(region) > 32:
        return False
    return all(ch.isalnum() or ch in "-_" for ch in region)


def _valid_date(date: str) -> bool:
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except (TypeError, ValueError):
        return False
    return True


def _station_error(station_id: int, exc: Exception):
    if isinstance(exc, StationNotFound) or station_id <= 0:
        return fail(40002, "换热站不存在")
    return fail(50001, "服务内部错误")


@heat_router.get("/stations")
def api_stations(region: str = Query(None)):
    if region is not None:
        region = region.strip()
        if not region:
            region = None
        elif not _valid_region(region):
            return fail(40001, "参数校验失败")
    try:
        return ok({"stations": master_data.get_stations(region)})
    except Exception:
        return fail(50001, "服务内部错误")


@heat_router.get("/station/{station_id}/realtime")
def api_realtime(station_id: int):
    try:
        return ok(heat_run.get_realtime(station_id))
    except Exception as exc:
        return _station_error(station_id, exc)


@heat_router.get("/balance")
def api_balance(station_id: int = Query(None, alias="stationId")):
    if station_id is None:
        return fail(40001, "参数校验失败")
    try:
        return ok(heat_run.get_balance(station_id))
    except Exception as exc:
        return _station_error(station_id, exc)


@heat_router.get("/loss")
def api_loss(date: str = Query(None)):
    if not date or not _valid_date(date):
        return fail(40001, "参数校验失败")
    try:
        return ok(heat_run.get_loss(date))
    except Exception:
        return fail(50001, "服务内部错误")


@heat_router.get("/energy")
def api_energy(date: str = Query(None), region: str = Query(None)):
    if not date or not _valid_date(date):
        return fail(40001, "参数校验失败")
    if region is not None:
        region = region.strip()
        if not region:
            region = None
        elif not _valid_region(region):
            return fail(40001, "参数校验失败")
    try:
        return ok(heat_run.get_energy(date, region))
    except Exception:
        return fail(50001, "服务内部错误")


@router.post("/console/climate-compensate")
def api_climate(body: dict):
    if not isinstance(body, dict) or "stationId" not in body or "tw" not in body:
        return fail(40001, "缺少 stationId 或 tw")
    try:
        station_id = int(body["stationId"])
        tw = float(body["tw"])
    except (TypeError, ValueError):
        return fail(40001, "参数校验失败")
    if tw < -50 or tw > 50:
        return fail(40001, "参数校验失败")
    try:
        return ok(heat_run.apply_climate(station_id, tw))
    except Exception as exc:
        return _station_error(station_id, exc)


router.include_router(heat_router)
