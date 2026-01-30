import asyncio

import pytest

from app.core.security import create_access_token, decode_access_token
from app.database.init_db import init_db
from app.ml_models.autoencoder import AutoencoderConfig, AutoencoderDetector
from app.services.detection import DetectionService
from app.services.ingestion import IngestionService
from app.services.kafka_consumer import KafkaIngestor
from app.services.websocket_manager import WebSocketManager


def test_token_roundtrip():
    token = create_access_token("tester", expires_minutes=5)
    payload = decode_access_token(token)
    assert payload["sub"] == "tester"


def test_autoencoder_scores():
    pytest.importorskip("tensorflow")
    config = AutoencoderConfig(window_size=5, min_train_samples=20, epochs=2, batch_size=4)
    detector = AutoencoderDetector(config)
    for value in range(30):
        detector.update_and_score("metric:key", float(value))
    result = detector.update_and_score("metric:key", 100.0)
    assert result is not None
    assert 0.0 <= result.score <= 1.0


def test_kafka_handle_message():
    init_db()
    detection = DetectionService()
    manager = WebSocketManager()
    ingestion = IngestionService(detection, manager)
    ingestor = KafkaIngestor(ingestion)

    payload = {
        "timestamp": "2026-01-30T15:45:12Z",
        "source": "logistics",
        "metric_name": "delivery_delay_minutes",
        "value": 94.3,
        "unit": "minutes",
        "tags": ["warehouse=SP", "vehicle=TRUCK_12"],
    }

    asyncio.run(ingestor._handle_message(payload))
