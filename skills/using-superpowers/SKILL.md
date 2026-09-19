---
name: using-superpowers
description: Use when starting a conversation with Superpowers installed, or when choosing which Superpowers skill applies to a substantive task.
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

## Shared Core

**Invoke requested skills and follow them.** Otherwise choose the smallest
materially relevant skill before the action it governs; no mandatory skill chain.

1. **Goal:** Name the requested behavior, symptom, deliverable, task boundary,
   and finish condition.
2. **Target context:** Use known paths and direct proof. For an unknown entry,
   owner, or contract, use `superpowers:codebase-navigation`. Respect the context
   budget: retain a short evidence summary, avoid repeated full reads, and fetch
   only missing context that changes the next decision.
3. **Implementation:** Select only the process needed now: unresolved design
   choices → brainstorming; bugs → systematic-debugging; approved work → the
   explicitly selected execution mode. At an actual implementation boundary,
   use `superpowers:task-execution` within that mode, not to replace it.
   Existing approval remains valid within its scope; do not request it again.
4. **Target tests:** Verify the named claim with focused evidence. Expand only
   when evidence identifies a named boundary; evidence can also narrow scope
   and downgrade process. For missing evidence, state `Unknown` and the next
   cheapest verification; stop or hand off if unavailable.
5. **Truthful final:** Report changes, actual test evidence, and remaining limits.
   Stop when the finish condition is met; no further tools after done.

Announce the selected skill and purpose. Process skills govern implementation
skills; hypothetical relevance does not justify chaining them. Real feature
design still needs approval, not a second approval for an unchanged approved task.

## Non-Escalating Work

An audit, read-only investigation, explanation, or local correction to tests,
fixtures, assertions, harnesses, metadata, or non-behavioral documentation ends
with an evidence report or focused proof. It is not an implementation-plan workflow.
New production, public contract, routing, or authority scope requires the needed
approval before expansion. Uncertainty is not authorization.

A plan, tools, or manifest does not authorize branches, worktrees, dependencies,
broad/model tests, review, or deployment. A capability profile adjusts working
depth only, never tool permissions or parent workflow selection.

## Platform Adaptation

Read only the applicable harness reference:
- Codex: `references/codex-tools.md`
- Pi: `references/pi-tools.md`
- Antigravity: `references/antigravity-tools.md`
- Hermes Agent: `references/hermes-tools.md`

## User Instructions

User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, direct requests) take precedence
over skills, which override default behavior. A clear task boundary or proof
method can narrow or skip a workflow. Skills never override safety,
authorization, or deployment constraints; invocation grants no unrelated scope.
