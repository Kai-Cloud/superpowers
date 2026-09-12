#!/usr/bin/env bash
# Tests for the SDD workspace: scripts/sdd-workspace resolves a self-ignoring,
# PER-PLAN working-tree directory for SDD artifacts, and the SDD scripts write
# into their plan's directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SDD_SCRIPTS="$REPO_ROOT/skills/subagent-driven-development/scripts"

FAILURES=0
PASSES=0
TEST_ROOT=""

pass() {
    echo "  [PASS] $1"
    PASSES=$((PASSES + 1))
}
fail() {
    echo "  [FAIL] $1"
    FAILURES=$((FAILURES + 1))
}

# Compare existing paths in the shell's physical namespace on both sides.
# Git Bash may print C:/... from git and /c/... (or /tmp/...) from pwd;
# macOS may spell the same directory as /var/... or /private/var/....
physical_path() {
    local path="$1"
    if [[ -d "$path" ]]; then
        (cd "$path" && pwd -P)
    elif [[ -f "$path" ]]; then
        local parent
        parent="$(cd "$(dirname "$path")" && pwd -P)" || return 1
        printf '%s/%s\n' "$parent" "$(basename "$path")"
    else
        return 1
    fi
}

same_path() {
    local expected actual
    expected="$(physical_path "$1")" && actual="$(physical_path "$2")" \
        && [[ "$expected" == "$actual" ]]
}

assert_same_path() {
    if same_path "$1" "$2"; then
        pass "$3"
    else
        fail "$3"
        printf '    expected: %s\n    got:      %s\n' "$1" "$2"
    fi
}

cleanup() {
    if [[ -n "$TEST_ROOT" && -d "$TEST_ROOT" ]]; then
        rm -rf "$TEST_ROOT"
    fi
}

