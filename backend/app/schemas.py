from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MetricIn(BaseModel):
    timestamp: Optional[datetime] = None
    source: str
    metric_name: str
    value: float
    unit: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class MetricOut(BaseModel):
    timestamp: datetime
    source: str
    metric_name: str
    value: float
    unit: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class AnomalyOut(BaseModel):
    timestamp: datetime
    source: str
    metric_name: str
    value: float
    anomaly_score: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    model_used: str
    status: str
    model_config = {"protected_namespaces": ()}


class InferenceOutput(BaseModel):
    metric_name: str
    timestamp: datetime
    value: float
    anomaly_score: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    model_used: str
    status: str
    model_config = {"protected_namespaces": ()}


class IngestResponse(BaseModel):
    received: int
    anomalies: list[AnomalyOut]


class TrainRequest(BaseModel):
    metric_name: str
    source: str


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
