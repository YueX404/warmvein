"""Climate compensation: outdoor temp tw -> secondary supply/return setpoints."""


def climate_compensate(tw: float, tn: float = 18.0, Tg_d: float = 75.0,
                       tw_d: float = -9.0, dT_d: float = 25.0) -> dict:
    """Outdoor temperature tw (C) to secondary network setpoints.

    Tg_set = tn + (Tg_d - tn) * (tw - tn) / (tw_d - tn)
    th_set = Tg_set - dT_d
    """
    Tg_set = tn + (Tg_d - tn) * (tw - tn) / (tw_d - tn)
    th_set = Tg_set - dT_d
    return {"TgSet": round(Tg_set, 1), "thSet": round(th_set, 1), "tw": tw}
