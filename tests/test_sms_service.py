from pathlib import Path
import json

import pytest

from services.sms_service import mask_phone, build_content, send_sms
from consumers.sms_consumer import dispatch_record, handle_notify


def test_mask_phone():
    assert mask_phone("13812341234") == "138****1234"


def test_mask_phone_keeps_non_mobile():
    assert mask_phone("12345") == "12345"


def test_build_content_fills_vars():
    assert build_content("停暖时间{planTime}", {"planTime": "09-01"}) == "停暖时间09-01"


class _FakeRedis:
    def __init__(self, data=None):
        self.data = dict(data or {})
        self.ttls = {}

    def get(self, key):
        return self.data.get(key)

    def incr(self, key):
        self.data[key] = str(int(self.data.get(key) or 0) + 1)
        return int(self.data[key])

    def expire(self, key, ttl):
        self.ttls[key] = ttl


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def mappings(self):
        return self

    def first(self):
        return self._row


class _FakeSession:
    def __init__(self, template=None):
        self.template = template
        self.rows = []

    def execute(self, stmt, params):
        sql = str(stmt)
        if "biz_sms_template" in sql:
            return _FakeResult(self.template)
        self.rows.append(params)
        return _FakeResult(None)

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeSender:
    def __init__(self, results=None):
        self.calls = []
        self.results = list(results or [{"success": True, "bizId": "mock-1"}])

    def _do_send(self, phone, content):
        self.calls.append((phone, content))
        if self.results:
            return self.results.pop(0)
        return {"success": True, "bizId": "mock"}


_UNSET = object()


def _send(phones, *, template=_UNSET, redis=None, sender=None, tpl_vars=None, code="ALARM_YELLOW"):
    if template is _UNSET:
        template = {"content": "站{stationName}"}
    session = _FakeSession(template=template)
    redis = redis or _FakeRedis()
    sender = sender or _FakeSender()
    slept = []
    batch_id = send_sms(
        code,
        phones,
        tpl_vars if tpl_vars is not None else {"stationName": "一号站"},
        redis_client=redis,
        session_factory=lambda: session,
        sender=sender,
        sleep=slept.append,
    )
    return batch_id, session, redis, sender, slept


def test_send_sms_missing_template_raises():
    with pytest.raises(ValueError, match="template not found"):
        _send(["13812341234"], template=None)


def test_send_sms_success_masks_and_logs():
    batch_id, session, redis, sender, _ = _send(["13812341234"])
    assert batch_id.startswith("b")
    assert sender.calls == [("13812341234", "站一号站")]
    assert session.rows[0]["pm"] == "138****1234"
    assert session.rows[0]["t"] == "ALARM_YELLOW"
    assert session.rows[0]["st"] == 2
    assert session.rows[0]["r"] == "mock-1"
    assert redis.data["sms:limit:13812341234"] == "1"
    assert redis.ttls["sms:limit:13812341234"] == 86400


def test_send_sms_skips_invalid_phone():
    _, session, _, sender, _ = _send(["138", "not-a-phone"])
    assert sender.calls == []
    assert session.rows == []


def test_send_sms_rate_limit_skips_and_logs():
    redis = _FakeRedis({"sms:limit:13812341234": "20"})
    _, session, redis, sender, _ = _send(["13812341234"], redis=redis)
    assert sender.calls == []
    assert session.rows[0]["st"] == 4
    assert session.rows[0]["pm"] == "138****1234"


def test_send_sms_retries_then_succeeds():
    sender = _FakeSender([
        {"success": False},
        {"success": True, "bizId": "ok-2"},
    ])
    _, session, _, sender, slept = _send(["13812341234"], sender=sender)
    assert len(sender.calls) == 2
    assert session.rows[0]["st"] == 2
    assert session.rows[0]["r"] == "ok-2"
    assert slept == [1]


def test_send_sms_retries_three_times_then_fails():
    sender = _FakeSender([
        {"success": False},
        {"success": False},
        {"success": False},
    ])
    _, session, redis, sender, slept = _send(["13812341234"], sender=sender)
    assert len(sender.calls) == 3
    assert session.rows[0]["st"] == 3
    assert "sms:limit:13812341234" not in redis.data
    assert slept == [1, 2]


def _capture_send():
    sent = []

    def send(template_code, phones, vars):
        sent.append({"code": template_code, "phones": phones, "vars": vars})
        return "b1"

    return sent, send


def test_handle_maps_red_and_sends():
    sent, send = _capture_send()
    result = handle_notify(
        {
            "level": 4,
            "phone": "13812341234",
            "alarmType": "frost",
            "stationName": "一号站",
        },
        send=send,
    )
    assert result == "ok"
    assert sent[0]["code"] == "ALARM_RED"
    assert sent[0]["phones"] == ["13812341234"]
    assert sent[0]["vars"]["stationName"] == "一号站"
    assert sent[0]["vars"]["type"] == "frost"


