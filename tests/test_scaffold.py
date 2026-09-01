"""F0 脚手架冒烟测试：契约冻结后的回归基线。"""

from fastapi.testclient import TestClient

from main import app
from response import fail, ok

client = TestClient(app)


def test_health_returns_unified_envelope():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body == {"code": 0, "message": "ok", "data": {"status": "healthy"}}


def test_all_seven_module_routers_exist():
    from fastapi import APIRouter

    import main

    names = (
        "heat_router",
        "alarm_router",
        "workorder_router",
        "plan_router",
        "sms_router",
        "twin_router",
        "public_router",
    )
    assert main.heat_router.routes, "heat_router 应由 Dev-1 Task 1 填充主数据接口"
    for name in names:
        router = getattr(main, name)
        assert isinstance(router, APIRouter)


def test_response_ok_envelope():
    assert ok({"a": 1}) == {"code": 0, "message": "ok", "data": {"a": 1}}
    assert ok() == {"code": 0, "message": "ok", "data": None}


def test_response_fail_envelope():
    body = fail(40001, "参数校验失败")
    assert body == {"code": 40001, "message": "参数校验失败", "data": None}


def test_kafka_topics_contract():
    from kafka_topics import (
        HEAT_ALARM_TOPIC,
        HEAT_FORECAST_TOPIC,
        HEAT_SENSOR_TOPIC,
        SMS_NOTIFY_TOPIC,
    )

    assert HEAT_SENSOR_TOPIC == "heat-sensor-topic"
    assert HEAT_ALARM_TOPIC == "heat-alarm-topic"
    assert HEAT_FORECAST_TOPIC == "heat-forecast-topic"
    assert SMS_NOTIFY_TOPIC == "sms-notify-topic"
