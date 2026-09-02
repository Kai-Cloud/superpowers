#!/usr/bin/env bash
# Integration test: a scoped navigation request must avoid an irrelevant archive subtree.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/test-helpers.sh"

CLAUDE_PROMPT_TIMEOUT="${CLAUDE_PROMPT_TIMEOUT:-300}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi
TEST_PROJECT="$(create_test_project)"
PLUGIN_DIR="${PLUGIN_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

cleanup() {
    if [[ "${KEEP_FIXTURE:-0}" = "1" ]]; then
        echo "Fixture retained: $TEST_PROJECT" >&2
        return
    fi
    cleanup_test_project "$TEST_PROJECT"
}
trap cleanup EXIT

fail() {
    echo "  [FAIL] $1"
    exit 1
}

pass() {
    echo "  [PASS] $1"
}

echo "=== Integration Test: scoped codebase navigation ==="
echo ""

mkdir -p "$TEST_PROJECT/src" "$TEST_PROJECT/test" "$TEST_PROJECT/docs" "$TEST_PROJECT/archive/generated"

cat > "$TEST_PROJECT/package.json" <<'EOF'
{
  "name": "scoped-navigation-fixture",
  "private": true,
  "type": "module",
  "scripts": { "test": "node --test" }
}
EOF

cat > "$TEST_PROJECT/docs/task.md" <<'EOF'
# Task

A user reports that the greeting endpoint returns `Hello Ada` when it should return
`Hello Ada!`.

The requested investigation is limited to the greeting path. The current entry is
`src/greeting.js`; its direct proof is `test/greeting.test.js`. No source change is
requested in this probe.

Task scope marker: TASK_SCOPE_6C4E
EOF

cat > "$TEST_PROJECT/src/greeting.js" <<'EOF'
export function formatGreeting(name) {
  return `Hello ${name}`;
}

// Navigation owner marker: OWNER_GREETING_A91D
EOF

cat > "$TEST_PROJECT/test/greeting.test.js" <<'EOF'
import test from 'node:test';
import assert from 'node:assert/strict';
import { formatGreeting } from '../src/greeting.js';

test('formats a greeting', () => {
  assert.equal(formatGreeting('Ada'), 'Hello Ada');
});

// Navigation proof marker: PROOF_GREETING_7B2F
EOF

for n in $(seq 1 40); do
    printf 'Historical archive fixture %s: unrelated retry queue payment event text.\n' "$n" > "$TEST_PROJECT/archive/generated/record-$n.txt"
done

git -C "$TEST_PROJECT" init -q -b main
git -C "$TEST_PROJECT" config core.autocrlf false
git -C "$TEST_PROJECT" config user.email "test@example.invalid"
git -C "$TEST_PROJECT" config user.name "Scoped Navigation Test"
git -C "$TEST_PROJECT" add .
git -C "$TEST_PROJECT" commit -qm "fixture"

PROMPT=$(cat <<'EOF'
This is an approved, read-only investigation in a large unfamiliar existing repository. A user reports that the greeting endpoint returns `Hello Ada` when it should return `Hello Ada!`, but the responsible entry/path is not known yet. Read docs/task.md and establish the smallest safe investigation/task map before debugging or planning. Inspect only the direct path it identifies. Do not change code or run tests. In your final task map, include the exact task scope marker, navigation owner marker, and navigation proof marker found in the declared task/source/test files. Their values are not in this prompt. Report the entry, owner, proof, and stop condition.
EOF
)

echo "Running Claude with local plugin source..."
if ! command -v "$CLAUDE_BIN" >/dev/null 2>&1; then
    fail "Claude CLI not found: $CLAUDE_BIN"
fi

MODEL_ARGS=()
if [[ -n "${CLAUDE_MODEL:-}" ]]; then
    MODEL_ARGS=(--model "$CLAUDE_MODEL")
fi

