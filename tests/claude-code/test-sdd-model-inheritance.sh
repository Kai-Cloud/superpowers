#!/usr/bin/env bash
# Model-free source checks only; this does not prove effective child routing.
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
    grep -q 'run_in_background: false' "$path" || fail "$template is not foreground"
done

grep -q 'Do not use the Skill tool or invoke any skill' "$SDD_DIR/task-reviewer-prompt.md" \
    || fail "task reviewer still permits nested skill invocation"
grep -q 'Do not use the Skill tool or invoke any skill' "$SDD_DIR/re-review-prompt.md" \
    || fail "re-reviewer still permits nested skill invocation"

grep -q 'parent session owns model selection' "$SDD_DIR/SKILL.md" \
    || fail "SKILL.md does not require parent-model inheritance"
! grep -q 'Always specify the model explicitly' "$SDD_DIR/SKILL.md" \
    || fail "SKILL.md still requires explicit model selection"

# Release consistency is tested independently by
# tests/version-bump/test-version-registry.py; model behavior is release-agnostic.

# Include prose, diagrams, escalation/final routing, and harness boundaries.
# No CLI/model calls: these assertions only detect contradictory source contracts.
python "$SCRIPT_DIR/test-dispatch-contracts.py"

printf '%s\n' '[PASS] Static dispatch contracts are consistent; runtime inheritance is unverified'
