from sqlalchemy import text

from db import SessionLocal


def create_from_alarm(alarm_id: int, assignee: str) -> int:
    with SessionLocal() as s:
        r = s.execute(text(
            "INSERT INTO biz_work_order(alarm_id, assignee, order_type, status, created_at, updated_at) "
            "VALUES(:a,:as,'repair',0,NOW(),NOW())"
        ), {"a": alarm_id, "as": assignee})
        s.commit()
        return r.lastrowid


def get_order(order_id: int) -> dict:
    with SessionLocal() as s:
        row = s.execute(text(
            "SELECT order_id, alarm_id, assignee, status, created_at, updated_at "
            "FROM biz_work_order WHERE order_id=:o"
        ), {"o": order_id}).mappings().first()
        return dict(row) if row else {}
