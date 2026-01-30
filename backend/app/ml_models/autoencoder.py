from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    import tensorflow as tf


@dataclass
class AutoencoderConfig:
    window_size: int = 30
    latent_dim: int = 8
    threshold_quantile: float = 0.95
    min_train_samples: int = 200
    retrain_interval: int = 200
    epochs: int = 20
    batch_size: int = 32


@dataclass
class AutoencoderScore:
    score: float
    threshold: float


@dataclass
class AutoencoderState:
    model: Any | None = None
    buffer: deque[float] = field(default_factory=deque)
    mean: float = 0.0
    std: float = 1.0
    err_min: float = 0.0
    err_max: float = 1.0
    threshold: float = 0.85
    samples_since_train: int = 0


class AutoencoderDetector:
    def __init__(self, config: AutoencoderConfig | None = None):
        self.config = config or AutoencoderConfig()
        self._states: dict[str, AutoencoderState] = {}
        self._tf = self._load_tf()

    def update_and_score(self, metric_key: str, value: float) -> AutoencoderScore | None:
        state = self._get_state(metric_key)
        state.buffer.append(float(value))
        state.samples_since_train += 1

        if len(state.buffer) < self.config.window_size:
            return None

        if state.model is None:
            self._try_train(state)
        elif self.config.retrain_interval > 0 and state.samples_since_train >= self.config.retrain_interval:
            self._try_train(state)

        if state.model is None:
            return None

        window = self._latest_window(state)
        score = self._score_window(state, window)
        return AutoencoderScore(score=score, threshold=state.threshold)

    def retrain(self, metric_key: str, values: list[float]) -> None:
        state = self._get_state(metric_key)
        state.buffer.clear()
        for value in values:
            state.buffer.append(float(value))
        self._try_train(state)

    def get_threshold(self, metric_key: str) -> float | None:
        state = self._states.get(metric_key)
        if not state:
            return None
        return state.threshold

    def _load_tf(self):
        try:
            import tensorflow as tf
        except Exception as exc:
            raise RuntimeError(
                "TensorFlow is required for AutoencoderDetector. Install backend/requirements-ml.txt"
            ) from exc
        return tf

    def _get_state(self, metric_key: str) -> AutoencoderState:
        state = self._states.get(metric_key)
        if state is None:
            state = AutoencoderState(buffer=deque(maxlen=self.config.min_train_samples * 2))
            self._states[metric_key] = state
        return state

    def _try_train(self, state: AutoencoderState) -> None:
        sequences = self._build_sequences(state)
        if len(sequences) < max(5, self.config.min_train_samples // self.config.window_size):
            return

        data = np.array(sequences, dtype=np.float32)
        state.mean = float(np.mean(data))
        state.std = float(np.std(data) or 1.0)
        normalized = (data - state.mean) / state.std

        model = self._build_model()
        model.fit(
            normalized,
            normalized,
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            verbose=0,
        )

        reconstruction = model.predict(normalized, verbose=0)
        errors = np.mean(np.square(normalized - reconstruction), axis=(1, 2))
        state.err_min = float(errors.min())
        state.err_max = float(errors.max())
        normalized_errors = self._normalize_errors(errors, state)
        state.threshold = float(np.quantile(normalized_errors, self.config.threshold_quantile))
        state.model = model
        state.samples_since_train = 0

    def _build_model(self):
        tf = self._tf
        inputs = tf.keras.Input(shape=(self.config.window_size, 1))
        x = tf.keras.layers.Flatten()(inputs)
        x = tf.keras.layers.Dense(self.config.window_size // 2, activation="relu")(x)
        x = tf.keras.layers.Dense(self.config.latent_dim, activation="relu")(x)
        x = tf.keras.layers.Dense(self.config.window_size // 2, activation="relu")(x)
        x = tf.keras.layers.Dense(self.config.window_size, activation="linear")(x)
        outputs = tf.keras.layers.Reshape((self.config.window_size, 1))(x)
        model = tf.keras.Model(inputs, outputs)
        model.compile(optimizer="adam", loss="mse")
        return model

    def _build_sequences(self, state: AutoencoderState) -> list[np.ndarray]:
        values = np.array(state.buffer, dtype=np.float32)
        window = self.config.window_size
        if len(values) < window:
            return []
        sequences = [values[i : i + window] for i in range(len(values) - window + 1)]
        return [seq.reshape(window, 1) for seq in sequences]

    def _latest_window(self, state: AutoencoderState) -> np.ndarray:
        window = np.array(list(state.buffer)[-self.config.window_size :], dtype=np.float32)
        return window.reshape(self.config.window_size, 1)

    def _score_window(self, state: AutoencoderState, window: np.ndarray) -> float:
        model = state.model
        if model is None:
            return 0.0
        normalized = (window - state.mean) / state.std
        reconstructed = model.predict(normalized[None, ...], verbose=0)[0]
        error = float(np.mean(np.square(normalized - reconstructed)))
        normalized_error = self._normalize_error(error, state)
        return float(np.clip(normalized_error, 0.0, 1.0))

    @staticmethod
    def _normalize_errors(errors: np.ndarray, state: AutoencoderState) -> np.ndarray:
        if state.err_max <= state.err_min:
            return np.zeros_like(errors)
        return (errors - state.err_min) / (state.err_max - state.err_min)

    @staticmethod
    def _normalize_error(error: float, state: AutoencoderState) -> float:
        if state.err_max <= state.err_min:
            return 0.0
        return (error - state.err_min) / (state.err_max - state.err_min)