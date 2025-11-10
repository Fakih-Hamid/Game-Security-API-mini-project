from __future__ import annotations

from statistics import mean
from typing import Iterable

from app.models.game_session import GameSession
from app.models.security_event import SecurityEvent
from app.services.anomaly_detector import AnomalyFinding


class ThreatScorer:
    """Combine telemetry, anomalies, and historical events to compute risk."""

    def __init__(self, baseline_weight: float = 0.4) -> None:
        self.baseline_weight = baseline_weight

    def score_player(
        self,
        *,
        baseline: int,
        sessions: Iterable[GameSession],
        anomalies: Iterable[AnomalyFinding],
        events: Iterable[SecurityEvent],
    ) -> int:
        dynamic_score = 0.0

        anomalies = list(anomalies)
        events = list(events)
        sessions = list(sessions)

        dynamic_score += sum(self._severity_value(finding.severity) for finding in anomalies)
        dynamic_score += sum(self._severity_value(event.severity) for event in events)

        if sessions:
            avg_headshot = mean(s.headshot_rate for s in sessions)
            if avg_headshot > 0.75:
                dynamic_score += (avg_headshot - 0.75) * 80

            avg_apm = mean(s.actions_per_minute for s in sessions)
            if avg_apm > 210:
                dynamic_score += min(20, (avg_apm - 210) * 0.2)

        combined = (
            baseline * self.baseline_weight + dynamic_score * (1 - self.baseline_weight)
        )
        return max(0, min(100, int(round(combined))))

    @staticmethod
    def _severity_value(severity: str) -> float:
        mapping = {"low": 5, "medium": 12, "high": 20}
        return mapping.get(severity, 8)

