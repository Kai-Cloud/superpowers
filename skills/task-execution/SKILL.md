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
   At project or phase start, name the current usable slice: entry, user action,
   observable acceptance, exclusions; reuse the existing brief in a few lines.
   Conversational quick fixes do not require full product planning.
2. **Target context:** Use the known path, contract, and current evidence. Keep
   one task and its test evidence at a time. Retain a short context-budget
   summary; avoid repeated full reads. Fetch missing excerpts, not entire files
   already understood. Expand only for a named dependency revealed by evidence.
3. **Implementation:** Establish the focused failing proof for a new behavior;
   make the smallest meaningful change. Preserve correct baseline behavior.
   Before an edit, compare old and new: if `old == new`, skip the no-op.
   For a critical external dependency, do early minimum real-boundary validation
   when authorized. Label mock, model process, and actual service/broker evidence
   separately; do not call an untested boundary live-verified. Simulation is valid
   as the explicit phase goal; no unauthorized network access or trading.
   If repeated infrastructure-only increments or the same-fix loop do not advance
   acceptance, reassess the next dependency against the user outcome. This is
   not a mechanical stop and not an autonomous scope change: continue justified
   work under existing authorization; ask only for newly needed scope/authority.
   Preserve required tests and safety controls rather than remove them to ship.
   A no-op is not progress or success. Never retry a failed or no-op tool call
   with unchanged parameters. First identify the cause and change the input or
   approach; if no justified change is available, report blocked and stop.
4. **Target tests:** Run the exact proof for the named claim, check its result,
   and retain evidence tied to this revision. Reuse valid unchanged evidence.
   Broader checks require a named integration gate or task authorization;
   spare time is not a reason to add review or test loops.
5. **Truthful final:** In the existing final summary, report changes, tests
   actually run, and capability status with its evidence/limits: usable for the
   named acceptance, simulated, unverified, or blocked (per capability if mixed).
   No separate JSON or status artifact. When acceptance is met, stop using tools.
   If blocked or evidence is unavailable,
   state what remains unknown and the next cheapest verification, then stop or
   hand off. Do not turn a partial result into a completion claim.

An authorized review has a finite scope and stop condition. Address concrete
findings within that scope; do not autonomously recruit reviewers or reopen
review until no possible improvement remains. Permissions and human decisions
remain unchanged by this skill or a capability profile.
