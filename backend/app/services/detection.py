from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import structlog

from app.core.config import get_settings
from app.domain.entities import MetricEvent
from app.ml_models.autoencoder import AutoencoderConfig, AutoencoderDetector
from app.ml_models.isolation_forest import IsolationForestDetector
from app.schemas import InferenceOutput


@dataclass
class DetectionResult:
    score: float
    is_anomaly: bool
    threshold: float
    status: str
    model_used: str = "IsolationForest"


class DetectionService:
    def __init__(self) -> None:
        logger = structlog.get_logger(__name__)
        settings = get_settings()
        self.threshold = settings.anomaly_threshold
        self.strategy = settings.model_strategy.lower()
        self._iforest = IsolationForestDetector(
            min_samples=settings.model_min_samples,
            contamination=settings.isolation_forest_contamination,
            window_size=settings.model_window_size,
        )
        self._autoencoder = None
        if settings.autoencoder_enabled:
            config = AutoencoderConfig(
                window_size=settings.autoencoder_window_size,
                latent_dim=settings.autoencoder_latent_dim,
                threshold_quantile=settings.autoencoder_threshold_quantile,
                min_train_samples=settings.autoencoder_min_train_samples,
                retrain_interval=settings.autoencoder_retrain_interval,
                epochs=settings.autoencoder_epochs,
                batch_size=settings.autoencoder_batch_size,
            )
            try:
                self._autoencoder = AutoencoderDetector(config)
            except RuntimeError as exc:
                logger.warning("autoencoder_disabled", error=str(exc))

    def score(self, metric_key: str, value: float) -> DetectionResult | None:
        score = self._iforest.update_and_score(metric_key, value)
        if score is None:
            return None
        return self._build_result(score, self.threshold, "IsolationForest")

    def score_event(self, event: MetricEvent) -> DetectionResult | None:
        metric_key = f"{event.source}:{event.metric_name}"
        if self.strategy == "isolation_forest":
            return self.score(metric_key, event.value)

        auto_result = None
        if self._autoencoder:
            auto_score = self._autoencoder.update_and_score(metric_key, event.value)
            if auto_score:
                auto_result = self._build_result(
                    auto_score.score,
                    auto_score.threshold,
                    "Autoencoder",
                )

        if self.strategy == "autoencoder":
            return auto_result or self.score(metric_key, event.value)

        iforest_result = self.score(metric_key, event.value)
        if auto_result and iforest_result:
            return auto_result if auto_result.score >= iforest_result.score else iforest_result
        return auto_result or iforest_result

    def retrain(self, metric_key: str, values: list[float]) -> None:
        self._iforest.retrain(metric_key, values)
        if self._autoencoder:
            self._autoencoder.retrain(metric_key, values)

    def get_threshold(self, metric_key: str, model_used: str) -> float:
        if model_used == "Autoencoder" and self._autoencoder:
            return self._autoencoder.get_threshold(metric_key) or self.threshold
        return self.threshold

    def build_output(
        self,
        metric_name: str,
        timestamp: datetime,
        value: float,
        result: DetectionResult,
    ) -> InferenceOutput:
        return InferenceOutput(
            metric_name=metric_name,
            timestamp=timestamp,
            value=value,
            anomaly_score=result.score,
            threshold=result.threshold,
            model_used=result.model_used,
            status=result.status,
        )

    @staticmethod
    def _build_result(score: float, threshold: float, model_used: str) -> DetectionResult:
        is_anomaly = score >= threshold
        return DetectionResult(
            score=score,
            is_anomaly=is_anomaly,
            threshold=threshold,
            status="anomaly_detected" if is_anomaly else "normal",
            model_used=model_used,
        )
