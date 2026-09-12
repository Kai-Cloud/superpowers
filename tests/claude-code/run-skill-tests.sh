#!/usr/bin/env bash
# Deterministic tests by default. Live recall/integration is explicit and bounded.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/test-helpers.sh"

VERBOSE=false
SPECIFIC_TEST=""
TIMEOUT=900
RUN_MODEL=false
RUN_INTEGRATION=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --verbose|-v) VERBOSE=true; shift ;;
        --test|-t) SPECIFIC_TEST="${2:?Missing test name}"; shift 2 ;;
        --timeout) TIMEOUT="${2:?Missing timeout}"; shift 2 ;;
        --model) RUN_MODEL=true; shift ;;
        --integration|-i) RUN_INTEGRATION=true; shift ;;
        --help|-h)
            printf '%s\n' "Usage: $0 [--verbose] [--test NAME] [--timeout SECONDS] [--model] [--integration]" \
                'Default: local deterministic/fixture tests only; no Claude CLI probes.' \
                '--model: SDD description recall (9 calls, not a unit test).' \
                '--integration: real SDD execution (1 call; set --timeout above CLAUDE_PROMPT_TIMEOUT).' \
                'Live tests require ALLOW_MODEL_TESTS=1, external CLAUDE_TEST_ARTIFACTS,' \
                'and finite CLAUDE_MAX_CALLS, CLAUDE_PROMPT_TIMEOUT, CLAUDE_MAX_BUDGET_USD.'
            exit 0 ;;
        *) printf 'ERROR: Unknown option: %s\n' "$1" >&2; exit 2 ;;
    esac
done
[[ "$TIMEOUT" =~ ^[1-9][0-9]{0,5}$ ]] || { printf 'ERROR: --timeout must be finite positive seconds.\n' >&2; exit 2; }

offline_tests=(
    test-launcher.sh
    test-brief-oracle.sh
    test-skill-runner.sh
    test-worktree-path-policy.sh
    test-sdd-workspace.sh
    test-sdd-model-inheritance.sh
)
model_tests=(test-subagent-driven-development.sh)
integration_tests=(test-subagent-driven-development-integration.sh)
tests=("${offline_tests[@]}")
if [ "$RUN_MODEL" = true ]; then tests+=("${model_tests[@]}"); fi
if [ "$RUN_INTEGRATION" = true ]; then tests+=("${integration_tests[@]}"); fi
if [ -n "$SPECIFIC_TEST" ]; then tests=("$SPECIFIC_TEST"); fi

# Validate the entire selection before any test or fixture side effect.
for test in "${tests[@]}"; do
    case "$test" in
        test-subagent-driven-development.sh|test-subagent-driven-development-integration.sh|test-worktree-native-preference.sh)
            require_model_tests || exit 2 ;;
        *)
            known=false
            for local_test in "${offline_tests[@]}"; do
                if [ "$test" = "$local_test" ]; then known=true; break; fi
            done
            if [ "$known" != true ]; then printf 'ERROR: Unknown test: %s\n' "$test" >&2; exit 2; fi ;;
    esac
    [ -f "$SCRIPT_DIR/$test" ] || { printf 'ERROR: Missing test: %s\n' "$test" >&2; exit 2; }
done
printf 'Claude Code test suite: %s\n' "$CLAUDE_TEST_REPO_ROOT"
passed=0
failed=0
for test in "${tests[@]}"; do
    printf '\nRunning: %s\n' "$test"
    start_time=$(date +%s)
    status=0
    if [ "$VERBOSE" = true ]; then
        timeout --kill-after=5 "$TIMEOUT" bash "$SCRIPT_DIR/$test" || status=$?
    else
        output=$(timeout --kill-after=5 "$TIMEOUT" bash "$SCRIPT_DIR/$test" 2>&1) || status=$?
        if [ "$status" -ne 0 ]; then printf '%s\n' "$output"; fi
    fi
    duration=$(( $(date +%s) - start_time ))
    if [ "$status" -eq 0 ]; then
        printf '[PASS] %s (%ss)\n' "$test" "$duration"
        passed=$((passed + 1))
    else
        printf '[FAIL] %s (%ss, exit %s)\n' "$test" "$duration" "$status"
        failed=$((failed + 1))
    fi
done
printf '\nPassed: %s; Failed: %s\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
