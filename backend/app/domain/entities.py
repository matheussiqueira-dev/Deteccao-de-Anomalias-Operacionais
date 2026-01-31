from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class MetricEvent:
    timestamp: datetime
    source: str
    metric_name: str
    value: float
    unit: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnomalyResult:
    timestamp: datetime
    source: str
    metric_name: str
    value: float
    anomaly_score: float
    threshold: float
    model_used: str
    status: str
