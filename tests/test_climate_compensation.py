from algorithm.climate_compensation import climate_compensate


def test_colder_outdoor_raises_supply_temp():
    warm = climate_compensate(tw=0.0)
    cold = climate_compensate(tw=-9.0)
    assert cold["TgSet"] > warm["TgSet"]


def test_design_point_exact():
    r = climate_compensate(tw=-9.0)
    assert abs(r["TgSet"] - 75.0) < 0.01
