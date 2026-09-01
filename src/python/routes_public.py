from fastapi import APIRouter

from response import fail, ok
from services import public_svc
from services.public_svc import DESC_MAX_LEN

router = APIRouter()
public_api = APIRouter(prefix="/public")


def _parse_positive_int(value) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


@public_api.post("/notify/stop-heating")
def api_notify(body: dict):
    try:
        if not isinstance(body, dict) or "stationId" not in body:
            return fail(40001, "缺少 stationId")
        station_id = _parse_positive_int(body.get("stationId"))
        if station_id is None:
            return fail(40001, "参数校验失败")
        plan_time = str(body.get("planTime", ""))
        if len(plan_time) > 32:
            return fail(40001, "参数校验失败")
        result = public_svc.notify_stop_heating(station_id, plan_time)
        if result.get("reason") == "sms_gateway":
            return fail(50003, "短信网关失败", result)
        return ok(result)
    except Exception:
        return fail(50001, "服务内部错误")


@public_api.post("/repair/report")
def api_repair(body: dict):
    try:
        if not isinstance(body, dict) or not body.get("userId") or not body.get("desc"):
            return fail(40001, "缺少 userId 或 desc")
        user_id = _parse_positive_int(body.get("userId"))
        desc = str(body.get("desc", "")).strip()
        if user_id is None or not desc or len(desc) > DESC_MAX_LEN:
            return fail(40001, "参数校验失败")
        return ok(public_svc.create_repair_report(user_id, desc))
    except Exception:
        return fail(50001, "服务内部错误")


router.include_router(public_api)
