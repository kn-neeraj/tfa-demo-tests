#!/bin/bash
# =============================================================
# run_testbed.sh — Run TFA test bed on BrowserStack Automate
#
# Prerequisites:
#   pip install browserstack-sdk selenium pytest
#
# Usage:
#   cd test_bed/
#   bash run_testbed.sh
#
# After the run completes, note the Build ID printed at the end.
# Paste it into the TFA skill to begin log analysis.
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "================================================"
echo "  TFA Skill Evaluation — BrowserStack Test Bed"
echo "================================================"
echo ""
echo "Running tests via BrowserStack SDK..."
echo "Config: browserstack.yml"
echo "Platforms: Windows 11 Chrome, OS X Ventura Firefox"
echo ""

# Run passing tests first to confirm setup, then failures
browserstack-sdk pytest test_passing.py test_failures.py \
  -v \
  --tb=short \
  2>&1 | tee run_output.log

echo ""
echo "================================================"
echo "  Run complete. Check BrowserStack Automate:"
echo "  https://automate.browserstack.com"
echo ""
echo "  Find your build: 'tfa-test-bed'"
echo "  Copy the Build ID and paste it to the TFA skill."
echo "================================================"
echo ""

# Try to extract build ID from SDK output
BUILD_ID=$(grep -oE 'build_id=[a-z0-9]+' run_output.log | head -1 | cut -d= -f2 || true)
if [ -n "$BUILD_ID" ]; then
  echo "  Detected Build ID: $BUILD_ID"
fi
