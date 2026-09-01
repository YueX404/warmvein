from fastapi import APIRouter

from response import fail, ok
from services import workorder

router = APIRouter()


@router.post("/workorder/create")
def api_create(body: dict):
    if not body.get("alarmId") or not body.get("assignee"):
        return fail(40001, "缺少 alarmId 或 assignee")
    return ok({"orderId": workorder.create_from_alarm(body["alarmId"], body["assignee"])})


@router.get("/workorder/{order_id}")
def api_get(order_id: int):
    o = workorder.get_order(order_id)
    return ok(o) if o else fail(40002, "工单不存在")
