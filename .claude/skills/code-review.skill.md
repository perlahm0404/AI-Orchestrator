# Code Review

**Command**: `/code-review`

**Description**: Conduct thorough code review using QA team standards and Ralph verification

## What This Does

Invokes a structured code review process following QA team governance:

1. **Static analysis** - ESLint, TypeScript, security patterns
2. **Test coverage** - Verify tests exist and pass
3. **Ralph verification** - Run full verification pipeline
4. **Knowledge Object check** - Query relevant KOs for learned patterns
5. **OWASP review** - Check for security vulnerabilities

## Capabilities

- **Analyzes** diffs, commits, or file ranges
- **Runs** automated tools (lint, typecheck, tests)
- **Queries** Knowledge Objects for past learnings
- **Generates** structured review report
- **Suggests** fixes with confidence scores

## Usage

```bash
# Review staged changes
/code-review

# Review specific commit
/code-review commit abc1234

# Review specific files
/code-review src/services/auth.ts src/utils/crypto.ts

# Review PR (if on feature branch)
/code-review pr
```

## Review Checklist

The skill automatically checks:

### Security (OWASP Top 10)
- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all external data
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (proper escaping)
- [ ] Authentication/authorization checks

### Code Quality
- [ ] TypeScript strict mode compliance
- [ ] No `any` types without justification
- [ ] Error handling present
- [ ] No console.log in production code
- [ ] Proper async/await usage

### Testing
- [ ] Unit tests for new functions
- [ ] Edge cases covered
- [ ] Mocks properly scoped
- [ ] No flaky test patterns

### Performance
- [ ] No N+1 queries
- [ ] Proper caching patterns
- [ ] No memory leaks (listeners cleaned up)

## Output

- **Review report** with findings by severity (P0/P1/P2)
- **Ralph verdict** (PASS/FAIL/BLOCKED)
- **Suggested fixes** with code snippets
- **KO references** for relevant patterns

## Integration

Uses the following MCP servers:
- `git` - For diff and commit analysis
- `memory` - Query learned patterns
- `sequential-thinking` - Structured analysis

## Related

- `/deploy` - For deployment after review passes
- `aibrain ko search --tags code-review,security` - Query patterns
- `governance/contracts/qa-team.yaml` - QA team autonomy contract
