#!/usr/bin/env bash
# Regression test for task-scoped codebase navigation rules.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

failures=0

assert_file() {
    local file="$1"
    local label="$2"
    if [[ -f "$file" ]]; then
        echo "  [PASS] $label"
    else
        echo "  [FAIL] $label"
        echo "    Missing: $file"
        failures=$((failures + 1))
    fi
}

assert_contains() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    if grep -Fq "$pattern" "$file"; then
        echo "  [PASS] $label"
    else
        echo "  [FAIL] $label"
        echo "    Expected: $pattern"
        echo "    In: $file"
        failures=$((failures + 1))
    fi
}

assert_not_contains() {
    local file="$1"
    local pattern="$2"
    local label="$3"
    if grep -Fq "$pattern" "$file"; then
        echo "  [FAIL] $label"
        echo "    Unexpected: $pattern"
        echo "    In: $file"
        failures=$((failures + 1))
    else
        echo "  [PASS] $label"
    fi
}

NAVIGATION="$REPO_ROOT/skills/codebase-navigation/SKILL.md"
ROUTER="$REPO_ROOT/skills/using-superpowers/SKILL.md"
BRAINSTORMING="$REPO_ROOT/skills/brainstorming/SKILL.md"
DEBUGGING="$REPO_ROOT/skills/systematic-debugging/SKILL.md"
TRACING="$REPO_ROOT/skills/systematic-debugging/root-cause-tracing.md"
REVIEW="$REPO_ROOT/skills/receiving-code-review/SKILL.md"
FINAL_REVIEW="$REPO_ROOT/skills/requesting-code-review/code-reviewer.md"
VERIFY="$REPO_ROOT/skills/verification-before-completion/SKILL.md"
WORKTREES="$REPO_ROOT/skills/using-git-worktrees/SKILL.md"
PLANS="$REPO_ROOT/skills/writing-plans/SKILL.md"
FINISHING="$REPO_ROOT/skills/finishing-a-development-branch/SKILL.md"
EXECUTING="$REPO_ROOT/skills/executing-plans/SKILL.md"
SDD="$REPO_ROOT/skills/subagent-driven-development/SKILL.md"
TDD="$REPO_ROOT/skills/test-driven-development/SKILL.md"
WRITING_SKILLS="$REPO_ROOT/skills/writing-skills/SKILL.md"
REQUESTING_REVIEW="$REPO_ROOT/skills/requesting-code-review/SKILL.md"
ROOT_INSTRUCTIONS="$REPO_ROOT/CLAUDE.md"
RUNNER="$REPO_ROOT/tests/claude-code/run-skill-tests.sh"

echo "=== Scoped Codebase Navigation Test ==="
echo ""

assert_file "$NAVIGATION" "codebase-navigation skill exists"
assert_contains "$NAVIGATION" "Target:       exact symbol / API / event / config key / error / table" "navigation skill names search target"
assert_contains "$NAVIGATION" "Scope:        first-party directories that can answer this task" "navigation skill scopes search"
assert_contains "$NAVIGATION" "Exclusions:   generated, vendor, build, fixture, or unrelated directories as applicable" "navigation skill excludes irrelevant search paths"
assert_contains "$NAVIGATION" "Decision:     what a match or no-match will change" "navigation skill ties search to a decision"
assert_contains "$NAVIGATION" "Stop:         when direct callers/consumers or the named risk boundary are enumerated" "navigation skill defines search stop"
assert_contains "$NAVIGATION" "Unknown" "navigation skill preserves explicit unknowns"
assert_contains "$NAVIGATION" "Do not read or summarize the whole repository by" "navigation skill rejects default full-repository reading"

assert_contains "$ROUTER" "## Scope Before Process Selection" "global router scopes before selecting process skills"
assert_contains "$ROUTER" "Do not chain process skills merely because a task exists" "global router rejects hypothetical workflow chaining"

assert_contains "$BRAINSTORMING" "description: Use when starting a new project" "brainstorming still triggers for new projects"
assert_contains "$BRAINSTORMING" "do not inventory every repository file" "brainstorming task context stays bounded"
assert_contains "$BRAINSTORMING" "A large or unfamiliar repository by itself is not an architectural change." "brainstorming rejects size-only escalation"
assert_contains "$BRAINSTORMING" "Upgrade only when evidence shows" "brainstorming requires evidence for escalation"
assert_contains "$BRAINSTORMING" "Existing repository and task path unknown?" "brainstorming flow routes unknown existing paths to navigation"

assert_contains "$DEBUGGING" "## Investigation Boundary" "debugging defines an investigation boundary"
assert_contains "$DEBUGGING" "Never inspect every component merely because the system has multiple components." "debugging rejects global component inspection"
assert_contains "$DEBUGGING" "superpowers:codebase-navigation" "debugging routes unknown large-repo paths to navigation"
assert_contains "$TRACING" "## Trace Boundary" "root-cause tracing defines a trace boundary"
assert_contains "$TRACING" "A long stack trace is not a" "root-cause tracing rejects unbounded caller reading"
assert_contains "$TRACING" "reason to read every caller, sibling subsystem, or related directory" "root-cause tracing names the forbidden crawl"

assert_contains "$REVIEW" "Target: exact symbol / API / event / config key" "review usage checks name a search target"
assert_contains "$REVIEW" "Stop: direct producers/consumers or the named risk boundary are enumerated" "review usage checks define a stop condition"
assert_contains "$FINAL_REVIEW" "Whole-branch means the named Git range, not every file in the repository." "final review starts from named diff range"
assert_contains "$FINAL_REVIEW" "Do not crawl unrelated code" "final review rejects unrelated repository crawl"

