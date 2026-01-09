from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable, List, Sequence

from app.models.game_session import GameSession


@dataclass
class AnomalyFinding:
    category: str
    severity: str
    detail: str
    session_id: int


class AnomalyDetector:
    """Detect suspicious behaviour patterns from historical session data."""

    def __init__(
        self,
        reaction_time_threshold_ms: int = 110,
        headshot_rate_threshold: float = 0.9,
        improvement_multiplier: float = 1.6,
        bot_consistency_threshold: float = 0.05,
    ) -> None:
        self.reaction_time_threshold_ms = reaction_time_threshold_ms
        self.headshot_rate_threshold = headshot_rate_threshold
        self.improvement_multiplier = improvement_multiplier
        self.bot_consistency_threshold = bot_consistency_threshold

    def detect(self, sessions: Sequence[GameSession]) -> List[AnomalyFinding]:
        if not sessions:
            return []

        ordered = sorted(sessions, key=lambda s: s.recorded_at)
        findings: List[AnomalyFinding] = []

        findings.extend(self._detect_reaction_time_outliers(ordered))
        findings.extend(self._detect_headshot_anomalies(ordered))
        findings.extend(self._detect_rapid_improvement(ordered))
        findings.extend(self._detect_bot_like_patterns(ordered))

        return findings

    def _detect_reaction_time_outliers(
        self, sessions: Sequence[GameSession]
    ) -> Iterable[AnomalyFinding]:
        streak = 0
        for session in sessions:
            if session.reaction_time_ms < self.reaction_time_threshold_ms:
                streak += 1
                if streak >= 3:
                    yield AnomalyFinding(
                        category="reaction_time",
                        severity="high" if session.reaction_time_ms < 90 else "medium",
                        detail=f"sustained reaction time under {self.reaction_time_threshold_ms}ms",
                        session_id=session.id,
                    )
            else:
                streak = 0

    def _detect_headshot_anomalies(
        self, sessions: Sequence[GameSession]
    ) -> Iterable[AnomalyFinding]:
        for session in sessions:
            if session.headshot_rate >= self.headshot_rate_threshold:
                yield AnomalyFinding(
                    category="headshot_rate",
                    severity="high",
                    detail=f"headshot rate {session.headshot_rate:.0%}",
                    session_id=session.id,
                )

    def _detect_rapid_improvement(
        self, sessions: Sequence[GameSession]
    ) -> Iterable[AnomalyFinding]:
        window = 5
        if len(sessions) < window * 2:
            return []

        historical = sessions[:-window]
        recent = sessions[-window:]
        historical_rate = mean(s.headshot_rate for s in historical)
        recent_rate = mean(s.headshot_rate for s in recent)

        if historical_rate == 0:
            return []

        if recent_rate >= historical_rate * self.improvement_multiplier:
            yield AnomalyFinding(
                category="rapid_improvement",
                severity="medium",
                detail="headshot performance spiked drastically",
                session_id=recent[-1].id,
            )

    def _detect_bot_like_patterns(
        self, sessions: Sequence[GameSession]
    ) -> Iterable[AnomalyFinding]:
        if len(sessions) < 4:
            return []

        recent = sessions[-4:]
        apm_values = [s.actions_per_minute for s in recent]
        avg = mean(apm_values)
        variance = mean(abs(apm - avg) for apm in apm_values) / (avg or 1)

        if variance <= self.bot_consistency_threshold:
            yield AnomalyFinding(
                category="bot_like",
                severity="medium",
                detail="actions per minute extremely consistent",
                session_id=recent[-1].id,
            )

