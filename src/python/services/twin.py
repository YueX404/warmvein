"""Stop-heat recovery service: validate input then run the twin algorithm."""

from algorithm.twin_recovery import simulate_recovery

_MAX_STEPS = 168
_MIN_TEMP = -30.0
_MAX_TEMP = 150.0


class TwinParamError(ValueError):
    """Raised when recovery request fields fail type/range checks."""


def _parse_steps(value) -> int:
    try:
        steps = int(value)
    except (TypeError, ValueError) as exc:
        raise TwinParamError("steps") from exc
    if steps < 1 or steps > _MAX_STEPS:
        raise TwinParamError("steps")
    return steps


def _parse_temp(value) -> float:
    try:
        temp = float(value)
    except (TypeError, ValueError) as exc:
        raise TwinParamError("curve") from exc
    if temp < _MIN_TEMP or temp > _MAX_TEMP:
        raise TwinParamError("curve")
    return temp


def _from_list(curve: list) -> list:
    if not curve:
        raise TwinParamError("curve")
    return [_parse_temp(item) for item in curve]


def _from_object(curve: dict, default_steps: int) -> tuple:
    if "targetSupplyTemp" not in curve:
        raise TwinParamError("curve")
    target = _parse_temp(curve["targetSupplyTemp"])
    ramp = _parse_temp(curve.get("rampRate", 2.0))
    start = _parse_temp(curve.get("startSupplyTemp", 20.0))
    steps = _parse_steps(curve.get("steps", default_steps))
    if ramp <= 0:
        raise TwinParamError("curve")
    temps = []
    tg = start
    for _ in range(steps):
        if tg < target:
            tg = min(target, tg + ramp)
        elif tg > target:
            tg = max(target, tg - ramp)
        temps.append(tg)
    return temps, steps


def run_recovery(station_id: int, supply_curve, steps: int = 20) -> dict:
    n = _parse_steps(steps)
    if isinstance(supply_curve, list):
        curve = _from_list(supply_curve)
    elif isinstance(supply_curve, dict):
        curve, n = _from_object(supply_curve, n)
    else:
        raise TwinParamError("curve")
    return simulate_recovery(station_id, curve, n)
