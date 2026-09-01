from pathlib import Path
import json

from services.alarm_engine import (
    DEDUP_WINDOW_SEC,
    dedup_key,
    judge_level,
    risk_level_from_frost,
    to_schema_type,
)
from consumers.alarm_consumer import dispatch_record, handle_alarm


def test_judge_frost_red():
    assert judge_level("frost", 4) == 4


def test_judge_corrosion_yellow():
    assert judge_level("corrosion", 2) == 2


def test_dedup_key_stable():
    assert dedup_key(1, "frost") == dedup_key(1, "frost")


def test_frost_high():
    assert risk_level_from_frost("high") == 4


def test_schema_type_frost_maps_freeze():
    assert to_schema_type("frost") == "freeze"
    assert to_schema_type("imbalance") == "balance"
    assert to_schema_type("steal") == "theft"


class _FakeRedis:
    def __init__(self):
        self.data = {}

    def set(self, name, value, nx=False, ex=None):
        if nx and name in self.data:
            return False
        self.data[name] = str(value)
        return True

    def delete(self, name):
        self.data.pop(name, None)


class _FakeSession:
    def __init__(self, fail=False):
        self.fail = fail
        self.rows = []

    def execute(self, _stmt, params):
        if self.fail:
            raise RuntimeError("db down")
        self.rows.append(params)

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _handle(msg, redis=None, session=None, publish=None):
    redis = redis or _FakeRedis()
    session = session or _FakeSession()
    published = []
    pub = publish if publish is not None else published.append
    result = handle_alarm(
        msg,
        redis_client=redis,
        session_factory=lambda: session,
        publish=pub,
    )
    return result, redis, session, published


_VALID = {"station_id": 1, "alarmType": "frost", "level": 4}


def test_handle_skips_missing_station_id():
    result, redis, session, published = _handle({"alarmType": "frost"})
    assert result == "skip"
    assert session.rows == []
    assert published == []
    assert redis.data == {}


def test_handle_skips_blank_alarm_type():
    result, redis, session, published = _handle({"station_id": 1})
    assert result == "skip"
    assert session.rows == []
    assert published == []


def test_handle_skips_unknown_alarm_type():
    result, _, session, published = _handle(
        {"station_id": 1, "alarmType": "not-a-type"}
    )
    assert result == "skip"
    assert session.rows == []
    assert published == []


def test_handle_dedup_when_nx_fails():
    redis = _FakeRedis()
    redis.data[dedup_key(1, "frost")] = "1"
    result, _, session, published = _handle(_VALID, redis=redis)
    assert result == "dedup"
    assert session.rows == []
    assert published == []


def test_handle_inserts_schema_type_and_publishes():
    result, redis, session, published = _handle(_VALID)
    assert result == "ok"
    assert session.rows[0]["t"] == "freeze"
    assert session.rows[0]["l"] == 4
    assert session.rows[0]["s"] == 1
    assert published[0]["level"] == 4
    assert dedup_key(1, "frost") in redis.data
    assert DEDUP_WINDOW_SEC == 300


def test_handle_db_failure_releases_dedup_key():
    result, redis, session, published = _handle(
        _VALID, session=_FakeSession(fail=True)
    )
    assert result == "error"
    assert published == []
    assert redis.data == {}


def test_handle_sms_failure_keeps_row_and_key():
    def boom(_alarm):
        raise RuntimeError("sms down")

    result, redis, session, _ = _handle(_VALID, publish=boom)
    assert result == "ok"
    assert session.rows
    assert dedup_key(1, "frost") in redis.data


def test_handle_frost_string_level():
    result, _, session, _ = _handle(
        {"station_id": 1, "alarmType": "frost", "level": "high"}
    )
    assert result == "ok"
    assert session.rows[0]["l"] == 4


def test_handle_non_frost_string_level_uses_type_table():
    result, _, session, _ = _handle(
        {"station_id": 1, "alarmType": "corrosion", "level": "high"}
    )
    assert result == "ok"
    assert session.rows[0]["l"] == 2


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


def test_dispatch_commits_on_ok_skip_dedup():
    kafka = _FakeKafka()
    assert dispatch_record(_FakeMsg(_VALID), kafka, handle=lambda _: "ok") == "ok"
    assert kafka.commits == 1
    kafka = _FakeKafka()
    dispatch_record(_FakeMsg(_VALID), kafka, handle=lambda _: "skip")
    assert kafka.commits == 1
    kafka = _FakeKafka()
    dispatch_record(_FakeMsg(_VALID), kafka, handle=lambda _: "dedup")
    assert kafka.commits == 1


def test_dispatch_retries_error_then_commits():
    kafka = _FakeKafka()
    n = {"i": 0}

    def flaky(_payload):
        n["i"] += 1
        return "error" if n["i"] == 1 else "ok"

    slept = []
    result = dispatch_record(
        _FakeMsg(_VALID), kafka, handle=flaky, sleep=slept.append
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


def test_consumer_has_main_guard():
    text = Path("src/python/consumers/alarm_consumer.py").read_text(
        encoding="utf-8"
    )
    assert 'if __name__ == "__main__"' in text
    assert "consume()" in text
    assert "enable_auto_commit=False" in text
