# Deployment

**Command**: `/deploy`

**Description**: Safe deployment orchestration following Operator team governance

## What This Does

Invokes a structured deployment process with proper gates and verification:

1. **Pre-deployment checks** - Tests, lint, build verification
2. **Environment validation** - Config, secrets, infrastructure ready
3. **Deployment execution** - With rollback preparation
4. **Post-deployment verification** - Health checks, smoke tests
5. **Rollback capability** - Automatic if health checks fail

## Governance

Follows Operator Team autonomy contract (`governance/contracts/operator-team.yaml`):

| Environment | Autonomy Level | Human Approval |
|-------------|---------------|----------------|
| dev | L2 (auto) | Not required |
| staging | L1 (semi-auto) | Required for first deploy |
| prod | L0.5 (manual) | Always required |

## Usage

```bash
# Deploy to dev (auto-approved)
/deploy dev

# Deploy to staging (requires approval)
/deploy staging

# Deploy to production (requires explicit approval)
/deploy prod

# Rollback
/deploy rollback prod

# Check deployment status
/deploy status prod
```

## Pre-Deployment Checklist

Automatically verified before deployment:

### Build
- [ ] All tests passing
- [ ] TypeScript compilation clean
- [ ] ESLint passing
- [ ] Build artifacts generated

### Config
- [ ] Environment variables set
- [ ] Secrets available (not values, just presence)
- [ ] Infrastructure IDs verified
- [ ] Domain/DNS configured

### Safety
- [ ] Rollback plan documented
- [ ] Previous deployment backup
- [ ] Health check endpoints ready
- [ ] Monitoring alerts configured

## Environment-Specific Commands

### CredentialMate Frontend (SST)
```bash
cd /Users/tmac/1_REPOS/credentialmate/apps/frontend-web
npx sst deploy --stage {env}  # dev, staging, or prod
```

### KareMatch (Turborepo)
```bash
cd /Users/tmac/1_REPOS/karematch
pnpm deploy:{env}
```

## Post-Deployment

- **Health checks** - HTTP 200 from health endpoints
- **Smoke tests** - Core user flows verified
- **Metrics check** - Error rate within threshold
- **Notification** - Slack/email on success/failure

## Rollback

If post-deployment checks fail:
1. Automatic rollback initiated
2. Previous version restored
3. Failure report generated
4. Incident created for analysis

## Output

- **Deployment report** with timing and verification results
- **CloudFront/infrastructure IDs** for reference
- **Health check results**
- **Rollback status** if triggered

## Integration

Uses MCP servers:
- `git` - Tag and track deployments
- `fetch` - Health check endpoints
- `time` - Deployment timing and windows

## Related

- `/code-review` - Run before deployment
- `docs/INFRASTRUCTURE.md` - Infrastructure details
- `governance/contracts/operator-team.yaml` - Operator autonomy
