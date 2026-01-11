#!/usr/bin/env python3
"""
Test script for Meta-Agent Integration (v6.0)

Validates that all 3 meta-agents (Governance, PM, CMO) work correctly
with the conditional gate system.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tasks.work_queue import WorkQueue
from adapters.credentialmate import CredentialMateAdapter
from agents.coordinator.governance_agent import GovernanceAgent
from agents.coordinator.product_manager import ProductManagerAgent
from agents.coordinator.cmo_agent import CMOAgent


def test_meta_agent_gates():
    """Test meta-agent gates with 3 diverse tasks."""

    print("="*80)
    print("🧪 Testing Meta-Agent Integration (v6.0)")
    print("="*80)
    print()

    # Load test work queue
    queue_path = Path(__file__).parent / "tasks" / "work_queue_credentialmate_test.json"
    queue = WorkQueue.load(queue_path)

    print(f"📋 Loaded test work queue: {len(queue.features)} tasks\n")

    # Load adapter
    adapter = CredentialMateAdapter()

    # Create meta-agents
    governance_agent = GovernanceAgent(adapter)
    pm_agent = ProductManagerAgent(adapter)
    cmo_agent = CMOAgent(adapter)

    print("🤖 Created all 3 meta-agents\n")

    # Test each task
    for i, task in enumerate(queue.features, 1):
        print(f"\n{'─'*80}")
        print(f"Task {i}/{len(queue.features)}: {task.id}")
        print(f"{'─'*80}\n")
        print(f"Description: {task.description}")
        print(f"Type: {task.type}")
        print(f"Affects user experience: {task.affects_user_experience}")
        print(f"Is GTM-related: {task.is_gtm_related}")
        print(f"Touches PHI code: {task.touches_phi_code}")
        print(f"Evidence refs: {task.evidence_refs}")
        print()

        # Build task_data
        task_data = {
            "type": task.type,
            "files": [task.file],
            "affects_user_experience": task.affects_user_experience,
            "touches_phi_code": task.touches_phi_code,
        }

        print("🛡️  Running meta-agent gates...\n")

        # GATE 1: Governance (ALWAYS runs)
        print("GATE 1: Governance Agent")
        try:
            governance_result = governance_agent.execute(task.id, task.description, task_data)
            print(f"   Decision: {governance_result.decision}")
            print(f"   Risk Level: {governance_result.risk_assessment.risk_level}")
            print(f"   Reason: {governance_result.risk_assessment.reason}")

            if governance_result.decision == "BLOCKED":
                print(f"\n   ❌ BLOCKED by Governance")
                continue
            elif governance_result.decision == "REQUIRES_APPROVAL":
                print(f"\n   ⚠️  REQUIRES APPROVAL (auto-approved in test mode)")
            else:
                print(f"\n   ✅ APPROVED by Governance")
        except Exception as e:
            print(f"\n   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            continue

        print()

        # GATE 2: PM (CONDITIONAL - only if feature OR affects users)
        should_pm_validate = (
            task.type == "feature" or
            task.affects_user_experience
        )

        if should_pm_validate:
            print("GATE 2: Product Manager Agent")
            try:
                pm_result = pm_agent.execute(task.id, task.description, task_data)
                print(f"   Decision: {pm_result.decision}")
                print(f"   Reason: {pm_result.reason}")
                print(f"   Evidence count: {pm_result.evidence_count}")
                print(f"   Roadmap aligned: {pm_result.roadmap_aligned}")
                print(f"   Has outcome metrics: {pm_result.has_outcome_metrics}")

                if pm_result.decision == "BLOCKED":
                    print(f"\n   ❌ BLOCKED by PM")
                    if pm_result.recommendations:
                        print(f"\n   Recommendations:")
                        for rec in pm_result.recommendations:
                            print(f"      - {rec}")
                    continue
                elif pm_result.decision == "MODIFIED":
                    print(f"\n   📝 MODIFIED by PM (added outcome metrics)")
                else:
                    print(f"\n   ✅ APPROVED by PM")
            except Exception as e:
                print(f"\n   ❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
                continue
        else:
            print("GATE 2: Product Manager Agent")
            print("   ⏭️  SKIPPED (not a feature, no user impact)")

        print()

        # GATE 3: CMO (CONDITIONAL - only if GTM-related)
        should_cmo_review = task.is_gtm_related

        if should_cmo_review:
            print("GATE 3: CMO Agent")
            try:
                cmo_result = cmo_agent.execute(task.id, task.description, task_data)
                print(f"   Decision: {cmo_result.decision}")
                print(f"   Reason: {cmo_result.reason}")
                print(f"   Messaging aligned: {cmo_result.messaging_aligned}")
                print(f"   Has demand evidence: {cmo_result.has_demand_evidence}")

                if cmo_result.decision == "PROPOSE_ALTERNATIVE":
                    print(f"\n   ⚠️  CMO PROPOSES ALTERNATIVE")
                    print(f"   Suggested: {cmo_result.proposed_alternative}")
                    if cmo_result.recommendations:
                        print(f"\n   Recommendations:")
                        for rec in cmo_result.recommendations:
                            print(f"      - {rec}")
                else:
                    print(f"\n   ✅ APPROVED by CMO")
            except Exception as e:
                print(f"\n   ❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
                continue
        else:
            print("GATE 3: CMO Agent")
            print("   ⏭️  SKIPPED (not GTM-related)")

        print()
        print("✅ All meta-agent gates passed (or auto-approved)")

    print(f"\n{'='*80}")
    print("🎉 Meta-Agent Integration Test Complete")
    print("="*80)
    print()


if __name__ == "__main__":
    test_meta_agent_gates()
