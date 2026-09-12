---
name: using-superpowers
description: Use when starting a conversation with Superpowers installed, or when choosing which Superpowers skill applies to a substantive task.
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

## Start With the Task Boundary

**Invoke requested skills and follow them.** For other work, choose the smallest
materially relevant skill before the action it governs:

1. Name the requested behavior, symptom, or deliverable and its task boundary.
2. Use the known entry/path and direct proof. If an existing repository's path,
   owner, or contract is unknown, use `superpowers:codebase-navigation` to build
   a bounded task map; known local files do not need another navigation pass.
3. Select only the process needed now: design choices → brainstorming; a bug →
   systematic-debugging; an approved multi-step deliverable → planning or the
   execution mode explicitly selected by your human partner.
4. Expand only when evidence identifies a named boundary that changes the
   decision. New evidence can also narrow the scope and downgrade the process.
   If evidence is missing, state `Unknown` and the next cheapest verification;
   stop or hand off when that evidence is unavailable.
5. Announce "Using [skill] to [purpose]" and follow the selected skill's checklist.

Process skills set the approach before implementation skills when both apply.
A hypothetical chance of relevance is not a reason to chain skills. Entering
plan mode does not itself create a need for brainstorming; unresolved design
choices do. Real feature design still needs your human partner's approval.

## Non-Escalating Work

An audit, read-only investigation, explanation, or known local correction to
tests, fixtures, assertions, harnesses, metadata, or non-behavioral documentation
ends with an evidence report or focused proof. It is not an implementation-plan
workflow. Do the authorized inspection/correction, verify its named claim, and
stop rather than starting a design, worktree, execution, or integration ceremony.

If evidence instead establishes a production behavior, public contract, routing,
or authority change, explain that new boundary and obtain the needed approval
before expanding the task. Uncertainty alone does not authorize expansion.
A plan, available tools, or a manifest is not consent to create branches or
worktrees, install dependencies, or run broad/model tests; use task-scoped
user/project authorization for preparation and verification.

## Platform Adaptation

If your harness appears here, read its reference file for special instructions:

- Codex: `references/codex-tools.md`
- Pi: `references/pi-tools.md`
- Antigravity: `references/antigravity-tools.md`
- Hermes Agent: `references/hermes-tools.md`

## User Instructions

User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take
precedence over skills, which in turn override default behavior. A clear task
boundary, proof method, or contrary process instruction can narrow or skip an
otherwise applicable workflow. Skills never override safety, authorization, or
deployment constraints, and invoking one does not authorize unrelated work.
