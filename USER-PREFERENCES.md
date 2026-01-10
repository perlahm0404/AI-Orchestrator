# User Preferences (tmac)

**Last Updated**: 2026-01-10
**Purpose**: Working preferences, communication style, and decision-making patterns for tmac

> **For AI Agents**: Read this file on session start to understand tmac's working style and preferences.

---

## 🎯 Core Working Principles

### High-Level Philosophy

| Principle | Description |
|-----------|-------------|
| **Evidence-Based** | Decisions backed by data, tests, and Ralph verification |
| **Iterate Fast** | Ship working code quickly, iterate based on feedback |
| **Autonomous First** | Prefer agents handle tasks; human review at checkpoints |
| **Document Everything** | Institutional memory survives sessions via externalized artifacts |
| **Quality Gates** | Ralph PASS required, no shortcuts (never `--no-verify`) |

### Decision-Making Style

- **Bias toward action**: Prefer "try and adjust" over "analyze forever"
- **Comfort with ambiguity**: Start with 80% clarity, refine as you go
- **Trust but verify**: Approve agent work after Ralph PASS, but spot-check key changes
- **Long-term thinking**: Optimize for maintainability and scale, not just "works now"

---

## 💬 Communication Preferences

### Tone & Style

| Aspect | Preference |
|--------|------------|
| **Formality** | Casual, direct, no corporate jargon |
| **Brevity** | Concise summaries preferred (bullet points > paragraphs) |
| **Emojis** | Yes, use them for quick visual parsing (✅, 🔄, 🚫, etc.) |
| **Technical Depth** | High - assume deep technical knowledge, skip basics |

### Response Format

**Good**:
```
✅ Task complete: Fixed authentication timeout
- Modified: src/auth/session.ts:42
- Tests: All passing (15/15)
- Ralph: PASS

Next: Commit and create PR?
```

**Bad**:
```
I have successfully completed the task you assigned to me. The authentication
timeout issue has been resolved through careful analysis and implementation of
a robust solution. I modified the session management logic in the authentication
module. All test cases are now passing. The Ralph verification system has
confirmed that the changes meet all quality standards.

Would you like me to proceed with creating a git commit and pull request?
```

**Prefer**: Actionable summaries with clear next steps.

---

## 🛠️ Technical Preferences

### Code Style

| Aspect | Preference |
|--------|------------|
| **Languages** | TypeScript > JavaScript, Python 3.11+ |
| **Type Safety** | Strict mode preferred, avoid `any` |
| **Testing** | TDD-friendly, 80%+ coverage target |
| **Comments** | Code should be self-documenting; comments for "why", not "what" |
| **Naming** | Descriptive over clever (e.g., `getUserCredentials` not `fetch`) |

### Architecture