main() {
    echo "=== Test: sdd-workspace ==="

    TEST_ROOT="$(mktemp -d)"
    trap cleanup EXIT

    # Keep Git's spelling as input to assertions: on Git Bash it differs
    # from shell output. All writes and fixture commits stay outside the repo.
    git init -q -b main "$TEST_ROOT/repo with spaces"
    local repo shell_repo
    repo="$(cd "$TEST_ROOT/repo with spaces" && git rev-parse --show-toplevel)"
    shell_repo="$(cd "$repo" && pwd -P)"

    assert_same_path "$repo/." "$shell_repo" "normalizes the expected existing path"
    assert_same_path "$shell_repo" "$repo/." "normalizes the actual existing path"
    if same_path "$repo/missing" "$repo/missing"; then
        fail "missing paths cannot compare equal"
    else
        pass "missing paths cannot compare equal"
    fi
    if [[ "$(git -C "$repo" branch --show-current)" == "main" ]]; then
        pass "primary fixture runs on main"
    else
        fail "primary fixture runs on main"
    fi

    cat > "$repo/plan-a.md" <<'PLAN'
# Plan A

## Task 1: First thing

Do the first thing.
PLAN
    cat > "$repo/plan-b.md" <<'PLAN'
# Plan B

## Task 1: Other thing

Do the other thing.
PLAN

    # --- argument validation ---
    local rc=0
    (cd "$repo" && "$SDD_SCRIPTS/sdd-workspace" >/dev/null 2>&1) || rc=$?
    if [[ "$rc" -eq 2 ]]; then
        pass "sdd-workspace without a plan errors with exit 2"
    else
        fail "sdd-workspace without a plan errors with exit 2"
        echo "    exit: $rc"
    fi

    rc=0
    (cd "$repo" && "$SDD_SCRIPTS/sdd-workspace" no-such-plan.md >/dev/null 2>&1) || rc=$?
    if [[ "$rc" -eq 2 ]]; then
        pass "sdd-workspace with a missing plan file errors with exit 2"
    else
        fail "sdd-workspace with a missing plan file errors with exit 2"
        echo "    exit: $rc"
    fi

    # --- per-plan resolution ---
    local dir_a dir_b
    dir_a="$(cd "$repo" && "$SDD_SCRIPTS/sdd-workspace" plan-a.md)"
    dir_b="$(cd "$repo" && "$SDD_SCRIPTS/sdd-workspace" plan-b.md)"

    assert_same_path "$repo/.superpowers/sdd/plan-a" "$dir_a" \
        "prints <repo-root>/.superpowers/sdd/<plan-basename>"

    if [[ -d "$dir_a" && -d "$dir_b" ]] && ! same_path "$dir_a" "$dir_b"; then
        pass "two plans resolve to two distinct directories"
    else
        fail "two plans resolve to two distinct directories"
        echo "    a: $dir_a"
        echo "    b: $dir_b"
    fi

    if [[ -f "$repo/.superpowers/sdd/.gitignore" && "$(cat "$repo/.superpowers/sdd/.gitignore")" == "*" ]]; then
        pass "self-ignoring .gitignore created at .superpowers/sdd/ with '*'"
    else
        fail "self-ignoring .gitignore created at .superpowers/sdd/ with '*'"
    fi

    printf 'x\n' > "$dir_a/artifact.md"
    local status
    status="$(cd "$repo" && git status --porcelain)"
    # plan-a.md/plan-b.md are intentionally untracked fixture files; only the
    # workspace must be invisible.
    if [[ "$status" != *".superpowers"* ]]; then
        pass "workspace invisible to git status"
    else
        fail "workspace invisible to git status"
        echo "    status: $status"
    fi

    ( cd "$repo" && git add -A )
    local staged
    staged="$(cd "$repo" && git diff --cached --name-only)"
    if [[ "$staged" != *".superpowers"* ]]; then
        pass "git add -A does not stage the workspace"
    else
        fail "git add -A does not stage the workspace"
        echo "    staged: $staged"
    fi

    # --- task-brief lands in its plan's directory ---
    local brief_out brief_path
    brief_out="$(cd "$repo" && "$SDD_SCRIPTS/task-brief" plan-a.md 1)"
    brief_path="$(printf '%s\n' "$brief_out" | sed -n 's/^wrote \(.*\): [0-9][0-9]* lines$/\1/p')"
    assert_same_path "$repo/.superpowers/sdd/plan-a/task-1-brief.md" "$brief_path" \
        "task-brief writes its brief under the plan's workspace"

    # --- review-package takes the plan first and lands in its directory ---
    local git_id=(-c user.email=t@example.com -c user.name=t -c commit.gpgsign=false)
    ( cd "$repo" \
        && git "${git_id[@]}" commit -qm c1 \
        && printf 'y\n' > f && git add f \
        && git "${git_id[@]}" commit -qm c2 )
    local rp_out rp_path base_short head_short
    rp_out="$(cd "$repo" && "$SDD_SCRIPTS/review-package" plan-a.md HEAD~1 HEAD)"
    rp_path="$(printf '%s\n' "$rp_out" | sed -n 's/^wrote \(.*\): [0-9].*$/\1/p')"
    base_short="$(git -C "$repo" rev-parse --short HEAD~1)"
    head_short="$(git -C "$repo" rev-parse --short HEAD)"
    assert_same_path "$repo/.superpowers/sdd/plan-a/review-$base_short..$head_short.diff" "$rp_path" \
        "review-package writes its diff under the plan's workspace"

    rc=0
    (cd "$repo" && "$SDD_SCRIPTS/review-package" HEAD~1 HEAD >/dev/null 2>&1) || rc=$?
    if [[ "$rc" -eq 2 ]]; then
        pass "review-package without a plan errors with exit 2"
    else
        fail "review-package without a plan errors with exit 2"
        echo "    exit: $rc"
    fi

    local rp_explicit explicit_path explicit_expected="$TEST_ROOT/explicit output.diff"
    rp_explicit="$(cd "$repo" && "$SDD_SCRIPTS/review-package" plan-a.md HEAD~1 HEAD "$explicit_expected")"
    explicit_path="$(printf '%s\n' "$rp_explicit" | sed -n 's/^wrote \(.*\): [0-9].*$/\1/p')"
    if [[ -s "$explicit_expected" ]] && same_path "$explicit_expected" "$explicit_path"; then
        pass "review-package honors an explicit OUTFILE with spaces"
    else
        fail "review-package honors an explicit OUTFILE with spaces"
        echo "    got: $rp_explicit"
    fi

    # --- Worktree isolation: a linked worktree resolves its own workspace ---
    local wt="$TEST_ROOT/linked worktree with spaces"
    ( cd "$repo" && git worktree add -q "$wt" -b wt-feature )
    local wt_root wt_dir
    wt_root="$(cd "$wt" && git rev-parse --show-toplevel)"
    wt_dir="$(cd "$wt" && "$SDD_SCRIPTS/sdd-workspace" plan-a.md)"
    if same_path "$wt_root/.superpowers/sdd/plan-a" "$wt_dir" && ! same_path "$dir_a" "$wt_dir"; then
        pass "linked worktree resolves its own distinct workspace"
    else
        fail "linked worktree resolves its own distinct workspace"
        echo "    main: $dir_a"
        echo "    wt:   $wt_dir"
    fi

    brief_out="$(cd "$wt" && "$SDD_SCRIPTS/task-brief" plan-a.md 1)"
    brief_path="$(printf '%s\n' "$brief_out" | sed -n 's/^wrote \(.*\): [0-9][0-9]* lines$/\1/p')"
    assert_same_path "$wt_root/.superpowers/sdd/plan-a/task-1-brief.md" "$brief_path" \
        "task-brief writes under the linked worktree's workspace"

    rp_out="$(cd "$wt" && "$SDD_SCRIPTS/review-package" plan-a.md HEAD~1 HEAD)"
    rp_path="$(printf '%s\n' "$rp_out" | sed -n 's/^wrote \(.*\): [0-9].*$/\1/p')"
    assert_same_path "$wt_root/.superpowers/sdd/plan-a/review-$base_short..$head_short.diff" "$rp_path" \
        "review-package writes under the linked worktree's workspace"

    printf 'y\n' > "$wt_dir/artifact.md"
    local wt_status
    wt_status="$(cd "$wt" && git status --porcelain)"
    if [[ "$wt_status" != *".superpowers"* ]]; then
        pass "worktree workspace invisible to git status"
    else
        fail "worktree workspace invisible to git status"
        echo "    status: $wt_status"
    fi

    echo ""
    if [[ "$FAILURES" -ne 0 ]]; then
        echo "FAILED: $FAILURES assertion(s)."
        exit 1
    fi
    echo "PASS: $PASSES assertion(s)."
}

main "$@"
