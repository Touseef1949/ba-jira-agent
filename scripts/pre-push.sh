#!/usr/bin/env bash
# ── pre-push hook for BA Jira Agent ──────────────────────────────────────────
# Runs fast pytest suite (test_tools.py + test_agent_service.py) before every
# `git push`. Blocks the push on failure.
#
# Installation:
#   ln -sf ../../scripts/pre-push.sh .git/hooks/pre-push
#
# The hook also checks for markdown-only changes and skips tests when the push
# only touches *.md files.
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Determine project root ───────────────────────────────────────────────────
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ "$HOOK_DIR" == *.git/hooks ]]; then
    PROJECT_ROOT="$(cd "$HOOK_DIR/../.." && pwd)"
else
    PROJECT_ROOT="$(cd "$HOOK_DIR/.." && pwd)"
fi

cd "$PROJECT_ROOT"

# ── Skip tests for markdown-only pushes ──────────────────────────────────────
SKIP_TESTS=0
while read -r _local _remote; do
    if [ "$_local" = "0000000000000000000000000000000000000000" ]; then
        # Branch is being deleted — skip
        exit 0
    fi

    CHANGED_FILES="$(git diff --name-only "$_local" "$_remote" 2>/dev/null || true)"
    NON_MD_COUNT=$(echo "$CHANGED_FILES" | grep -cv '\.md$' || true)

    if [ "$NON_MD_COUNT" -eq 0 ]; then
        echo "[pre-push] ℹ️  Markdown-only change detected — skipping tests."
        exit 0
    fi
done

if [ "$SKIP_TESTS" -eq 1 ]; then
    exit 0
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚡ pre-push: Running fast checks (tools + agent_service)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Run the fast test suite ──────────────────────────────────────────────────
# shellcheck disable=SC2086
if ! /usr/local/bin/python3 -m pytest \
    tests/test_tools.py \
    tests/test_agent_service.py \
    -q --no-header --tb=short \
    -W ignore::pytest.PytestUnknownMarkWarning; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Pre-push tests FAILED — push blocked."
    echo "   Run locally: pytest tests/test_tools.py tests/test_agent_service.py -v"
    echo "   Use --no-verify to bypass (not recommended)."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi

echo ""
echo "✅ Pre-push checks passed."
exit 0
