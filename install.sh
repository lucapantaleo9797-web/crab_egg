#!/usr/bin/env bash
# CrabEgg Installer — One-liner install for OpenClaw
# Usage: curl -fsSL https://raw.githubusercontent.com/lucapantaleo9797-web/crab_egg/main/install.sh | bash

set -e

SKILL_DIR="${HOME}/.openclaw/skills/crabegg"
REPO_URL="https://github.com/lucapantaleo9797-web/crab_egg.git"

echo ""
echo "  ,;;,"
echo " ( o o)  CrabEgg Installer"
echo "/'   '\\"
echo ""

# Check if OpenClaw is installed
if ! command -v openclaw &> /dev/null; then
    echo "  Warning: 'openclaw' command not found."
    echo "  CrabEgg will still be installed, but you'll need OpenClaw to use it."
    echo "  Install OpenClaw: https://docs.openclaw.ai/getting-started"
    echo ""
fi

# Check if already installed
if [ -d "$SKILL_DIR" ]; then
    echo "  CrabEgg is already installed at $SKILL_DIR"
    echo "  Updating..."
    cd "$SKILL_DIR"
    git pull origin main 2>/dev/null || {
        echo "  Not a git repo. Removing and re-cloning..."
        rm -rf "$SKILL_DIR"
    }
fi

# Clone if needed
if [ ! -d "$SKILL_DIR" ]; then
    echo "  Cloning CrabEgg..."
    mkdir -p "$(dirname "$SKILL_DIR")"
    git clone "$REPO_URL" "$SKILL_DIR"
fi

# Make scripts executable
echo "  Making scripts executable..."
chmod +x "$SKILL_DIR/scripts/"*.py 2>/dev/null || true

# Check Python dependencies
echo "  Checking dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install requests --quiet 2>/dev/null || pip install requests --quiet 2>/dev/null || true
elif command -v pip &> /dev/null; then
    pip install requests --quiet 2>/dev/null || true
else
    echo "  Warning: pip not found. Install 'requests' manually: pip install requests"
fi

# Verify
if [ -f "$SKILL_DIR/SKILL.md" ]; then
    echo ""
    echo "  ,;;,"
    echo " ( o o)  CrabEgg installed successfully!"
    echo "/'   '\\"
    echo ""
    echo "  Location: $SKILL_DIR"
    echo ""
    echo "  To start: Open OpenClaw and say 'Hatch a CrabEgg'"
    echo ""
    echo "  Files installed:"
    find "$SKILL_DIR" -type f -not -path "*/.git/*" -not -path "*__pycache__*" | wc -l | xargs echo "   "
    echo ""
else
    echo "  ERROR: Installation failed. SKILL.md not found."
    exit 1
fi
