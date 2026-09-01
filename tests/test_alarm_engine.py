from services.alarm_engine import judge_level, dedup_key, risk_level_from_frost


def test_judge_frost_red():
    assert judge_level("frost", 4) == 4


def test_judge_corrosion_yellow():
    assert judge_level("corrosion", 2) == 2


def test_dedup_key_stable():
    assert dedup_key(1, "frost") == dedup_key(1, "frost")


def test_frost_high():
    assert risk_level_from_frost("high") == 4
