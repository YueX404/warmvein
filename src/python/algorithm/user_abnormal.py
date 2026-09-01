"""Household heat-use anomaly: blocked, steal, water, or normal."""


def detect_user_abnormal(flow: float, room_temp: float, mean_flow: float, std_flow: float) -> str:
    """Classify a household against regional flow mean/std.

    blocked: room below 18 C with near-normal flow
    steal: flow z-score above 2
    water: room below 16 C with high flow
    """
    z = (flow - mean_flow) / std_flow if std_flow else 0.0
    if room_temp < 18 and abs(z) < 1:
        return "blocked"
    if z > 2:
        return "steal"
    if room_temp < 16 and flow > mean_flow + std_flow:
        return "water"
    return "normal"
