"""
Council Effectiveness Tracking

Tracks whether debate recommendations were correct over time.
Enables learning from past decisions to improve future debates.

Usage:
    from orchestration.council_effectiveness import (
        record_outcome,
        get_effectiveness_report,
        get_council_stats
    )

    # Record outcome after decision is implemented
    record_outcome(council_id, outcome="SUCCESS", notes="...")

    # Get effectiveness report
    report = get_effectiveness_report()
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum


class Outcome(Enum):
    """Possible outcomes for a council decision."""
    SUCCESS = "SUCCESS"        # Recommendation was correct
    PARTIAL = "PARTIAL"        # Recommendation was partially correct
    FAILURE = "FAILURE"        # Recommendation was incorrect
    PENDING = "PENDING"        # Outcome not yet determined
    CANCELLED = "CANCELLED"    # Decision was not implemented


@dataclass
class OutcomeRecord:
    """Record of a council decision outcome."""
    council_id: str
    recommendation: str        # ADOPT/REJECT/CONDITIONAL/SPLIT
    confidence: float          # Original confidence
    outcome: Outcome
    recorded_at: str           # ISO timestamp
    recorded_by: str           # Who recorded (user or auto)
    notes: str                 # Additional context
    ko_id: Optional[str] = None  # Associated KO if any

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["outcome"] = self.outcome.value
        return result


# Directory for effectiveness data
EFFECTIVENESS_DIR = Path(".aibrain/council-effectiveness")
OUTCOMES_FILE = EFFECTIVENESS_DIR / "outcomes.jsonl"


def _ensure_dir() -> None:
    """Ensure effectiveness directory exists."""
    EFFECTIVENESS_DIR.mkdir(parents=True, exist_ok=True)


def record_outcome(
    council_id: str,
    outcome: str,
    notes: str = "",
    recorded_by: str = "user"
) -> OutcomeRecord:
    """
    Record the outcome of a council decision.

    Args:
        council_id: Council ID (e.g., COUNCIL-20260131-123456)
        outcome: One of SUCCESS, PARTIAL, FAILURE, CANCELLED
        notes: Additional context about the outcome
        recorded_by: Who is recording (user, automated, etc.)

    Returns:
        OutcomeRecord that was saved
    """
    _ensure_dir()

    # Get original debate info
    debate_info = _get_debate_info(council_id)

    record = OutcomeRecord(
        council_id=council_id,
        recommendation=debate_info.get("recommendation", "UNKNOWN"),
        confidence=debate_info.get("confidence", 0.0),
        outcome=Outcome[outcome.upper()],
        recorded_at=datetime.now(timezone.utc).isoformat(),
        recorded_by=recorded_by,
        notes=notes,
        ko_id=debate_info.get("ko_id")
    )

    # Append to outcomes file
    with open(OUTCOMES_FILE, "a") as f:
        f.write(json.dumps(record.to_dict()) + "\n")

    # Update KO effectiveness if linked
    if record.ko_id:
        _update_ko_effectiveness(record.ko_id, record.outcome, council_id)

    return record


def get_outcomes(council_id: Optional[str] = None) -> List[OutcomeRecord]:
    """
    Get outcome records.

    Args:
        council_id: Filter by specific council (optional)

    Returns:
        List of OutcomeRecords
    """
    if not OUTCOMES_FILE.exists():
        return []

    records = []
    with open(OUTCOMES_FILE) as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    data["outcome"] = Outcome[data["outcome"]]
                    record = OutcomeRecord(**data)
                    if council_id is None or record.council_id == council_id:
                        records.append(record)
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

    return records


def get_effectiveness_report() -> Dict[str, Any]:
    """
    Generate effectiveness report across all councils.

    Returns:
        {
            "total_decisions": int,
            "outcomes": {SUCCESS: int, PARTIAL: int, FAILURE: int, ...},
            "success_rate": float (0-100),
            "by_recommendation": {...},
            "by_confidence_band": {...},
            "recent_outcomes": [...]
        }
    """
    records = get_outcomes()

    if not records:
        return {
            "total_decisions": 0,
            "outcomes": {},
            "success_rate": 0.0,
            "by_recommendation": {},
            "by_confidence_band": {},
            "recent_outcomes": []
        }

    # Count outcomes
    outcome_counts: Dict[str, int] = {}
    for record in records:
        key = record.outcome.value
        outcome_counts[key] = outcome_counts.get(key, 0) + 1

    # Calculate success rate (SUCCESS + 0.5*PARTIAL) / total non-pending
    completed = [r for r in records if r.outcome not in (Outcome.PENDING, Outcome.CANCELLED)]
    if completed:
        success_score = sum(
            1.0 if r.outcome == Outcome.SUCCESS else
            0.5 if r.outcome == Outcome.PARTIAL else
            0.0
            for r in completed
        )
        success_rate = (success_score / len(completed)) * 100
    else:
        success_rate = 0.0

    # Group by recommendation type
    by_recommendation: Dict[str, Dict[str, Any]] = {}
    for record in records:
        rec = record.recommendation
        if rec not in by_recommendation:
            by_recommendation[rec] = {"total": 0, "success": 0, "failure": 0}
        by_recommendation[rec]["total"] += 1
        if record.outcome == Outcome.SUCCESS:
            by_recommendation[rec]["success"] += 1
        elif record.outcome == Outcome.FAILURE:
            by_recommendation[rec]["failure"] += 1

    # Group by confidence band
    by_confidence: Dict[str, Dict[str, Any]] = {
        "high (>0.8)": {"total": 0, "success": 0},
        "medium (0.5-0.8)": {"total": 0, "success": 0},
        "low (<0.5)": {"total": 0, "success": 0}
    }
    for record in completed:
        if record.confidence > 0.8:
            band = "high (>0.8)"
        elif record.confidence >= 0.5:
            band = "medium (0.5-0.8)"
        else:
            band = "low (<0.5)"
        by_confidence[band]["total"] += 1
        if record.outcome == Outcome.SUCCESS:
            by_confidence[band]["success"] += 1

    # Recent outcomes (last 10)
    recent = sorted(records, key=lambda r: r.recorded_at, reverse=True)[:10]

    return {
        "total_decisions": len(records),
        "outcomes": outcome_counts,
        "success_rate": round(success_rate, 1),
        "by_recommendation": by_recommendation,
        "by_confidence_band": by_confidence,
        "recent_outcomes": [r.to_dict() for r in recent]
    }


def get_council_stats() -> Dict[str, Any]:
    """
    Get overall council pattern statistics.

    Combines debate metrics with effectiveness data.
    """
    from pathlib import Path

    councils_dir = Path(".aibrain/councils")

    # Count total debates
    total_debates = 0
    recommendation_counts: Dict[str, int] = {}
    total_cost = 0.0

    if councils_dir.exists():
        for council_dir in councils_dir.iterdir():
            if not council_dir.is_dir():
                continue

            manifest_path = council_dir / "manifest.jsonl"
            if manifest_path.exists():
                total_debates += 1

                # Parse manifest for stats
                with open(manifest_path) as f:
                    for line in f:
                        if line.strip():
                            try:
                                event = json.loads(line)
                                event_type = event.get("event") or event.get("event_type")

                                if event_type == "synthesis":
                                    rec = event.get("recommendation") or event.get("data", {}).get("recommendation")
                                    if rec:
                                        recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1

                                if event_type == "cost_summary":
                                    cost = event.get("total_cost") or event.get("data", {}).get("total_cost", 0)
                                    total_cost += cost
                            except json.JSONDecodeError:
                                continue

    # Get effectiveness data
    effectiveness = get_effectiveness_report()

    return {
        "total_debates": total_debates,
        "recommendation_distribution": recommendation_counts,
        "total_cost": round(total_cost, 2),
        "avg_cost_per_debate": round(total_cost / max(total_debates, 1), 2),
        "outcomes_recorded": effectiveness["total_decisions"],
        "success_rate": effectiveness["success_rate"],
        "by_recommendation": effectiveness["by_recommendation"]
    }


def _get_debate_info(council_id: str) -> Dict[str, Any]:
    """Get debate info from manifest."""
    manifest_path = Path(f".aibrain/councils/{council_id}/manifest.jsonl")

    if not manifest_path.exists():
        return {}

    info: Dict[str, Any] = {}
    with open(manifest_path) as f:
        for line in f:
            if line.strip():
                try:
                    event = json.loads(line)
                    event_type = event.get("event") or event.get("event_type")

                    if event_type == "synthesis":
                        info["recommendation"] = event.get("recommendation") or event.get("data", {}).get("recommendation")
                        info["confidence"] = event.get("confidence") or event.get("data", {}).get("confidence", 0)

                    if event_type == "ko_created":
                        info["ko_id"] = event.get("ko_id") or event.get("data", {}).get("ko_id")

                except json.JSONDecodeError:
                    continue

    return info


def _update_ko_effectiveness(ko_id: str, outcome: Outcome, council_id: str) -> None:
    """Update KO with effectiveness data."""
    from knowledge.metrics import record_outcome as ko_record_outcome

    try:
        success = outcome in (Outcome.SUCCESS, Outcome.PARTIAL)
        # Use council_id as task_id for tracking
        ko_record_outcome(
            task_id=council_id,
            success=success,
            iterations=1,
            consulted_ko_ids=[ko_id]
        )
    except Exception as e:
        print(f"Warning: Failed to update KO effectiveness: {e}")
