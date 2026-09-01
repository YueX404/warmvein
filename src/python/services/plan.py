from sqlalchemy import text

from db import SessionLocal

_TYPE_MAP = {
    "frost": "freeze",
    "freeze": "freeze",
    "leak": "burst",
    "burst": "burst",
    "shutdown": "shutdown",
    "steal": "third_party",
    "theft": "third_party",
    "third_party": "third_party",
}


def match(alarm_type: str, level: int) -> dict:
    ptype = _TYPE_MAP.get(alarm_type, alarm_type)
    with SessionLocal() as s:
        row = s.execute(text(
            "SELECT plan_id, name, plan_type, alarm_level, trigger_condition, steps, resource_list, status "
            "FROM biz_plan WHERE plan_type=:t AND status=1 "
            "AND (alarm_level IS NULL OR alarm_level=:lv) "
            "ORDER BY alarm_level DESC LIMIT 1"),
            {"t": ptype, "lv": level}).mappings().first()
    return dict(row) if row else {"plan_type": ptype, "plan_id": None}


def activate(plan_id: int, alarm_id: int | None = None, operator: str = "") -> int:
    if not plan_id:
        return 0
    with SessionLocal() as s:
        exists = s.execute(text(
            "SELECT plan_id FROM biz_plan WHERE plan_id=:p AND status=1"),
            {"p": plan_id}).first()
        if not exists:
            return 0
        r = s.execute(text(
            "INSERT INTO biz_plan_execution(plan_id, alarm_id, operator, status, started_at) "
            "VALUES(:p,:a,:op,0,NOW())"),
            {"p": plan_id, "a": alarm_id, "op": operator or "system"})
        s.commit()
        return r.lastrowid
