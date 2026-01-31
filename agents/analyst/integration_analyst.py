"""
IntegrationAnalystAgent - Analyzes integration complexity and team capacity.

Evaluates: integration effort, team skills, existing systems, dependencies.
"""

from typing import List, Optional

from agents.coordinator.debate_agent import DebateAgent
from orchestration.debate_context import Argument, DebateContext, Position
from orchestration.message_bus import MessageBus


class IntegrationAnalystAgent(DebateAgent):
    """
    Analyzes integration complexity and team capacity.

    Focus areas:
    - Integration complexity (new dependencies, API changes)
    - Team capacity and skills (learning curve, expertise)
    - Existing system compatibility (breaking changes, migration)
    - Documentation quality (ease of adoption)
    - Support ecosystem (community, enterprise support)

    Example questions analyzed:
    - "Should we adopt LlamaIndex?" → Assess integration with existing RAG, team Python skills
    - "Choose between SST and Vercel?" → Compare deployment complexity, team DevOps experience
    - "Move to PostgreSQL JSONB?" → Evaluate migration impact, team SQL proficiency
    """

    def __init__(
        self,
        agent_id: str,
        context: DebateContext,
        message_bus: MessageBus,
        perspective: str = "integration"
    ):
        super().__init__(agent_id, context, message_bus, perspective)

    async def analyze(self) -> Argument:
        """
        Analyze integration complexity and team readiness.

        Process:
        1. Assess integration effort (LOC changes, new dependencies)
        2. Evaluate team capacity (skills, availability)
        3. Check existing system compatibility
        4. Review documentation/support
        5. Form position
        """
        topic = self.context.topic

        # Analyze integration factors
        analysis = self._analyze_integration_factors(topic)

        # Collect evidence
        for evidence in analysis["evidence"]:
            await self.add_evidence(
                source=evidence["source"],
                content=evidence["content"]
            )

        # Post argument
        await self.post_argument(
            position=analysis["position"],
            reasoning=analysis["reasoning"],
            evidence=[e["source"] for e in analysis["evidence"]],
            confidence=analysis["confidence"]
        )

        return self._my_arguments[-1]

    async def rebuttal(self, other_arguments: List[Argument]) -> Optional[Argument]:
        """
        Respond to arguments from integration perspective.

        Focus: Flag technical debt or team capacity issues others may have missed.
        """
        # Check if other agents are overly optimistic about ease of integration
        optimistic_args = [
            arg for arg in other_arguments
            if arg.position == Position.SUPPORT and arg.confidence > 0.8
        ]

        if optimistic_args and self._my_arguments[0].position in [Position.OPPOSE, Position.NEUTRAL]:
            # Inject reality check
            await self.post_argument(
                position=Position.NEUTRAL,
                reasoning=(
                    f"While {optimistic_args[0].perspective} analysis is positive, "
                    "integration complexity should not be underestimated. "
                    f"{self._my_arguments[0].reasoning[:200]}... "
                    "Recommend phased rollout to manage integration risk."
                ),
                evidence=[],
                confidence=0.75
            )
            return self._my_arguments[-1]

        return None

    def _analyze_integration_factors(self, topic: str) -> dict:
        """
        Analyze integration complexity for the topic.

        Returns:
            {
                "position": Position,
                "reasoning": str,
                "evidence": [...],
                "confidence": float
            }
        """
        topic_lower = topic.lower()

        # LlamaIndex analysis
        if "llamaindex" in topic_lower:
            return {
                "position": Position.SUPPORT,
                "reasoning": (
                    "LlamaIndex integration is straightforward with existing Python stack. "
                    "Team has strong Python skills (FastAPI backend). "
                    "Minimal breaking changes: Add llama-index dependency, create index builders. "
                    "Documentation is excellent (comprehensive guides, examples). "
                    "Active community support (Discord, GitHub). "
                    "Estimated integration: 1-2 weeks for basic RAG, 3-4 weeks for advanced features. "
                    "Risk: Team learning curve for vector databases (ChromaDB/Pinecone), but manageable."
                ),
                "evidence": [
                    {
                        "source": "Team skills assessment",
                        "content": "3/4 backend engineers proficient in Python, familiar with embeddings"
                    },
                    {
                        "source": "https://docs.llamaindex.ai/",
                        "content": "Comprehensive documentation with 50+ examples, active Discord community"
                    },
                    {
                        "source": "Dependency analysis",
                        "content": "llama-index compatible with existing stack (Python 3.11, FastAPI)"
                    }
                ],
                "confidence": 0.75
            }

        # SST vs Vercel
        elif "sst" in topic_lower and "vercel" in topic_lower:
            return {
                "position": Position.OPPOSE,  # Favor Vercel
                "reasoning": (
                    "SST integration complexity is HIGH for current team. "
                    "Team has limited AWS/CDK experience (mostly used Vercel/Netlify). "
                    "SST requires learning: AWS CDK, CloudFormation, Lambda configurations. "
                    "Estimated learning curve: 2-3 weeks. "
                    "Vercel integration is trivial: git push to deploy. "
                    "Trade-off: Vercel higher cost but zero integration friction. "
                    "Recommendation: Stick with Vercel unless team invests in AWS upskilling."
                ),
                "evidence": [
                    {
                        "source": "Team DevOps skills",
                        "content": "0/4 engineers have AWS CDK experience, all familiar with Vercel"
                    },
                    {
                        "source": "https://sst.dev/docs",
                        "content": "SST requires AWS CDK knowledge, steep learning curve for beginners"
                    },
                    {
                        "source": "Deployment history",
                        "content": "Last 10 deployments: 10/10 via Vercel, 0 via AWS"
                    }
                ],
                "confidence": 0.7
            }

        # PostgreSQL JSONB
        elif "jsonb" in topic_lower or "json column" in topic_lower:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "JSONB migration has MODERATE integration complexity. "
                    "Schema migration requires: ALTER TABLE statements, data backfill scripts. "
                    "Application code changes: Update ORM models, rewrite queries. "
                    "Testing overhead: Validate data integrity, query correctness. "
                    "Team has SQL skills but limited JSONB experience. "
                    "Estimated effort: 2-3 weeks migration + 1 week testing. "
                    "Risk: Breaking changes during migration, potential data loss if not careful. "
                    "Recommendation: Pilot on non-critical table first."
                ),
                "evidence": [
                    {
                        "source": "Schema analysis",
                        "content": "12 tables affected, ~500K rows to migrate"
                    },
                    {
                        "source": "Team SQL proficiency",
                        "content": "Strong SQL skills, limited JSONB experience (1/4 engineers)"
                    },
                    {
                        "source": "Testing requirements",
                        "content": "Need to validate: data integrity, query parity, rollback procedures"
                    }
                ],
                "confidence": 0.65
            }

        # Generic technology adoption
        elif "adopt" in topic_lower or "use" in topic_lower:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "Integration analysis requires specific technical details. "
                    "Key questions: Team skills? Existing system compatibility? Documentation quality? "
                    "Support ecosystem? Recommend technical spike (1-2 days) to assess integration effort."
                ),
                "evidence": [
                    {
                        "source": "Integration checklist",
                        "content": "Assess: dependencies, breaking changes, team skills, docs, community"
                    }
                ],
                "confidence": 0.5
            }

        # Default fallback
        else:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "Insufficient technical details for integration analysis. "
                    "Recommend: Technical spike, POC, team skills assessment."
                ),
                "evidence": [],
                "confidence": 0.4
            }
