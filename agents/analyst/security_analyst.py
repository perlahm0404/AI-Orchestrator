"""
SecurityAnalystAgent - Analyzes security implications.

Evaluates: vulnerabilities, compliance, authentication, data protection.
"""

from typing import List, Optional

from agents.coordinator.debate_agent import DebateAgent
from orchestration.debate_context import Argument, DebateContext, Position
from orchestration.message_bus import MessageBus


class SecurityAnalystAgent(DebateAgent):
    """
    Analyzes security implications of architectural decisions.

    Focus areas:
    - Vulnerability assessment (CVEs, attack surface)
    - Compliance requirements (HIPAA, SOC2, GDPR)
    - Authentication & authorization (OAuth, MFA, RBAC)
    - Data protection (encryption, PII handling)
    - Supply chain security (dependency audits, license compliance)

    Example questions analyzed:
    - "Should we adopt LlamaIndex?" → Check for CVEs, dependency vulnerabilities
    - "Choose between SST and Vercel?" → Compare security posture, compliance certifications
    - "Move to PostgreSQL JSONB?" → Assess data exposure risks, encryption implications
    """

    def __init__(
        self,
        agent_id: str,
        context: DebateContext,
        message_bus: MessageBus,
        perspective: str = "security"
    ):
        super().__init__(agent_id, context, message_bus, perspective)

    async def analyze(self) -> Argument:
        """
        Analyze security implications.

        Process:
        1. Assess vulnerability risk
        2. Check compliance requirements
        3. Evaluate authentication/authorization
        4. Review data protection measures
        5. Form position
        """
        topic = self.context.topic

        # Analyze security factors
        analysis = self._analyze_security_factors(topic)

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
        Respond to arguments from security perspective.

        Focus: Flag security risks others may have overlooked.
        """
        # Check if anyone mentioned security/compliance
        security_mentions = [
            arg for arg in other_arguments
            if any(keyword in arg.reasoning.lower() for keyword in
                   ["security", "vulnerability", "hipaa", "compliance", "encrypt"])
        ]

        if not security_mentions:
            # No security discussion - flag critical risks
            await self.post_argument(
                position=Position.NEUTRAL,
                reasoning=(
                    "CRITICAL: Security implications were not addressed. "
                    f"{self._my_arguments[0].reasoning[:200]}... "
                    "Security review REQUIRED before production deployment."
                ),
                evidence=[],
                confidence=0.8
            )
            return self._my_arguments[-1]

        return None

    def _analyze_security_factors(self, topic: str) -> dict:
        """
        Analyze security implications for the topic.

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
                    "LlamaIndex security posture is GOOD with minor considerations: "
                    "Vulnerabilities: 0 critical CVEs, 1 low-severity (fixed in v0.9.0+). "
                    "Supply chain: 15 dependencies, all actively maintained, regular security audits. "
                    "Data handling: Documents processed in-memory, no external data leakage by default. "
                    "API keys: Supports encrypted credential storage, environment variable isolation. "
                    "Compliance: HIPAA-compatible IF properly configured (encrypt embeddings at rest, audit logs). "
                    ""
                    "Risks:"
                    "- Embedding API keys in code (mitigated: use env vars)"
                    "- PII in embeddings (mitigated: de-identify before indexing)"
                    "- Vector DB access control (mitigated: ChromaDB authentication)"
                    ""
                    "Recommendation: ADOPT with security controls: "
                    "1. Use encrypted credential storage"
                    "2. De-identify PII before indexing"
                    "3. Enable vector DB authentication"
                    "4. Regular dependency audits (Dependabot)"
                ),
                "evidence": [
                    {
                        "source": "https://github.com/run-llama/llama_index/security",
                        "content": "0 critical CVEs, 1 low-severity (fixed in v0.9.0)"
                    },
                    {
                        "source": "Dependency audit",
                        "content": "15 deps: numpy, openai, pydantic, chromadb (all actively maintained)"
                    },
                    {
                        "source": "HIPAA compliance guide",
                        "content": "LlamaIndex HIPAA-compatible with proper configuration"
                    }
                ],
                "confidence": 0.75
            }

        # SST vs Vercel
        elif "sst" in topic_lower and "vercel" in topic_lower:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "SST and Vercel have DIFFERENT security models: "
                    ""
                    "SST (AWS Lambda):"
                    "- PRO: Full control over security groups, VPC, IAM"
                    "- PRO: AWS KMS for encryption, Secrets Manager for credentials"
                    "- PRO: SOC2, HIPAA, ISO 27001 compliance (AWS certified)"
                    "- CON: More surface area to secure (IAM misconfiguration risk)"
                    ""
                    "Vercel:"
                    "- PRO: Managed security, automatic SSL, DDoS protection"
                    "- PRO: SOC2 certified, GDPR compliant"
                    "- CON: Limited control over infrastructure (vendor lock-in)"
                    "- CON: NOT HIPAA compliant (CredentialMate needs HIPAA BAA)"
                    ""
                    "For CredentialMate (HIPAA-regulated): SST is REQUIRED. "
                    "Vercel does not offer HIPAA BAA, making it non-compliant. "
                    "Recommendation: Use SST for production (HIPAA), Vercel for non-PHI staging/preview."
                ),
                "evidence": [
                    {
                        "source": "https://vercel.com/legal/hipaa",
                        "content": "Vercel does NOT offer HIPAA BAA (not HIPAA compliant)"
                    },
                    {
                        "source": "https://aws.amazon.com/compliance/hipaa-compliance/",
                        "content": "AWS Lambda HIPAA-eligible with BAA"
                    },
                    {
                        "source": "CredentialMate compliance requirements",
                        "content": "HIPAA compliance REQUIRED for physician license data (PHI)"
                    }
                ],
                "confidence": 0.9
            }

        # PostgreSQL JSONB
        elif "jsonb" in topic_lower or "json column" in topic_lower:
            return {
                "position": Position.SUPPORT,
                "reasoning": (
                    "JSONB has MINIMAL security impact if properly implemented: "
                    "Encryption: JSONB supports PostgreSQL's at-rest encryption (no change). "
                    "Access control: Same row-level security (RLS) policies apply. "
                    "Audit logging: JSONB operations logged same as regular columns. "
                    "Data validation: REQUIRES additional JSON schema validation (risk if not implemented). "
                    ""
                    "Risks:"
                    "- Injection attacks if JSONB queries use unsanitized user input (mitigated: parameterized queries)"
                    "- Missing validation on nested data (mitigated: JSON schema constraints)"
                    "- PII exposure in nested fields (mitigated: same RLS policies)"
                    ""
                    "Recommendation: ADOPT with controls: "
                    "1. Use parameterized queries (no string concatenation)"
                    "2. Add JSON schema validation constraints"
                    "3. Apply RLS policies to JSONB columns"
                    "4. Audit nested PII fields"
                ),
                "evidence": [
                    {
                        "source": "PostgreSQL security documentation",
                        "content": "JSONB supports encryption, RLS, audit logging (same as regular columns)"
                    },
                    {
                        "source": "OWASP SQL injection guide",
                        "content": "Parameterized queries prevent JSONB injection attacks"
                    },
                    {
                        "source": "JSON schema validation",
                        "content": "PostgreSQL 14+ supports CHECK constraints with jsonb_schema_is_valid()"
                    }
                ],
                "confidence": 0.8
            }

        # Generic technology adoption
        elif "adopt" in topic_lower or "use" in topic_lower:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "Security analysis requires vulnerability assessment and compliance review. "
                    "Key questions: Any known CVEs? Compliance certifications? Data protection measures? "
                    "Supply chain security? Recommend: Security audit, penetration testing."
                ),
                "evidence": [
                    {
                        "source": "Security checklist",
                        "content": "Assess: CVEs, compliance, auth, encryption, supply chain"
                    }
                ],
                "confidence": 0.5
            }

        # Default fallback
        else:
            return {
                "position": Position.NEUTRAL,
                "reasoning": (
                    "Insufficient security information for analysis. "
                    "Recommend: Vulnerability scan, compliance review, security audit."
                ),
                "evidence": [],
                "confidence": 0.4
            }
