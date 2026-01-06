"""
AI Orchestrator Tests

Test categories:
- governance/: Governance and safety tests
  - test_negative_capabilities.py: Prove safety systems work
- agents/: Agent behavior tests
- integration/: End-to-end tests

Key test principle: Negative capability tests prove that
forbidden actions are actually blocked. A passing test
suite means nothing if we haven't proven what CAN'T happen.

See: v4 Planning.md Section "Negative Capability Tests"
"""
