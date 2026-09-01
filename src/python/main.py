#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安塞区城市安全生命线管网 AI 智慧平台 — FastAPI 服务入口

F0 脚手架：一次性挂载全部 7 个模块路由后锁定，之后无人再改。
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from response import fail

from routes_heat import router as heat_router
from routes_alarm import router as alarm_router
from routes_workorder import router as workorder_router
from routes_plan import router as plan_router
from routes_sms import router as sms_router
from routes_twin import router as twin_router
from routes_public import router as public_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="安塞供暖智慧运行平台",
    version="2026.08.31",
    description="城市安全生命线管网 AI 智慧平台 — 供暖管网智慧运行核心闭环",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.APP_CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, _exc: Exception):
    """Catch-all: log with traceback, return unified error response to client."""
    logger.exception("未处理异常 %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content=fail(50001, "服务内部错误"))


# Mount all 7 module routers under /api prefix (locked after F0)
for _router in (
    heat_router,
    alarm_router,
    workorder_router,
    plan_router,
    sms_router,
    twin_router,
    public_router,
):
    app.include_router(_router, prefix="/api")


@app.get("/health")
def health():
    return {"code": 0, "message": "ok", "data": {"status": "healthy"}}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)
