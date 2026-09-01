from fastapi import APIRouter
from response import ok, fail
from services import plan

router = APIRouter()

_ALARM_TYPE_MAX = 32
_OPERATOR_MAX = 32


def _as_int(value) -> int | None:
    if type(value) is not int:
        return None
    return value


def _parse_match(body: dict):
    alarm_type = body.get("alarmType")
    if not isinstance(alarm_type, str) or not alarm_type.strip():
        return None, "缺少 alarmType"
    alarm_type = alarm_type.strip()
    if len(alarm_type) > _ALARM_TYPE_MAX:
        return None, "alarmType 非法"
    if "level" not in body or body.get("level") is None:
        level = 2
    else:
        level = _as_int(body.get("level"))
        if level is None or level < 1 or level > 4:
            return None, "level 非法"
    return {"alarmType": alarm_type, "level": level}, None


def _parse_activate(body: dict):
    plan_id = _as_int(body.get("planId"))
    if plan_id is None or plan_id < 1:
        return None, "缺少 planId"
    alarm_id = body.get("alarmId")
    if alarm_id is not None:
        alarm_id = _as_int(alarm_id)
        if alarm_id is None or alarm_id < 1:
            return None, "alarmId 非法"
    operator = body.get("operator", "")
    if operator is None:
        operator = ""
    if not isinstance(operator, str):
        return None, "operator 非法"
    operator = operator.strip()
    if len(operator) > _OPERATOR_MAX:
        return None, "operator 超长"
    return {"planId": plan_id, "alarmId": alarm_id, "operator": operator}, None


@router.post("/plan/match")
def api_match(body: dict):
    parsed, err = _parse_match(body)
    if err:
        return fail(40001, err)
    return ok(plan.match(parsed["alarmType"], parsed["level"]))


@router.post("/plan/activate")
def api_activate(body: dict):
    parsed, err = _parse_activate(body)
    if err:
        return fail(40001, err)
    exec_id = plan.activate(parsed["planId"], parsed["alarmId"], parsed["operator"])
    if not exec_id:
        return fail(40002, "预案不存在")
    return ok({"ok": True, "execId": exec_id})
