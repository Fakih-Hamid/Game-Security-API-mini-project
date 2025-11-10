from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass
class LogScanResult:
    suspicious_players: List[int]
    anomaly_counts: Dict[str, int]
    insights: List[str]


class LogAnalyzer:
    """Parse raw gameplay logs and highlight noteworthy security signals."""

    def __init__(self) -> None:
        self.reaction_threshold_ms = 110
        self.headshot_threshold = 0.9
        self.flagged_actions = {"wallhack_trigger", "aimbot_lock", "speed_hack"}

    def scan(self, log_rows: Iterable[Dict]) -> LogScanResult:
        suspicion_scores: Dict[int, int] = defaultdict(int)
        anomaly_counts: Dict[str, int] = defaultdict(int)
        insights: List[str] = []

        for row in log_rows:
            player_id = row.get("player_id")
            if player_id is None:
                continue

            action_type = row.get("action", "").lower()
            headshot_rate = row.get("headshot_rate")
            reaction_time_ms = row.get("reaction_time_ms")

            if headshot_rate and headshot_rate >= self.headshot_threshold:
                anomaly_counts["headshot_spike"] += 1
                suspicion_scores[player_id] += 2

            if reaction_time_ms and reaction_time_ms < self.reaction_threshold_ms:
                anomaly_counts["impossible_reaction"] += 1
                suspicion_scores[player_id] += 3

            if action_type in self.flagged_actions:
                anomaly_counts[action_type] += 1
                suspicion_scores[player_id] += 4

            if row.get("movement_speed") and row["movement_speed"] > 1.8:
                anomaly_counts["speed_anomaly"] += 1
                suspicion_scores[player_id] += 2

            if row.get("manual_flag"):
                anomaly_counts["manual_flag"] += 1
                suspicion_scores[player_id] += 1

        suspicious_players = [
            player_id
            for player_id, score in sorted(
                suspicion_scores.items(), key=lambda item: item[1], reverse=True
            )
            if score >= 5
        ]

        if suspicious_players:
            insights.append(
                f"{len(suspicious_players)} players exceeded the suspicion threshold"
            )

        if anomaly_counts:
            top_category = max(anomaly_counts.items(), key=lambda item: item[1])[0]
            insights.append(f"Most common signal: {top_category}")

        return LogScanResult(
            suspicious_players=suspicious_players,
            anomaly_counts=dict(anomaly_counts),
            insights=insights,
        )

