#!/usr/bin/env bash
# Offline boundary tests. A fail-closed PATH stub prevents accidental model calls.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/claude-launcher.XXXXXX")
trap 'rm -rf "$TEST_ROOT"' EXIT
export TEST_ROOT REPO_ROOT
mkdir -p "$TEST_ROOT/bin" "$TEST_ROOT/plugin snapshot/.claude-plugin" "$TEST_ROOT/workspace" "$TEST_ROOT/user-config/plugins"
printf '{"name":"offline-fixture","version":"0.0.0"}\n' > "$TEST_ROOT/plugin snapshot/.claude-plugin/plugin.json"
printf 'fixture content\n' > "$TEST_ROOT/plugin snapshot/content.txt"
printf 'must not load\n' > "$TEST_ROOT/user-config/plugins/sentinel"
cat > "$TEST_ROOT/bin/claude" <<'STUB'
#!/usr/bin/env bash
printf 'UNEXPECTED DEFAULT CLI\n' >> "$TEST_ROOT/default-cli-called"
exit 97
STUB
cat > "$TEST_ROOT/selected stub.sh" <<'STUB'
#!/usr/bin/env bash
printf '%s\0' "$@" > "$TEST_ROOT/argv"
printf '%s\0' "${CLAUDE_CONFIG_DIR:-}" "${CLAUDE_CODE_SUBAGENT_MODEL:-}" "${CLAUDECODE:-}" "${ANTHROPIC_AUTH_TOKEN:-}" "${ANTHROPIC_API_KEY:-}" "${ANTHROPIC_BASE_URL:-}" > "$TEST_ROOT/env"
printf 'call\n' >> "$TEST_ROOT/calls"
if [ "${STUB_SLEEP:-0}" != 0 ]; then sleep "$STUB_SLEEP"; fi
if [ "${STUB_STREAM:-0}" = 1 ]; then
    printf '%s\n' '{"type":"system","subtype":"init","claude_code_version":"test-cli","model":"observed-model","plugins":[{"name":"offline-fixture","path":"observed-plugin-path"}]}' '{"type":"result","subtype":"success","total_cost_usd":0.25,"usage":{"input_tokens":8,"output_tokens":3},"modelUsage":{"observed-model":{}},"result":"OK"}'
else
    printf 'plain output\n'
fi
printf 'stub diagnostic\n' >&2
exit "${STUB_EXIT:-0}"
STUB
chmod +x "$TEST_ROOT/bin/claude" "$TEST_ROOT/selected stub.sh"
export PATH="$TEST_ROOT/bin:$PATH"
export CLAUDE_BIN="$TEST_ROOT/selected stub.sh" CLAUDE_TEST_MODE=1
export CLAUDE_CONFIG_DIR="$TEST_ROOT/user-config"
export CLAUDE_MODEL='exact-model[1m]' CLAUDE_EFFORT=high CLAUDE_MAX_BUDGET_USD=100
export CLAUDE_MAX_CALLS=1 ALLOW_MODEL_TESTS=1
export CLAUDECODE=nested ANTHROPIC_AUTH_TOKEN=fixture-token ANTHROPIC_API_KEY=conflicting-fixture-key
export ANTHROPIC_BASE_URL=https://offline.invalid
export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || command -v python)}"
source "$SCRIPT_DIR/test-helpers.sh"
cd "$TEST_ROOT/workspace"

fail() { printf '[FAIL] %s\n' "$*" >&2; exit 1; }
pass() { printf '[PASS] %s\n' "$*"; }
new_case() {
    export CLAUDE_TEST_ARTIFACTS="$TEST_ROOT/$1"
    unset STUB_STREAM STUB_EXIT STUB_SLEEP CLAUDE_OUTPUT_FORMAT
}
no_call() {
    rm -f "$TEST_ROOT/calls"
    if run_claude prompt "${1:-3}" > "$TEST_ROOT/rejected-output" 2>&1; then fail 'Invalid launch was accepted'; fi
    [ ! -e "$TEST_ROOT/calls" ] || fail 'Rejected launch still invoked the CLI'
}

# The ordinary API must preserve text and arguments without shell expansion.
new_case default-root
unset PLUGIN_DIR
prompt=$'literal "$HOME"; * $(not-a-command)\nsecond line'
output=$(run_claude "$prompt" 3 'Read,Bash(echo *)') || fail 'Shared launcher did not select CLAUDE_BIN'
[ "$output" = 'plain output' ] || fail 'Text stdout was changed or mixed with diagnostics'
"$PYTHON_BIN" - "$TEST_ROOT/argv" "$prompt" "$REPO_ROOT" <<'PY'
import pathlib, sys
args = pathlib.Path(sys.argv[1]).read_bytes().decode().split('\0')[:-1]
assert args[args.index('-p') + 1] == sys.argv[2], args
assert pathlib.Path(args[args.index('--plugin-dir') + 1]).resolve() == pathlib.Path(sys.argv[3]).resolve(), args
assert '--allowed-tools=Read,Bash(echo *)' in args, args
assert args[args.index('--output-format') + 1] == 'text', args
assert '--verbose' not in args and '--include-hook-events' not in args, args
PY
pass 'Selected argv launcher, root from BASH_SOURCE, and ordinary text output'

