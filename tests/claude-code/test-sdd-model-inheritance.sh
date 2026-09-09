#!/usr/bin/env bash
# Test: SDD dispatches inherit the parent session model in the fork variant.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SDD_DIR="$REPO_ROOT/skills/subagent-driven-development"

fail() {
    echo "[FAIL] $1"
    exit 1
}

for template in implementer-prompt.md task-reviewer-prompt.md re-review-prompt.md; do
    path="$SDD_DIR/$template"
    test -f "$path" || fail "missing $template"
    ! grep -q 'model:[[:space:]]*\[MODEL' "$path" || fail "$template still exposes a model placeholder"
done

grep -q 'parent session owns model selection' "$SDD_DIR/SKILL.md" \
    || fail "SKILL.md does not require parent-model inheritance"
! grep -q 'Always specify the model explicitly' "$SDD_DIR/SKILL.md" \
    || fail "SKILL.md still requires explicit model selection"

grep -q '"version": "6.3.3"' "$REPO_ROOT/package.json" \
    || fail "package version is not 6.3.3"
grep -q '"version": "6.3.3"' "$REPO_ROOT/.claude-plugin/plugin.json" \
    || fail "Claude plugin version is not 6.3.3"

echo "[PASS] SDD dispatch templates inherit the parent model"