- **Modular**: Small, focused files over monoliths
- **Separation of Concerns**: Clear boundaries (UI, business logic, data)
- **DRY (Don't Repeat Yourself)**: Abstract common patterns, but don't over-engineer
- **YAGNI (You Aren't Gonna Need It)**: Build for current needs, not hypothetical futures

### Tools & Stack

| Category | Preferred |
|----------|-----------|
| **Backend** | FastAPI, Node.js/Express |
| **Frontend** | Next.js 14+, React |
| **Database** | PostgreSQL |
| **ORM** | Drizzle (Node), SQLAlchemy 2.0 (Python) |
| **Testing** | Vitest (unit), Playwright (E2E) |
| **CI/CD** | GitHub Actions |
| **Monorepo** | Turborepo |

---

## 📋 Workflow Preferences

### Session Flow

1. **Start with context**: Read STATE.md, DECISIONS.md, sessions/latest.md
2. **Plan briefly**: 1-2 minute overview, not 10-minute detailed plan
3. **Iterate quickly**: Ship working code fast, refine in next iteration
4. **Document at checkpoints**: Update STATE.md on significant milestones
5. **End with handoff**: Create session summary for next session

### Work Breakdown

| Task Size | Approach |
|-----------|----------|
| **Small (<30 min)** | Just do it, no planning needed |
| **Medium (30 min - 2 hrs)** | Brief bullet-point plan, then execute |
| **Large (2+ hrs)** | Use TodoWrite, break into subtasks, track progress |

### Approval Checkpoints

**Auto-Approve (Agent decides)**:
- Lint fixes (ESLint, Prettier)
- Type error fixes (non-breaking)
- Test fixes (flaky tests, missing assertions)
- Documentation updates

**Require Approval**:
- Schema changes (migrations)
- New dependencies
- Breaking API changes
- Security-sensitive code (auth, permissions)
- Deployment config changes

---

## 🔍 Quality Standards

### Ralph Verification

- **PASS**: Required for all changes
- **FAIL**: Fix the issue, don't bypass
- **BLOCKED**: Ask human (R/O/A decision)
- **Never**: Use `--no-verify` or `-n` flags

### Test Coverage

| Type | Minimum | Target |
|------|---------|--------|
| **Unit** | 70% | 80% |
| **Integration** | 50% | 70% |
| **E2E** | Critical paths only | Happy path + error cases |

### Code Review Focus

When reviewing agent work, tmac checks:
1. **Ralph PASS?** (blocking issue)
2. **Tests added/updated?** (required for behavior changes)
3. **Breaking changes?** (requires explicit callout)
4. **Security implications?** (auth, validation, data exposure)

---

## 🚀 Project-Specific Preferences

### CredentialMate (L1 Autonomy)

- **Compliance First**: HIPAA requirements non-negotiable
- **Audit Trails**: Log all PHI access
- **Security**: Encrypt at rest and in transit
- **Conservative Changes**: Max 50 lines, max 5 files
- **Human Approval**: Required for schema, API, dependencies

### KareMatch (L2 Autonomy)

- **Move Fast**: Higher risk tolerance
- **Iterate Publicly**: Ship to staging frequently
- **User Feedback**: Real-world testing over perfect planning
- **Moderate Changes**: Max 100 lines, max 10 files
- **Human Approval**: Required for breaking changes only

### AI_Orchestrator (Core)

- **Dogfood**: Use the system to improve itself
- **Document Learnings**: Every session → Knowledge Objects
- **Governance**: Contracts and guardrails are sacred
- **Meta-Improvement**: Optimize autonomy metrics continuously

---

## 🎨 Documentation Preferences

### Format

- **Markdown**: All docs in Markdown
- **Structure**: Clear headings, tables for comparisons
- **Brevity**: 1-2 pages max for most docs
- **Visuals**: Diagrams (mermaid) for architecture, tables for data

### Naming Conventions

| Document Type | Format | Example |
|---------------|--------|---------|
| **Session** | `YYYY-MM-DD-description.md` | `2026-01-10-reports-api-complete.md` |
| **Plan** | `description-plan.md` | `cme-systemic-fix-plan.md` |
| **ADR** | `ADR-NNN-description.md` | `ADR-001-provider-report-generation.md` |
| **KO** | `KO-{project}-NNN.md` | `KO-km-001.md` |

### Mission Control - Desktop Command Center 🚀

**Location**: `~/Desktop/Mission-Control/`

**Purpose**: Single protected folder with symlinks to all critical documentation. No desktop clutter, just one folder to protect.

**What's in Mission Control**:
| File | Priority | Purpose |
|------|----------|---------|
| CATALOG.md | 1 | Master documentation index |
| STATE.md | 1 | Current implementation status |
| ROADMAP.md | 2 | Future features roadmap |
| USER-PREFERENCES.md | 2 | tmac's working preferences |
| DECISIONS.md | 2 | Build decisions with rationale |
| latest-session.md | 3 | Most recent session handoff |

**Priority Levels**:
| Level | Meaning | Action |
|-------|---------|--------|
| **1** | Critical - Always accessible | NEVER remove, archive, or move |
| **2** | High - Keep unless major cleanup | Require explicit approval to move |
| **3** | Medium - Optional but recommended | Can be cleaned up with notice |

**Cleanup Policy** (CRITICAL for AI Agents):
- **NEVER** archive, move, or delete `~/Desktop/Mission-Control/`
- **NEVER** remove files from Mission-Control folder
- **ALWAYS** check `.desktop-pins.json` before cleanup operations
- **ASK** tmac before modifying Mission-Control contents

**Adding Files to Mission Control**:
```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator
ln -sf "$(pwd)/NEW_FILE.md" ~/Desktop/Mission-Control/NEW_FILE.md
# Update .desktop-pins.json
```

### Documentation Triggers

**Update STATE.md** when:
- Milestone reached (feature complete, tests passing)
- Blocker identified (stuck, need human decision)
- Implementation state changes (pending → in-progress → complete)

**Create Session Handoff** when:
- Session ending (>30 min of work done)
- Significant progress (task completed, tests passing)
- Blocked (human input needed before continuing)

---

## ⏰ Time Preferences

### Session Length

| Duration | Type | Notes |
|----------|------|-------|
| **15-30 min** | Quick fix | Single bug, small change |
| **1-2 hrs** | Feature work | New endpoint, UI component |
| **2-4 hrs** | Complex feature | Multi-file changes, testing |
| **4+ hrs** | Autonomous loop | Agent runs unattended |

### Availability

- **Peak productivity**: Afternoons (1pm-6pm PST)
- **Async work**: Autonomous loops overnight
- **Immediate response needed**: Rarely - most work can wait 1-2 hours

---

## 🤖 Agent Collaboration

### What Agents Should Do

- **Proactive**: Suggest next steps, identify blockers
- **Transparent**: Show reasoning, explain decisions
- **Self-Correcting**: Iterate on failures, don't give up
- **Context-Aware**: Read STATE.md, DECISIONS.md, sessions/latest.md

### What Agents Should NOT Do

- **Assume Requirements**: Ask when unclear
- **Bypass Quality Gates**: Never `--no-verify`, always Ralph PASS
- **Over-Engineer**: Build for today's needs, not hypothetical futures
- **Hide Failures**: Report blockers immediately

### Escalation Triggers

**Ask human when**:
- Ralph BLOCKED (guardrail violation)
- Multiple approaches failed (3+ iterations, no progress)
- Ambiguous requirements (unclear what "done" looks like)
- Breaking changes (requires strategic decision)

---

## 📊 Metrics & Reporting

### What tmac Tracks

| Metric | Frequency | Tool |
|--------|-----------|------|
| **Autonomy %** | Weekly | `aibrain status` |
| **Ralph PASS Rate** | Per session | Session handoffs |
| **KO Effectiveness** | Monthly | `aibrain ko metrics` |
| **Cost (API usage)** | Monthly | CloudWatch |

### Reporting Format

**Prefer**:
```
Week of 2026-01-06:
- Autonomy: 87% → 89% (+2%)
- Tasks completed: 45
- Ralph PASS rate: 78%
- Top blocker: E2E tests (flaky Playwright setup)
```

**Not**:
Long prose reports with background, analysis, and recommendations.

---

## 🔄 Continuous Improvement

### Learning from Sessions

After each session, tmac reviews:
1. **What worked well?** (capture in KOs)
2. **What blocked progress?** (fix or document)
3. **What can be automated?** (improve autonomy)

### Feedback Loop

- **Positive feedback**: "Great work, approved" (brief)
- **Constructive feedback**: Specific, actionable (e.g., "Add type annotations to new functions")
- **Blocking feedback**: Clear rationale, suggest alternative (e.g., "Reject: Schema change needs migration plan first")

---

## 📝 Examples

### Good Session Interaction

**Agent**:
```
Reading STATE.md... CredentialMate reports feature at 80%.
Reading sessions/latest.md... Last session blocked on E2E provider error.

Plan:
1. Debug provider creation in test setup
2. Fix E2E test
3. Run full test suite
4. Update STATE.md if passing

Starting task 1...
```

**tmac**: _(no response needed - agent proceeds autonomously)_

**Agent** (later):
```
✅ All tasks complete
- Fixed: test setup provider creation
- Tests: 12/12 passing (was 0/12)
- Ralph: PASS
- Updated: STATE.md (80% → 90%)

Next: Create PR for ADR-001 backend phase?
```

**tmac**: "Approved, create PR"

### Bad Session Interaction

**Agent**:
```
Hello! I'm ready to assist you with your software development tasks today.
Before we begin, I'd like to understand the full scope of what you'd like to
accomplish. Could you please provide a detailed description of your requirements
and any constraints I should be aware of?
```

**tmac**: _(Frustrated - agent should read STATE.md/sessions/latest.md and just start)_

---

## 🆘 When in Doubt

**Agent unsure?**
1. Check STATE.md for current status
2. Check DECISIONS.md for past decisions
3. Check USER-PREFERENCES.md (this file) for working style
4. Check sessions/latest.md for recent context
5. Still unclear? Ask tmac with specific question

**tmac unsure?**
1. Review session handoff
2. Check Ralph output
3. Spot-check key files
4. Ask agent for summary if needed

---

## 📚 Related Documents

- [CATALOG.md](./CATALOG.md) - Master documentation index
- [STATE.md](./STATE.md) - Current implementation status
- [DECISIONS.md](./DECISIONS.md) - Build decisions
- [CLAUDE.md](./CLAUDE.md) - Project instructions

---

**Maintained by**: tmac
**Last Updated**: 2026-01-10
**Review Frequency**: Quarterly (or when patterns change)
