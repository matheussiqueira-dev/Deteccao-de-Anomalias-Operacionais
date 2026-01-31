from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database import crud
from app.database.session import get_db
from app.schemas import IngestResponse, MetricIn, MetricOut

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_metrics(
    payload: MetricIn | List[MetricIn],
    request: Request,
    db: Session = Depends(get_db),
) -> IngestResponse:
    metrics = payload if isinstance(payload, list) else [payload]
    service = request.app.state.ingestion_service
    anomalies = service.ingest_metrics(db, metrics)
    if anomalies:
        await service.broadcast_anomalies(anomalies)
    return IngestResponse(received=len(metrics), anomalies=anomalies)


@router.get("/history", response_model=list[MetricOut])
def metrics_history(
    metric_name: str = Query(...),
    source: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(1000, le=5000),
    db: Session = Depends(get_db),
) -> list[MetricOut]:
    metrics = crud.get_metrics_history(
        db,
        metric_name=metric_name,
        source=source,
        start=start,
        end=end,
        limit=limit,
    )
    return [
        MetricOut(
            timestamp=m.timestamp,
            source=m.source,
            metric_name=m.metric_name,
            value=m.value,
            unit=m.unit,
            tags=m.tags or [],
        )
        for m in metrics
    ]
