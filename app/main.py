import hmac
import hashlib
import json
import logging
import time
import uuid
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Response, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import ValidationError

from app.config import settings
from app.models import WebhookPayload, PaginatedResponse
from app.storage import db_repo
from app.logging_utils import setup_logger
from app.metrics import track_http_request, track_webhook_result, generate_prometheus_output
from datetime import datetime


setup_logger(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lyftr Backend Assignment")

@app.middleware("http")
async def metrics_and_logging_middleware(request: Request, call_next):
    start_time = time.time()
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000

    track_http_request(request.url.path, response.status_code)

    # Structured logging
    log_data = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": round(process_time, 2)
    }
    
    if hasattr(request.state, "webhook_log_context"):
        log_data.update(request.state.webhook_log_context)

    logger.info("Request processed", extra=log_data)
    
    return response

async def verify_signature(request: Request, x_signature: str):
    if not x_signature:
        raise HTTPException(status_code=401, detail="invalid signature")

    body_bytes = await request.body()
    secret_bytes = settings.webhook_secret.encode("utf-8")
    
    expected_signature = hmac.new(
        secret_bytes, 
        body_bytes, 
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, x_signature):
        raise HTTPException(status_code=401, detail="invalid signature")

@app.post("/webhook")
async def receive_message(request: Request):
    """
    Ingests inbound messages exactly once.
    """
    x_signature = request.headers.get("X-Signature")
    
    try:
        await verify_signature(request, x_signature)
    except HTTPException as e:
        track_webhook_result("invalid_signature")
        request.state.webhook_log_context = {"result": "invalid_signature"}
        raise e

    try:
        body_json = await request.json()
        payload = WebhookPayload(**body_json)
    except (json.JSONDecodeError, ValidationError):
        track_webhook_result("validation_error")
        request.state.webhook_log_context = {"result": "validation_error"}
        raise HTTPException(status_code=422, detail="Invalid payload")

    result = db_repo.insert_message(payload)

    track_webhook_result(result)
    
    request.state.webhook_log_context = {
        "message_id": payload.message_id,
        "dup": result == "duplicate",
        "result": result
    }

    return {"status": "ok"}

@app.get("/messages", response_model=PaginatedResponse)
def list_messages(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sender: Optional[str] = Query(None, alias="from"),
    since: Optional[str] = None,
    q: Optional[str] = None
):
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            pass

    data, total = db_repo.get_messages(
        limit=limit, 
        offset=offset, 
        sender=sender, 
        since=since_dt, 
        text_search=q
    )

    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/stats")
def get_stats():
    return db_repo.get_stats()

@app.get("/health/live")
def liveness():
    return {"status": "ok"}

@app.get("/health/ready")
def readiness():
    if not settings.webhook_secret:
        raise HTTPException(status_code=503, detail="Secret not configured")

    try:
        with db_repo._get_conn() as conn:
            conn.execute("SELECT 1")
    except Exception:
        raise HTTPException(status_code=503, detail="Database unreachable")

    return {"status": "ready"}

@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return generate_prometheus_output()