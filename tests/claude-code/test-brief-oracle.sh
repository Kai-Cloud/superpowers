#!/usr/bin/env bash
# Offline fixed answers: reading a task brief is valid; reading the full plan is not.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/test-helpers.sh"

if ! declare -F assert_task_brief_contract >/dev/null; then
    printf '[FAIL] Missing shared task-brief oracle\n' >&2
    exit 1
fi

check_answer() {
    local expected="$1" answer="$2" name="$3" actual=fail
    if assert_task_brief_contract "$answer" >/dev/null 2>&1; then actual=pass; fi
    if [ "$actual" != "$expected" ]; then
        printf '[FAIL] %s: expected %s, got %s\n' "$name" "$expected" "$actual" >&2
        exit 1
    fi
    printf '[PASS] %s\n' "$name"
}

check_answer pass 'Controller provides: task brief file with full task text and relevant context
Implementer reads task brief file: yes
Implementer must read full plan file: no' 'Brief-file handoff is accepted'
check_answer pass 'Controller provides: full task text directly
Implementer reads task brief file: no
Implementer must read full plan file: no' 'Complete inline task text remains accepted'
check_answer pass 'Controller provides: TASK-BRIEF file with complete task context
Implementer reads task brief file: YES
Implementer must read full plan file: NO' 'Case and task-brief spelling do not change meaning'
check_answer fail 'Controller provides: path to full plan
Implementer reads task brief file: no
Implementer must read full plan file: yes' 'Full-plan handoff is rejected'
check_answer fail 'Controller provides: task brief file with full task text
Implementer reads task brief file: yes
Implementer must read full plan file: yes' 'Brief plus mandatory full-plan read is rejected'
check_answer fail 'Controller provides: task brief file with full task text
Implementer reads task brief file: yes' 'Missing full-plan decision is rejected'
check_answer fail 'Controller provides: task brief file with full task text
Implementer must read full plan file: no
Implementer must read full plan file: yes' 'Contradictory full-plan decisions are rejected'
check_answer fail 'Controller provides: path to full plan
Implementer must read full plan file: no' 'Plan-only context is rejected even with a no answer'
check_answer fail 'Controller provides: nothing; do not read any files
Implementer must read full plan file: no' 'Blank task context is rejected'
