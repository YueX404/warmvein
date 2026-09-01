"""Frost blockage risk from supply temperature, outdoor temperature, and velocity."""


def frost_risk(T_supply: float, tw: float, velocity: float, v_min: float = 0.2) -> str:
    """Return low/medium/high frost-blockage risk for a pipe segment."""
    if T_supply < 5 and tw < 0:
        return "high"
    if T_supply < 10 and tw < -5:
        return "medium"
    if velocity < v_min:
        return "medium"
    return "low"
