#!/bin/bash
# Install Git Hooks for Documentation Governance
#
# Usage: ./governance/install-hooks.sh

set -e

echo "📦 Installing Git Hooks for Documentation Governance..."

# Check we're in git repo
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository"
    echo "   Run this from the root of AI_Orchestrator"
    exit 1
fi

# Install pre-commit hook
if [ -f ".git/hooks/pre-commit" ]; then
    echo "⚠️  .git/hooks/pre-commit already exists"
    echo "   Backing up to .git/hooks/pre-commit.backup"
    mv .git/hooks/pre-commit .git/hooks/pre-commit.backup
fi

echo "   Installing pre-commit hook..."
cp governance/hooks/pre-commit-documentation .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "✅ Git hooks installed successfully!"
echo ""
echo "📋 What's installed:"
echo "   - pre-commit: Documentation structure validation (ADR-010)"
echo ""
echo "🧪 Test the hook:"
echo "   echo '# Test' > test.md"
echo "   git add test.md"
echo "   git commit -m 'test'  # Should block"
echo "   rm test.md"
echo ""
echo "📖 Documentation:"
echo "   See: governance/DOCUMENTATION-GOVERNANCE.md"
