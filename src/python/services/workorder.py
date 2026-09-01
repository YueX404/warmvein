from sqlalchemy import text

from db import SessionLocal

_INSERT_ORDER = (
    "INSERT INTO biz_work_order(alarm_id, assignee, order_type, status, created_at, updated_at) "
    "VALUES(:a,:as,'repair',0,NOW(),NOW())"
)
_SELECT_ORDER = (
    "SELECT order_id, alarm_id, assignee, status, created_at, updated_at "
    "FROM biz_work_order WHERE order_id=:o"
)
_SELECT_TRACE = (
    "SELECT action, operator, created_at FROM biz_work_order_trace "
    "WHERE order_id=:o ORDER BY created_at, trace_id"
)
_INSERT_TRACE = (
    "INSERT INTO biz_work_order_trace(order_id, action, operator, created_at) "
    "VALUES(:o,:act,:op,NOW())"
)


def create_from_alarm(alarm_id: int, assignee: str) -> int:
    with SessionLocal() as s:
        r = s.execute(text(_INSERT_ORDER), {"a": alarm_id, "as": assignee})
        oid = r.lastrowid
        if not oid:
            raise RuntimeError("work order insert returned no id")
        s.execute(text(_INSERT_TRACE), {"o": oid, "act": "create", "op": "系统"})
        s.commit()
        return oid


def get_order(order_id: int) -> dict:
    with SessionLocal() as s:
        row = s.execute(text(_SELECT_ORDER), {"o": order_id}).mappings().first()
        if not row:
            return {}
        traces = s.execute(text(_SELECT_TRACE), {"o": order_id}).mappings().all()
        out = dict(row)
        out["trace"] = [dict(t) for t in traces]
        return out
