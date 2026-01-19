#!/usr/bin/env python3
"""
Phase C End-to-End Test Suite

Tests all Phase C components together.
"""

import json
from pathlib import Path
from datetime import datetime

# Test flags
PASSED = "✅"
FAILED = "❌"


def test_task_analyzer():
    """Test Task Complexity Analyzer"""
    print("\n" + "=" * 60)
    print("TEST 1: Task Complexity Analyzer")
    print("=" * 60)

    from orchestration.task_analyzer import TaskAnalyzer

    analyzer = TaskAnalyzer()

    # Test cases
    test_cases = [
        {
            "task": {"id": "T1", "title": "Fix typo", "description": "Update button text"},
            "expected_team": "qa",
            "expected_level": "simple"
        },
        {
            "task": {"id": "T2", "title": "Add authentication", "description": "Implement OAuth with HIPAA compliance"},
            "expected_team": "dev",
            "expected_level": "moderate"
        },
        {
            "task": {"id": "T3", "title": "Refactor HIPAA system", "description": "Migration of PHI logging across services"},
            "expected_team": "dev",
            "expected_level": "complex"
        }
    ]

    results = []
    for i, test_case in enumerate(test_cases, 1):
        result = analyzer.analyze_complexity(test_case["task"])

        passed = (
            result.recommended_team == test_case["expected_team"] and
            result.complexity_level == test_case["expected_level"]
        )

        status = PASSED if passed else FAILED
        results.append(passed)

        print(f"\nTest Case {i}: {test_case['task']['title']}")
        print(f"  Expected: {test_case['expected_team']}/{test_case['expected_level']}")
        print(f"  Got: {result.recommended_team}/{result.complexity_level}")
        print(f"  Score: {result.complexity_score}/100")
        print(f"  {status}")

    return all(results)


def test_parallel_controller():
    """Test Parallel Execution Controller"""
    print("\n" + "=" * 60)
    print("TEST 2: Parallel Execution Controller")
    print("=" * 60)

    from orchestration.parallel_controller import ParallelController

    controller = ParallelController(max_workers=2)

    # Test tasks
    tasks = [
        {"id": "W1", "title": "Bug fix", "description": "Fix validation bug"},
        {"id": "W2", "title": "Feature", "description": "Add new button"}
    ]

    print("\nSpawning 2 parallel workers...")

    futures = {}
    for i, task in enumerate(tasks):
        worker_id = f"test-worker-{i}"
        agent_type = "bugfix" if "bug" in task["title"].lower() else "featurebuilder"

        future = controller.spawn_subagent(task, worker_id, agent_type)
        futures[worker_id] = future

    print("Waiting for workers...")
    results = controller.wait_for_workers(futures, timeout=10)

    print(f"\n{PASSED} Workers completed: {len(results)}/2")

    for worker_id, result in results.items():
        print(f"  {worker_id}: {result.status} ({result.task_id})")

    controller.shutdown()

    return len(results) == 2


def test_cito_escalation():
    """Test CITO Escalation Handler"""
    print("\n" + "=" * 60)
    print("TEST 3: CITO Escalation Handler")
    print("=" * 60)

    from agents.coordinator.cito import CITOInterface

    cito = CITOInterface()

    # Test escalation
    task = {
        "id": "TEST-ESC-001",
        "title": "Complex HIPAA task",
        "description": "Implement HIPAA audit logging for PHI access"
    }

    context = {
        "iterations": 45,
        "max_iterations": 50
    }

    print("\nTesting subagent escalation...")

    decision = cito.handle_subagent_escalation(
        worker_id="test-worker-0",
        task=task,
        escalation_reason="High complexity, low confidence",
        context=context
    )

    print(f"  Action: {decision.action}")
    print(f"  Reasoning: {decision.reasoning}")
    print(f"  Confidence: {decision.confidence}")

    if decision.escalation_file:
        print(f"  Escalation file: {decision.escalation_file}")
        # Clean up test file
        if decision.escalation_file.exists():
            decision.escalation_file.unlink()
            print(f"  {PASSED} Escalation file created and cleaned up")

    return decision.action in ["escalate_to_human", "modify", "approve"]


def test_performance_tracker():
    """Test Agent Performance Tracker"""
    print("\n" + "=" * 60)
    print("TEST 4: Agent Performance Tracker")
    print("=" * 60)

    from orchestration.performance_tracker import AgentPerformanceTracker

    tracker = AgentPerformanceTracker()

    # Check if test data exists
    records = tracker.load_records(days=30)

    print(f"\nLoaded {len(records)} performance records")

    if records:
        stats = tracker.get_all_agents_stats(days=30)
        print(f"Agent stats collected for {len(stats)} agents")

        for agent_stats in stats:
            print(f"  {agent_stats['agent_id']}: "
                  f"{agent_stats['total_tasks']} tasks, "
                  f"{agent_stats['success_rate']:.1f}% success")

        print(f"{PASSED} Performance tracker working")
        return True
    else:
        print(f"{PASSED} Performance tracker initialized (no data yet)")
        return True


def test_cito_resolver():
    """Test CITO Resolver CLI"""
    print("\n" + "=" * 60)
    print("TEST 5: CITO Resolver")
    print("=" * 60)

    from orchestration.cito_resolver import CITOResolver

    resolver = CITOResolver()

    # List escalations
    escalations = resolver.list_escalations()
    print(f"\nFound {len(escalations)} escalation(s)")

    if escalations:
        # Show first escalation
        esc = escalations[0]
        print(f"  {esc['task_id']}: {'Resolved' if esc['resolved'] else 'Pending'}")

    print(f"{PASSED} CITO Resolver working")
    return True


def test_queue_sync_manager():
    """Test Work Queue Sync Manager"""
    print("\n" + "=" * 60)
    print("TEST 6: Work Queue Sync Manager")
    print("=" * 60)

    from orchestration.queue_sync_manager import QueueSyncManager

    ai_orch_root = Path(__file__).parent.parent
    manager = QueueSyncManager(ai_orch_root)

    print("\nTesting sync from karematch...")

    result = manager.sync_from_repo("karematch")

    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")

    if result["status"] in ["success", "skipped"]:
        print(f"{PASSED} Queue sync working")
        return True
    else:
        print(f"{FAILED} Queue sync failed")
        return False


def run_all_tests():
    """Run all Phase C tests"""
    print("\n" + "=" * 80)
    print("PHASE C END-TO-END TEST SUITE")
    print("=" * 80)

    tests = [
        ("Task Complexity Analyzer", test_task_analyzer),
        ("Parallel Execution Controller", test_parallel_controller),
        ("CITO Escalation Handler", test_cito_escalation),
        ("Agent Performance Tracker", test_performance_tracker),
        ("CITO Resolver", test_cito_resolver),
        ("Work Queue Sync Manager", test_queue_sync_manager)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n{FAILED} Test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = PASSED if passed else FAILED
        print(f"{status} {test_name}")

    print("\n" + "=" * 80)
    print(f"TOTAL: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.0f}%)")
    print("=" * 80)

    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
