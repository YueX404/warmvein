"""Pipe heat loss: Q = K * pi * D * L * (T_avg - T_ambient), unit W."""

import math


def pipe_heat_loss(K: float, D: float, L: float, Tg: float, Th: float, Tamb: float) -> float:
    """Segment heat loss in watts. K: W/(m2·C); D: m; L: m; temps: C."""
    T_avg = (Tg + Th) / 2.0
    return K * math.pi * D * L * (T_avg - Tamb)
