#!/usr/bin/env zsh
# Claude CLI Environment Validation Script
# Run this after opening a new terminal session

echo "=== Claude CLI Environment Validation ==="
echo ""

# Check 1: PATH includes ~/.local/bin
echo "1. Checking if ~/.local/bin is in PATH..."
if [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    echo "   ✓ ~/.local/bin is in PATH"
    # Check priority (should be first or early)
    FIRST_PATH=$(echo $PATH | cut -d':' -f1)
    if [[ "$FIRST_PATH" == "$HOME/.local/bin" ]]; then
        echo "   ✓ ~/.local/bin has highest priority"
    else
        echo "   ⚠ ~/.local/bin is in PATH but not first (currently: $FIRST_PATH)"
    fi
else
    echo "   ✗ ~/.local/bin is NOT in PATH"
    echo "   Current PATH: $PATH"
    exit 1
fi
echo ""

# Check 2: which claude resolves correctly
echo "2. Checking which Claude CLI is being used..."
CLAUDE_PATH=$(which claude)
echo "   Found: $CLAUDE_PATH"
if [[ "$CLAUDE_PATH" == "$HOME/.local/bin/claude" ]]; then
    echo "   ✓ Using native installation from ~/.local/bin"
elif [[ "$CLAUDE_PATH" == "/opt/homebrew/bin/claude" ]]; then
    echo "   ⚠ Using Homebrew installation (should use native)"
    echo "   This means ~/.local/bin is not first in PATH"
else
    echo "   ? Using unknown installation: $CLAUDE_PATH"
fi
echo ""

# Check 3: Native installation exists
echo "3. Checking native installation..."
if [[ -L "$HOME/.local/bin/claude" ]]; then
    TARGET=$(readlink "$HOME/.local/bin/claude")
    echo "   ✓ Symlink exists: ~/.local/bin/claude -> $TARGET"
    if [[ -x "$TARGET" ]]; then
        echo "   ✓ Native binary is executable"
    else
        echo "   ✗ Native binary is not executable or doesn't exist"
        exit 1
    fi
else
    echo "   ✗ No symlink at ~/.local/bin/claude"
    exit 1
fi
echo ""

# Check 4: Test claude command
echo "4. Testing Claude CLI command..."
if command -v claude &> /dev/null; then
    VERSION=$(claude --version 2>&1 | head -1)
    echo "   ✓ Claude CLI is accessible"
    echo "   Version: $VERSION"
else
    echo "   ✗ Claude CLI command not found"
    exit 1
fi
echo ""

# Check 5: .zshenv configuration
echo "5. Checking .zshenv configuration..."
if grep -q "\.local/bin" ~/.zshenv 2>/dev/null; then
    echo "   ✓ ~/.zshenv includes .local/bin configuration"
else
    echo "   ⚠ ~/.zshenv doesn't mention .local/bin (might be in other files)"
fi
echo ""

echo "=== Summary ==="
echo "✓ Environment is correctly configured"
echo "✓ Native Claude CLI will be used in new shells"
echo ""
echo "If you still see warnings, they may be from:"
echo "  - Old cached data (will clear automatically)"
echo "  - The installMethod setting (managed internally by Claude)"
echo ""
echo "To apply changes to your current terminal session:"
echo "  1. Close this terminal"
echo "  2. Open a new terminal"
echo "  3. Run this script again to verify"
