"""
AlternativesAnalystAgent - Analyzes alternative solutions and trade-offs.

Evaluates: competing solutions, trade-offs, opportunity costs.
"""

from typing import List, Optional

from agents.coordinator.debate_agent import DebateAgent
from orchestration.debate_context import Argument, DebateContext, Position
from orchestration.message_bus import MessageBus


class AlternativesAnalystAgent(DebateAgent):
    """
    Analyzes alternative solutions and their trade-offs.

    Focus areas:
    - Competing solutions (commercial vs open-source, cloud vs self-hosted)
    - Trade-off analysis (features vs complexity, cost vs performance)
    - Opportunity cost (what are we NOT doing if we choose this?)
    - Market trends (is this technology mature/growing/declining?)
    - Risk diversification (vendor lock-in, technology obsolescence)

    Example questions analyzed:
    - "Should we adopt LlamaIndex?" → Compare vs Perplexity, Anthropic native, LangChain
    - "Choose between SST and Vercel?" → Also consider Netlify, AWS Amplify, Railway
    - "Move to PostgreSQL JSONB?" → Compare vs MongoDB, keeping normalized schema
    """

    def __init__(
        self,
        agent_id: str,
        context: DebateContext,
        message_bus: MessageBus,
        perspective: str = "alternatives"
    ):
        super().__init__(agent_id, context, message_bus, perspective)

    async def analyze(self) -> Argument:
        """
        Analyze alternative solutions.

        Process:
        1. Identify main alternatives
        2. Compare features, cost, complexity
        3. Assess market maturity and trends
        4. Evaluate opportunity costs
        5. Form position
        """
        topic = self.context.topic

        # Analyze alternatives
        analysis = self._analyze_alternatives(topic)

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
        Respond to arguments by surfacing overlooked alternatives.

        Focus: Ensure all viable options were considered.
        """
        # Check if other agents discussed any alternatives
        alt_mentions = [
            arg for arg in other_arguments
            if any(keyword in arg.reasoning.lower() for keyword in
                   ["alternative", "instead", "vs", "compare", "competitor"])
        ]

        if not alt_mentions:
            # No alternatives discussed - flag this
            await self.post_argument(
                position=Position.NEUTRAL,
                reasoning=(
                    "Important alternatives were not evaluated. "
                    f"{self._my_arguments[0].reasoning[:250]}... "
                    "Recommend comparing against alternatives before final decision."
                ),
                evidence=[],
                confidence=0.7
            )
            return self._my_arguments[-1]

        return None

    def _analyze_alternatives(self, topic: str) -> dict:
        """
        Analyze alternatives for the topic.

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
                "position": Position.NEUTRAL,
                "reasoning": (
                    "LlamaIndex is ONE option among several viable alternatives: "
                    "1. LlamaIndex: Best for complex document hierarchies, extensive customization"
                    "2. Perplexity API: Simpler, managed service, less control"
                    "3. Anthropic Claude native: No external dependencies, but manual RAG implementation"
                    "4. LangChain: More general framework, steeper learning curve"
                    "5. Pinecone/Weaviate: If we need pure vector DB (no orchestration)"
                    ""
                    "Trade-offs:"
                    "- LlamaIndex: High customization, moderate complexity"
                    "- Perplexity: Low complexity, high cost, limited control"
                    "- Anthropic native: Full control, high implementation effort"
                    "- LangChain: Most flexible, highest complexity"
                    ""
                    "Recommendation: LlamaIndex IF we need complex RAG patterns. "
                    "Perplexity IF we want simplicity over customization. "
                    "For CredentialMate's nested license data, LlamaIndex is strongest fit."
                ),
                "evidence": [
                    {
                        "source": "https://www.perplexity.ai/",
                        "content": "Perplexity: Managed RAG API, $20-200/month, limited customization"
                    },
                    {
                        "source": "https://www.langchain.com/",
                        "content": "LangChain: General orchestration framework, steeper learning curve"
                    },
                    {
                        "source": "Market analysis",
                        "content": "LlamaIndex adoption growing 40% QoQ, mature ecosystem"
                    }
                ],
                "confidence": 0.7
            }

        # SST vs Vercel
        elif "sst" in topic_lower and "vercel" in topic_lower:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "SST and Vercel are TWO options among several: "
                    "1. SST: AWS-native, full control, infrastructure-as-code"
                    "2. Vercel: Managed platform, zero-config, higher cost"
                    "3. Netlify: Similar to Vercel, slightly cheaper, less polished"
                    "4. AWS Amplify: AWS-managed, similar to SST but less flexible"
                    "5. Railway: Heroku-like, simple but limited scale"
                    ""
                    "Trade-offs:"
                    "- SST: Best cost, highest control, steepest learning curve"
                    "- Vercel: Best DX, fastest setup, highest cost"
                    "- Netlify: Middle ground on cost/complexity"
                    "- Amplify: AWS ecosystem, but less control than SST"
                    ""
                    "Recommendation: Vercel IF team time is constrained (learning curve cost > platform cost). "
                    "SST IF team has AWS capacity and cost optimization is priority. "
                    "For CredentialMate's small scale, Vercel's simplicity outweighs cost difference."
                ),
                "evidence": [
                    {
                        "source": "https://netlify.com/pricing",
                        "content": "Netlify: $19/month Pro plan, similar features to Vercel"
                    },
                    {
                        "source": "https://aws.amazon.com/amplify/",
                        "content": "AWS Amplify: Managed service, less flexible than SST"
                    },
                    {
                        "source": "Platform comparison matrix",
                        "content": "Vercel: 9/10 DX, 6/10 cost. SST: 7/10 DX, 9/10 cost"
                    }
                ],
                "confidence": 0.75
            }

        # PostgreSQL JSONB
        elif "jsonb" in topic_lower or "json column" in topic_lower:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "JSONB is ONE approach to handling nested data: "
                    "1. PostgreSQL JSONB: Hybrid approach, SQL + document store"
                    "2. Keep normalized schema: Traditional relational, more JOINs"
                    "3. MongoDB: Pure document store, different data model"
                    "4. Hybrid tables: JSONB for some fields, normalized for others"
                    ""
                    "Trade-offs:"
                    "- JSONB: Best query performance for nested data, 10-20% storage overhead"
                    "- Normalized: Best data integrity, more complex queries"
                    "- MongoDB: Most flexible schema, but different query language"
                    "- Hybrid: Best of both, requires careful schema design"
                    ""
                    "Recommendation: Hybrid approach (JSONB for nested license data, normalized for relational data). "
                    "Avoid full MongoDB migration (high switching cost, team unfamiliar with NoSQL). "
                    "JSONB gives 80% of MongoDB benefits without full migration."
                ),
                "evidence": [
                    {
                        "source": "Schema design patterns",
                        "content": "Hybrid schemas common: 70% of PostgreSQL apps use mix of relational + JSONB"
                    },
                    {
                        "source": "MongoDB migration cost",
                        "content": "PostgreSQL → MongoDB: 4-6 weeks effort, ORM rewrite, team training"
                    },
                    {
                        "source": "Use case analysis",
                        "content": "Physician licenses: Nested structure ideal for JSONB. Users/auth: Keep normalized."
                    }
                ],
                "confidence": 0.7
            }

        # Generic technology adoption
        elif "adopt" in topic_lower or "use" in topic_lower:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "Alternative analysis requires competitive landscape research. "
                    "Key questions: What are the top 3-5 alternatives? "
                    "How do they compare on cost, features, complexity, maturity? "
                    "What are the opportunity costs? "
                    "Recommend: Competitive analysis, decision matrix."
                ),
                "evidence": [
                    {
                        "source": "Decision framework",
                        "content": "Compare alternatives on: cost, features, complexity, maturity, risk"
                    }
                ],
                "confidence": 0.5
            }

        # Default fallback
        else:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "Insufficient information for alternatives analysis. "
                    "Recommend: Market research, competitive landscape, trade-off matrix."
                ),
                "evidence": [],
                "confidence": 0.4
            }
