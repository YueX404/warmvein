from fastapi import APIRouter
from response import ok, fail
from services import plan

router = APIRouter()


@router.post("/plan/match")
def api_match(body: dict):
    if not body.get("alarmType"):
        return fail(40001, "缺少 alarmType")
    return ok(plan.match(body["alarmType"], body.get("level", 2)))


@router.post("/plan/activate")
def api_activate(body: dict):
    if not body.get("planId"):
        return fail(40001, "缺少 planId")
    exec_id = plan.activate(body["planId"], body.get("alarmId"), body.get("operator", ""))
    if not exec_id:
        return fail(40002, "预案不存在")
    return ok({"ok": True, "execId": exec_id})
