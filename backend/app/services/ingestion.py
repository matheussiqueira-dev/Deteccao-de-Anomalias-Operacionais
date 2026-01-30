from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session
import structlog

from app.database import crud
from app.domain.entities import MetricEvent
from app.services.detection import DetectionService
from app.services.websocket_manager import WebSocketManager
from app.schemas import MetricIn, AnomalyOut


logger = structlog.get_logger(__name__)


class IngestionService:
    def __init__(self, detection: DetectionService, ws_manager: WebSocketManager):
        self.detection = detection
        self.ws_manager = ws_manager

    def ingest_metrics(self, db: Session, metrics: list[MetricIn]) -> list[AnomalyOut]:
        anomalies: list[AnomalyOut] = []
        for metric in metrics:
            timestamp = metric.timestamp or datetime.now(tz=timezone.utc)
            event = MetricEvent(
                timestamp=timestamp,
                source=metric.source,
                metric_name=metric.metric_name,
                value=metric.value,
                unit=metric.unit,
                tags=metric.tags,
            )
            crud.create_metric(
                db,
                timestamp=event.timestamp,
                source=event.source,
                metric_name=event.metric_name,
                value=event.value,
                unit=event.unit,
                tags=event.tags,
            )
            detection_result = self.detection.score_event(event)
            if detection_result:
                inference = self.detection.build_output(
                    metric_name=event.metric_name,
                    timestamp=event.timestamp,
                    value=event.value,
                    result=detection_result,
                )
                if detection_result.is_anomaly:
                    anomaly = crud.create_anomaly(
                        db,
                        timestamp=event.timestamp,
                        source=event.source,
                        metric_name=event.metric_name,
                        value=event.value,
                        anomaly_score=detection_result.score,
                        threshold=detection_result.threshold,
                        model_used=detection_result.model_used,
                    )
                    anomaly_out = AnomalyOut(
                        timestamp=anomaly.timestamp,
                        source=event.source,
                        metric_name=inference.metric_name,
                        value=inference.value,
                        anomaly_score=inference.anomaly_score,
                        threshold=inference.threshold,
                        model_used=inference.model_used,
                        status=inference.status,
                    )
                    anomalies.append(anomaly_out)
        db.commit()
        logger.info("metrics_ingested", total=len(metrics), anomalies=len(anomalies))
        return anomalies

    async def broadcast_anomalies(self, anomalies: list[AnomalyOut]) -> None:
        for anomaly in anomalies:
            await self.ws_manager.broadcast(
                {
                    "type": "alert",
                    "data": {
                        "metric": anomaly.metric_name,
                        "score": anomaly.anomaly_score,
                        "value": anomaly.value,
                        "timestamp": anomaly.timestamp.isoformat(),
                        "source": anomaly.source,
                    },
                }
            )
