"""
Knowledge Objects Module

Durable semantic memory that captures institutional learning from resolved issues.

Episodic memory (audit_log) explains *what happened*.
Knowledge Objects explain *what must never be forgotten*.

Lifecycle:
1. Issue resolved with RESOLVED_FULL status
2. Agent drafts Knowledge Object (knowledge/drafts/)
3. Human approves/edits/skips
4. Approved KO moves to knowledge/approved/ and Postgres

See: v4-KNOWLEDGE-OBJECTS-v1.md for full specification
"""
