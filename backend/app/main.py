from __future__ import annotations

import asyncio
from contextlib import suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import routes_anomalies, routes_auth, routes_health, routes_metrics, routes_train, ws
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.init_db import init_db
from app.services.detection import DetectionService
from app.services.ingestion import IngestionService
from app.services.kafka_consumer import KafkaIngestor
from app.services.websocket_manager import WebSocketManager

settings = get_settings()

configure_logging()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.metrics_enabled:
    Instrumentator().instrument(app).expose(app, include_in_schema=False)

app.include_router(routes_auth.router)
app.include_router(routes_metrics.router)
app.include_router(routes_anomalies.router)
app.include_router(routes_train.router)
app.include_router(routes_health.router)
app.include_router(ws.router)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    app.state.ws_manager = WebSocketManager()
    app.state.detection_service = DetectionService()
    app.state.ingestion_service = IngestionService(
        app.state.detection_service,
        app.state.ws_manager,
    )
    app.state.kafka_ingestor = KafkaIngestor(app.state.ingestion_service)
    app.state.kafka_task = asyncio.create_task(app.state.kafka_ingestor.start())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    task = getattr(app.state, "kafka_task", None)
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
