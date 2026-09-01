from datetime import datetime

from fastapi import APIRouter

from response import fail, ok
from services import workorder

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
