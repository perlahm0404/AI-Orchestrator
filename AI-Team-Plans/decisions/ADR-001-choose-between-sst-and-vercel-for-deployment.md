# ADR 001: Choose between SST and Vercel for deployment

**Status**: Proposed
**Date**: 2026-01-31
**Decision Type**: Strategic
**Council ID**: TEST-ADR-SST-001

## Context

CredentialMate needs to choose deployment platform.

## Council Debate Summary

**Topic**: Choose between SST and Vercel for deployment?

**Perspectives Analyzed**: 3 (alternatives, cost, integration, performance, security)

**Debate Duration**: 0.0 seconds

**Rounds**: 3

### Vote Breakdown

| Position | Count | Percentage |
|----------|-------|------------|
| NEUTRAL | 4 | 80.0% |
| OPPOSE | 1 | 20.0% |
| SUPPORT | 0 | 0.0% |

### Agent Positions

### Alternatives Analysis (NEUTRAL)
**Confidence**: 0.70

Important alternatives were not evaluated. SST and Vercel are TWO options among several: 1. SST: AWS-native, full control, infrastructure-as-code2. Vercel: Managed platform, zero-config, higher cost3. Netlify: Similar to Vercel, slightly cheaper, less polished4. AWS Amplify: AWS-managed, simi... Recommend comparing against alternatives before final decision.

### Cost Analysis (NEUTRAL)
**Confidence**: 0.70

Important cost considerations were not addressed by other perspectives. Initial cost analysis: SST is infrastructure-as-code with AWS direct pricing (no markup). Vercel charges 20-30% markup on compute/bandwidth. For CredentialMate scale (~10K r... Recommend cost-benefit analysis before final decision.

### Integration Analysis (OPPOSE)
**Confidence**: 0.70

SST integration complexity is HIGH for current team. Team has limited AWS/CDK experience (mostly used Vercel/Netlify). SST requires learning: AWS CDK, CloudFormation, Lambda configurations. Estimated learning curve: 2-3 weeks. Vercel integration is trivial: git push to deploy. Trade-off: Vercel higher cost but zero integration friction. Recommendation: Stick with Vercel unless team invests in AWS upskilling.

**Evidence**:
- Team DevOps skills
- https://sst.dev/docs
- Deployment history

### Performance Analysis (NEUTRAL)
**Confidence**: 0.70

Performance implications were not addressed by other perspectives. Key findings: SST and Vercel have SIMILAR performance characteristics. Cold start times: SST (Lambda) ~200-500ms, Vercel (Edge) ~50-150ms. Warm request latency: Both ~20-50ms. CDN performance: Both use CloudFront/E... Recommend load testing before production deployment.

### Security Analysis (NEUTRAL)
**Confidence**: 0.80

CRITICAL: Security implications were not addressed. SST and Vercel have DIFFERENT security models: SST (AWS Lambda):- PRO: Full control over security groups, VPC, IAM- PRO: AWS KMS for encryption, Secrets Manager for credentials- PRO: SOC2, HIPAA, ISO ... Security review REQUIRED before production deployment.


## Decision

**Recommendation**: SPLIT

**Confidence**: 0.58

## Key Considerations

- Integration concern: SST integration complexity is HIGH for current team. Team has limited AWS/CDK experience (mostly used Vercel/Netlify). SST requires learning: AWS CDK,
- Security trade-off: CRITICAL: Security implications were not addressed. SST and Vercel have DIFFERENT security models: SST (AWS Lambda):- PRO: Full control over security 

## Consequences

### Positive
- **Cost**: SST is infrastructure-as-code with AWS direct pricing (no markup)

### Negative
- **Integration**: SST integration complexity is HIGH for current team

### Risks
- **Security**: SST and Vercel have DIFFERENT security models: SST (AWS Lambda):- PRO: Full control over security groups, VPC, IAM- PRO: AWS KMS for encryption, Secrets Manager for credentials- PRO: SOC2, HIPAA, ISO 27001 compliance (AWS certified)- CON: More surface area to secure (IAM misconfiguration risk)Vercel:- PRO: Managed security, automatic SSL, DDoS protection- PRO: SOC2 certified, GDPR compliant- CON: Limited control over infrastructure (vendor lock-in)- CON: NOT HIPAA compliant (CredentialMate needs HIPAA BAA)For CredentialMate (HIPAA-regulated): SST is REQUIRED

## Implementation Notes

- Recommendation: Stick with Vercel unless team invests in AWS upskilling
- Railway: Heroku-like, simple but limited scaleTrade-offs:- SST: Best cost, highest control, steepest learning curve- Vercel: Best DX, fastest setup, highest cost- Netlify: Middle ground on cost/complexity- Amplify: AWS ecosystem, but less control than SSTRecommendation: Vercel IF team time is constrained (learning curve cost > platform cost)
- Recommend comparing against alternatives before final decision

## Alternatives Considered

SST and Vercel are TWO options among several: 1. SST: AWS-native, full control, infrastructure-as-code2. Vercel: Managed platform, zero-config, higher cost3. Netlify: Similar to Vercel, slightly cheaper, less polished4. AWS Amplify: AWS-managed, similar to SST but less flexible5. Railway: Heroku-like, simple but limited scaleTrade-offs:- SST: Best cost, highest control, steepest learning curve- Vercel: Best DX, fastest setup, highest cost- Netlify: Middle ground on cost/complexity- Amplify: AWS ecosystem, but less control than SSTRecommendation: Vercel IF team time is constrained (learning curve cost > platform cost). SST IF team has AWS capacity and cost optimization is priority. For CredentialMate's small scale, Vercel's simplicity outweighs cost difference.

## Debate Audit Trail

Full debate manifest: `.aibrain/councils/TEST-ADR-SST-001/manifest.jsonl`

Timeline: `9 total arguments (R2: 5 args, R3: 4 args)`

---

**Council Participants**:
- `alternatives_analyst` (Alternatives Analyst)
- `cost_analyst` (Cost Analyst)
- `integration_analyst` (Integration Analyst)
- `performance_analyst` (Performance Analyst)
- `security_analyst` (Security Analyst)

**Generated**: 2026-01-31T15:46:08.851904+00:00
**Approved By**: Pending
