"""
Council Pattern - Metrics Dashboard

Provides comprehensive analytics for council debates including:
- Time-series analysis of debates
- Quality metrics (depth, consensus strength)
- Cost efficiency tracking
- Recommendation accuracy trends

Usage:
    from orchestration.council_dashboard import (
        get_dashboard_data,
        get_debate_quality_metrics,
        get_trend_analysis
    )

    # Get full dashboard data
    data = get_dashboard_data()

    # Get quality metrics for a specific debate
    quality = get_debate_quality_metrics(council_id)
"""

import json
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List


# Directories
COUNCILS_DIR = Path(".aibrain/councils")


@dataclass
class DebateQualityMetrics:
    """Quality metrics for a single debate."""
    council_id: str
    total_arguments: int
    arguments_per_agent: float
    avg_confidence: float
    confidence_spread: float  # std dev of confidences
    rebuttal_depth: int       # rounds with rebuttals
    consensus_strength: float  # 0-1, higher = more agreement
    evidence_count: int
    unique_perspectives: int
    duration_seconds: float
    cost_efficiency: float    # recommendation strength / cost


@dataclass
class TrendPoint:
    """A single point in trend analysis."""
    period: str  # e.g., "2026-01", "2026-W05"
    debates: int
    avg_confidence: float
    avg_cost: float
    success_rate: float
    dominant_recommendation: str


