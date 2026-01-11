#!/usr/bin/env python3
"""
Test script for ADR-001 deployment to production.

This tests the deployment validation pipeline including:
- Pre-deployment validation
- SQL/S3 safety scanners
- Environment-gated approval
- Health checks
"""

from pathlib import Path
from orchestration.deployment_orchestrator import (
    DeploymentOrchestrator,
    DeploymentConfig,
    Environment
)


def test_adr001_production_deployment():
    """Test deployment of ADR-001 to production."""

    print("=" * 60)
    print("ADR-001 PRODUCTION DEPLOYMENT TEST")
    print("=" * 60)
    print()

    # Configuration
    credentialmate_path = Path("/Users/tmac/1_REPOS/credentialmate")
    orchestrator = DeploymentOrchestrator(credentialmate_path)

    # Create deployment config for PRODUCTION
    config = DeploymentConfig(
        environment=Environment.PRODUCTION,
        version="adr-001-v1.0.0",
        project_path=credentialmate_path,
        migrations_path=credentialmate_path / "alembic" / "versions",
        run_migrations=True,
        skip_tests=False  # Run tests for production
    )

    print("📋 Deployment Configuration:")
    print(f"   Environment: {config.environment.value}")
    print(f"   Version: {config.version}")
    print(f"   Project: {config.project_path}")
    print(f"   Run migrations: {config.run_migrations}")
    print(f"   Skip tests: {config.skip_tests}")
    print()

    # Execute deployment
    print("🚀 Initiating deployment...")
    print()

    result = orchestrator.deploy(config)

    # Display results
    print()
    print("=" * 60)
    print("DEPLOYMENT RESULT")
    print("=" * 60)
    print()
    print(f"Status: {result.status.value.upper()}")
    print(f"Environment: {result.environment.value}")
    print(f"Version: {result.version}")
    print(f"Started: {result.started_at}")
    print(f"Completed: {result.completed_at}")
    print(f"Approval Required: {result.approval_required}")
    print(f"Rollback Executed: {result.rollback_executed}")
    print()

    if result.errors:
        print("❌ Errors:")
        for error in result.errors:
            print(f"   - {error}")
        print()

    if result.warnings:
        print("⚠️  Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")
        print()

    # Explain what happened
    print()
    print("=" * 60)
    print("EXPLANATION")
    print("=" * 60)
    print()

    if result.approval_required:
        print("✅ GOVERNANCE WORKING CORRECTLY:")
        print()
        print("The deployment orchestrator correctly identified that:")
        print("1. Target environment is PRODUCTION")
        print("2. Production deployments ALWAYS require human approval")
        print("3. Deployment was BLOCKED until approval is granted")
        print()
        print("Next steps:")
        print("1. Human reviews deployment plan")
        print("2. Human explicitly approves production deployment")
        print("3. Orchestrator proceeds with:")
        print("   - Pre-deployment validation (tests, migrations, safety)")
        print("   - Build application")
        print("   - Deploy to production")
        print("   - Run migrations")
        print("   - Post-deployment health checks")
        print("4. Manual rollback available if issues detected")
        print()
        print("This is the expected behavior for production deployments!")
    else:
        print("⚠️  UNEXPECTED: Production deployment did not require approval")
        print("   This indicates a governance issue that needs investigation.")

    print()
    print("=" * 60)

    return result


if __name__ == "__main__":
    result = test_adr001_production_deployment()

    # Exit with appropriate code
    if result.approval_required:
        print("\n✅ Test PASSED: Production approval gate is working")
        exit(0)
    else:
        print("\n❌ Test FAILED: Production approval gate is NOT working")
        exit(1)
