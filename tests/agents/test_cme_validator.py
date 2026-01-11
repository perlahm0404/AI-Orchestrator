"""
Tests for CME Data Validator Agent

Validates that CME validator correctly identifies data integrity issues.
"""
# type: ignore

import pytest
from pathlib import Path
from agents.domain.cme_data_validator import (
    CMEDataValidator,
    ValidationResults,
    ValidationFailure
)


class TestCMEDataValidator:
    """Test suite for CME Data Validator."""

    @pytest.fixture
    def mock_credentialmate_path(self, tmp_path):
        """Create mock CredentialMate project structure."""
        project = tmp_path / "credentialmate"
        project.mkdir()

        # Create directory structure
        backend = project / "apps/backend-api"
        backend.mkdir(parents=True)

        tests_unit = backend / "tests/unit/cme"
        tests_unit.mkdir(parents=True)

        tests_integration = backend / "tests/integration"
        tests_integration.mkdir(parents=True)

        # Create mock test files
        (tests_unit / "test_topic_normalization.py").write_text("# Mock test")
        (tests_integration / "test_cme_parity.py").write_text("# Mock parity test")

        return str(project)

    @pytest.fixture
    def validator(self, mock_credentialmate_path):
        """Create validator instance."""
        return CMEDataValidator(mock_credentialmate_path)

    def test_initialization(self, validator):
        """Test validator initializes correctly."""
        assert validator.project_path.name == "credentialmate"
        assert isinstance(validator.results, ValidationResults)

    def test_validate_all_runs_all_checks(self, validator, monkeypatch):
        """Test that validate_all runs all validation checks."""
        checks_run = []

        def mock_check(name):
            def check_method():
                checks_run.append(name)
                validator.results.total_checks += 1
                validator.results.passed += 1
            return check_method

        # Mock all check methods
        monkeypatch.setattr(validator, "_check_cme_cycles_linked", mock_check("cycles"))
        monkeypatch.setattr(validator, "_check_gap_calculation_parity", mock_check("parity"))
        monkeypatch.setattr(validator, "_check_certification_overlays", mock_check("overlays"))
        monkeypatch.setattr(validator, "_check_category_1_accuracy", mock_check("category"))
        monkeypatch.setattr(validator, "_check_topic_matching", mock_check("topic"))

        results = validator.validate_all()

        assert len(checks_run) == 5
        assert "cycles" in checks_run
        assert "parity" in checks_run
        assert "overlays" in checks_run
        assert "category" in checks_run
        assert "topic" in checks_run
        assert results.total_checks == 5
        assert results.passed == 5

    def test_check_cme_cycles_linked_success(self, validator, monkeypatch):
        """Test cycles check passes when no orphaned activities."""
        def mock_query(query):
            return {"orphaned_count": 0}

        monkeypatch.setattr(validator, "_run_db_query", lambda q: mock_query(q))

        validator._check_cme_cycles_linked()

        assert validator.results.total_checks == 1
        assert validator.results.passed == 1
        assert len(validator.results.failures) == 0

    def test_check_cme_cycles_linked_failure(self, validator, monkeypatch):
        """Test cycles check fails when orphaned activities found."""
        def mock_query(query):
            return {"orphaned_count": 5}

        monkeypatch.setattr(validator, "_run_db_query", lambda q: mock_query(q))

        validator._check_cme_cycles_linked()

        assert validator.results.total_checks == 1
        assert validator.results.passed == 0
        assert len(validator.results.failures) == 1

        failure = validator.results.failures[0]
        assert failure.check_name == "cme_cycles_linked"
        assert failure.severity == "critical"
        assert "5 CME activities" in failure.message

    def test_check_gap_parity_missing_test(self, tmp_path):
        """Test parity check fails when test file missing."""
        # Create validator with path that doesn't have test files
        empty_project = tmp_path / "empty_project"
        empty_project.mkdir()

        validator = CMEDataValidator(str(empty_project))
        validator._check_gap_calculation_parity()

        assert validator.results.total_checks == 1
        assert len(validator.results.failures) == 1

        failure = validator.results.failures[0]
        assert failure.check_name == "gap_calculation_parity"
        assert "does not exist" in failure.message

    def test_check_gap_parity_test_exists(self, validator, monkeypatch):
        """Test parity check passes when test exists and passes."""
        def mock_pytest(test_path):
            return {"passed": True}

        monkeypatch.setattr(validator, "_run_pytest", mock_pytest)

        validator._check_gap_calculation_parity()

        assert validator.results.total_checks == 1
        assert validator.results.passed == 1
        assert len(validator.results.failures) == 0

    def test_check_certification_overlays_success(self, validator, monkeypatch):
        """Test certification overlays check passes."""
        def mock_query(query):
            return {"rows": []}  # No incorrect providers

        monkeypatch.setattr(validator, "_run_db_query", lambda q: mock_query(q))

        validator._check_certification_overlays()

        assert validator.results.total_checks == 1
        assert validator.results.passed == 1
        assert len(validator.results.failures) == 0

    def test_check_certification_overlays_failure(self, validator, monkeypatch):
        """Test certification overlays check fails when incorrect requirements found."""
        def mock_query(query):
            return {"rows": [
                {"id": "123", "required_hours": 30, "has_ancc_certification": True},
                {"id": "456", "required_hours": 30, "has_ancc_certification": True}
            ]}

        monkeypatch.setattr(validator, "_run_db_query", lambda q: mock_query(q))

        validator._check_certification_overlays()

        assert validator.results.total_checks == 1
        assert validator.results.passed == 0
        assert len(validator.results.failures) == 1

        failure = validator.results.failures[0]
        assert failure.check_name == "certification_overlays"
        assert failure.severity == "critical"
        assert "2 CA NP+ANCC providers" in failure.message


    def test_validation_results_has_failures(self):
        """Test has_failures property."""
        results = ValidationResults()

        # No failures
        assert not results.has_failures

        # Add warning - should not trigger has_failures
        results.warnings.append(ValidationFailure(
            check_name="test",
            severity="warning",
            message="warning",
            affected_entity="test"
        ))
        assert not results.has_failures

        # Add critical failure - should trigger
        results.failures.append(ValidationFailure(
            check_name="test",
            severity="critical",
            message="critical",
            affected_entity="test"
        ))
        assert results.has_failures

    def test_validation_results_pass_rate(self):
        """Test pass rate calculation."""
        results = ValidationResults()

        # Empty results = 100%
        assert results.pass_rate == 100.0

        # 3 out of 5 checks passed = 60%
        results.total_checks = 5
        results.passed = 3
        assert results.pass_rate == 60.0

        # All passed = 100%
        results.total_checks = 10
        results.passed = 10
        assert results.pass_rate == 100.0


    def test_run_db_query_mock(self, validator):
        """Test _run_db_query returns mock data."""
        result = validator._run_db_query("SELECT * FROM test")

        assert result is not None
        assert "rows" in result
        assert result["count"] == 0

    def test_run_pytest_file_exists(self, validator, mock_credentialmate_path):
        """Test _run_pytest returns success when file exists."""
        test_file = Path(mock_credentialmate_path) / "apps/backend-api/tests/unit/cme/test_topic_normalization.py"

        result = validator._run_pytest(str(test_file))

        assert result["passed"] is True
        assert "error" not in result

    def test_run_pytest_file_missing(self, validator, tmp_path):
        """Test _run_pytest returns failure when file missing."""
        missing_file = tmp_path / "nonexistent_test.py"

        result = validator._run_pytest(str(missing_file))

        assert result["passed"] is False
        assert "error" in result
        assert "not found" in result["error"]
