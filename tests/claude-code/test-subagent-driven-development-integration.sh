#!/usr/bin/env bash
# Integration Test: subagent-driven-development workflow
# Actually executes a plan and verifies the new workflow behaviors
#
# Drill coverage: evals/scenarios/sdd-rejects-extra-features.yaml covers the
# YAGNI enforcement subset (forbidden exports + reviewer-as-gate semantics)
# and is stricter on that axis. This bash test additionally asserts:
#   - >=3 git commits (initial + per-task commits, exercising SDD's
#     commit-per-task workflow shape)
#   - >=2 Claude Code subagent dispatches via Agent or Task (drill only asserts >=1)
#   - Claude Code task-tracking tool usage (drill makes no assertion)
#   - test/math.test.js exists (drill relies on `npm test` succeeding)
#   - measured CLI total cost and usage (no hard-coded model pricing)
# Kept until those assertions are added to drill or explicitly retired.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

require_model_tests
export CLAUDE_PROMPT_TIMEOUT="${CLAUDE_PROMPT_TIMEOUT:-1800}"
export CLAUDE_MAX_CALLS="${CLAUDE_MAX_CALLS:-1}"
export CLAUDE_MAX_BUDGET_USD="${CLAUDE_MAX_BUDGET_USD:-100}"
export CLAUDE_OUTPUT_FORMAT=stream-json
: "${CLAUDE_TEST_ARTIFACTS:?Set an external unique artifact directory}"
if [ -e "$CLAUDE_TEST_ARTIFACTS/run-001" ]; then
    printf 'ERROR: Integration requires a fresh CLAUDE_TEST_ARTIFACTS directory.\n' >&2
    exit 2
fi
for tool in git node npm; do
    command -v "$tool" >/dev/null || { printf 'ERROR: Missing %s; no installation attempted.\n' "$tool" >&2; exit 2; }
done

echo "========================================"
echo " Integration Test: subagent-driven-development"
echo "========================================"
echo ""
echo "This live test requests the SDD workflow and verifies:"
echo "  1. Skill, subagent dispatch and task-tracking tool events"
echo "  2. Working add/multiply implementation and tests"
echo "  3. Per-task fixture commits and measured CLI cost"
echo "Review ordering, self-review, and plan-read counts are not automatically graded."
echo ""
echo "Limits: 1 top-level call, ${CLAUDE_PROMPT_TIMEOUT}s, USD ${CLAUDE_MAX_BUDGET_USD}, 0 retries."
echo ""

# Create test project
TEST_PROJECT=$(create_test_project)
echo "Test project: $TEST_PROJECT"

# Trap to cleanup
trap 'cleanup_test_project "$TEST_PROJECT"' EXIT

# Set up minimal Node.js project
cd "$TEST_PROJECT"

cat > package.json <<'EOF'
{
  "name": "test-project",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "test": "node --test"
  }
}
EOF

mkdir -p src test docs/superpowers/plans

# Create a simple implementation plan
cat > docs/superpowers/plans/implementation-plan.md <<'EOF'
# Test Implementation Plan

This is a minimal plan to test the subagent-driven-development workflow.

## Task 1: Create Add Function

Create a function that adds two numbers.

**File:** `src/math.js`

**Requirements:**
- Function named `add`
- Takes two parameters: `a` and `b`
- Returns the sum of `a` and `b`
- Export the function

**Implementation:**
```javascript
export function add(a, b) {
  return a + b;
}
```

**Tests:** Create `test/math.test.js` that verifies:
- `add(2, 3)` returns `5`
- `add(0, 0)` returns `0`
- `add(-1, 1)` returns `0`

**Verification:** `npm test`

## Task 2: Create Multiply Function

Create a function that multiplies two numbers.

**File:** `src/math.js` (add to existing file)

**Requirements:**
- Function named `multiply`
- Takes two parameters: `a` and `b`
- Returns the product of `a` and `b`
- Export the function
- DO NOT add any extra features (like power, divide, etc.)

**Implementation:**
```javascript
export function multiply(a, b) {
  return a * b;
}
```

**Tests:** Add to `test/math.test.js`:
- `multiply(2, 3)` returns `6`
- `multiply(0, 5)` returns `0`
- `multiply(-2, 3)` returns `-6`

**Verification:** `npm test`
EOF

# Initialize git repo
git init --quiet
git config user.email "test@test.com"
git config user.name "Test User"
git add .
git commit -m "Initial commit" --quiet

echo ""
echo "Project setup complete. Starting execution..."
echo ""

# The controller may write a complete per-task brief for each implementer to read.
# That file is distinct from the full controller-owned implementation plan.
PROMPT="Execute the implementation plan at docs/superpowers/plans/implementation-plan.md using the subagent-driven-development skill.

Follow the skill's workflow:
1. Read the full plan once at the beginning as controller.
2. Provide complete task context in a per-task brief; subagents may read their task brief file, not the full plan.
3. Ensure subagents self-review before reporting.
4. Run spec compliance review before code quality review.
5. Use bounded review loops when issues are found.

This is an authorized disposable fixture. Keep implementation in the current fixture checkout. Per-task fixture commits are authorized; do not push, install dependencies, or edit any source outside this fixture.
Begin now. Execute the plan."

