from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import crud
from app.database.session import get_db
from app.schemas import TrainRequest

router = APIRouter(prefix="/train", tags=["train"])


@router.post("")
def retrain(
    payload: TrainRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    values = crud.get_metric_values_for_training(
        db,
        metric_name=payload.metric_name,
        source=payload.source,
    )
    if len(values) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough data to retrain"
        )
    metric_key = f"{payload.source}:{payload.metric_name}"
    detector = request.app.state.detection_service
    if detector is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Detector not available"
        )
    detector.retrain(metric_key, values)
    return {"status": "ok", "message": "Model retrained"}
