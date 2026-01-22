"""
Integration tests for browser automation with editorial workflow

Tests:
- Python ↔ TypeScript communication
- Regulatory scraping returns valid data
- Competitor analysis returns SEO metadata
- Session creation and cleanup
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from agents.editorial.editorial_agent import EditorialAgent, EditorialTask
from governance.require_harness import HarnessContext


@pytest.fixture
def mock_adapter():
    """Mock application adapter"""
    adapter = Mock()
    adapter.get_context.return_value = Mock(
        project_name="credentialmate",
        project_path="/test/project"
    )
    return adapter


@pytest.fixture
def editorial_agent(mock_adapter):
    """EditorialAgent with mocked contract"""
    with patch('governance.contract.load') as mock_load:
        mock_load.return_value = Mock(
            limits={"max_iterations": 20, "max_retries": 3}
        )
        return EditorialAgent(app_adapter=mock_adapter)


@pytest.fixture
def sample_task():
    """Sample task with browser automation requirements"""
    return EditorialTask(
        task_id="BROWSER-TEST-001",
        category="test",
        topic="Browser Automation Test",
        keywords=["browser", "automation"],
        research_sources=[
            "https://www.rn.ca.gov/regulations/",
            "https://competitor.com/blog/nursing"
        ],
        target_audience="testers"
    )


class TestBrowserAutomationCommunication:
    """Test Python ↔ TypeScript communication"""

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_client_instantiation(self, mock_require, mock_client_class, editorial_agent, sample_task):
        """BrowserAutomationClient is properly instantiated"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        with HarnessContext():
            editorial_agent._conduct_research(sample_task)

        # Client should be instantiated
        assert mock_client_class.called

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_session_creation(self, mock_require, mock_client_class, editorial_agent, sample_task):
        """Browser session is created with correct config"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        with HarnessContext():
            editorial_agent._conduct_research(sample_task)

        # Session should be created
        mock_client.create_session.assert_called_once()

        # Check session config
        call_args = mock_client.create_session.call_args[0][0]
        assert call_args["headless"] is True
        assert "sessionId" in call_args
        assert "auditLogPath" in call_args

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_session_cleanup_always_called(self, mock_require, mock_client_class, editorial_agent, sample_task):
        """Session cleanup called even on errors"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Simulate error during scraping
        mock_client.scrape_regulatory_updates.side_effect = Exception("Network error")

        with HarnessContext():
            editorial_agent._conduct_research(sample_task)

        # Cleanup should still be called
        mock_client.cleanup_session.assert_called_once()


class TestRegulatoryDataScraping:
    """Test regulatory board scraping"""

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_regulatory_scraping_returns_updates(self, mock_require, mock_client_class, editorial_agent, sample_task):
        """Regulatory scraping returns update objects"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock regulatory updates
        mock_client.scrape_regulatory_updates.return_value = [
            {
                "title": "New CE Requirement for 2026",
                "date": "2026-01-15",
                "url": "https://www.rn.ca.gov/regulations/ce-2026",
                "confidence": 0.95
            },
            {
                "title": "License Renewal Changes",
                "date": "2026-01-10",
                "url": "https://www.rn.ca.gov/regulations/renewal",
                "confidence": 0.88
            }
        ]

        with HarnessContext():
            research_data = editorial_agent._conduct_research(sample_task)

        # Verify updates are in research data
        assert len(research_data["regulatory_updates"]) == 2
        assert research_data["regulatory_updates"][0]["title"] == "New CE Requirement for 2026"
        assert research_data["regulatory_updates"][0]["confidence"] == 0.95

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_regulatory_scraping_with_state_extraction(self, mock_require, mock_client_class, editorial_agent, sample_task):
        """State is correctly extracted from board URL"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.scrape_regulatory_updates.return_value = []

        with HarnessContext():
            editorial_agent._conduct_research(sample_task)

        # Check that state extraction was used
        call_args = mock_client.scrape_regulatory_updates.call_args.kwargs
        assert call_args["state"] == "California"  # From rn.ca.gov

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_regulatory_scraping_handles_errors_gracefully(self, mock_require, mock_client_class, editorial_agent, sample_task):
        """Scraping errors are captured, not raised"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.scrape_regulatory_updates.side_effect = Exception("Scraping failed")

        with HarnessContext():
            research_data = editorial_agent._conduct_research(sample_task)

        # Should have error entry in regulatory_updates
        assert len(research_data["regulatory_updates"]) > 0
        assert "error" in research_data["regulatory_updates"][0]


class TestCompetitorAnalysis:
    """Test competitor blog analysis"""

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_competitor_analysis_returns_metadata(self, mock_require, mock_client_class, editorial_agent, sample_task):
        """Competitor analysis returns SEO metadata"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock competitor analysis
        mock_client.analyze_competitor_blog.return_value = {
            "title": "Complete Guide to Nursing CE Requirements",
            "url": "https://competitor.com/blog/nursing",
            "seo_score": 82,
            "keywords": ["nursing", "CE", "requirements", "license"],
            "word_count": 2500,
            "structure": {
                "h1_count": 1,
                "h2_count": 5,
                "h3_count": 12
            }
        }

        with HarnessContext():
            research_data = editorial_agent._conduct_research(sample_task)

        # Verify analysis is in research data
        assert len(research_data["competitor_analysis"]) == 1
        analysis = research_data["competitor_analysis"][0]
        assert analysis["title"] == "Complete Guide to Nursing CE Requirements"
        assert analysis["seo_score"] == 82
        assert "keywords" in analysis

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_competitor_analysis_multiple_sources(self, mock_require, mock_client_class, editorial_agent):
        """Multiple competitor sources are analyzed"""
        task = EditorialTask(
            task_id="MULTI-COMPETITOR-001",
            category="test",
            topic="Test",
            keywords=["test"],
            research_sources=[
                "https://competitor1.com/blog/article1",
                "https://competitor2.com/blog/article2"
            ],
            target_audience="testers"
        )

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.analyze_competitor_blog.return_value = {"title": "Article"}

        with HarnessContext():
            research_data = editorial_agent._conduct_research(task)

        # Both sources should be analyzed
        assert mock_client.analyze_competitor_blog.call_count == 2
        assert len(research_data["competitor_analysis"]) == 2


class TestDataValidation:
    """Test data validation and structure"""

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_research_data_structure(self, mock_require, mock_client_class, editorial_agent, sample_task):
        """Research data has correct structure"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.scrape_regulatory_updates.return_value = []
        mock_client.analyze_competitor_blog.return_value = {}

        with HarnessContext():
            research_data = editorial_agent._conduct_research(sample_task)

        # Check structure
        assert "regulatory_updates" in research_data
        assert "competitor_analysis" in research_data
        assert "timestamp" in research_data

        assert isinstance(research_data["regulatory_updates"], list)
        assert isinstance(research_data["competitor_analysis"], list)
        assert isinstance(research_data["timestamp"], str)

    @patch('agents.editorial.editorial_agent.BrowserAutomationClient')
    @patch('governance.contract.require_allowed')
    def test_timestamp_is_iso_format(self, mock_require, mock_client_class, editorial_agent, sample_task):
        """Timestamp is in ISO 8601 format"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.scrape_regulatory_updates.return_value = []
        mock_client.analyze_competitor_blog.return_value = {}

        with HarnessContext():
            research_data = editorial_agent._conduct_research(sample_task)

        # Validate ISO format
        from datetime import datetime
        timestamp = research_data["timestamp"]
        datetime.fromisoformat(timestamp)  # Should not raise
