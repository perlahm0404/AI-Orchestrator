"""
Debate Quality Metrics for Council Pattern.

Tracks debate outcomes and measures recommendation accuracy over time.

Usage:
    from agents.coordinator.debate_metrics import MetricsCollector, QualityScore

    collector = MetricsCollector(storage_dir=Path(".aibrain/debate_metrics"))
    collector.record_debate("COUNCIL-001", "Topic", "ADOPT", 0.85)
    collector.record_outcome("COUNCIL-001", True, True)
    stats = collector.get_stats()
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class QualityScore:
    """Quality score for a single debate."""
    debate_id: str
    recommendation_followed: bool
    outcome_success: Optional[bool] = None


@dataclass
class DebateRecord:
    """Record of a single debate."""
    debate_id: str
    topic: str
    recommendation: str
    confidence: float
    recorded_at: str
    recommendation_followed: Optional[bool] = None
    outcome_success: Optional[bool] = None
    outcome_recorded_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DebateRecord":
        """Create from dictionary."""
        return cls(**data)


class DebateMetrics:
    """Container for debate metrics statistics."""

    def __init__(self) -> None:
        self.total_debates = 0
        self.recommendations_followed = 0
        self.successful_outcomes = 0
        self.high_confidence_debates = 0
        self.high_confidence_successes = 0
        self.low_confidence_debates = 0
        self.low_confidence_successes = 0


class MetricsCollector:
    """
    Collects and analyzes debate quality metrics.

    Tracks:
    - Total debates and outcomes
    - Recommendation accuracy
    - Confidence calibration
    """

    CONFIDENCE_THRESHOLD = 0.75  # Threshold for "high confidence"

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path(".aibrain/debate_metrics")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._records: Dict[str, DebateRecord] = {}
        self._load()

    def _load(self) -> None:
        """Load records from storage."""
        records_file = self.storage_dir / "debate_records.json"
        if records_file.exists():
            try:
                with records_file.open() as f:
                    data = json.load(f)
                    for record_data in data.get("records", []):
                        record = DebateRecord.from_dict(record_data)
                        self._records[record.debate_id] = record
            except (json.JSONDecodeError, KeyError):
                self._records = {}

    def _save(self) -> None:
        """Save records to storage."""
        records_file = self.storage_dir / "debate_records.json"
        data = {
            "records": [r.to_dict() for r in self._records.values()],
            "updated_at": datetime.utcnow().isoformat(),
        }
        with records_file.open("w") as f:
            json.dump(data, f, indent=2)

    def flush(self) -> None:
        """Flush records to disk."""
        self._save()

    def record_debate(
        self,
        debate_id: str,
        topic: str,
        recommendation: str,
        confidence: float,
    ) -> None:
        """
        Record a new debate.

        Args:
            debate_id: Unique debate identifier
            topic: Debate topic
            recommendation: Final recommendation (ADOPT, REJECT, CONDITIONAL)
            confidence: Confidence in the recommendation (0-1)
        """
        record = DebateRecord(
            debate_id=debate_id,
            topic=topic,
            recommendation=recommendation,
            confidence=confidence,
            recorded_at=datetime.utcnow().isoformat(),
        )
        self._records[debate_id] = record
        self._save()

    def record_outcome(
        self,
        debate_id: str,
        recommendation_followed: bool,
        outcome_success: Optional[bool] = None,
    ) -> None:
        """
        Record the outcome of a debate recommendation.

        Args:
            debate_id: Debate to update
            recommendation_followed: Whether the recommendation was followed
            outcome_success: Whether the outcome was successful (if known)
        """
        if debate_id in self._records:
            record = self._records[debate_id]
            record.recommendation_followed = recommendation_followed
            record.outcome_success = outcome_success
            record.outcome_recorded_at = datetime.utcnow().isoformat()
            self._save()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get overall statistics.

        Returns:
            Dict with total_debates, recommendations_followed, successful_outcomes
        """
        total = len(self._records)
        followed = sum(1 for r in self._records.values() if r.recommendation_followed)
        successful = sum(1 for r in self._records.values() if r.outcome_success)

        return {
            "total_debates": total,
            "recommendations_followed": followed,
            "successful_outcomes": successful,
        }

    def calculate_accuracy(self) -> float:
        """
        Calculate overall recommendation accuracy.

        Returns:
            Accuracy as a float (0-1), or 0 if no outcomes recorded
        """
        records_with_outcomes = [
            r for r in self._records.values()
            if r.outcome_success is not None
        ]

        if not records_with_outcomes:
            return 0.0

        successful = sum(1 for r in records_with_outcomes if r.outcome_success)
        return successful / len(records_with_outcomes)

    def get_calibration(self) -> Dict[str, float]:
        """
        Get confidence calibration data.

        Returns:
            Dict with high_confidence_accuracy and low_confidence_accuracy
        """
        high_conf_records = [
            r for r in self._records.values()
            if r.confidence >= self.CONFIDENCE_THRESHOLD and r.outcome_success is not None
        ]
        low_conf_records = [
            r for r in self._records.values()
            if r.confidence < self.CONFIDENCE_THRESHOLD and r.outcome_success is not None
        ]

        high_accuracy = 0.0
        if high_conf_records:
            high_accuracy = sum(1 for r in high_conf_records if r.outcome_success) / len(high_conf_records)

        low_accuracy = 0.0
        if low_conf_records:
            low_accuracy = sum(1 for r in low_conf_records if r.outcome_success) / len(low_conf_records)

        return {
            "high_confidence_accuracy": high_accuracy,
            "low_confidence_accuracy": low_accuracy,
        }

    def get_recent_debates(self, limit: int = 10) -> List[DebateRecord]:
        """Get most recent debate records."""
        sorted_records = sorted(
            self._records.values(),
            key=lambda r: r.recorded_at,
            reverse=True
        )
        return sorted_records[:limit]


# Alias for backward compatibility with tests
DebateMetricsCollector = MetricsCollector
