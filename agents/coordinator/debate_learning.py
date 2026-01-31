"""
Cross-Debate Learning for Council Pattern.

Learns patterns from completed debates and uses them to inform future decisions.

Usage:
    from agents.coordinator.debate_learning import DebateLearner, LearnedPattern

    learner = DebateLearner(storage_dir=Path(".aibrain/learned_patterns"))
    pattern = learner.learn_from_debate(debate_result)
    matches = learner.find_similar("Should we use LlamaIndex?")
"""

import json
import fnmatch
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class PatternType(str, Enum):
    """Types of learned patterns."""
    TOPIC_KEYWORD = "topic_keyword"
    TECHNOLOGY_COMPARISON = "technology_comparison"
    ARCHITECTURE_DECISION = "architecture_decision"


@dataclass
class LearnedPattern:
    """A pattern learned from past debates."""
    topic_pattern: str  # Glob pattern like "*redis*" or "*llamaindex*"
    recommendation: str  # ADOPT, REJECT, CONDITIONAL
    confidence: float
    success_rate: float = 0.0
    pattern_type: PatternType = PatternType.TOPIC_KEYWORD
    key_factors: List[str] = field(default_factory=list)
    outcome_count: int = 0
    success_count: int = 0
    created_at: str = ""
    last_used: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "topic_pattern": self.topic_pattern,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "success_rate": self.success_rate,
            "pattern_type": self.pattern_type.value if isinstance(self.pattern_type, PatternType) else self.pattern_type,
            "key_factors": self.key_factors,
            "outcome_count": self.outcome_count,
            "success_count": self.success_count,
            "created_at": self.created_at,
            "last_used": self.last_used,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearnedPattern":
        """Create from dictionary."""
        pattern_type = data.get("pattern_type", PatternType.TOPIC_KEYWORD)
        if isinstance(pattern_type, str):
            pattern_type = PatternType(pattern_type)

        return cls(
            topic_pattern=data["topic_pattern"],
            recommendation=data["recommendation"],
            confidence=data["confidence"],
            success_rate=data.get("success_rate", 0.0),
            pattern_type=pattern_type,
            key_factors=data.get("key_factors", []),
            outcome_count=data.get("outcome_count", 0),
            success_count=data.get("success_count", 0),
            created_at=data.get("created_at", ""),
            last_used=data.get("last_used", ""),
        )


class DebateLearner:
    """
    Learns and applies patterns from past debates.

    Stores patterns in a JSON file and can query for similar patterns
    when analyzing new topics.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path(".aibrain/learned_patterns")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._patterns: Dict[str, LearnedPattern] = {}
        self._load()

    def _load(self) -> None:
        """Load patterns from storage."""
        patterns_file = self.storage_dir / "patterns.json"
        if patterns_file.exists():
            try:
                with patterns_file.open() as f:
                    data = json.load(f)
                    for pattern_data in data.get("patterns", []):
                        pattern = LearnedPattern.from_dict(pattern_data)
                        self._patterns[pattern.topic_pattern] = pattern
            except (json.JSONDecodeError, KeyError):
                self._patterns = {}

    def _save(self) -> None:
        """Save patterns to storage."""
        patterns_file = self.storage_dir / "patterns.json"
        data = {
            "patterns": [p.to_dict() for p in self._patterns.values()],
            "updated_at": datetime.utcnow().isoformat(),
        }
        with patterns_file.open("w") as f:
            json.dump(data, f, indent=2)

    def learn_from_debate(self, debate_result: Any) -> Optional[LearnedPattern]:
        """
        Learn a pattern from a completed debate.

        Args:
            debate_result: Result from a completed debate

        Returns:
            LearnedPattern if pattern was learned, None otherwise
        """
        topic = getattr(debate_result, 'topic', '')
        recommendation = getattr(debate_result, 'recommendation', '')
        confidence = getattr(debate_result, 'confidence', 0.0)
        key_factors = getattr(debate_result, 'key_factors', [])

        if not topic or not recommendation:
            return None

        # Extract keywords for pattern
        keywords = self._extract_keywords(topic)
        if not keywords:
            return None

        # Create pattern from most significant keyword
        pattern_str = f"*{keywords[0].lower()}*"

        pattern = LearnedPattern(
            topic_pattern=pattern_str,
            recommendation=recommendation,
            confidence=confidence,
            key_factors=key_factors,
            created_at=datetime.utcnow().isoformat(),
        )

        self.add_pattern(pattern)
        return pattern

    def add_pattern(self, pattern: LearnedPattern, create_ko: bool = False) -> None:
        """
        Add a pattern to the learner.

        Args:
            pattern: Pattern to add
            create_ko: Whether to create a Knowledge Object
        """
        if not pattern.created_at:
            pattern.created_at = datetime.utcnow().isoformat()

        self._patterns[pattern.topic_pattern] = pattern
        self._save()

        if create_ko:
            self._create_ko_for_pattern(pattern)

    def get_pattern(self, topic_pattern: str) -> Optional[LearnedPattern]:
        """Get a pattern by its topic pattern."""
        return self._patterns.get(topic_pattern)

    def find_similar(self, topic: str) -> List[LearnedPattern]:
        """
        Find patterns similar to a given topic.

        Args:
            topic: Topic to search for

        Returns:
            List of matching patterns, sorted by confidence
        """
        topic_lower = topic.lower()
        matches = []

        for pattern in self._patterns.values():
            # Check if pattern matches topic
            if fnmatch.fnmatch(topic_lower, pattern.topic_pattern):
                matches.append(pattern)
            # Also check if any keyword in topic matches pattern
            elif any(kw in pattern.topic_pattern.replace("*", "") for kw in topic_lower.split()):
                matches.append(pattern)

        # Sort by confidence descending
        matches.sort(key=lambda p: p.confidence, reverse=True)
        return matches

    def record_outcome(self, topic_pattern: str, success: bool) -> None:
        """
        Record the outcome of following a pattern's recommendation.

        Args:
            topic_pattern: Pattern that was used
            success: Whether the outcome was successful
        """
        pattern = self._patterns.get(topic_pattern)
        if pattern:
            pattern.outcome_count += 1
            if success:
                pattern.success_count += 1
            pattern.success_rate = pattern.success_count / pattern.outcome_count
            pattern.last_used = datetime.utcnow().isoformat()
            self._save()

    def _extract_keywords(self, topic: str) -> List[str]:
        """Extract significant keywords from a topic."""
        # Remove common words
        stop_words = {
            "should", "we", "use", "adopt", "for", "the", "a", "an", "our",
            "is", "it", "to", "in", "of", "and", "or", "with", "this", "that"
        }

        words = topic.lower().split()
        keywords = [w.strip("?.,!") for w in words if w.lower() not in stop_words]

        # Prioritize technical terms (longer words often more specific)
        keywords.sort(key=len, reverse=True)
        return keywords[:3]

    def _create_ko_for_pattern(self, pattern: LearnedPattern) -> None:
        """Create a Knowledge Object for a pattern."""
        try:
            from knowledge.ko_manager import create_ko  # type: ignore[import-untyped]

            create_ko(
                type="council_pattern",
                topic=f"Debate pattern: {pattern.topic_pattern}",
                recommendation=pattern.recommendation,
                confidence=pattern.confidence,
                key_factors=pattern.key_factors,
                success_rate=pattern.success_rate,
            )
        except ImportError:
            pass  # KO system not available


def create_ko(*args: Any, **kwargs: Any) -> None:
    """Placeholder for KO creation - used in testing."""
    pass
