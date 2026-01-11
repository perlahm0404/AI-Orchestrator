#!/usr/bin/env python3
"""
Invoke Governance Agent to assess documentation validation system

This assesses the three-layer documentation governance system we just implemented:
- Git pre-commit hook
- CLI validator
- Ralph integration
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.coordinator.governance_agent import GovernanceAgent
from adapters import get_adapter

def main():
    print("=" * 70)
    print("🛡️  GOVERNANCE AGENT ASSESSMENT")
    print("=" * 70)
    print("\nAssessing: Documentation Validation & Governance System (ADR-010)")
    print()

    # Initialize adapter (uses default KareMatch for governance tasks)
    adapter = get_adapter()

    # Initialize governance agent
    agent = GovernanceAgent(app_adapter=adapter)

    # Task description
    task_id = "DOC-VALIDATION-001"
    task_description = """
Implement three-layer documentation validation and governance system:

**Layer 1: Git Pre-Commit Hook**
- File: governance/hooks/pre-commit-documentation
- Blocks commits with invalid file locations or missing frontmatter
- Validates naming conventions for ADRs, plans, queues
- Checks SOC2/ISO compliance metadata

**Layer 2: CLI Validator**
- File: governance/validators/documentation_validator.py
- Comprehensive audit of entire repository
- Validates frontmatter completeness (doc-id, compliance.*, project, domain)
- HIPAA classification check (CredentialMate = 'confidential')
- Auto-fix capability (planned)

**Layer 3: Ralph Integration**
- File: ralph/checkers/documentation_checker.py
- Integrates with PASS/FAIL/BLOCKED system
- Runs pre-merge, cannot be bypassed
- Blocks PRs with incomplete documentation

**Risk Factors**:
- Modifies governance system (meta-governance)
- Adds new git hooks (developer workflow impact)
- Blocks commits/merges (potential friction)
- Infrastructure change (validation pipeline)
- HIPAA compliance validation (classification checks)

**Files Modified**:
- governance/hooks/pre-commit-documentation
- governance/validators/documentation_validator.py
- ralph/checkers/documentation_checker.py
- governance/DOCUMENTATION-GOVERNANCE.md
- governance/install-hooks.sh
"""

    task_data = {
        "task_type": "infrastructure",
        "touches_phi_code": False,
        "files": [
            "governance/hooks/pre-commit-documentation",
            "governance/validators/documentation_validator.py",
            "ralph/checkers/documentation_checker.py",
            "governance/DOCUMENTATION-GOVERNANCE.md",
            "governance/install-hooks.sh"
        ]
    }

    # Execute assessment
    result = agent.execute(task_id, task_description, task_data)

    # Display results
    print("\n" + "=" * 70)
    print("📊 ASSESSMENT RESULTS")
    print("=" * 70)
    print(f"\n🎯 Decision: {result.decision}")
    print(f"⚠️  Risk Level: {result.risk_assessment.risk_level}")
    print(f"📝 Reason: {result.risk_assessment.reason}")

    print(f"\n🔍 Risk Breakdown:")
    print(f"   PHI Risk: {'✅ YES' if result.risk_assessment.phi_risk else '❌ NO'}")
    print(f"   Auth Risk: {'✅ YES' if result.risk_assessment.auth_risk else '❌ NO'}")
    print(f"   Billing Risk: {'✅ YES' if result.risk_assessment.billing_risk else '❌ NO'}")
    print(f"   Infrastructure Risk: {'✅ YES' if result.risk_assessment.infra_risk else '❌ NO'}")
    print(f"   State Expansion: {'✅ YES' if result.risk_assessment.state_expansion else '❌ NO'}")

    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"   {i}. {rec}")

    print(f"\n✅ Requires Human Approval: {'YES' if result.risk_assessment.requires_approval else 'NO'}")

    print("\n" + "=" * 70)
    print("🎯 NEXT STEPS")
    print("=" * 70)

    if result.decision == "REQUIRES_APPROVAL":
        print("\n⚠️  Human approval required before proceeding")
        print("\nQuestions for approval:")
        print("  1. Should we create ADR-011 for the validation system?")
        print("  2. Should we install the git hooks now?")
        print("  3. Should we add CI/CD integration?")
        print("  4. Should we expand validation to catch more edge cases?")
    elif result.decision == "APPROVED":
        print("\n✅ System approved - proceed with deployment")
        print("\nSuggested actions:")
        print("  1. Create ADR-011 documenting the validation architecture")
        print("  2. Install git hooks: ./governance/install-hooks.sh")
        print("  3. Run full validation: python governance/validators/documentation_validator.py --report")
        print("  4. Update DECISIONS.md with D-023 entry")
    else:
        print("\n🚫 System blocked - address issues before proceeding")

    print("\n" + "=" * 70)

    return result

if __name__ == "__main__":
    result = main()

    # Exit with appropriate code
    if result.decision == "BLOCKED":
        sys.exit(1)
    elif result.decision == "REQUIRES_APPROVAL":
        sys.exit(2)
    else:
        sys.exit(0)
