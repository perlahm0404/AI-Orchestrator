"""
Unit tests for CME cycle creation service.
"""

from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

from contexts.cme.services.cycle_creation_service import CycleCreationService  # type: ignore[import-not-found]


def _make_query(first_result: object) -> Mock:
    query = Mock()
    query.filter.return_value = query
    query.first.return_value = first_result
    return query


def test_cycle_start_date_inclusive_end() -> None:
    db = Mock()
    license_obj = SimpleNamespace(
        id=123,
        organization_id=10,
        provider_id=55,
        license_type="MD",
        state="MO",
        expiration_date=date(2026, 1, 30),
        deleted_at=None,
    )
    requirement = SimpleNamespace(
        id=9,
        total_hours_required=50.0,
        cycle_length_months=12,
    )

    db.query.side_effect = [
        _make_query(license_obj),
        _make_query(requirement),
        _make_query(None),
    ]

    service = CycleCreationService(db)
    cycle = service.create_cycle_for_license(license_obj.id)

    assert cycle is not None
    assert cycle.cycle_end_date == date(2026, 1, 30)
    assert cycle.cycle_start_date == date(2025, 1, 31)
    db.add.assert_called_once_with(cycle)