def test_handle_defaults_to_yellow():
    sent, send = _capture_send()
    result = handle_notify({"phone": "13812341234", "station_id": 1}, send=send)
    assert result == "ok"
    assert sent[0]["code"] == "ALARM_YELLOW"
    assert sent[0]["vars"]["stationName"] == 1


def test_handle_skips_missing_phone():
    sent, send = _capture_send()
    result = handle_notify({"level": 4, "station_id": 1}, send=send)
    assert result == "skip"
    assert sent == []


def test_consumer_has_main_guard():
    text = Path("src/python/consumers/sms_consumer.py").read_text(encoding="utf-8")
    assert 'if __name__ == "__main__"' in text
    assert "consume()" in text
    assert "SMS_NOTIFY_TOPIC" in text
    assert "enable_auto_commit=False" in text
    assert "ALARM_NOTICE" not in text
    assert 'auto_offset_reset="earliest"' in text


class _FakeMsg:
    def __init__(self, payload):
        self.value = (
            payload if isinstance(payload, bytes)
            else json.dumps(payload).encode()
        )


class _FakeKafka:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


_SMS_MSG = {"level": 4, "phone": "13812341234", "alarmType": "frost"}


def test_dispatch_commits_on_ok_and_skip():
    kafka = _FakeKafka()
    assert dispatch_record(_FakeMsg(_SMS_MSG), kafka, handle=lambda _: "ok") == "ok"
    assert kafka.commits == 1
    kafka = _FakeKafka()
    dispatch_record(_FakeMsg(_SMS_MSG), kafka, handle=lambda _: "skip")
    assert kafka.commits == 1


def test_dispatch_retries_error_then_commits():
    kafka = _FakeKafka()
    n = {"i": 0}

    def flaky(_payload):
        n["i"] += 1
        return "error" if n["i"] == 1 else "ok"

    slept = []
    result = dispatch_record(
        _FakeMsg(_SMS_MSG), kafka, handle=flaky, sleep=slept.append
    )
    assert result == "ok"
    assert n["i"] == 2
    assert kafka.commits == 1
    assert slept


def test_dispatch_send_raise_does_not_commit_until_ok():
    kafka = _FakeKafka()
    n = {"i": 0}

    def boom(_payload):
        n["i"] += 1
        if n["i"] == 1:
            raise RuntimeError("db down")
        return "ok"

    slept = []
    result = dispatch_record(
        _FakeMsg(_SMS_MSG), kafka, handle=boom, sleep=slept.append
    )
    assert result == "ok"
    assert n["i"] == 2
    assert kafka.commits == 1
    assert slept


def test_dispatch_commits_undecodable_payload():
    kafka = _FakeKafka()
    result = dispatch_record(_FakeMsg(b"not-json"), kafka, handle=lambda _: "ok")
    assert result == "skip"
    assert kafka.commits == 1


ALARM_RED_TPL = "【暖脉供热】{stationName}紧急预警(红色)，需立即到场！联系人:{leaderPhone}"


def test_handle_red_fills_leader_phone_fallback():
    sent, send = _capture_send()
    result = handle_notify(
        {"level": 4, "phone": "13812341234", "stationName": "一号站"},
        send=send,
    )
    assert result == "ok"
    content = build_content(ALARM_RED_TPL, sent[0]["vars"])
    assert "{leaderPhone}" not in content
    assert "请登录平台" in content


def test_handle_red_uses_leader_phone_from_payload():
    sent, send = _capture_send()
    handle_notify(
        {
            "level": 4,
            "phone": "13812341234",
            "stationName": "一号站",
            "leaderPhone": "13900001111",
        },
        send=send,
    )
    content = build_content(ALARM_RED_TPL, sent[0]["vars"])
    assert "13900001111" in content


class _BoomThenOkSender:
    def __init__(self):
        self.calls = 0

    def _do_send(self, phone, content):
        self.calls += 1
        if self.calls < 3:
            raise RuntimeError("gateway timeout")
        return {"success": True, "bizId": "recovered"}


class _AlwaysBoomSender:
    def _do_send(self, phone, content):
        raise RuntimeError("gateway down")


def test_send_sms_retries_when_do_send_raises():
    sender = _BoomThenOkSender()
    _, session, _, _, slept = _send(["13812341234"], sender=sender)
    assert sender.calls == 3
    assert session.rows[0]["st"] == 2
    assert session.rows[0]["r"] == "recovered"
    assert slept == [1, 2]


def test_send_sms_logs_fail_when_do_send_always_raises():
    _, session, redis, _, slept = _send(["13812341234"], sender=_AlwaysBoomSender())
    assert session.rows[0]["st"] == 3
    assert session.rows[0]["e"] == "RuntimeError"
    assert "sms:limit:13812341234" not in redis.data
    assert slept == [1, 2]
