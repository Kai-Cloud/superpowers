#!/usr/bin/env bash
# Test: subagent-driven-development skill
# Verifies that the skill is loaded and follows correct workflow
#
# No drill coverage: this test asks the agent to *describe* SDD (string-
# matches its verbal explanation against expected keywords like
# "self-review", "skeptical", "worktree", "Step 1", "loop"). Drill scenarios
# test behavior (real subagent dispatch, plan-following, review loops),
# not description-recall. Kept by design.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

# This is paid description recall, not an offline unit test.
require_model_tests
export CLAUDE_PROMPT_TIMEOUT="${CLAUDE_PROMPT_TIMEOUT:-90}"
export CLAUDE_MAX_CALLS="${CLAUDE_MAX_CALLS:-9}"
export CLAUDE_MAX_BUDGET_USD="${CLAUDE_MAX_BUDGET_USD:-100}"
export CLAUDE_OUTPUT_FORMAT="${CLAUDE_OUTPUT_FORMAT:-text}"
if [ "$CLAUDE_OUTPUT_FORMAT" != text ]; then
    printf 'ERROR: Description recall requires CLAUDE_OUTPUT_FORMAT=text.\n' >&2
    exit 2
fi
# Never let a recall prompt modify the tested checkout.
TEST_PROJECT=$(create_test_project)
trap 'cleanup_test_project "$TEST_PROJECT"' EXIT
cd "$TEST_PROJECT"

echo "=== Test: subagent-driven-development skill recall (9 calls maximum) ==="
echo ""

# Test 1: Verify skill can be loaded
echo "Test 1: Skill loading..."

output=$(run_claude "What is the subagent-driven-development skill? Describe its key steps briefly." "$CLAUDE_PROMPT_TIMEOUT")

if assert_contains "$output" "subagent-driven-development\|Subagent-Driven Development\|Subagent Driven" "Skill is recognized"; then
    : # pass
else
    exit 1
fi

if assert_contains "$output" "Load Plan\|read.*plan\|extract.*tasks" "Mentions loading plan"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 2: Verify skill describes correct workflow order
echo "Test 2: Workflow ordering..."

output=$(run_claude "In the subagent-driven-development skill, what comes first: spec compliance review or code quality review? Answer using exactly this structure:
First: <review type>
Second: <review type>" "$CLAUDE_PROMPT_TIMEOUT")

if assert_order "$output" "First:.*spec.*compliance" "Second:.*code.*quality" "Spec compliance before code quality"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 3: Verify self-review is mentioned
echo "Test 3: Self-review requirement..."

output=$(run_claude "Does the subagent-driven-development skill require implementers to self-review before handoff, and can self-review replace the external reviews? Answer using exactly this structure:
Self-review required: <yes or no>
Self-review replaces external review: <yes or no>" "$CLAUDE_PROMPT_TIMEOUT")

if assert_contains "$output" "Self-review required:.*yes" "Mentions self-review"; then
    : # pass
else
    exit 1
fi

if assert_contains "$output" "Self-review replaces external review:.*no" "Self-review does not replace external review"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 4: Verify plan is read once
echo "Test 4: Plan reading efficiency..."

output=$(run_claude "In subagent-driven-development, how many times should the controller read the plan file? When does this happen?" "$CLAUDE_PROMPT_TIMEOUT")

if assert_contains "$output" "once\|one time\|single" "Read plan once"; then
    : # pass
else
    exit 1
fi

if assert_contains "$output" "Step 1\|beginning\|start\|Load Plan" "Read at beginning"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 5: Verify spec compliance reviewer is skeptical
echo "Test 5: Spec compliance reviewer mindset..."

output=$(run_claude "What is the spec compliance reviewer's attitude toward the implementer's report in subagent-driven-development?" "$CLAUDE_PROMPT_TIMEOUT")

if assert_contains "$output" "not.*trust\|don't trust\|skeptical\|verify.*independently\|suspiciously" "Reviewer is skeptical"; then
    : # pass
else
    exit 1
fi

if assert_contains "$output" "read.*code\|inspect.*code\|verify.*code\|read.*diff\|trust.*diff" "Reviewer reads code"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 6: Verify review loops
echo "Test 6: Review loop requirements..."

output=$(run_claude "In subagent-driven-development, what happens if a reviewer finds issues? Is it a one-time review or a loop?" "$CLAUDE_PROMPT_TIMEOUT")

if assert_contains "$output" "loop\|again\|repeat\|until.*approved\|until.*compliant" "Review loops mentioned"; then
    : # pass
else
    exit 1
fi

if assert_contains "$output" "implementer.*fix\|fix.*issues" "Implementer fixes issues"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 7: A complete task brief is not the controller's full plan.
echo "Test 7: Task context provision..."

output=$(run_claude "In subagent-driven-development, how does the controller provide complete task information to the implementer subagent? Distinguish the per-task brief from the full implementation plan. Answer using exactly this structure:
Controller provides: <context and delivery method>
Implementer reads task brief file: <yes or no>
Implementer must read full plan file: <yes or no>" "$CLAUDE_PROMPT_TIMEOUT")

if assert_task_brief_contract "$output"; then
    echo "  [PASS] Complete task context without requiring the full plan"
else
    printf '  [FAIL] Expected a complete task brief or inline text, not a full-plan handoff.\n%s\n' "$output"
    exit 1
fi

echo ""

# Test 8: Verify worktree requirement
echo "Test 8: Worktree requirement..."

output=$(run_claude "What workflow skills are required before using subagent-driven-development? List any prerequisites or required skills." "$CLAUDE_PROMPT_TIMEOUT")

if assert_contains "$output" "using-git-worktrees\|worktree" "Mentions worktree requirement"; then
    : # pass
else
    exit 1
fi

echo ""

# Test 9: Verify main branch warning
echo "Test 9: Main branch red flag..."

output=$(run_claude "In subagent-driven-development, is it okay to start implementation directly on the main branch?" "$CLAUDE_PROMPT_TIMEOUT")

if assert_contains "$output" "worktree\|feature.*branch\|not.*main\|never.*main\|avoid.*main\|don't.*main\|consent\|permission" "Warns against main branch"; then
    : # pass
else
    exit 1
fi

echo ""

echo "=== All subagent-driven-development skill tests passed ==="
