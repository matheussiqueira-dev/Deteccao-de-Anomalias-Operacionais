from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String, Index, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    source = Column(String(50), index=True, nullable=False)
    metric_name = Column(String(100), index=True, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)
    tags = Column(JSON, nullable=True)


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    source = Column(String(50), index=True, nullable=False)
    metric_name = Column(String(100), index=True, nullable=False)
    value = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    threshold = Column(Float, nullable=True)
    model_used = Column(String(50), nullable=False)


Index("ix_metrics_time_metric", Metric.timestamp, Metric.metric_name)
Index("ix_anomalies_time_metric", Anomaly.timestamp, Anomaly.metric_name)
