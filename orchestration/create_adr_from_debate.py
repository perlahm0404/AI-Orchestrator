"""
Standalone function to create ADR from council debate.

Simplified interface that doesn't require full agent infrastructure.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from orchestration.council_adr_generator import CouncilADRGenerator
from orchestration.adr_registry import ADRRegistry, ADREntry

logger = logging.getLogger(__name__)


def create_adr_from_debate(
    debate_result,  # DebateResult from CouncilOrchestrator
    context: str,
    project: str = "ai-orchestrator",
    orchestrator_root: Path = None
) -> Dict[str, Any]:
    """
    Create ADR from council debate result.

    This is a simplified standalone function that doesn't require
    full ADRCreatorAgent infrastructure.

    Args:
        debate_result: DebateResult from CouncilOrchestrator
        context: Background context for the decision
        project: Project name (default: "ai-orchestrator")
        orchestrator_root: Root directory (default: auto-detect)

    Returns:
        {
            "status": "completed" | "failed",
            "adr_number": "ADR-042",
            "adr_path": "/path/to/ADR-042-topic.md",
            "council_id": "COUNCIL-20260130-001",
            "recommendation": "ADOPT",
            "confidence": 0.75
        }
    """
    if orchestrator_root is None:
        # Auto-detect: find git root
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                orchestrator_root = current
                break
            current = current.parent
        else:
            orchestrator_root = Path(__file__).parent.parent

    logger.info(f"🚀 Creating ADR from council debate: {debate_result.council_id}")

    try:
        # Step 1: Reserve ADR number
        registry = ADRRegistry(orchestrator_root)
        adr_number = registry.reserve_adr_number()
        adr_id = f"ADR-{adr_number:03d}"

        logger.info(f"🔢 Reserved ADR number: {adr_id}")

        # Step 2: Generate ADR markdown from debate result
        council_generator = CouncilADRGenerator()
        adr_markdown = council_generator.generate_from_debate(
            adr_number=adr_number,
            result=debate_result,
            context=context,
            status="Proposed",
            approved_by="Pending"
        )

        # Step 3: Write ADR file
        decisions_dir = orchestrator_root / "AI-Team-Plans" / "decisions"
        decisions_dir.mkdir(parents=True, exist_ok=True)

        # Create slug from topic
        title_slug = _slugify(debate_result.topic)
        adr_filename = f"{adr_id}-{title_slug}.md"
        adr_path = decisions_dir / adr_filename

        adr_path.write_text(adr_markdown)
        logger.info(f"✅ Council ADR written: {adr_path}")

        # Step 4: Update ADR registry
        entry = ADREntry(
            number=adr_id,
            title=debate_result.topic[:80],  # Truncate if needed
            project=project,
            status="draft",
            date=datetime.now().strftime("%Y%m%d"),
            advisor="council-orchestrator",
            file_path=f"AI-Team-Plans/decisions/{adr_filename}",
            tags=["council", "debate", debate_result.recommendation.lower()],
            domains=["architecture"]
        )

        registry.register_adr(entry)
        logger.info(f"✅ ADR registry updated")

        logger.info(f"✅ Council ADR creation complete: {adr_id}")

        return {
            "status": "completed",
            "adr_number": adr_id,
            "adr_path": str(adr_path),
            "council_id": debate_result.council_id,
            "recommendation": debate_result.recommendation,
            "confidence": debate_result.confidence
        }

    except Exception as e:
        error_msg = f"Council ADR creation failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "failed",
            "reason": error_msg
        }


def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    import re
    # Remove question marks, convert to lowercase
    slug = text.replace("?", "").lower()
    # Replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    # Truncate to 50 chars
    return slug[:50].strip('-')