new_case stream
export PLUGIN_DIR="$TEST_ROOT/plugin snapshot" CLAUDE_OUTPUT_FORMAT=stream-json STUB_STREAM=1
run_claude "$prompt" 3 '' > "$TEST_ROOT/stream-output"
"$PYTHON_BIN" - "$TEST_ROOT" <<'PY'
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
args = (root / 'argv').read_bytes().decode().split('\0')[:-1]
for flag in ['--verbose', '--include-hook-events', '--strict-mcp-config', '--no-chrome']:
    assert flag in args, args
for flag, value in [('--output-format', 'stream-json'), ('--setting-sources', 'user'), ('--model', 'exact-model[1m]'), ('--effort', 'high'), ('--max-budget-usd', '100'), ('--permission-mode', 'bypassPermissions')]:
    assert args[args.index(flag) + 1] == value, args
assert not any(a.startswith('--allowed-tools') for a in args), args
assert pathlib.Path(args[args.index('--plugin-dir') + 1]).resolve() == (root / 'plugin snapshot').resolve()
config, child_model, nested, token, key, route = (root / 'env').read_bytes().decode().split('\0')[:-1]
run, = (root / 'stream').glob('run-*')
assert pathlib.Path(config).resolve() == (run / 'config').resolve()
assert not (pathlib.Path(config) / 'plugins' / 'sentinel').exists()
assert child_model == 'inherit' and nested == '' and token == 'fixture-token' and key == '' and route == 'https://offline.invalid'
settings = json.loads(pathlib.Path(args[args.index('--settings') + 1]).read_text())
assert settings['enabledPlugins'] == {}
mcp = json.loads(pathlib.Path(args[args.index('--mcp-config') + 1]).read_text())
assert mcp == {'mcpServers': {}}
p = json.loads((run / 'provenance.json').read_text())
assert p['requested']['model'] == 'exact-model[1m]'
assert pathlib.Path(p['requested']['plugin_dir']).resolve() == (root / 'plugin snapshot').resolve()
assert p['requested']['max_budget_usd'] == 100 and p['requested']['timeout_seconds'] == 3
assert p['requested']['retry_count'] == 0 and p['requested']['test_mode'] is True
assert p['source']['content_sha256'] and p['source']['git_sha'] is None
assert p['observed']['init']['model'] == 'observed-model'
assert p['observed']['init']['claude_code_version'] == 'test-cli'
assert p['observed']['init']['plugins'][0]['path'] == 'observed-plugin-path'
assert p['observed']['plugin_source_verified'] is False
assert p['observed']['child_models'] == 'NOT_VERIFIED'
assert p['observed']['result']['total_cost_usd'] == 0.25
assert p['exit_code'] == 0
assert (run / 'stdout.txt').read_bytes() == (root / 'stream-output').read_bytes()
assert (run / 'stderr.txt').read_text().strip() == 'stub diagnostic'
manifest = json.loads((run / 'source-manifest.json').read_text())
assert manifest['content.txt'] == hashlib.sha256(b'fixture content\n').hexdigest()
assert 'fixture-token' not in (run / 'provenance.json').read_text()
PY
pass 'Snapshot, isolation, routing env, stream flags, and honest provenance'

# A failed call consumes its reservation and cannot silently retry.
new_case failed
export STUB_EXIT=42
set +e
run_claude prompt 3 > "$TEST_ROOT/failure-stdout" 2> "$TEST_ROOT/failure-stderr"
status=$?
set -e
[ "$status" -eq 42 ] || fail 'Original CLI exit status was lost'
no_call
pass 'Failure status and one-call cap persist across command substitutions'

new_case timeout
export STUB_SLEEP=5
set +e
run_claude prompt 1 > /dev/null 2>&1
status=$?
set -e
[ "$status" -eq 124 ] || fail 'Finite timeout did not stop the CLI'
no_call
pass 'Timed-out invocation consumes its call without retry'

new_case opt-in
unset ALLOW_MODEL_TESTS
no_call
export ALLOW_MODEL_TESTS=1
pass 'Explicit model-test opt-in is required even for stubs'
new_case limits
for limit in 0 -1 infinite 1s; do no_call "$limit"; done
for budget in 0 -1 NaN Infinity 101; do
    export CLAUDE_MAX_BUDGET_USD="$budget"
    no_call
 done
export CLAUDE_MAX_BUDGET_USD=100 CLAUDE_MAX_CALLS=0
no_call
export CLAUDE_MAX_CALLS=1
pass 'Unbounded or invalid timeout, cost, and call limits are rejected'

new_case shim
unset CLAUDE_TEST_MODE
no_call
export CLAUDE_TEST_MODE=1
pass 'Script shims cannot masquerade as Windows native model CLI'
new_case source-cwd
(cd "$REPO_ROOT"; no_call)
export CLAUDE_TEST_ARTIFACTS="$REPO_ROOT/tests"
no_call
export CLAUDE_TEST_ARTIFACTS="$TEST_ROOT/plugin snapshot/artifacts"
no_call
pass 'Source cwd and in-source artifacts are rejected'
[ ! -e "$TEST_ROOT/default-cli-called" ] || fail 'The default CLI was probed or invoked'
printf 'Launcher offline tests passed.\n'
