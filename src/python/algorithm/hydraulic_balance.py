"""Hydraulic balance: beta = actual flow / design flow."""


def compute_balance(actual: dict, design: dict) -> dict:
    result = {}
    for bid, g_act in actual.items():
        g_des = design.get(bid, 0.0) or 0.0
        beta = round(g_act / g_des, 3) if g_des else 0.0
        result[bid] = {
            "beta": beta,
            "unbalanced": beta < 0.9 or beta > 1.1,
            "suggest_open": None if not g_des else round((1 - beta) * 100, 1),
        }
    return result
