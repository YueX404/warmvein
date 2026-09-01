from fastapi import APIRouter

from response import fail, ok
from services import twin
from services.twin import TwinParamError

router = APIRouter(prefix="/twin")


@router.post("/simulate/recovery")
def api_recovery(body: dict):
    if not isinstance(body, dict) or "stationId" not in body or "curve" not in body:
        return fail(40001, "缺少 stationId 或 curve")
    try:
        station_id = int(body["stationId"])
    except (TypeError, ValueError):
        return fail(40001, "参数校验失败")
    if station_id <= 0:
        return fail(40002, "换热站不存在")
    try:
        return ok(twin.run_recovery(station_id, body["curve"], body.get("steps", 20)))
    except TwinParamError:
        return fail(40001, "参数校验失败")
    except Exception:
        return fail(50001, "服务内部错误")
