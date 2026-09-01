from algorithm.climate_compensation import climate_compensate


def test_colder_outdoor_raises_supply_temp():
    warm = climate_compensate(tw=0.0)
    cold = climate_compensate(tw=-9.0)
    assert cold["TgSet"] > warm["TgSet"]


def test_design_point_exact():
    r = climate_compensate(tw=-9.0)
    assert abs(r["TgSet"] - 75.0) < 0.01
    assert abs(r["thSet"] - 50.0) < 0.01


def test_equal_design_temps_no_divide_by_zero():
    r = climate_compensate(tw=0.0, tn=18.0, Tg_d=75.0, tw_d=18.0)
    assert r["TgSet"] == 75.0
    assert r["thSet"] == 50.0
