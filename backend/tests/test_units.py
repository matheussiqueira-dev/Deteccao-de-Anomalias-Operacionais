import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.api import routes_auth, routes_health, ws
from app.database import crud
from app.database.session import SessionLocal
from app.schemas import InferenceOutput, MetricIn
from app.services.detection import DetectionResult
from app.services.ingestion import IngestionService
from app.services.websocket_manager import WebSocketManager


def test_auth_login_invalid_username(client):
    response = client.post(
        "/auth/login",
        json={"username": "invalid", "password": "radar"},
    )
    assert response.status_code == 401


def test_auth_login_invalid_password(client):
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 401


def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException):
        routes_auth.get_current_user(token="not-a-valid-token")


def test_get_current_user_missing_subject(monkeypatch):
    monkeypatch.setattr(routes_auth, "decode_access_token", lambda token: {})
    with pytest.raises(HTTPException):
        routes_auth.get_current_user(token="valid-but-empty")


def test_health_db_failure():
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise RuntimeError("db down")

    status = routes_health.health(db=BrokenSession())
    assert status["status"] == "degraded"
    assert status["database"] == "unavailable"


def test_train_retrain_success(client):
    db = SessionLocal()
    now = datetime.now(tz=timezone.utc)
    for i in range(12):
        crud.create_metric(
            db,
            timestamp=now + timedelta(seconds=i),
            source="logistics",
            metric_name="delivery_delay_minutes",
            value=float(i),
            unit="minutes",
            tags=["seed=true"],
        )
    db.commit()
    db.close()

    response = client.post(
        "/train",
        json={"metric_name": "delivery_delay_minutes", "source": "logistics"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_ingestion_creates_anomaly(client):
    class DummyDetection:
        def score_event(self, event):
            return DetectionResult(
                score=0.9,
                is_anomaly=True,
                threshold=0.5,
                status="anomaly_detected",
            )

        def build_output(self, metric_name, timestamp, value, result):
            return InferenceOutput(
                metric_name=metric_name,
                timestamp=timestamp,
                value=value,
                anomaly_score=result.score,
                threshold=result.threshold,
                model_used=result.model_used,
                status=result.status,
            )

    service = IngestionService(DummyDetection(), WebSocketManager())
    db = SessionLocal()
    metric = MetricIn(
        timestamp=datetime.now(tz=timezone.utc),
        source="ops",
        metric_name="latency_ms",
        value=123.4,
        unit="ms",
        tags=["region=SP"],
    )
    anomalies = service.ingest_metrics(db, [metric])
    db.close()

    assert len(anomalies) == 1
    asyncio.run(service.broadcast_anomalies(anomalies))


def test_websocket_manager_broadcast_handles_failure():
    class FailingWebSocket:
        def __init__(self):
            self.accepted = False

        async def accept(self):
            self.accepted = True

        async def send_json(self, message):
            raise RuntimeError("send failed")

    manager = WebSocketManager()
    socket = FailingWebSocket()
    asyncio.run(manager.connect(socket))
    asyncio.run(manager.broadcast({"type": "alert"}))
    assert socket not in manager._connections


def test_crud_metrics_history_filters(client):
    db = SessionLocal()
    now = datetime.now(tz=timezone.utc)
    crud.create_metric(
        db,
        timestamp=now,
        source="finance",
        metric_name="daily_expense",
        value=10.0,
    )
    crud.create_metric(
        db,
        timestamp=now + timedelta(seconds=5),
        source="logistics",
        metric_name="daily_expense",
        value=20.0,
    )
    db.commit()

    results = crud.get_metrics_history(
        db,
        metric_name="daily_expense",
        source="logistics",
        start=now + timedelta(seconds=1),
        end=now + timedelta(seconds=10),
    )
    db.close()
    assert len(results) == 1


def test_ws_parse_timestamp():
    before = datetime.now(tz=timezone.utc)
    parsed = ws._parse_timestamp(None)
    after = datetime.now(tz=timezone.utc)
    assert before <= parsed <= after

    explicit = ws._parse_timestamp("2026-01-30T15:45:12Z")
    assert explicit.year == 2026
