from datetime import datetime

from fastapi import APIRouter

from response import fail, ok
from services import patrol, workorder

router = APIRouter()

_STATUS_NAME = {
    0: "待派",
    1: "已派",
    2: "处置中",
    3: "待核验",
    4: "已销号",
}


def _fmt_dt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)[:19]


def _to_api(order: dict) -> dict:
    return {
        "orderId": order["order_id"],
        "alarmId": order["alarm_id"],
        "assignee": order["assignee"],
        "status": order["status"],
        "statusName": _STATUS_NAME.get(order["status"], ""),
        "createdAt": _fmt_dt(order.get("created_at")),
        "updatedAt": _fmt_dt(order.get("updated_at")),
        "trace": [
            {
                "action": t["action"],
                "operator": t["operator"],
                "time": _fmt_dt(t.get("created_at") or t.get("time")),
            }
            for t in order.get("trace") or []
        ],
    }


def _parse_create(body: dict):
    alarm_id = body.get("alarmId")
    assignee = body.get("assignee")
    if type(alarm_id) is not int or alarm_id <= 0:
        return None
    if not isinstance(assignee, str):
        return None
    assignee = assignee.strip()
    if not assignee or len(assignee) > 32:
        return None
    return alarm_id, assignee


@router.post("/workorder/create")
def api_create(body: dict):
    parsed = _parse_create(body)
    if parsed is None:
        return fail(40001, "参数校验失败")
    alarm_id, assignee = parsed
    return ok({"orderId": workorder.create_from_alarm(alarm_id, assignee)})


@router.get("/workorder/{order_id}")
def api_get(order_id: int):
    o = workorder.get_order(order_id)
    return ok(_to_api(o)) if o else fail(40002, "工单不存在")


_PATROL_TYPES = {"daily", "special", "emergency"}
_ASSIGNEE_MAX = 32
_PLAN_NAME_MAX = 64


def _parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
    return value


def _parse_patrol(body: dict):
    station_id = body.get("stationId")
    if type(station_id) is not int or station_id <= 0:
        return None
    patrol_type = body.get("patrolType")
    if not isinstance(patrol_type, str) or patrol_type not in _PATROL_TYPES:
        return None
    assignee = body.get("assignee")
    if not isinstance(assignee, str):
        return None
    assignee = assignee.strip()
    if not assignee or len(assignee) > _ASSIGNEE_MAX:
        return None
    plan_date = _parse_date(body.get("planDate"))
    if plan_date is None:
        return None
    plan_name = body.get("planName", "auto")
    if plan_name is None:
        plan_name = "auto"
    if not isinstance(plan_name, str):
        return None
    plan_name = plan_name.strip() or "auto"
    if len(plan_name) > _PLAN_NAME_MAX:
        return None
    return {
        "stationId": station_id,
        "patrolType": patrol_type,
        "assignee": assignee,
        "planDate": plan_date,
        "planName": plan_name,
    }


@router.post("/patrol/plan/generate")
def api_patrol_generate(body: dict):
    parsed = _parse_patrol(body)
    if parsed is None:
        return fail(40001, "缺少 stationId/patrolType/assignee/planDate")
    return ok({"patrolId": patrol.generate_plan(parsed)})

