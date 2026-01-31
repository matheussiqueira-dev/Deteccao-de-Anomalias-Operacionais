from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    status = {"status": "ok", "database": "ok"}
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        status["database"] = "unavailable"
        status["status"] = "degraded"
    return status
