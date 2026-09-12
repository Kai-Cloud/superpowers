#!/usr/bin/env bash
# All candidate validation here is deterministic; live smoke stays explicit.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/test-helpers.sh"
bash "$SCRIPT_DIR/run-skill-tests.sh"
for test in test-convergence-contracts.py test-validation-tiers.py test-bounded-smoke-oracles.py; do
    printf '\nRunning offline Python test: %s\n' "$test"
    claude_test_python -B "$SCRIPT_DIR/$test"
done
claude_test_python -B "$SCRIPT_DIR/../version-bump/test-version-registry.py"
claude_test_python -B "$SCRIPT_DIR/../version-bump/test-version-registry.py" --check