def get_dashboard_data(days: int = 30) -> Dict[str, Any]:
    """
    Get comprehensive dashboard data.

    Args:
        days: Number of days to analyze

    Returns:
        Dict with dashboard sections:
        - summary: Key metrics
        - trends: Time-series data
        - quality: Quality metrics
        - cost_analysis: Cost breakdown
        - recommendations: Distribution
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    debates = _load_debates(cutoff)

    if not debates:
        return {
            "summary": _empty_summary(),
            "trends": [],
            "quality": [],
            "cost_analysis": _empty_cost_analysis(),
            "recommendations": {},
            "period_days": days
        }

    # Summary
    summary = _compute_summary(debates)

    # Trends (weekly)
    trends = _compute_trends(debates, period="week")

    # Quality metrics for top debates
    quality_raw = [get_debate_quality_metrics(d["council_id"]) for d in debates[:10]]
    quality: List[DebateQualityMetrics] = [q for q in quality_raw if q is not None]

    # Cost analysis
    cost_analysis = _compute_cost_analysis(debates)

    # Recommendation distribution
    recommendations = _compute_recommendation_distribution(debates)

    return {
        "summary": summary,
        "trends": [asdict(t) for t in trends],
        "quality": [asdict(q) for q in quality],
        "cost_analysis": cost_analysis,
        "recommendations": recommendations,
        "period_days": days
    }


def get_debate_quality_metrics(council_id: str) -> Optional[DebateQualityMetrics]:
    """
    Compute quality metrics for a specific debate.

    Args:
        council_id: Council ID

    Returns:
        DebateQualityMetrics or None if not found
    """
    council_dir = COUNCILS_DIR / council_id
    manifest_path = council_dir / "manifest.jsonl"

    if not manifest_path.exists():
        return None

    events = _parse_manifest(manifest_path)
    if not events:
        return None

    # Extract arguments
    arguments = [e for e in events if _get_event_type(e) == "argument_posted"]
    if not arguments:
        return None

    # Compute metrics
    agent_ids = set()
    confidences = []
    evidence_total = 0
    perspectives = set()

    for arg in arguments:
        data = arg.get("data", {}) if "data" in arg else arg
        agent_ids.add(data.get("agent_id", ""))
        conf = data.get("confidence", 0.5)
        confidences.append(conf)
        evidence_total += len(data.get("evidence", []))
        perspectives.add(data.get("perspective", "unknown"))

    # Get synthesis info
    synthesis = next((e for e in events if _get_event_type(e) == "synthesis"), None)
    synth_data = synthesis.get("data", {}) if synthesis else {}
    recommendation = synth_data.get("recommendation", "UNKNOWN")
    final_confidence = synth_data.get("confidence", 0.5)

    # Get cost info
    cost_event = next((e for e in events if _get_event_type(e) == "cost_summary"), None)
    cost_data = cost_event.get("data", {}) if cost_event else {}
    total_cost = cost_data.get("total_cost", 0.01)  # Avoid div by zero

    # Calculate consensus strength
    vote_breakdown = synth_data.get("vote_breakdown", {})
    total_votes = sum(vote_breakdown.values()) if vote_breakdown else 1
    max_votes = max(vote_breakdown.values()) if vote_breakdown else 0
    consensus_strength = max_votes / total_votes if total_votes > 0 else 0.5

    # Calculate confidence spread
    if len(confidences) > 1:
        avg_conf = sum(confidences) / len(confidences)
        variance = sum((c - avg_conf) ** 2 for c in confidences) / len(confidences)
        confidence_spread = variance ** 0.5
    else:
        avg_conf = confidences[0] if confidences else 0.5
        confidence_spread = 0.0

    # Get duration from init to synthesis
    init_event = next((e for e in events if _get_event_type(e) == "council_init"), None)
    if init_event and synthesis:
        try:
            start = datetime.fromisoformat(init_event.get("timestamp", "").replace("Z", "+00:00"))
            end = datetime.fromisoformat(synthesis.get("timestamp", "").replace("Z", "+00:00"))
            duration = (end - start).total_seconds()
        except (ValueError, TypeError):
            duration = 0.0
    else:
        duration = 0.0

    # Rebuttal depth - count distinct rounds with arguments
    rounds_with_args = set()
    for e in events:
        if _get_event_type(e) == "round_start":
            round_num = e.get("data", {}).get("round_number", e.get("round_number", 1))
            rounds_with_args.add(round_num)

    # Cost efficiency: confidence / cost (higher = better)
    cost_efficiency = final_confidence / max(total_cost, 0.001)

    return DebateQualityMetrics(
        council_id=council_id,
        total_arguments=len(arguments),
        arguments_per_agent=len(arguments) / max(len(agent_ids), 1),
        avg_confidence=avg_conf,
        confidence_spread=confidence_spread,
        rebuttal_depth=len(rounds_with_args),
        consensus_strength=consensus_strength,
        evidence_count=evidence_total,
        unique_perspectives=len(perspectives),
        duration_seconds=duration,
        cost_efficiency=cost_efficiency
    )


def get_trend_analysis(
    period: str = "week",
    lookback: int = 12
) -> List[TrendPoint]:
    """
    Get trend analysis over time.

    Args:
        period: "day", "week", or "month"
        lookback: Number of periods to look back

    Returns:
        List of TrendPoints
    """
    if period == "day":
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback)
    elif period == "week":
        cutoff = datetime.now(timezone.utc) - timedelta(weeks=lookback)
    else:  # month
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback * 30)

    debates = _load_debates(cutoff)
    return _compute_trends(debates, period)


def _load_debates(since: datetime) -> List[Dict[str, Any]]:
    """Load debates since a given datetime."""
    if not COUNCILS_DIR.exists():
        return []

    debates = []
    for council_dir in COUNCILS_DIR.iterdir():
        if not council_dir.is_dir():
            continue

        manifest_path = council_dir / "manifest.jsonl"
        if not manifest_path.exists():
            continue

        events = _parse_manifest(manifest_path)
        if not events:
            continue

        init_event = next((e for e in events if _get_event_type(e) == "council_init"), None)
        if not init_event:
            continue

        try:
            timestamp_str = init_event.get("timestamp", "")
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if timestamp < since:
                continue
        except (ValueError, TypeError):
            continue

        # Extract debate summary
        synthesis = next((e for e in events if _get_event_type(e) == "synthesis"), None)
        synth_data = synthesis.get("data", {}) if synthesis else {}

        cost_event = next((e for e in events if _get_event_type(e) == "cost_summary"), None)
        cost_data = cost_event.get("data", {}) if cost_event else {}

        debates.append({
            "council_id": council_dir.name,
            "timestamp": timestamp,
            "topic": init_event.get("topic") or init_event.get("data", {}).get("topic", ""),
            "recommendation": synth_data.get("recommendation", "UNKNOWN"),
            "confidence": synth_data.get("confidence", 0.5),
            "cost": cost_data.get("total_cost", 0.0)
        })

    # Sort by timestamp descending
    debates.sort(key=lambda d: d["timestamp"], reverse=True)
    return debates


def _parse_manifest(path: Path) -> List[Dict[str, Any]]:
    """Parse manifest file."""
    events = []
    try:
        with open(path) as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except IOError:
        pass
    return events


def _get_event_type(event: Dict[str, Any]) -> str:
    """Get event type from event dict."""
    event_type = event.get("event_type") or event.get("event") or "unknown"
    return str(event_type)


def _compute_summary(debates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary statistics."""
    if not debates:
        return _empty_summary()

    total = len(debates)
    total_cost = sum(d.get("cost", 0) for d in debates)
    avg_confidence = sum(d.get("confidence", 0.5) for d in debates) / total

    # Count recommendations
    rec_counts: Dict[str, int] = defaultdict(int)
    for d in debates:
        rec_counts[d.get("recommendation", "UNKNOWN")] += 1

    most_common_rec = max(rec_counts.keys(), key=lambda k: rec_counts[k]) if rec_counts else "UNKNOWN"

    # Get effectiveness data
    from orchestration.council_effectiveness import get_effectiveness_report
    effectiveness = get_effectiveness_report()

    return {
        "total_debates": total,
        "total_cost": round(total_cost, 2),
        "avg_cost_per_debate": round(total_cost / total, 2),
        "avg_confidence": round(avg_confidence, 2),
        "most_common_recommendation": most_common_rec,
        "success_rate": effectiveness.get("success_rate", 0.0),
        "outcomes_recorded": effectiveness.get("total_decisions", 0)
    }


