---
name: requesting-code-review
description: Use when a human partner explicitly requests an independent review of a named Git range, or an explicitly selected SDD workflow requires its task-review process
---

# Requesting Code Review

Dispatch an independent reviewer only when your human partner explicitly asks for one. The reviewer gets precisely crafted context for one finite evidence pass — never your session's history.

**Core principle:** Review the named decision, then stop.

## When to Request Review

**Inside explicitly selected subagent-driven-development:**
- After each task, as required by that workflow

**Standalone:**
- When your human partner explicitly requests an independent review of a named range
- When your human partner explicitly requests review as a merge gate

Do not dispatch a standalone reviewer automatically after completing work,
before refactoring, when stuck, or because review might be valuable. Report the
available evidence inline unless an independent review was explicitly requested.

## Standalone Review

A standalone review is one finite pass over a named Git range and stated
requirements. It ends with its evidence report; it does not automatically
authorize remediation, another reviewer, a worktree, a plan,
subagent-driven-development, a broad suite, or model E2E.

Classify each concern in that report as one of:
- **Blocking:** a direct mismatch with a stated requirement, or verified broken
  behavior, security, data loss, or named contract risk.
- **Unknown — nonblocking:** the concern cannot be established from the range
  plus a justified direct boundary; include missing evidence and the next
  cheapest verification.
- **Deferred:** a minor improvement outside the requested scope.

Remediation and any re-review require a new explicit, scoped request from your
human partner. An explicitly selected SDD workflow uses its own scoped, capped
review loop instead.

## How to Request

A review begins from a named Git range and its requirements, not from an
assumption that a reviewer should reread an entire repository. If the change
may cross a direct contract boundary, name that boundary and why it can affect
the verdict. For a large/unfamiliar repository without a known path, establish
a bounded task map with `superpowers:codebase-navigation` before requesting broad review.

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Dispatch code reviewer subagent:**

Dispatch a `general-purpose` subagent, filling the template at [code-reviewer.md](code-reviewer.md)

**Placeholders:**
- `{DESCRIPTION}` - Brief summary of what you built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit

**3. Report the evidence:**
- State Blocking findings with the direct requirement, diff, or named boundary evidence.
- State Unknown — nonblocking items with their next cheapest verification.
- State Deferred items without turning them into a remediation agenda.
- End the standalone review. Apply remediation only under a new explicit, scoped request.

## Example

```
Human: Please commission an independent review of Task 2 before merge.

You: Dispatching one named-range review.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch code reviewer subagent]
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types
  PLAN_OR_REQUIREMENTS: Task 2 from docs/superpowers/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Blocking:
    Important: Missing progress indicators — requirement: report every 100 items
  Deferred: Magic number (100) is outside this named review request
  Assessment: Ready to merge? No

You: [Report the direct requirement failure and stop the standalone review]
[Await a separately scoped remediation request]
```

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll just review the diff myself instead of dispatching a reviewer" | When your human partner explicitly requested an independent review, dispatch the one named-range reviewer. Otherwise report the bounded evidence inline. |
| "The reviewer needs my whole session history to understand the change" | Hand it precisely crafted context, never your session's history. That keeps the reviewer on the work product, not your thought process. |

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

See template at: [code-reviewer.md](code-reviewer.md)