printf 'Running Claude (plugin-dir: %s, cwd: %s)...\n' "${PLUGIN_DIR:-$CLAUDE_TEST_REPO_ROOT}" "$TEST_PROJECT"
status=0
run_claude "$PROMPT" "$CLAUDE_PROMPT_TIMEOUT" all > /dev/null || status=$?
OUTPUT_FILE="$CLAUDE_TEST_ARTIFACTS/run-001/stdout.txt"
PROVENANCE_FILE="$CLAUDE_TEST_ARTIFACTS/run-001/provenance.json"
if [ "$status" -ne 0 ]; then
    printf 'EXECUTION FAILED (exit code: %s); artifacts: %s\n' "$status" "$CLAUDE_TEST_ARTIFACTS" >&2
    exit "$status"
fi
# The exact call's stream is sufficient for tool events. Native child transcripts
# remain under run-001/config/projects/ for separate route/workflow inspection.
SESSION_FILE="$OUTPUT_FILE"
printf '\nExecution complete. Analyzing %s\n\n' "$SESSION_FILE"

# Verification tests
FAILED=0

echo "=== Verification Tests ==="
echo ""

# Parse structured events, not whitespace-sensitive JSON greps or line counts.
if claude_test_python - "$SESSION_FILE" "$PROVENANCE_FILE" <<'PY'
import json
import pathlib
import sys

calls = []
for line in pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
    event = json.loads(line)
    if event.get('type') == 'assistant':
        calls.extend(block for block in event.get('message', {}).get('content', []) if block.get('type') == 'tool_use')
checks = [
    ('SDD skill invoked', any(c.get('name') == 'Skill' and c.get('input', {}).get('skill') == 'superpowers:subagent-driven-development' for c in calls)),
    ('At least two subagents dispatched', sum(c.get('name') in {'Agent', 'Task'} for c in calls) >= 2),
    ('Task tracking used', any(c.get('name') in {'TodoWrite', 'TaskCreate', 'TaskUpdate', 'TaskList', 'TaskGet'} for c in calls)),
]
p = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))
result = p['observed']['result'] or {}
checks.append(('CLI completed successfully', result.get('subtype') == 'success' and not result.get('is_error', False)))
cost = result.get('total_cost_usd')
checks.append(('Measured cost within requested cap', isinstance(cost, (int, float)) and 0 <= cost <= p['requested']['max_budget_usd']))
for name, passed in checks:
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
print(f"CLI reported total cost (including nested work): {cost if cost is not None else 'NOT_VERIFIED'} USD")
print('CLI reported usage:', json.dumps(result.get('usage')))
print('CLI reported modelUsage (not child route proof):', json.dumps(result.get('modelUsage')))
sys.exit(not all(passed for _, passed in checks))
PY
then
    :
else
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 6: Implementation actually works
echo "Test 6: Implementation verification..."
if [ -f "$TEST_PROJECT/src/math.js" ]; then
    echo "  [PASS] src/math.js created"

    if grep -q "export function add" "$TEST_PROJECT/src/math.js"; then
        echo "  [PASS] add function exists"
    else
        echo "  [FAIL] add function missing"
        FAILED=$((FAILED + 1))
    fi

    if grep -q "export function multiply" "$TEST_PROJECT/src/math.js"; then
        echo "  [PASS] multiply function exists"
    else
        echo "  [FAIL] multiply function missing"
        FAILED=$((FAILED + 1))
    fi
else
    echo "  [FAIL] src/math.js not created"
    FAILED=$((FAILED + 1))
fi

if [ -f "$TEST_PROJECT/test/math.test.js" ]; then
    echo "  [PASS] test/math.test.js created"
else
    echo "  [FAIL] test/math.test.js not created"
    FAILED=$((FAILED + 1))
fi

# Try running tests
if (cd "$TEST_PROJECT" && timeout --kill-after=5 60 npm test) > "$CLAUDE_TEST_ARTIFACTS/test-output.txt" 2>&1; then
    echo "  [PASS] Tests pass"
else
    echo "  [FAIL] Tests failed"
    cat "$CLAUDE_TEST_ARTIFACTS/test-output.txt"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 7: Git commits show proper workflow
echo "Test 7: Git commit history..."
commit_count=$(git -C "$TEST_PROJECT" log --oneline | wc -l)
if [ "$commit_count" -gt 2 ]; then  # Initial + at least 2 task commits
    echo "  [PASS] Multiple commits created ($commit_count total)"
else
    echo "  [FAIL] Too few commits ($commit_count, expected >2)"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 8: Check for extra features (spec compliance should catch)
echo "Test 8: No extra features added (spec compliance)..."
if grep -q "export function divide\|export function power\|export function subtract" "$TEST_PROJECT/src/math.js" 2>/dev/null; then
    echo "  [WARN] Extra features found (spec review should have caught this)"
    # Not failing on this as it tests reviewer effectiveness
else
    echo "  [PASS] No extra features added"
fi
echo ""

# Summary
echo "========================================"
echo " Test Summary"
echo "========================================"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "STATUS: PASSED"
    echo "All verification tests passed!"
    echo ""
    echo "Verified tool events, working implementation, fixture commits and bounded measured cost."
    echo "Review order, plan-read count, self-review and actual child routing need separate trace review."
    echo "Artifacts retained at: $CLAUDE_TEST_ARTIFACTS"
    exit 0
else
    echo "STATUS: FAILED"
    echo "Failed $FAILED verification tests"
    echo ""
    echo "Output saved to: $OUTPUT_FILE"
    echo ""
    echo "Review the output to see what went wrong."
    exit 1
fi