assert_contains "$VERIFY" "complete for the named claim, not the largest available suite" "verification scales full command to the claim"
assert_contains "$WORKTREES" "do not install/download every detected" "worktree setup is proportional to task proof"
assert_contains "$WORKTREES" "ecosystem merely because its manifest exists" "worktree setup rejects manifest-driven installs"
assert_contains "$PLANS" "not a requirement" "plans stay comprehensive only within task boundary"
assert_contains "$PLANS" "to understand or enumerate the whole repository" "plans reject full-repository enumeration"
assert_contains "$FINISHING" "an automatic excuse to run every unrelated suite" "finish verification is proportional to integration claim"
assert_contains "$EXECUTING" "do not solve missing context by reading the whole repository" "inline plan execution uses bounded task maps"
assert_contains "$EXECUTING" "Unknown" "inline plan execution preserves explicit unknowns"

assert_contains "$SDD" "codebase-navigation" "SDD points large-repository tasks to navigation"
assert_contains "$SDD" "Do not let an implementer rediscover the whole repository" "SDD preserves task-scoped context"
assert_contains "$SDD" "continuous execution never authorizes adding unrelated tasks" "SDD continuation cannot widen scope"

# Convergence-first policy: read-only work and known local non-production
# corrections must not silently turn into a delivery workflow.
assert_contains "$ROUTER" "Non-escalating work is not an implementation-plan workflow." "router defines a non-escalating work path"
assert_contains "$ROUTER" "explicitly selects that escalation" "router requires explicit escalation selection"
assert_contains "$BRAINSTORMING" "## Not Design Work" "brainstorming excludes evidence-only work"
assert_contains "$TDD" "description: Use when implementing a production feature" "TDD discovery targets production behavior changes"
assert_contains "$TDD" "## Test-Only Corrections" "TDD scopes test-only corrections to focused proof"
assert_contains "$WRITING_SKILLS" "## Behavior-Shaping Changes" "writing-skills distinguishes behavior-shaping edits"
assert_contains "$WRITING_SKILLS" "## Validation Tiers" "writing-skills defines risk-tiered validation"
assert_contains "$WRITING_SKILLS" "### Focused — default" "focused local validation is the default tier"
assert_contains "$WRITING_SKILLS" "### Targeted Behavior — explicit opt-in" "targeted behavior validation requires opt-in"
assert_contains "$WRITING_SKILLS" "### Full Pressure — explicit opt-in" "full pressure validation requires opt-in"
assert_contains "$WRITING_SKILLS" "Do not escalate a failed tier automatically." "validation failures do not auto-escalate"
assert_contains "$WRITING_SKILLS" "scenario list, model, run count, time limit, and cost limit" "model validation requires a fixed budget"
assert_contains "$ROOT_INSTRUCTIONS" "Validation is risk-tiered" "root instructions require proportional validation"
assert_contains "$ROOT_INSTRUCTIONS" "Long LLM evaluations require explicit approval" "root instructions require approval for model evals"
assert_contains "$PLANS" "A plan is not authorization to execute." "plan documentation does not authorize execution"
assert_contains "$EXECUTING" "description: Use when a human partner explicitly selects inline execution" "inline execution discovery requires explicit selection"
assert_contains "$EXECUTING" "## Eligibility" "inline execution has an eligibility gate"
assert_contains "$EXECUTING" "explicitly selected inline execution" "inline execution requires explicit selection"
assert_contains "$SDD" "description: Use when a human partner explicitly selects subagent-driven-development" "SDD discovery requires explicit selection"
assert_contains "$SDD" "## Eligibility" "SDD has an eligibility gate"
assert_contains "$SDD" "explicitly selected subagent-driven-development" "SDD requires explicit selection"
assert_contains "$WORKTREES" "description: Use when a human partner explicitly requests an isolated workspace" "worktree discovery requires explicit consent"
assert_contains "$WORKTREES" "A plan or subagent availability is not consent to create a worktree." "worktree consent stays separate from planning"
assert_contains "$REQUESTING_REVIEW" "## Standalone Review" "standalone reviews have a finite path"
assert_contains "$REQUESTING_REVIEW" "your human partner explicitly requests an independent review" "standalone reviewer dispatch requires explicit request"
assert_contains "$REQUESTING_REVIEW" "ends with its evidence report" "standalone review does not auto-authorize remediation"
assert_contains "$FINAL_REVIEW" "Unknown — nonblocking" "reviewer labels unverified concerns nonblocking"
assert_not_contains "$FINAL_REVIEW" "git worktree add" "standalone reviewer cannot create a worktree"
assert_contains "$RUNNER" "RUN_INTEGRATION=false" "model integrations remain opt-in by default"

assert_contains "$RUNNER" "test-scoped-codebase-navigation.sh" "main runner includes scoped navigation regression test"
assert_contains "$RUNNER" "test-scoped-codebase-navigation-integration.sh" "integration runner includes navigation behavior test"
assert_contains "$RUNNER" "test-scoped-codebase-navigation.sh" "fast runner includes navigation static test"

echo ""
if [[ "$failures" -gt 0 ]]; then
    echo "STATUS: FAILED ($failures failures)"
    exit 1
fi

echo "STATUS: PASSED"
