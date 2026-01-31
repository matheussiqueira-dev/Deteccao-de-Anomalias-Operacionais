from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Anomaly, Metric


def create_metric(
    db: Session,
    timestamp: datetime,
    source: str,
    metric_name: str,
    value: float,
    unit: str | None = None,
    tags: list[str] | None = None,
) -> Metric:
    metric = Metric(
        timestamp=timestamp,
        source=source,
        metric_name=metric_name,
        value=value,
        unit=unit,
        tags=tags or [],
    )
    db.add(metric)
    return metric


def create_anomaly(
    db: Session,
    timestamp: datetime,
    source: str,
    metric_name: str,
    value: float,
    anomaly_score: float,
    threshold: float | None,
    model_used: str,
) -> Anomaly:
    anomaly = Anomaly(
        timestamp=timestamp,
        source=source,
        metric_name=metric_name,
        value=value,
        anomaly_score=anomaly_score,
        threshold=threshold,
        model_used=model_used,
    )
    db.add(anomaly)
    return anomaly


def get_latest_anomalies(db: Session, limit: int = 50) -> list[Anomaly]:
    stmt = select(Anomaly).order_by(Anomaly.timestamp.desc()).limit(limit)
    return list(db.scalars(stmt))


def get_metrics_history(
    db: Session,
    metric_name: str,
    source: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 1000,
) -> list[Metric]:
    stmt = select(Metric).where(Metric.metric_name == metric_name)
    if source:
        stmt = stmt.where(Metric.source == source)
    if start:
        stmt = stmt.where(Metric.timestamp >= start)
    if end:
        stmt = stmt.where(Metric.timestamp <= end)
    stmt = stmt.order_by(Metric.timestamp.asc()).limit(limit)
    return list(db.scalars(stmt))


def get_metric_values_for_training(
    db: Session,
    metric_name: str,
    source: str | None = None,
    limit: int = 5000,
) -> list[float]:
    stmt = select(Metric.value).where(Metric.metric_name == metric_name)
    if source:
        stmt = stmt.where(Metric.source == source)
    stmt = stmt.order_by(Metric.timestamp.desc()).limit(limit)
    return [row[0] for row in db.execute(stmt).all()]
