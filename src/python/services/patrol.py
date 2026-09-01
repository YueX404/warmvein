from sqlalchemy import text

from db import SessionLocal

_INSERT = (
    "INSERT INTO biz_patrol(station_id, plan_name, patrol_type, assignee, plan_date, status, created_at, updated_at) "
    "VALUES(:sid,:name,:pt,:asg,:pd,0,NOW(),NOW())"
)


def generate_plan(rule: dict) -> int:
    with SessionLocal() as s:
        r = s.execute(text(_INSERT), {
            "sid": rule["stationId"],
            "name": rule.get("planName", "auto"),
            "pt": rule["patrolType"],
            "asg": rule["assignee"],
            "pd": rule["planDate"],
        })
        pid = r.lastrowid
        if not pid:
            raise RuntimeError("patrol insert returned no id")
        s.commit()
        return pid