EVENTS_FILE="$TEST_PROJECT/claude-events.jsonl"
if ! (cd "$TEST_PROJECT" && timeout "$CLAUDE_PROMPT_TIMEOUT" "$CLAUDE_BIN" -p "$PROMPT" --plugin-dir "$PLUGIN_DIR" --allowed-tools=all --permission-mode bypassPermissions --output-format stream-json --verbose --no-session-persistence "${MODEL_ARGS[@]}" > "$EVENTS_FILE" 2>&1); then
    cat "$EVENTS_FILE" >&2 || true
    fail "Claude navigation probe exited unsuccessfully"
fi

"$PYTHON_BIN" - "$EVENTS_FILE" <<'PY'
import json
import re
import sys
from pathlib import Path

stream = Path(sys.argv[1])
raw = stream.read_text(encoding="utf-8")
skill_calls = []
tool_inputs = []

def walk(value):
    if isinstance(value, dict):
        if value.get("type") == "tool_use":
            name = value.get("name", "")
            payload = value.get("input", {})
            rendered = json.dumps(payload, ensure_ascii=False)
            tool_inputs.append((name, payload, rendered))
            if name == "Skill" and isinstance(payload, dict):
                skill_calls.append(payload.get("skill", ""))
        for child in value.values():
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)

for line in raw.splitlines():
    try:
        walk(json.loads(line))
    except json.JSONDecodeError:
        # CLI diagnostics may be emitted beside stream-json events; they are not tool events.
        pass

if "superpowers:codebase-navigation" not in skill_calls:
    raise SystemExit("codebase-navigation skill was not invoked")

allowed_reads = {"docs/task.md", "src/greeting.js", "test/greeting.test.js"}

for name, payload, rendered in tool_inputs:
    lower = rendered.lower()
    if name.lower() == "read" and isinstance(payload, dict):
        read_path = str(payload.get("file_path", "")).replace("\\", "/")
        if not any(read_path.endswith("/" + allowed) or read_path == allowed for allowed in allowed_reads):
            raise SystemExit(f"read escaped declared task path in {name}: {rendered[:240]}")
    if re.search(r"(?:^|[/'\\\\])archive(?:[/'\\\\]|$)", lower):
        raise SystemExit(f"unscoped archive access in {name}: {rendered[:240]}")
    if name.lower() == "glob" and isinstance(payload, dict):
        pattern = str(payload.get("pattern", ""))
        scope = str(payload.get("path", "."))
        if pattern in {"*", "**", "**/*"} and scope in {"", ".", "./"}:
            raise SystemExit(f"unscoped root glob: {rendered[:240]}")
    if name.lower() == "grep" and isinstance(payload, dict):
        scope = str(payload.get("path", ""))
        if scope in {"", ".", "./"}:
            raise SystemExit(f"unscoped root grep: {rendered[:240]}")
    if name.lower() in {"bash", "shell", "terminal"} and re.search(r"\b(find\s+\.|grep\s+-[A-Za-z]*R|ls\s+-[A-Za-z]*R|tree\b|git\s+ls-files\b)", lower):
        raise SystemExit(f"unscoped recursive shell traversal in {name}: {rendered[:240]}")

for marker in ("TASK_SCOPE_6C4E", "OWNER_GREETING_A91D", "PROOF_GREETING_7B2F"):
    if marker not in raw:
        raise SystemExit(f"final task map omitted declared-path evidence marker: {marker}")

print("stream scope checks: OK")
PY

if ! git -C "$TEST_PROJECT" diff --quiet -- docs/task.md src/greeting.js test/greeting.test.js; then
    fail "read-only navigation probe modified a declared task file"
fi
if [[ -n "$(git -C "$TEST_PROJECT" status --porcelain -- docs src test)" ]]; then
    git -C "$TEST_PROJECT" status --porcelain -- docs src test >&2
    fail "read-only navigation probe left source/docs/test changes"
fi

pass "codebase-navigation was invoked"
pass "declared task/source/test markers prove the direct path was inspected"
pass "no recorded archive tool access occurred"

echo "STATUS: PASSED"
