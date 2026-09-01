from algorithm.frost_risk import frost_risk
from algorithm.user_abnormal import detect_user_abnormal


def test_frost_high():
    assert frost_risk(4.0, -2.0, 0.5) == "high"


def test_frost_low():
    assert frost_risk(60.0, 5.0, 1.0) == "low"


def test_frost_medium_by_temp():
    assert frost_risk(8.0, -6.0, 1.0) == "medium"


def test_frost_medium_by_velocity():
    assert frost_risk(60.0, 5.0, 0.1) == "medium"


def test_user_steal():
    assert detect_user_abnormal(3.0, 21.0, 1.0, 0.4) == "steal"


def test_user_blocked():
    assert detect_user_abnormal(1.0, 15.0, 1.0, 0.4) == "blocked"


def test_user_water():
    assert detect_user_abnormal(1.5, 15.0, 1.0, 0.4) == "water"


def test_user_normal():
    assert detect_user_abnormal(1.0, 20.0, 1.0, 0.4) == "normal"
