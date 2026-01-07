"""
Knowledge Object Consultation Metrics

Tracks effectiveness of KO consultations to measure learning impact.

Metrics tracked:
- Consultation count (how often KO was consulted)
- Success rate (consultations that led to successful task completion)
- Iteration reduction (fewer iterations after seeing relevant KOs)
- Time saved (estimated developer time saved)

Usage:
    from knowledge.metrics import record_consultation, record_outcome, get_effectiveness

    # When agent consults KO before starting work
    record_consultation(ko_id="KO-km-001", task_id="TASK-123")

    # When task completes
    record_outcome(
        task_id="TASK-123",
        success=True,
        iterations=3,
        consulted_ko_ids=["KO-km-001"]
    )

    # Get effectiveness report
    report = get_effectiveness("KO-km-001")
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json


METRICS_FILE = Path(__file__).parent / "metrics.json"


@dataclass
class ConsultationMetrics:
    """Metrics for a single KO."""
    ko_id: str
    total_consultations: int = 0
    successful_outcomes: int = 0
    failed_outcomes: int = 0
    total_iterations_with_ko: int = 0
    total_iterations_without_ko: int = 0
    first_consulted: Optional[str] = None
    last_consulted: Optional[str] = None


def _load_metrics() -> Dict[str, ConsultationMetrics]:
    """Load metrics from JSON file."""
    if not METRICS_FILE.exists():
        return {}

    try:
        with open(METRICS_FILE, 'r') as f:
            data = json.load(f)
            return {
                ko_id: ConsultationMetrics(**metrics_data)
                for ko_id, metrics_data in data.items()
            }
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save_metrics(metrics: Dict[str, ConsultationMetrics]):
    """Save metrics to JSON file."""
    data = {
        ko_id: {
            'ko_id': m.ko_id,
            'total_consultations': m.total_consultations,
            'successful_outcomes': m.successful_outcomes,
            'failed_outcomes': m.failed_outcomes,
            'total_iterations_with_ko': m.total_iterations_with_ko,
            'total_iterations_without_ko': m.total_iterations_without_ko,
            'first_consulted': m.first_consulted,
            'last_consulted': m.last_consulted
        }
        for ko_id, m in metrics.items()
    }

    with open(METRICS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def record_consultation(ko_id: str, task_id: str):
    """
    Record that a KO was consulted for a task.

    Args:
        ko_id: Knowledge Object ID
        task_id: Task ID being worked on
    """
    metrics = _load_metrics()

    if ko_id not in metrics:
        metrics[ko_id] = ConsultationMetrics(ko_id=ko_id)

    m = metrics[ko_id]
    m.total_consultations += 1

    timestamp = datetime.now().isoformat()
    if m.first_consulted is None:
        m.first_consulted = timestamp
    m.last_consulted = timestamp

    _save_metrics(metrics)


def record_outcome(
    task_id: str,
    success: bool,
    iterations: int,
    consulted_ko_ids: List[str]
):
    """
    Record the outcome of a task that consulted KOs.

    Args:
        task_id: Task ID
        success: Whether task completed successfully
        iterations: Number of iterations taken
        consulted_ko_ids: List of KO IDs that were consulted
    """
    if not consulted_ko_ids:
        return  # No KOs consulted, nothing to record

    metrics = _load_metrics()

    for ko_id in consulted_ko_ids:
        if ko_id not in metrics:
            metrics[ko_id] = ConsultationMetrics(ko_id=ko_id)

        m = metrics[ko_id]

        if success:
            m.successful_outcomes += 1
        else:
            m.failed_outcomes += 1

        m.total_iterations_with_ko += iterations

    _save_metrics(metrics)


def get_effectiveness(ko_id: str) -> Optional[Dict[str, any]]:
    """
    Get effectiveness report for a KO.

    Returns:
        Dict with:
        - success_rate: % of consultations that led to success
        - avg_iterations: Average iterations when this KO was consulted
        - total_consultations: Total times consulted
        - impact_score: Composite effectiveness score (0-100)
    """
    metrics = _load_metrics()

    if ko_id not in metrics:
        return None

    m = metrics[ko_id]
    total_outcomes = m.successful_outcomes + m.failed_outcomes

    if total_outcomes == 0:
        success_rate = 0.0
        avg_iterations = 0.0
    else:
        success_rate = (m.successful_outcomes / total_outcomes) * 100
        avg_iterations = m.total_iterations_with_ko / total_outcomes

    # Impact score: weighted by success rate and consultation frequency
    # Higher score = more effective KO
    impact_score = (success_rate * 0.7) + (min(m.total_consultations / 10, 1.0) * 30)

    return {
        'ko_id': ko_id,
        'total_consultations': m.total_consultations,
        'successful_outcomes': m.successful_outcomes,
        'failed_outcomes': m.failed_outcomes,
        'success_rate': round(success_rate, 1),
        'avg_iterations': round(avg_iterations, 1),
        'impact_score': round(impact_score, 1),
        'first_consulted': m.first_consulted,
        'last_consulted': m.last_consulted
    }


def get_all_effectiveness() -> List[Dict[str, any]]:
    """
    Get effectiveness reports for all KOs, sorted by impact score.

    Returns:
        List of effectiveness reports, highest impact first
    """
    metrics = _load_metrics()
    reports = []

    for ko_id in metrics.keys():
        report = get_effectiveness(ko_id)
        if report:
            reports.append(report)

    # Sort by impact score (highest first)
    reports.sort(key=lambda r: r['impact_score'], reverse=True)

    return reports


def get_summary_stats() -> Dict[str, any]:
    """
    Get summary statistics across all KOs.

    Returns:
        Dict with aggregate metrics:
        - total_kos_with_consultations: Number of KOs that have been consulted
        - total_consultations: Total consultation events
        - overall_success_rate: Success rate across all KO consultations
        - top_kos: Top 5 KOs by impact score
    """
    reports = get_all_effectiveness()

    if not reports:
        return {
            'total_kos_with_consultations': 0,
            'total_consultations': 0,
            'total_successful_outcomes': 0,
            'total_failed_outcomes': 0,
            'overall_success_rate': 0.0,
            'top_kos': []
        }

    total_consultations = sum(r['total_consultations'] for r in reports)
    total_successes = sum(r['successful_outcomes'] for r in reports)
    total_failures = sum(r['failed_outcomes'] for r in reports)

    overall_success_rate = 0.0
    if (total_successes + total_failures) > 0:
        overall_success_rate = (total_successes / (total_successes + total_failures)) * 100

    return {
        'total_kos_with_consultations': len(reports),
        'total_consultations': total_consultations,
        'total_successful_outcomes': total_successes,
        'total_failed_outcomes': total_failures,
        'overall_success_rate': round(overall_success_rate, 1),
        'top_kos': reports[:5]  # Top 5 by impact score
    }
