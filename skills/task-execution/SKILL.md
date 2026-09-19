---
name: task-execution
description: Use when beginning an actual implementation task within an authorized scope, including an already-approved plan or a bounded code change.
---

# Task Execution

Use at the implementation boundary, not for every question, explanation, or
read-only investigation. Keep parent workflow selection unchanged; preserve an
explicit inline or subagent-driven-development choice. This skill supplies a
local execution discipline, not a new approval or planning chain. An
already-approved task does not need approval again within the same scope.

1. **Goal:** Name the deliverable, acceptance condition, and authorized boundary.
2. **Target context:** Use the known path, contract, and current evidence. Keep
   one task and its test evidence at a time. Retain a short context-budget
   summary; avoid repeated full reads. Fetch missing excerpts, not entire files
   already understood. Expand only for a named dependency revealed by evidence.
3. **Implementation:** Establish the focused failing proof for a new behavior;
   make the smallest meaningful change. Preserve correct baseline behavior.
   Before an edit, compare old and new: if `old == new`, skip the no-op.
   A no-op is not progress or success. Never retry a failed or no-op tool call
   with unchanged parameters. First identify the cause and change the input or
   approach; if no justified change is available, report blocked and stop.
4. **Target tests:** Run the exact proof for the named claim, check its result,
   and retain evidence tied to this revision. Reuse valid unchanged evidence.
   Broader checks require a named integration gate or task authorization;
   spare time is not a reason to add review or test loops.
5. **Truthful final:** When acceptance is met, report changes, tests actually run,
   and limits, then stop using tools. If blocked or evidence is unavailable,
   state what remains unknown and the next cheapest verification, then stop or
   hand off. Do not turn a partial result into a completion claim.

An authorized review has a finite scope and stop condition. Address concrete
findings within that scope; do not autonomously recruit reviewers or reopen
review until no possible improvement remains. Permissions and human decisions
remain unchanged by this skill or a capability profile.
