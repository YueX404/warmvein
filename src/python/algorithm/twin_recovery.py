"""Stop-heat recovery: discrete-time warmup until all user rooms >= 18C."""

ROOM_TARGET = 18.0
INIT_TEMP = 5.0
# Distinct thermal inertia so tReach waits for every user, not a single node.
USER_K = (0.10, 0.08, 0.06)


def _step(T_node: float, Tg: float, K_loss: float = 0.1) -> float:
    return T_node + (Tg - T_node) * K_loss


def _supply_at(supply_curve: list, index: int) -> float:
    if not supply_curve:
        return INIT_TEMP
    if index < len(supply_curve):
        return float(supply_curve[index])
    return float(supply_curve[-1])


def simulate_recovery(station_id: int, supply_curve: list, steps: int = 20) -> dict:
    """Advance user rooms each hour; tReach is the first step all rooms hit 18C."""
    rooms = [INIT_TEMP] * len(USER_K)
    chart = []
    t_reach = steps
    reached = False
    for i in range(steps):
        tg = _supply_at(supply_curve, i)
        rooms = [_step(temp, tg, k_loss) for temp, k_loss in zip(rooms, USER_K)]
        chart.append(round(min(rooms), 2))
        if not reached and all(temp >= ROOM_TARGET for temp in rooms):
            t_reach = i + 1
            reached = True
    return {
        "stationId": station_id,
        "tReach": t_reach,
        "chart": chart,
        "converged": reached,
        "hoursToReach": t_reach if reached else None,
    }
