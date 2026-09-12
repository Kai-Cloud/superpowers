#!/usr/bin/env bash
# Offline runner tests use a fixture suite, never actual model tests.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/claude-runner.XXXXXX")
trap 'rm -rf "$TEST_ROOT"' EXIT
mkdir -p "$TEST_ROOT/suite/tests/claude-code" "$TEST_ROOT/bin"
cp "$SCRIPT_DIR/run-skill-tests.sh" "$TEST_ROOT/suite/tests/claude-code/"
cp "$SCRIPT_DIR/test-helpers.sh" "$TEST_ROOT/suite/tests/claude-code/"
export TEST_ROOT
for name in claude chmod; do
    printf '#!/usr/bin/env bash\nprintf "%%s\\n" "%s" >> "$TEST_ROOT/forbidden"\nexit 99\n' "$name" > "$TEST_ROOT/bin/$name"
done
chmod +x "$TEST_ROOT/bin/claude" "$TEST_ROOT/bin/chmod"
export PATH="$TEST_ROOT/bin:$PATH"
for name in test-launcher test-brief-oracle test-skill-runner test-worktree-path-policy test-sdd-workspace test-sdd-model-inheritance test-subagent-driven-development test-subagent-driven-development-integration; do
    printf '#!/usr/bin/env bash\nprintf "%%s\\n" "%s" >> "$TEST_ROOT/ran"\n' "$name" > "$TEST_ROOT/suite/tests/claude-code/$name.sh"
done
unset ALLOW_MODEL_TESTS
runner="$TEST_ROOT/suite/tests/claude-code/run-skill-tests.sh"
if ! bash "$runner" > "$TEST_ROOT/output" 2>&1; then
    printf '[FAIL] Default offline runner failed or probed Claude\n' >&2
    exit 1
fi
[ ! -e "$TEST_ROOT/forbidden" ] || { printf '[FAIL] Runner probed CLI or chmodded files\n' >&2; exit 1; }
if grep -q 'test-subagent-driven-development' "$TEST_ROOT/ran"; then
    printf '[FAIL] Default runner included a model test\n' >&2
    exit 1
fi
for required in test-launcher test-brief-oracle test-skill-runner; do
    grep -qx "$required" "$TEST_ROOT/ran" || { printf '[FAIL] Missing offline test: %s\n' "$required" >&2; exit 1; }
done
printf '[PASS] Default suite is offline without CLI probes or chmod\n'
for option in --model --integration; do
    rm -f "$TEST_ROOT/ran"
    if bash "$runner" "$option" > "$TEST_ROOT/output" 2>&1; then
        printf '[FAIL] %s did not require explicit opt-in\n' "$option" >&2
        exit 1
    fi
    [ ! -e "$TEST_ROOT/ran" ] || { printf '[FAIL] Ran tests before opt-in validation\n' >&2; exit 1; }
done
if bash "$runner" --test test-subagent-driven-development.sh > "$TEST_ROOT/output" 2>&1; then
    printf '[FAIL] Explicit test selection bypassed live opt-in\n' >&2
    exit 1
fi
if bash "$runner" --timeout 0 > "$TEST_ROOT/output" 2>&1; then
    printf '[FAIL] Unbounded runner timeout was accepted\n' >&2
    exit 1
fi
printf '[PASS] Live entrypoints and timeout validation fail closed\n'

# Direct entrypoints must reject before project setup, CLI calls, or git writes.
# A fake git is an alarm, so a pre-fix integration cannot create real commits.
printf '#!/usr/bin/env bash\nprintf "git\\n" >> "$TEST_ROOT/forbidden"\nexit 99\n' > "$TEST_ROOT/bin/git"
/bin/chmod +x "$TEST_ROOT/bin/git"
for entry in test-subagent-driven-development.sh test-subagent-driven-development-integration.sh; do
    rm -f "$TEST_ROOT/forbidden"
    if bash "$SCRIPT_DIR/$entry" > "$TEST_ROOT/output" 2>&1; then
        printf '[FAIL] Direct live entrypoint accepted missing opt-in: %s\n' "$entry" >&2
        exit 1
    fi
    [ ! -e "$TEST_ROOT/forbidden" ] || { printf '[FAIL] Live entrypoint had side effects before opt-in: %s\n' "$entry" >&2; exit 1; }
done
printf '[PASS] Direct live entrypoints reject before side effects\n'
