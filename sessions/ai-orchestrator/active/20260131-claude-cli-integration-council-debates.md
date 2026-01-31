# Session: Claude CLI Integration & Council Debates

**Date**: 2026-01-31
**Project**: AI Orchestrator
**Status**: Complete

---

## Summary

Migrated the Council Pattern debate system from Anthropic API (pay-per-call) to Claude Code CLI (claude.ai subscription-based), then validated the integration by running two LLM-powered architectural debates for CredentialMate.

---

## Completed Tasks

### 1. Claude Code CLI Integration

**Goal**: Replace all Anthropic SDK usage with Claude Code CLI to use claude.ai subscription instead of API keys.

**Files Modified**:
- `agents/coordinator/llm_analyst.py` - Rewrote LLMProvider to use `asyncio.create_subprocess_exec` calling `claude -p`
- `agents/coordinator/llm_debate_agent.py` - Added `_call_claude_cli()` with async subprocess
- `agents/coordinator/rebuttal_agent.py` - Updated model name to `claude-sonnet`
- `agents/coordinator/agent_templates.py` - Updated model names
- `cli/commands/council.py` - Fixed factory signature, updated help text
- `tests/integration/council/test_council_integration.py` - Check for CLI availability instead of ANTHROPIC_API_KEY
- `tests/integration/council/test_llm_analysts.py` - Updated cost assertions for subscription model
- `tests/integration/council/test_advanced_features.py` - Updated model names

**Key Changes**:
- LLMProvider uses `asyncio.create_subprocess_exec` to call `claude -p "prompt" --output-format text`
- Cost tracking changed to virtual costs (flat-rate subscription)
- Model names standardized to `claude-sonnet`, `claude-haiku`, `claude-opus`
- Tests auto-detect Claude CLI availability via `shutil.which("claude")`

**Result**: 96/96 council tests passing

**Commit**: `07db6df` - "refactor: replace Anthropic SDK with Claude Code CLI for LLM integration"

---

### 2. LLM-Powered Council Debates for CredentialMate

Ran two architectural debates using the new Claude CLI integration.

#### Debate 1: Document Storage

**Topic**: Should CredentialMate use S3 with server-side encryption vs PostgreSQL large objects for storing credential documents?

**Context**: HIPAA-compliant healthcare credentialing system with 400+ provider credentials

**Result**:
- **Recommendation**: S3 with SSE-KMS
- **Vote**: 5/5 analysts SUPPORT
- **Confidence**: 85% (all analysts)

**Key Arguments**:
| Analyst | Position | Key Point |
|---------|----------|-----------|
| Performance | SUPPORT | PostgreSQL large objects create query bloat |
| Alternatives | SUPPORT | S3 is industry-standard for HIPAA document storage |
| Cost | SUPPORT | S3 is 5-10x cheaper per GB |
| Security | SUPPORT | SSE-KMS with customer-managed keys is superior |
| Integration | SUPPORT | Better fit for HIPAA healthcare environment |

**Council ID**: `COUNCIL-20260131-212102`

---

#### Debate 2: Notification System

**Topic**: Should CredentialMate adopt a message queue (SQS/RabbitMQ) for credential expiration notifications vs simple cron-based email notifications?

**Context**: 400+ credentials, 46 at-risk, 6 expired needing timely alerts

**Result**:
- **Recommendation**: ADOPT (SQS)
- **Vote**: 4 SUPPORT, 1 NEUTRAL
- **Confidence**: 66.6%

**Key Arguments**:
| Analyst | Position | Key Point |
|---------|----------|-----------|
| Security | SUPPORT | Delivery guarantees & audit trails critical for HIPAA |
| Performance | SUPPORT | Exponential backoff, decoupled processing |
| Alternatives | SUPPORT | Dead-letter queues essential for missed alerts |
| Cost | SUPPORT | SQS ~$2-5/month; ROI from avoiding compliance violations |
| Integration | NEUTRAL | Supports in reasoning, moderate complexity increase |

**Council ID**: `COUNCIL-20260131-212817`

**Commit**: `87a842c` - "feat: add council debate manifests for CredentialMate architecture decisions"

---

## Architecture Decisions for CredentialMate

Based on council debates:

1. **Document Storage**: Use **S3 + SSE-KMS** for credential documents (licenses, certifications)
   - HIPAA compliant with customer-managed encryption keys
   - Scalable, cost-effective for document storage

2. **Notification System**: Adopt **AWS SQS** for expiration notifications
   - Delivery guarantees prevent silent failures
   - Dead-letter queues catch failed notifications
   - Audit trail for HIPAA compliance

---

## Pending Cleanup

Untracked files identified but not yet processed:
- Temp scripts: `generate_business_expense_report*.py`, `reclassify_*.py`, `test_*.py` (root)
- Should commit: `AI-Team-Plans/`, `mcp_integration/`, `sessions/`, `tests/comparison/`, `work/plans-active/`

---

## Next Steps

1. Clean up untracked files (delete temp, commit valuable work)
2. Implement S3 document storage in CredentialMate
3. Implement SQS notification workflow in CredentialMate
4. Record debate outcomes after implementation for effectiveness tracking

---

## Commits This Session

| Commit | Message |
|--------|---------|
| `07db6df` | refactor: replace Anthropic SDK with Claude Code CLI for LLM integration |
| `87a842c` | feat: add council debate manifests for CredentialMate architecture decisions |
