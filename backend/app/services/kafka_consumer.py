from __future__ import annotations

import asyncio
import json
from datetime import datetime

from sqlalchemy.orm import Session
import structlog

from app.core.config import get_settings
from app.database.session import SessionLocal
from app.schemas import MetricIn
from app.services.ingestion import IngestionService

logger = structlog.get_logger(__name__)


class KafkaIngestor:
    def __init__(self, ingestion_service: IngestionService):
        self.ingestion_service = ingestion_service
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        settings = get_settings()
        if not settings.kafka_enabled:
            logger.info("kafka_ingestion_disabled")
            return
        try:
            from aiokafka import AIOKafkaConsumer
        except Exception as exc:
            logger.warning("kafka_client_unavailable", error=str(exc))
            return

        consumer = AIOKafkaConsumer(
            settings.kafka_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            enable_auto_commit=True,
        )
        await consumer.start()
        logger.info("kafka_consumer_started", topic=settings.kafka_topic)
        try:
            async for msg in consumer:
                await self._handle_message(msg.value)
        finally:
            await consumer.stop()

    async def _handle_message(self, payload: dict) -> None:
        try:
            metric = MetricIn(
                timestamp=datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00")),
                source=payload["source"],
                metric_name=payload["metric_name"],
                value=float(payload["value"]),
                unit=payload.get("unit"),
                tags=payload.get("tags") or [],
            )
        except Exception as exc:
            logger.warning("kafka_payload_invalid", error=str(exc))
            return

        db: Session = SessionLocal()
        try:
            anomalies = self.ingestion_service.ingest_metrics(db, [metric])
            if anomalies:
                await self.ingestion_service.broadcast_anomalies(anomalies)
        finally:
            db.close()
