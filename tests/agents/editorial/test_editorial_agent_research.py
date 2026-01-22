"""
Unit tests for EditorialAgent browser automation integration

Tests:
- Browser automation integration in _conduct_research()
- Research data collection (regulatory + competitor)
- URL state extraction helper
- Session cleanup on error
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from agents.editorial.editorial_agent import EditorialAgent, EditorialTask
from governance.require_harness import HarnessContext


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def mock_app_adapter():
    """Mock application adapter"""
    adapter = Mock()
    adapter.get_context.return_value = Mock(
        project_name="credentialmate",
        project_path="/test/project"
    )
    return adapter


@pytest.fixture
def mock_contract():
    """Mock autonomy contract"""
    contract_data = {
        "agent": "editorial",
        "limits": {
            "max_iterations": 20,
            "max_retries": 3
        },
        "permissions": {
            "write_file": True,
            "browser_automation": True
        }
    }
    return Mock(**contract_data)


@pytest.fixture
def editorial_agent(mock_app_adapter, temp_dir, monkeypatch):
    """EditorialAgent instance with mocked dependencies"""
    # Patch Path.cwd() to return temp_dir
    monkeypatch.setattr(Path, "cwd", lambda: temp_dir)

    # Mock contract loading
    with patch('governance.contract.load') as mock_load:
        mock_load.return_value = Mock(
            limits={"max_iterations": 20, "max_retries": 3}
        )

        agent = EditorialAgent(app_adapter=mock_app_adapter)

    return agent


@pytest.fixture
def sample_task():
    """Sample editorial task with research sources"""
    return EditorialTask(
        task_id="RESEARCH-TEST-001",
        category="test",
        topic="California Nursing CE Requirements",
        keywords=["california", "nursing", "continuing education"],
        research_sources=[
            "https://www.rn.ca.gov/regulations/",  # Regulatory source
            "https://competitor.com/blog/nursing-ce"  # Competitor source
        ],
        target_audience="nurses",
        target_word_count=2000,
        min_seo_score=60
    )


class TestBrowserAutomationIntegration:
    """Test browser automation integration in research"""

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_conduct_research_with_browser_automation(
        self, mock_require, mock_client_class, editorial_agent, sample_task
    ):
        """_conduct_research() uses browser automation client"""
        # Mock browser automation client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.scrape_regulatory_updates.return_value = [
            {"title": "New CE requirement", "date": "2026-01-15", "confidence": 0.95}
        ]
        mock_client.analyze_competitor_blog.return_value = {
            "title": "Competitor Article",
            "seo_score": 82,
            "keywords": ["nursing", "CE"]
        }

        # Execute within harness context
        with HarnessContext():
            research_data = editorial_agent._conduct_research(sample_task)

        # Verify browser client was created
        assert mock_client_class.called

        # Verify session created
        mock_client.create_session.assert_called_once()
        session_config = mock_client.create_session.call_args[0][0]
        assert session_config["headless"] is True
        assert "sessionId" in session_config

        # Verify regulatory scraping called
        mock_client.scrape_regulatory_updates.assert_called_once()

        # Verify competitor analysis called
        mock_client.analyze_competitor_blog.assert_called_once()

        # Verify research data structure
        assert "regulatory_updates" in research_data
        assert "competitor_analysis" in research_data
        assert "timestamp" in research_data

        assert len(research_data["regulatory_updates"]) == 1
        assert len(research_data["competitor_analysis"]) == 1

        # Verify session cleanup called
        mock_client.cleanup_session.assert_called_once()

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_conduct_research_separates_sources_by_type(
        self, mock_require, mock_client_class, editorial_agent, sample_task
    ):
        """Research separates regulatory and competitor sources"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.scrape_regulatory_updates.return_value = []
        mock_client.analyze_competitor_blog.return_value = {}

        with HarnessContext():
            editorial_agent._conduct_research(sample_task)

        # Regulatory source (.gov) should trigger scraping
        mock_client.scrape_regulatory_updates.assert_called_once()
        call_args = mock_client.scrape_regulatory_updates.call_args
        assert "rn.ca.gov" in call_args.kwargs["board_url"]

        # Competitor source (non-.gov) should trigger analysis
        mock_client.analyze_competitor_blog.assert_called_once()
        call_args = mock_client.analyze_competitor_blog.call_args
        assert "competitor.com" in call_args.kwargs["url"]

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_conduct_research_cleans_up_on_error(
        self, mock_require, mock_client_class, editorial_agent, sample_task
    ):
        """Session cleanup called even when scraping fails"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Simulate scraping error
        mock_client.scrape_regulatory_updates.side_effect = Exception("Network timeout")

        with HarnessContext():
            research_data = editorial_agent._conduct_research(sample_task)

        # Session cleanup should still be called
        mock_client.cleanup_session.assert_called_once()

        # Research data should have error recorded
        assert len(research_data["regulatory_updates"]) > 0
        assert "error" in research_data["regulatory_updates"][0]

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_conduct_research_handles_import_error(
        self, mock_require, mock_client_class, editorial_agent, sample_task
    ):
        """Gracefully handles missing browser automation"""
        # Simulate ImportError
        mock_client_class.side_effect = ImportError("No module named 'adapters.browser_automation'")

        with HarnessContext():
            research_data = editorial_agent._conduct_research(sample_task)

        # Should return empty research data
        assert research_data["regulatory_updates"] == []
        assert research_data["competitor_analysis"] == []
        assert "timestamp" in research_data


class TestURLStateExtraction:
    """Test state extraction from board URLs"""

    def test_extract_state_california(self, editorial_agent):
        """Extract California from ca.gov URL"""
        urls = [
            "https://www.rn.ca.gov/regulations/",
            "https://portal.ca.gov/nursing-board"
        ]

        for url in urls:
            state = editorial_agent._extract_state_from_url(url)
            assert state == "California"

    def test_extract_state_new_york(self, editorial_agent):
        """Extract New York from ny.gov URL"""
        url = "https://www.op.nysed.gov/professions/nursing"
        state = editorial_agent._extract_state_from_url(url)
        assert state == "New York"

    def test_extract_state_texas(self, editorial_agent):
        """Extract Texas from tx.gov URL"""
        url = "https://www.bon.texas.gov/regulations"
        state = editorial_agent._extract_state_from_url(url)
        assert state == "Texas"

    def test_extract_state_florida(self, editorial_agent):
        """Extract Florida from fl.gov URL"""
        url = "https://floridasnursing.gov/renewals/"
        state = editorial_agent._extract_state_from_url(url)
        assert state == "Florida"

    def test_extract_state_from_path_pattern(self, editorial_agent):
        """Extract state from URL path pattern"""
        url = "https://example.com/california-nursing-board/regulations"
        state = editorial_agent._extract_state_from_url(url)
        assert state == "California"

    def test_extract_state_unknown_url(self, editorial_agent):
        """Unknown URL returns 'Unknown'"""
        url = "https://example.com/nursing"
        state = editorial_agent._extract_state_from_url(url)
        assert state == "Unknown"

    def test_extract_state_abbreviation_in_path(self, editorial_agent):
        """Extract state from abbreviation in path"""
        url = "https://example.com/boards/CA/nursing"
        state = editorial_agent._extract_state_from_url(url)
        assert state == "California"


class TestResearchDataCollection:
    """Test research data structure and collection"""

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_research_data_includes_timestamp(
        self, mock_require, mock_client_class, editorial_agent, sample_task
    ):
        """Research data includes timestamp"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.scrape_regulatory_updates.return_value = []
        mock_client.analyze_competitor_blog.return_value = {}

        with HarnessContext():
            research_data = editorial_agent._conduct_research(sample_task)

        assert "timestamp" in research_data
        # Timestamp should be ISO format
        from datetime import datetime
        datetime.fromisoformat(research_data["timestamp"])  # Should not raise

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_research_data_aggregates_multiple_sources(
        self, mock_require, mock_client_class, editorial_agent
    ):
        """Research data aggregates multiple sources"""
        task = EditorialTask(
            task_id="MULTI-SOURCE-001",
            category="test",
            topic="Multi-source test",
            keywords=["test"],
            research_sources=[
                "https://www.rn.ca.gov/",
                "https://www.bon.texas.gov/",
                "https://competitor1.com/blog/",
                "https://competitor2.com/blog/"
            ],
            target_audience="nurses"
        )

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_client.scrape_regulatory_updates.return_value = [{"title": "Update"}]
        mock_client.analyze_competitor_blog.return_value = {"title": "Blog"}

        with HarnessContext():
            research_data = editorial_agent._conduct_research(task)

        # Should have scraped 2 regulatory sources
        assert mock_client.scrape_regulatory_updates.call_count == 2

        # Should have analyzed 2 competitor sources
        assert mock_client.analyze_competitor_blog.call_count == 2

        # Data should be aggregated
        assert len(research_data["regulatory_updates"]) == 2
        assert len(research_data["competitor_analysis"]) == 2


class TestGovernanceContractEnforcement:
    """Test governance contract enforcement in research"""

    @patch('governance.contract.require_allowed')
    def test_checks_browser_automation_permission(self, mock_require, editorial_agent, sample_task):
        """Checks browser_automation permission before research"""
        # Mock browser automation to avoid actual execution
        with patch('agents.editorial.editorial_agent.BrowserAutomationClient'):
            with HarnessContext():
                try:
                    editorial_agent._conduct_research(sample_task)
                except:
                    pass  # Ignore other errors

        # Should have checked browser_automation permission
        mock_require.assert_any_call(editorial_agent.contract, "browser_automation")
