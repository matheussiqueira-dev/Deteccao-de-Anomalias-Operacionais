from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np
from sklearn.ensemble import IsolationForest


@dataclass
class ModelState:
    model: IsolationForest | None = None
    window: deque[float] = field(default_factory=deque)
    score_min: float = 0.0
    score_max: float = 1.0


class IsolationForestDetector:
    def __init__(self, min_samples: int = 50, contamination: float = 0.05, window_size: int = 200):
        self.min_samples = min_samples
        self.contamination = contamination
        self.window_size = window_size
        self._states: dict[str, ModelState] = {}

    def update_and_score(self, metric_key: str, value: float) -> float | None:
        state = self._get_state(metric_key)
        state.window.append(float(value))

        if len(state.window) < self.min_samples:
            return None

        if state.model is None:
            self._train_state(state)

        score_raw = self._score_raw(state, value)
        score_norm = self._normalize_score(state, score_raw)
        return score_norm

    def retrain(self, metric_key: str, values: list[float]) -> None:
        state = self._get_state(metric_key)
        state.window.clear()
        for value in values:
            state.window.append(float(value))
        if len(state.window) >= self.min_samples:
            self._train_state(state)

    def _get_state(self, metric_key: str) -> ModelState:
        state = self._states.get(metric_key)
        if state is None:
            state = ModelState(window=deque(maxlen=self.window_size))
            self._states[metric_key] = state
        return state

    def _train_state(self, state: ModelState) -> None:
        data = np.array(state.window).reshape(-1, 1)
        state.model = IsolationForest(
            n_estimators=200,
            contamination=self.contamination,
            random_state=42,
        )
        state.model.fit(data)
        scores = -state.model.decision_function(data)
        state.score_min = float(scores.min())
        state.score_max = float(scores.max())

    def _score_raw(self, state: ModelState, value: float) -> float:
        assert state.model is not None
        data = np.array([[float(value)]])
        return float(-state.model.decision_function(data)[0])

    def _normalize_score(self, state: ModelState, raw: float) -> float:
        if state.score_max <= state.score_min:
            return 0.0
        normalized = (raw - state.score_min) / (state.score_max - state.score_min)
        return float(np.clip(normalized, 0.0, 1.0))
