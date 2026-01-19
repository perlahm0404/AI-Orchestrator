#!/usr/bin/env python3
"""
Task Complexity Analyzer - Routes tasks based on complexity scoring

Analyzes tasks and assigns complexity scores (0-100) to determine optimal team routing.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class TaskComplexity:
    """Result of task complexity analysis"""
    complexity_score: int           # 0-100
    complexity_level: str           # "simple" | "moderate" | "complex" | "strategic"
    estimated_files: int            # Estimated number of files to modify
    estimated_iterations: int       # Estimated iteration budget
    recommended_team: str           # "qa" | "dev" | "cito"
    recommended_agent: Optional[str]  # Specific agent type (e.g., "bugfix", "featurebuilder")
    confidence: float               # 0.0-1.0
    reasoning: str                  # Human-readable explanation
    signals: Dict[str, int]         # Breakdown of score components


class TaskAnalyzer:
    """Analyzes task complexity and recommends routing"""

    # Keywords for description analysis
    KEYWORDS = {
        # High complexity keywords (15 points each)
        "refactor": 15,
        "migration": 15,
        "architecture": 15,
        "redesign": 15,

        # Medium complexity keywords (10 points each)
        "feature": 10,
        "implement": 10,
        "integration": 10,
        "api": 10,

        # Low complexity keywords (5 points each)
        "bug": 5,
        "fix": 5,
        "update": 5,
        "typo": 3,

        # Domain-specific keywords
        "hipaa": 25,
        "phi": 25,
        "pii": 20,
        "security": 20,
        "auth": 20,
        "authentication": 20,
        "compliance": 15,
        "audit": 15
    }

    # File count thresholds
    FILE_THRESHOLDS = {
        1: 0,
        2: 5,
        3: 8,
        5: 12,
        10: 18,
        float('inf'): 20
    }

    # Complexity level thresholds
    COMPLEXITY_THRESHOLDS = {
        "simple": (0, 30),
        "moderate": (31, 60),
        "complex": (61, 80),
        "strategic": (81, 100)
    }

    # Team routing based on complexity
    TEAM_ROUTING = {
        "simple": ("qa", ["bugfix", "codequality", "testfixer"]),
        "moderate": ("dev", ["featurebuilder", "testwriter"]),
        "complex": ("dev", ["featurebuilder"]),  # CITO oversight
        "strategic": ("cito", None)  # CITO handles directly
    }

    # Iteration budgets by complexity
    ITERATION_BUDGETS = {
        "simple": 15,
        "moderate": 30,
        "complex": 50,
        "strategic": 100
    }

    def __init__(self) -> None:
        pass

    def analyze_complexity(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> TaskComplexity:
        """
        Analyze task complexity and recommend routing

        Args:
            task: Task dictionary with id, title, description, etc.
            context: Optional context (file lists, git diff, etc.)

        Returns:
            TaskComplexity with score and routing recommendation
        """
        title = task.get("title", "")
        description = task.get("description", "")
        combined_text = f"{title} {description}".lower()

        # Initialize signals
        signals = {
            "file_count": 0,
            "description": 0,
            "scope": 0,
            "domain": 0
        }

        # 1. File Count Signal (20 pts max)
        estimated_files = self._estimate_file_count(combined_text, context)
        signals["file_count"] = self._score_file_count(estimated_files)

        # 2. Description Signal (30 pts max)
        signals["description"] = self._score_description(combined_text)

        # 3. Change Scope Signal (25 pts max)
        signals["scope"] = self._score_change_scope(combined_text)

        # 4. Domain Signal (25 pts max)
        signals["domain"] = self._score_domain(combined_text)

        # Calculate total score (capped at 100)
        total_score = min(100, sum(signals.values()))

        # Determine complexity level
        complexity_level = self._determine_level(total_score)

        # Get team routing
        team, agents = self.TEAM_ROUTING[complexity_level]
        recommended_agent = agents[0] if agents else None

        # Get iteration budget
        estimated_iterations = self.ITERATION_BUDGETS[complexity_level]

        # Calculate confidence
        confidence = self._calculate_confidence(signals, combined_text)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            complexity_level, total_score, signals, estimated_files, team
        )

        return TaskComplexity(
            complexity_score=total_score,
            complexity_level=complexity_level,
            estimated_files=estimated_files,
            estimated_iterations=estimated_iterations,
            recommended_team=team,
            recommended_agent=recommended_agent,
            confidence=confidence,
            reasoning=reasoning,
            signals=signals
        )

    def _estimate_file_count(self, text: str, context: Optional[Dict[str, Any]]) -> int:
        """Estimate number of files to be modified"""
        # If context provides file list, use it
        if context and "files" in context:
            return len(context["files"])

        # Otherwise estimate from text
        # Look for file references (*.ts, *.tsx, path/to/file)
        file_patterns = [
            r'\w+\.(ts|tsx|js|jsx|py|json|yaml|md)',
            r'[\w/]+/[\w-]+\.\w+',
        ]

        files_mentioned = set()
        for pattern in file_patterns:
            matches = re.findall(pattern, text)
            files_mentioned.update(matches)

        if files_mentioned:
            return len(files_mentioned)

        # Heuristic: multiple components/modules mentioned
        if re.search(r'(multiple|several|many)\s+(file|component|module)', text):
            return 5

        # Default to 2 files for moderate changes
        if any(word in text for word in ["update", "modify", "change"]):
            return 2

        return 1

    def _score_file_count(self, file_count: int) -> int:
        """Score based on file count (0-20 points)"""
        for threshold, score in sorted(self.FILE_THRESHOLDS.items()):
            if file_count <= threshold:
                return score
        return 20

    def _score_description(self, text: str) -> int:
        """Score based on keywords in description (0-30 points)"""
        score = 0
        matched_keywords = []

        for keyword, points in self.KEYWORDS.items():
            if keyword in text:
                score += points
                matched_keywords.append(keyword)

        # Cap at 30 points
        return min(30, score)

    def _score_change_scope(self, text: str) -> int:
        """Score based on change scope (0-25 points)"""
        # Migration/breaking changes (25 pts)
        if any(word in text for word in ["migration", "breaking change", "schema change"]):
            return 25

        # API changes (20 pts)
        if any(word in text for word in ["api change", "endpoint", "contract change"]):
            return 20

        # Cross-cutting concerns (15 pts)
        if any(word in text for word in ["middleware", "interceptor", "hook", "decorator"]):
            return 15

        # Component/service internal (10 pts)
        if any(word in text for word in ["component", "service", "utility"]):
            return 10

        # Isolated changes (5 pts)
        if any(word in text for word in ["internal", "private", "helper"]):
            return 5

        return 0

    def _score_domain(self, text: str) -> int:
        """Score based on domain sensitivity (0-25 points)"""
        # PHI/HIPAA (25 pts)
        if any(word in text for word in ["hipaa", "phi", "patient data", "health information"]):
            return 25

        # PII/Security (20 pts)
        if any(word in text for word in ["pii", "security", "auth", "credential", "password"]):
            return 20

        # Financial/Payment (15 pts)
        if any(word in text for word in ["payment", "billing", "financial", "transaction"]):
            return 15

        # Business logic (10 pts)
        if any(word in text for word in ["matching", "algorithm", "business rule"]):
            return 10

        # UI/UX (5 pts)
        if any(word in text for word in ["ui", "ux", "styling", "layout", "design"]):
            return 5

        return 0

    def _determine_level(self, score: int) -> str:
        """Determine complexity level from score"""
        for level, (min_score, max_score) in self.COMPLEXITY_THRESHOLDS.items():
            if min_score <= score <= max_score:
                return level
        return "simple"

    def _calculate_confidence(self, signals: Dict[str, int], text: str) -> float:
        """Calculate confidence in the analysis"""
        # High confidence if we have strong signals
        signal_count = sum(1 for score in signals.values() if score > 0)

        # More signals = higher confidence
        confidence = 0.5 + (signal_count * 0.1)

        # Bonus for explicit file mentions or detailed description
        if len(text) > 100:
            confidence += 0.1

        # Cap at 1.0
        return min(1.0, confidence)

    def _generate_reasoning(
        self, level: str, score: int, signals: Dict[str, int],
        files: int, team: str
    ) -> str:
        """Generate human-readable reasoning"""
        parts = []

        # Overall assessment
        parts.append(f"Complexity: {level.upper()} (score: {score}/100)")

        # Signal breakdown
        signal_parts = []
        if signals["file_count"] > 0:
            signal_parts.append(f"file count ({files} files, +{signals['file_count']} pts)")
        if signals["description"] > 0:
            signal_parts.append(f"description keywords (+{signals['description']} pts)")
        if signals["scope"] > 0:
            signal_parts.append(f"change scope (+{signals['scope']} pts)")
        if signals["domain"] > 0:
            signal_parts.append(f"domain sensitivity (+{signals['domain']} pts)")

        if signal_parts:
            parts.append("Based on: " + ", ".join(signal_parts))

        # Team routing
        if team == "qa":
            parts.append("Recommended for QA Team (simple fixes, stable code)")
        elif team == "dev":
            if level == "complex":
                parts.append("Recommended for Dev Team with CITO oversight (complex implementation)")
            else:
                parts.append("Recommended for Dev Team (moderate feature work)")
        elif team == "cito":
            parts.append("Recommended for CITO direct handling (strategic, high-risk)")

        return ". ".join(parts)


# CLI for testing
if __name__ == "__main__":
    import json
    import sys

    analyzer = TaskAnalyzer()

    # Test tasks
    test_tasks = [
        {
            "id": "TASK-001",
            "title": "Fix typo in button label",
            "description": "Update button text from 'Submitt' to 'Submit'"
        },
        {
            "id": "TASK-002",
            "title": "Implement user authentication",
            "description": "Add OAuth and email auth with session management"
        },
        {
            "id": "TASK-003",
            "title": "Refactor HIPAA logging system",
            "description": "Migration to new audit logging format for PHI access tracking across multiple services"
        },
        {
            "id": "TASK-004",
            "title": "Add new feature for therapist matching",
            "description": "Implement matching algorithm with explainability UI"
        }
    ]

    for task in test_tasks:
        result = analyzer.analyze_complexity(task)
        print(f"\n{'='*60}")
        print(f"Task: {task['title']}")
        print(f"{'='*60}")
        print(f"Score: {result.complexity_score}/100")
        print(f"Level: {result.complexity_level}")
        print(f"Team: {result.recommended_team}")
        print(f"Agent: {result.recommended_agent}")
        print(f"Iterations: {result.estimated_iterations}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Signals: {result.signals}")
        print(f"\nReasoning: {result.reasoning}")
