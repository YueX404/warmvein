from algorithm.heat_loss import pipe_heat_loss


def test_loss_positive_and_scales_with_length():
    a = pipe_heat_loss(0.5, 0.1, 100.0, 75.0, 50.0, -5.0)
    b = pipe_heat_loss(0.5, 0.1, 200.0, 75.0, 50.0, -5.0)
    assert a > 0 and b == 2 * a


def test_loss_zero_when_isothermal():
    assert pipe_heat_loss(0.5, 0.1, 100.0, 20.0, 20.0, 20.0) == 0.0


def test_loss_scales_with_temperature_difference():
    low_dt = pipe_heat_loss(0.5, 0.1, 100.0, 40.0, 40.0, 20.0)
    high_dt = pipe_heat_loss(0.5, 0.1, 100.0, 60.0, 60.0, 20.0)
    assert high_dt == 2 * low_dt
