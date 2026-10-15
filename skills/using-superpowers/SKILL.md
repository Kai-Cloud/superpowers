---
name: using-superpowers
description: Use when starting a conversation with Superpowers installed, or when choosing which Superpowers skill applies to a substantive task.
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

## Shared Core

**Invoke requested skills and follow them.** Otherwise select from evidence,
not keywords: use the smallest materially relevant process, including none.

When the cause, target, and correction are established by sufficient evidence
(current contract, reproduction, diagnostic, or verified diff), take minimal
authorized action and focused verification; no skill is required. Confidence is
not evidence. Explicitly requested skills and required parent workflows remain binding.

1. **Goal:** Name requested behavior, task boundary, and finish condition. Separate
   the user goal from a suggested diagnosis; check an unverified causal premise
   against a safe current baseline before repair, reusing valid evidence.
2. **Target context:** Use known paths and relevant excerpts. For an unknown entry,
   owner, or contract, use `superpowers:codebase-navigation`. Keep the context budget:
   avoid repeated full reads; expand for evidence, not repository size. Batch
   independent known relevant reads in the same tool round where supported;
   serialize actual information dependencies. Read batching authorizes neither
   parallel agents nor mutations.
3. **Implementation:** Unresolved design → brainstorming; unresolved failure cause
   → systematic-debugging; new or unresolved code behavior lacking a failing proof
   → test-driven-development. Use `superpowers:task-execution` when needed or required
   by the parent workflow. Preserve selected execution mode and existing approval.
4. **Target tests:** Verify the named claim. Expand only for an evidenced boundary;
   evidence can also narrow process. State `Unknown` and the next cheapest
   verification for missing evidence; stop or hand off if unavailable.
5. **Truthful final:** Report changes, actual tests, and limits. Stop at the finish
   condition; no further tools after done.

Announce selected skills and purpose. If misinvoked, exit or narrow immediately;
explicit requests and required parent workflows remain binding. No extra reflection
report is required. Real feature design needs approval, not renewed approval for unchanged work.

## Non-Escalating Work

An audit, read-only investigation, explanation, or local correction to tests,
fixtures, assertions, harnesses, metadata, or non-behavioral documentation ends
with an evidence report or focused proof, not an implementation-plan workflow.
Uncertainty grants no new scope.

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
