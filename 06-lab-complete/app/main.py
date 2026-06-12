"""
Production AI Agent — Final Project (Lab 6)

REST API with Redis-backed state, API key auth, rate limit, and cost guard.
"""
import signal
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.agent import ask_user
from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_and_record_cost
from app.logging_config import log_event, setup_logging
from app.rate_limiter import check_rate_limit
from app.redis_client import redis_client
from app.schemas import AskMetadata, AskRequest, AskResponse

logger = setup_logging()

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    log_event(
        logger,
        "startup",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        instance_id=settings.instance_id,
    )

    redis_client.connect()
    if not redis_client.ping():
        raise RuntimeError("Redis is not available")

    _is_ready = True
    log_event(
        logger,
        "ready",
        redis="memory" if redis_client.using_memory else "redis",
        instance_id=settings.instance_id,
    )

    yield

    _is_ready = False
    log_event(logger, "shutdown", instance_id=settings.instance_id)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Instance-Id"] = settings.instance_id
        if "server" in response.headers:
            del response.headers["server"]
        log_event(
            logger,
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            ms=round((time.time() - start) * 1000, 1),
            instance_id=settings.instance_id,
        )
        return response
    except Exception:
        _error_count += 1
        raise


@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "instance_id": settings.instance_id,
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
        },
    }


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(body: AskRequest, _key: str = Depends(verify_api_key)):
    check_rate_limit(body.user_id)
    cost_usd = check_and_record_cost(body.user_id)

    log_event(
        logger,
        "agent_call",
        user_id=body.user_id,
        question_length=len(body.question),
        instance_id=settings.instance_id,
    )

    answer, conversation_length = ask_user(body.user_id, body.question)

    return AskResponse(
        answer=answer,
        user_id=body.user_id,
        conversation_length=conversation_length,
        metadata=AskMetadata(
            environment=settings.environment,
            model=settings.model_name,
            cost_usd=cost_usd,
        ),
    )


@app.get("/health", tags=["Operations"])
def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "instance_id": settings.instance_id,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "storage": "memory" if redis_client.using_memory else "redis",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    if not _is_ready or not redis_client.ping():
        raise HTTPException(status_code=503, detail="Not ready")
    return {
        "ready": True,
        "redis": "ok",
        "instance_id": settings.instance_id,
    }


def _handle_signal(signum, _frame):
    log_event(logger, "signal", signum=signum, instance_id=settings.instance_id)


signal.signal(signal.SIGTERM, _handle_signal)


if __name__ == "__main__":
    log_event(
        logger,
        "boot",
        host=settings.host,
        port=settings.port,
        environment=settings.environment,
    )
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
