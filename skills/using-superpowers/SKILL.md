---
name: using-superpowers
description: Use when starting a conversation with Superpowers installed, or when choosing which Superpowers skill applies to a substantive task.
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

## Shared Core

**Invoke requested skills and follow them.** Otherwise select from evidence,
not keyword matches: use the smallest materially relevant process, including none.

When the cause, target, and correction are established by sufficient evidence
(current contract, reproduction, diagnostic, or verified diff), take the minimal
authorized action and focused verification; no skill is required. Labels like
"bug" or "implementation" do not mandate ceremony. Confidence is not evidence.
Explicitly requested skills and required parent-workflow steps remain binding.

1. **Goal:** Name the requested behavior, task boundary, and finish condition.
2. **Target context:** Use known paths and proof. For an unknown entry, owner,
   or contract, use `superpowers:codebase-navigation`. Respect the context budget:
   avoid repeated full reads; fetch only evidence that changes the next decision.
3. **Implementation:** Unresolved design choices → brainstorming; unresolved
   failure cause → systematic-debugging; new or unresolved code behavior lacking
   a failing proof → test-driven-development. Use `superpowers:task-execution`
   when its discipline is needed or the parent workflow requires it. Preserve
   the explicitly selected execution mode and existing approval within scope.
4. **Target tests:** Verify the named claim. Expand only for an evidenced boundary;
   evidence can also narrow process. State `Unknown` and the next cheapest
   verification for missing evidence; stop or hand off if unavailable.
5. **Truthful final:** Report changes, actual tests, and limits. Stop when the
   finish condition is met; no further tools after done.

Announce a selected skill and purpose. If misinvoked, exit or narrow immediately
when its trigger is absent; do not finish irrelevant phases. Preserve explicit
requests and required parent workflow; no extra reflection report is required.
Real feature design needs approval, not renewed approval for unchanged work.

## Non-Escalating Work

An audit, read-only investigation, explanation, or local correction to tests,
fixtures, assertions, harnesses, metadata, or non-behavioral documentation ends
with an evidence report or focused proof, not an implementation-plan workflow.
New scope needs authorization; uncertainty grants none.

Plans, tools, and manifests do not authorize branches, worktrees, dependencies,
broad/model tests, review, or deployment. Profiles adjust depth, not permissions
or parent workflow.

## Platform Adaptation

Read only the applicable reference:
- Codex: `references/codex-tools.md`
- Pi: `references/pi-tools.md`
- Antigravity: `references/antigravity-tools.md`
- Hermes Agent: `references/hermes-tools.md`

## User Instructions

User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, direct requests) take precedence
over skills. A task boundary or proof method can narrow or skip a workflow.
Skills never override safety, authorization, or deployment constraints.