def _empty_summary() -> Dict[str, Any]:
    """Return empty summary."""
    return {
        "total_debates": 0,
        "total_cost": 0.0,
        "avg_cost_per_debate": 0.0,
        "avg_confidence": 0.0,
        "most_common_recommendation": "N/A",
        "success_rate": 0.0,
        "outcomes_recorded": 0
    }


def _compute_trends(
    debates: List[Dict[str, Any]],
    period: str
) -> List[TrendPoint]:
    """Compute trends by period."""
    if not debates:
        return []

    # Group by period
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for d in debates:
        ts = d.get("timestamp")
        if not ts:
            continue

        if period == "day":
            key = ts.strftime("%Y-%m-%d")
        elif period == "week":
            key = f"{ts.year}-W{ts.isocalendar()[1]:02d}"
        else:  # month
            key = ts.strftime("%Y-%m")

        groups[key].append(d)

    # Compute metrics per period
    trends = []
    for period_key in sorted(groups.keys()):
        period_debates = groups[period_key]
        count = len(period_debates)
        avg_conf = sum(d.get("confidence", 0.5) for d in period_debates) / count
        avg_cost = sum(d.get("cost", 0) for d in period_debates) / count

        # Dominant recommendation
        rec_counts: Dict[str, int] = defaultdict(int)
        for d in period_debates:
            rec_counts[d.get("recommendation", "UNKNOWN")] += 1
        dominant = max(rec_counts.keys(), key=lambda k: rec_counts[k]) if rec_counts else "UNKNOWN"

        trends.append(TrendPoint(
            period=period_key,
            debates=count,
            avg_confidence=round(avg_conf, 2),
            avg_cost=round(avg_cost, 4),
            success_rate=0.0,  # Would need outcome data per period
            dominant_recommendation=dominant
        ))

    return trends


def _compute_cost_analysis(debates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute cost analysis."""
    if not debates:
        return _empty_cost_analysis()

    costs = [d.get("cost", 0) for d in debates]

    return {
        "total": round(sum(costs), 2),
        "average": round(sum(costs) / len(costs), 4),
        "min": round(min(costs), 4),
        "max": round(max(costs), 4),
        "budget_utilization": round(sum(costs) / (len(costs) * 2.0) * 100, 1)  # % of $2 budget
    }


def _empty_cost_analysis() -> Dict[str, Any]:
    """Return empty cost analysis."""
    return {
        "total": 0.0,
        "average": 0.0,
        "min": 0.0,
        "max": 0.0,
        "budget_utilization": 0.0
    }


def _compute_recommendation_distribution(debates: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Compute recommendation distribution with statistics."""
    if not debates:
        return {}

    distribution: Dict[str, Dict[str, Any]] = {}
    total = len(debates)

    rec_debates: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for d in debates:
        rec = d.get("recommendation", "UNKNOWN")
        rec_debates[rec].append(d)

    for rec, rec_list in rec_debates.items():
        count = len(rec_list)
        avg_conf = sum(d.get("confidence", 0.5) for d in rec_list) / count
        avg_cost = sum(d.get("cost", 0) for d in rec_list) / count

        distribution[rec] = {
            "count": count,
            "percentage": round(count / total * 100, 1),
            "avg_confidence": round(avg_conf, 2),
            "avg_cost": round(avg_cost, 4)
        }

    return distribution
