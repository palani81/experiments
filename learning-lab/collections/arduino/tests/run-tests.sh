#!/bin/bash

# Arduino Learning Lab - Test Runner Script
# Runs all tests and displays results

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Arduino Learning Lab - Automated Test Suite              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
  echo "❌ Error: Node.js is not installed."
  echo "   Please install Node.js to run tests."
  exit 1
fi

echo "ℹ️  Node.js version: $(node -v)"
echo "ℹ️  Working directory: $SCRIPT_DIR"
echo "ℹ️  Project directory: $PROJECT_ROOT"
echo ""

# Run the main test suite
echo "🧪 Running test suite..."
echo ""

if node "$SCRIPT_DIR/test-app.js"; then
  echo ""
  echo "╔════════════════════════════════════════════════════════════╗"
  echo "║                   ✅ Tests Passed! ✅                      ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo ""
  exit 0
else
  echo ""
  echo "╔════════════════════════════════════════════════════════════╗"
  echo "║                  ❌ Tests Failed ❌                        ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo ""
  exit 1
fi
