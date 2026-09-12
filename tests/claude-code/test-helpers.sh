#!/usr/bin/env bash
# Helper functions for Claude Code skill tests

# Derive the source checkout when sourced, not from a temporary fixture's cwd.
CLAUDE_TEST_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
export CLAUDE_TEST_REPO_ROOT

claude_test_python() {
    if [ -n "${PYTHON_BIN:-}" ]; then
        "$PYTHON_BIN" "$@"
    elif command -v python3 >/dev/null 2>&1; then
        python3 "$@"
    elif command -v python >/dev/null 2>&1; then
        python "$@"
    else
        printf 'ERROR: Python 3 is required for offline test artifacts; no installation attempted.\n' >&2
        return 1
    fi
}

# Native Windows CLI argv/config paths use cygpath, never guessed drive rewrites.
claude_test_native_path() {
    if command -v cygpath >/dev/null 2>&1; then cygpath -am "$1"; else printf '%s\n' "$1"; fi
}

require_model_tests() {
    if [ "${ALLOW_MODEL_TESTS:-}" != 1 ]; then
        printf 'ERROR: Live tests require explicit ALLOW_MODEL_TESTS=1.\n' >&2
        return 1
    fi
}

# Standard-library metadata only: never probe the CLI or read user credentials.
# The manifest hashes source bytes (including dirty/untracked files), not a claimed version.
claude_test_artifact() {
    claude_test_python - "$@" <<'PY'
import hashlib
import json
import os
import pathlib
import struct
import subprocess
import sys
from datetime import datetime, timezone

mode, *args = sys.argv[1:]
if mode == 'prepare':
    source, repo, artifacts, cwd, binary, timeout, budget, cap, test_mode, model, effort, output, *argv = args
    timeout, cap = int(timeout), int(cap)
    budget = float(budget)
    source, repo, artifacts, cwd, binary = map(lambda p: pathlib.Path(p).resolve(), (source, repo, artifacts, cwd, binary))
    for path, name in ((cwd, 'cwd'), (artifacts, 'artifacts')):
        if path.is_relative_to(source) or path.is_relative_to(repo):
            raise SystemExit(f'ERROR: {name} must be external to the source checkout/snapshot')
    if os.name == 'nt' and test_mode != '1':
        with binary.open('rb') as f:
            header = f.read(64)
            if binary.suffix.lower() != '.exe' or header[:2] != b'MZ' or len(header) < 64:
                raise SystemExit('ERROR: Windows model tests require a native .exe; stubs require CLAUDE_TEST_MODE=1')
            f.seek(struct.unpack_from('<I', header, 60)[0])
            if f.read(4) != b'PE\0\0':
                raise SystemExit('ERROR: CLAUDE_BIN is not a native Windows PE executable')
    artifacts.mkdir(parents=True, exist_ok=True)
    # A filesystem reservation survives command substitution and concurrent shells.
    run = None
    for number in range(1, cap + 1):
        candidate = artifacts / f'run-{number:03d}'
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        run = candidate
        break
    if run is None:
        raise SystemExit('ERROR: CLAUDE_MAX_CALLS exhausted; no retries or extra calls permitted')
    config = run / 'config'
    config.mkdir()
    settings = {'enabledPlugins': {}, 'autoUpdatesChannel': 'stable'}
    (config / 'settings.json').write_text(json.dumps(settings), encoding='utf-8')
    (run / 'settings.json').write_text(json.dumps(settings), encoding='utf-8')
    (run / 'mcp.json').write_text('{"mcpServers":{}}', encoding='utf-8')
    manifest = {}
    for base, dirs, files in os.walk(source):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', 'node_modules', '__pycache__'})
        for name in sorted(files):
            path = pathlib.Path(base) / name
            if name == '.git':
                continue
            payload = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
            manifest[path.relative_to(source).as_posix()] = hashlib.sha256(payload).hexdigest()
    serialized = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    (run / 'source-manifest.json').write_bytes(serialized + b'\n')
    def git(*command):
        result = subprocess.run(['git', '-C', str(source), *command], capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    git_sha = dirty = None
    top = git('rev-parse', '--show-toplevel')
    if top and pathlib.Path(top).resolve() == source:
        git_sha = git('rev-parse', 'HEAD')
        dirty = git('status', '--porcelain', '--untracked-files=all')
    provenance = {
        'started_at': datetime.now(timezone.utc).isoformat(),
        'requested': {'cli_bin': str(binary), 'plugin_dir': str(source), 'cwd': str(cwd),
                      'model': model or None, 'effort': effort, 'output_format': output,
                      'timeout_seconds': timeout, 'max_budget_usd': budget, 'max_calls': cap,
                      'retry_count': 0, 'test_mode': test_mode == '1', 'child_model': 'inherit'},
        'source': {'git_sha': git_sha, 'dirty': bool(dirty) if dirty is not None else None,
                   'content_sha256': hashlib.sha256(serialized).hexdigest(),
                   'digest_excludes': ['.git', 'node_modules', '__pycache__']},
        'observed': {'init': None, 'result': None, 'plugin_source_verified': False,
                     'child_models': 'NOT_VERIFIED'},
        'argv': argv,
        'exit_code': None,
    }
    (run / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print(run.as_posix())
elif mode == 'finish':
    run, status, *argv = args
    run = pathlib.Path(run)
    path = run / 'provenance.json'
    provenance = json.loads(path.read_text(encoding='utf-8'))
    provenance['argv'] = argv
    provenance['exit_code'] = int(status)
    provenance['finished_at'] = datetime.now(timezone.utc).isoformat()
    for line in (run / 'stdout.txt').read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get('type') == 'system' and event.get('subtype') == 'init':
            provenance['observed']['init'] = {key: event[key] for key in ('model', 'claude_code_version', 'plugins', 'skills', 'session_id', 'cwd') if key in event}
        elif event.get('type') == 'result':
            provenance['observed']['result'] = {key: event[key] for key in ('subtype', 'is_error', 'total_cost_usd', 'usage', 'modelUsage', 'session_id') if key in event}
    path.write_text(json.dumps(provenance, indent=2), encoding='utf-8')
PY
}

# Single CLI entrypoint. Text remains the default; stream JSON is opt-in.
# Live contract: ALLOW_MODEL_TESTS=1, CLAUDE_BIN, PLUGIN_DIR (default: this repo),
# CLAUDE_MODEL, CLAUDE_EFFORT=high, CLAUDE_MAX_BUDGET_USD<=100,
# CLAUDE_TEST_ARTIFACTS=external unique directory, CLAUDE_MAX_CALLS=1 by default.
# Usage: run_claude PROMPT [TIMEOUT_SECONDS=60] [allowed_tools]
run_claude() (
    require_model_tests || return
    local prompt="${1:?Prompt required}" timeout_seconds="${2:-60}" allowed_tools="${3:-}"
    local budget="${CLAUDE_MAX_BUDGET_USD:-100}" cap="${CLAUDE_MAX_CALLS:-1}"
    local format="${CLAUDE_OUTPUT_FORMAT:-text}" effort="${CLAUDE_EFFORT:-high}"
    if ! [[ "$timeout_seconds" =~ ^[1-9][0-9]{0,5}$ && "$cap" =~ ^[1-9][0-9]{0,3}$ && "$budget" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
        printf 'ERROR: Positive finite timeout, cost and call limits are required.\n' >&2
        return 2
    fi
    if ! claude_test_python -c 'import sys; x=float(sys.argv[1]); sys.exit(not 0 < x <= 100)' "$budget"; then
        printf 'ERROR: CLAUDE_MAX_BUDGET_USD must be greater than zero and at most 100.\n' >&2
        return 2
    fi
    case "$format" in text|json|stream-json) ;; *) printf 'ERROR: Unsupported output format.\n' >&2; return 2;; esac
    case "$effort" in low|medium|high|xhigh|max) ;; *) printf 'ERROR: Unsupported effort.\n' >&2; return 2;; esac
    local plugin="${PLUGIN_DIR:-$CLAUDE_TEST_REPO_ROOT}" binary="${CLAUDE_BIN:-claude}"
    local artifacts="${CLAUDE_TEST_ARTIFACTS:-}"
    if [ -z "$artifacts" ]; then
        printf 'ERROR: Set CLAUDE_TEST_ARTIFACTS to an external unique directory.\n' >&2
        return 2
    fi
    case "$plugin" in /*|[A-Za-z]:[\\/]*) ;; *) printf 'ERROR: PLUGIN_DIR must be absolute.\n' >&2; return 2;; esac
    case "$artifacts" in /*|[A-Za-z]:[\\/]*) ;; *) printf 'ERROR: CLAUDE_TEST_ARTIFACTS must be absolute.\n' >&2; return 2;; esac
    plugin=$(cd "$plugin" && pwd -P) || return
    if [ ! -f "$plugin/.claude-plugin/plugin.json" ]; then
        printf 'ERROR: PLUGIN_DIR does not contain a Claude plugin manifest.\n' >&2
        return 2
    fi
    binary=$(command -v "$binary") || { printf 'ERROR: CLAUDE_BIN was not found; no installation attempted.\n' >&2; return 2; }
    binary=$(claude_test_native_path "$binary") || return
    plugin=$(claude_test_native_path "$plugin") || return
    artifacts=$(claude_test_native_path "$artifacts") || return
    local cmd=("$binary" -p "$prompt" --plugin-dir "$plugin" --output-format "$format"
        --effort "$effort" --max-budget-usd "$budget")
    if [ -n "${CLAUDE_MODEL:-}" ]; then cmd+=(--model "$CLAUDE_MODEL"); fi
    if [ -n "$allowed_tools" ]; then cmd+=(--allowed-tools="$allowed_tools"); fi
    if [ "$format" = stream-json ]; then cmd+=(--verbose --include-hook-events); fi
    local run_dir
    run_dir=$(claude_test_artifact prepare "$plugin" "$(claude_test_native_path "$CLAUDE_TEST_REPO_ROOT")" "$artifacts" "$(claude_test_native_path "$PWD")" \
        "$binary" "$timeout_seconds" "$budget" "$cap" "${CLAUDE_TEST_MODE:-0}" "${CLAUDE_MODEL:-}" "$effort" "$format" "${cmd[@]}") || return
    cmd+=(--settings "$run_dir/settings.json" --setting-sources user
        --strict-mcp-config --mcp-config "$run_dir/mcp.json" --no-chrome --permission-mode bypassPermissions)
    # Only these disposable-fixture child processes use bypassPermissions.
    # Credentials stay in the child environment, never in provenance or argv.
    export CLAUDE_CONFIG_DIR="$run_dir/config" CLAUDE_CODE_SUBAGENT_MODEL=inherit
    export DISABLE_AUTOUPDATER=1 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
    unset CLAUDECODE
    if [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ]; then unset ANTHROPIC_API_KEY; fi
    local status=0
    timeout --kill-after=5 "$timeout_seconds" "${cmd[@]}" > "$run_dir/stdout.txt" 2> "$run_dir/stderr.txt" || status=$?
    claude_test_artifact finish "$run_dir" "$status" "${cmd[@]}" || return
    printf 'Claude test artifacts: %s\n' "$run_dir" >&2
    if [ "$status" -eq 0 ]; then
        cat "$run_dir/stdout.txt"
    else
        cat "$run_dir/stdout.txt" "$run_dir/stderr.txt" >&2
    fi
    return "$status"
)

# Fixed, structured recall oracle: allow a complete brief file or inline text,
# but never require the implementer to load the controller's full plan.
assert_task_brief_contract() {
    local answer="$1"
    printf '%s\n' "$answer" | grep -Eiq '^Controller provides:.*(task[ -]brief|full.*(task )?text|complete.*task)' &&
    printf '%s\n' "$answer" | grep -Eiq '^Implementer must read full plan file:[[:space:]]*no[[:space:].]*$' &&
    ! printf '%s\n' "$answer" | grep -Ei '^Implementer must read full plan file:' | grep -Eivq ':[[:space:]]*no[[:space:].]*$'
}

# Check if output contains a pattern
# Usage: assert_contains "output" "pattern" "test name"
# Matching is case-insensitive: patterns are prose keywords, and models
# freely capitalize skill terms ("Do Not Trust", "Spec Compliance").
assert_contains() {
    local output="$1"
    local pattern="$2"
    local test_name="${3:-test}"

    if echo "$output" | grep -qi "$pattern"; then
        echo "  [PASS] $test_name"
        return 0
    else
        echo "  [FAIL] $test_name"
        echo "  Expected to find: $pattern"
        echo "  In output:"
        echo "$output" | sed 's/^/    /'
        return 1
    fi
}

# Check if output does NOT contain a pattern
# Usage: assert_not_contains "output" "pattern" "test name"
assert_not_contains() {
    local output="$1"
    local pattern="$2"
    local test_name="${3:-test}"

    if echo "$output" | grep -qi "$pattern"; then
        echo "  [FAIL] $test_name"
        echo "  Did not expect to find: $pattern"
        echo "  In output:"
        echo "$output" | sed 's/^/    /'
        return 1
    else
        echo "  [PASS] $test_name"
        return 0
    fi
}

# Check if output matches a count
# Usage: assert_count "output" "pattern" expected_count "test name"
assert_count() {
    local output="$1"
    local pattern="$2"
    local expected="$3"
    local test_name="${4:-test}"

    local actual=$(echo "$output" | grep -ci "$pattern" || echo "0")

    if [ "$actual" -eq "$expected" ]; then
        echo "  [PASS] $test_name (found $actual instances)"
        return 0
    else
        echo "  [FAIL] $test_name"
        echo "  Expected $expected instances of: $pattern"
        echo "  Found $actual instances"
        echo "  In output:"
        echo "$output" | sed 's/^/    /'
        return 1
    fi
}

# Check if pattern A appears before pattern B
# Usage: assert_order "output" "pattern_a" "pattern_b" "test name"
assert_order() {
    local output="$1"
    local pattern_a="$2"
    local pattern_b="$3"
    local test_name="${4:-test}"

    # Get line numbers where patterns appear
    local line_a=$(echo "$output" | grep -ni "$pattern_a" | head -1 | cut -d: -f1)
    local line_b=$(echo "$output" | grep -ni "$pattern_b" | head -1 | cut -d: -f1)

    if [ -z "$line_a" ]; then
        echo "  [FAIL] $test_name: pattern A not found: $pattern_a"
        echo "  In output:"
        echo "$output" | sed 's/^/    /'
        return 1
    fi

    if [ -z "$line_b" ]; then
        echo "  [FAIL] $test_name: pattern B not found: $pattern_b"
        echo "  In output:"
        echo "$output" | sed 's/^/    /'
        return 1
    fi

    if [ "$line_a" -lt "$line_b" ]; then
        echo "  [PASS] $test_name (A at line $line_a, B at line $line_b)"
        return 0
    else
        echo "  [FAIL] $test_name"
        echo "  Expected '$pattern_a' before '$pattern_b'"
        echo "  But found A at line $line_a, B at line $line_b"
        return 1
    fi
}

# Create a temporary test project directory
# Usage: test_project=$(create_test_project)
create_test_project() {
    local test_dir=$(mktemp -d)
    echo "$test_dir"
}

# Cleanup test project
# Usage: cleanup_test_project "$test_dir"
cleanup_test_project() {
    local test_dir="$1"
    if [ -d "$test_dir" ]; then
        rm -rf "$test_dir"
    fi
}

# Create a simple plan file for testing
# Usage: create_test_plan "$project_dir" "$plan_name"
create_test_plan() {
    local project_dir="$1"
    local plan_name="${2:-test-plan}"
    local plan_file="$project_dir/docs/superpowers/plans/$plan_name.md"

    mkdir -p "$(dirname "$plan_file")"

    cat > "$plan_file" <<'EOF'
# Test Implementation Plan

## Task 1: Create Hello Function

Create a simple hello function that returns "Hello, World!".

**File:** `src/hello.js`

**Implementation:**
```javascript
export function hello() {
  return "Hello, World!";
}
```

**Tests:** Write a test that verifies the function returns the expected string.

**Verification:** `npm test`

## Task 2: Create Goodbye Function

Create a goodbye function that takes a name and returns a goodbye message.

**File:** `src/goodbye.js`

**Implementation:**
```javascript
export function goodbye(name) {
  return `Goodbye, ${name}!`;
}
```

**Tests:** Write tests for:
- Default name
- Custom name
- Edge cases (empty string, null)

**Verification:** `npm test`
EOF

    echo "$plan_file"
}

# Export functions for use in tests
export -f run_claude
export -f assert_contains
export -f assert_not_contains
export -f assert_count
export -f assert_order
export -f create_test_project
export -f cleanup_test_project
export -f create_test_plan
