from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database import crud
from app.schemas import AnomalyOut

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("/latest", response_model=list[AnomalyOut])
def latest_anomalies(
    request: Request,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
) -> list[AnomalyOut]:
    anomalies = crud.get_latest_anomalies(db, limit=limit)
    return [
        AnomalyOut(
            timestamp=a.timestamp,
            source=a.source,
            metric_name=a.metric_name,
            value=a.value,
            anomaly_score=a.anomaly_score,
            threshold=a.threshold
            if a.threshold is not None
            else request.app.state.detection_service.get_threshold(
                f"{a.source}:{a.metric_name}",
                a.model_used,
            ),
            model_used=a.model_used,
            status="anomaly_detected",
        )
        for a in anomalies
    ]
