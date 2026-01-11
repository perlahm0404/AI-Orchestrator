"""
Audit Module

Comprehensive logging with causality tracking.

Every action is logged with:
- Who (agent, session)
- What (action type, details)
- When (timestamp)
- Why (caused_by - links to prior action)

Causality chains allow tracing:
- "Why did this happen?" → Follow caused_by links backward
- "What did this cause?" → Query for actions caused by this one

See: v4 Planning.md Section "Enhanced Audit Schema"
"""
