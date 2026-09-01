from fastapi import APIRouter, Query

from response import fail, ok
from services import master_data

router = APIRouter(prefix="/heat")


def _valid_region(region: str) -> bool:
    if len(region) > 32:
        return False
    return all(ch.isalnum() or ch in "-_" for ch in region)


@router.get("/stations")
def api_stations(region: str = Query(None)):
    if region is not None:
        region = region.strip()
        if not region:
            region = None
        elif not _valid_region(region):
            return fail(40001, "参数校验失败")
    try:
        return ok({"stations": master_data.get_stations(region)})
    except Exception:
        return fail(50001, "服务内部错误")
