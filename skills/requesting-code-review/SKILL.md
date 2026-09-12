---
name: requesting-code-review
description: Use when a human partner explicitly requests an independent review of a named Git range, or an explicitly selected SDD workflow requires its task-review process
---

# Requesting Code Review

Request an independent review for a named scope. The reviewer receives its
requirements, evidence, and diff, not the coordinator's session history.

## Entry Boundary

This skill is for the **coordinator**, not a dispatched reviewer. If you are
already a reviewer, do not invoke Skill, dispatch nested agents, or restart a
review workflow. Inspect the supplied evidence, return your report, and stop.

- A named read-only audit or Git-range review is non-escalating work. Review
  the range directly unless your human partner explicitly requested an
  independent reviewer. Tool availability alone does not authorize dispatch.
- An explicitly selected SDD implementation uses its required task review,
  scoped re-review, and final-review gates. Reuse those seats; do not add a
  second review of the same diff because it might be helpful.
- A completed feature, an available plan, or an intent to merge is not by
  itself authorization to start SDD or a new implementation workflow.

## Review Package and Dispatch

1. Identify the requested base/head and requirements. For an SDD task, use the
   recorded pre-task base, not `HEAD~1` (a task may contain several commits).
2. Pass the existing review package, brief, report, and relevant constraints.
   Use SDD's task or re-review template for those gates; use
   [code-reviewer.md](code-reviewer.md) for a requested independent range review
   or the final whole-branch review. An unavailable package calls for the named
   range's diff, not rediscovery of the whole project.
3. Fill the template directly. Preserve the same effective parent model using
   the harness's supported mechanism. Omitting `model` alone is not proof of
   inheritance; unconfirmed routing stays unverified. Do not change global
   model settings or substitute another model. SDD's Model Selection and
   Dispatch section defines its complete adapter contract.
4. On **Claude Code**, dispatch foreground with `run_in_background: false` and
   wait for the blocking return. On an asynchronous adapter, use supported
   completion events and bounded idle waits with a finite deadline; do not
   short-poll, duplicate dispatch, or invent results. Do not copy Claude-only
   fields to other harnesses.
5. Every reviewer dispatch explicitly says: read-only; no Skill invocation
   (including `requesting-code-review`); no nested agents/reviewers; no workflow
   restart; no checkout, index, HEAD, branch, or worktree mutation. The reviewer
   returns findings and stops. It does not run its own review process.

## Act Within the Existing Authorization

**Standalone audit:** return the report and stop. Do not fix, edit, or start an
implementation plan merely because the report contains Critical or Important
findings. A finding is evidence, not permission. Offer the smallest proposed
next step for your human partner to authorize separately.

**Already-approved implementation:** corrections may proceed only inside that
approved implementation scope. In SDD, the coordinator resumes the implementer
and uses the existing scoped re-review, at most five repair rounds per task and
one final fix wave. Reviewers never apply fixes. New scope needs new approval;
Minor or out-of-scope observations go to the ledger rather than extending the
loop. Address or explicitly adjudicate blocking findings before completion.

## Example: Requested Independent Audit

```text
Human: Independently review base123..head456. Read-only; do not fix anything.
Coordinator: Pass requirements and range package to one read-only reviewer.
Reviewer: Return findings with file:line evidence and a verdict; no Skill/agents.
Coordinator: Report the findings and stop. No fix dispatch follows this audit.
```

## Common Mistakes

| Excuse | Boundary |
|--------|----------|
| "The reviewer should invoke requesting-code-review" | The coordinator fills the template; the child reviews evidence and stops. |
| "Critical findings authorize immediate fixes" | Only already-approved implementation permits in-scope repairs; standalone audits stop at their report. |
| "Another reviewer would increase confidence" | Reuse the required review seat and evidence; do not duplicate work. |
| "The reviewer needs the whole session" | Give it the requirements, report, diff, and named risks, not accumulated history. |

See the final/range-review template at [code-reviewer.md](code-reviewer.md).
