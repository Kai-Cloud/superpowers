---
name: executing-plans
description: Use when a human partner explicitly selects inline execution of a named, approved multi-task implementation plan
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Explicit inline execution stays inline.** Execute the approved tasks in this
session even when subagent tools are available. Do not redirect to
superpowers:subagent-driven-development or delegate implementation merely
because those tools exist. A different workflow requires your human partner's
explicit selection. An audit or read-only investigation does not enter this
implementation workflow.

## The Process

### Step 1: Load and Review Plan
1. Verify the existing checkout and use it by default. Use
   superpowers:using-git-worktrees only when your human partner explicitly
   requests a worktree or an applicable repository rule requires one. Reuse an
   existing worktree; honor explicit current-checkout/no-worktree instructions.
2. Read plan file
3. Review critically - identify any questions or concerns about the plan
4. If concerns: Raise them with your human partner before starting
5. If no concerns: Create todos for the plan items and proceed

### Step 2: Execute Tasks

For an approved file plan with numbered `Task N` headings, use this skill's
helpers via bash in the authorized checkout:

```bash
bash scripts/task-start PLAN_FILE N
# Implement the task; retain the printed BASE.
bash scripts/task-done PLAN_FILE N BASE -- EXECUTABLE ARG...
```

These share SDD's owned `.superpowers/sdd/` workspace and `progress.md`, not a
second controller or ledger. Start prints brief/base/workspace; done validates
plan/task/ownership/base before running explicit argv, retaining command, exit,
log path/hash and checkout evidence. Plan text is never shell-evaluated. A silent
exit 0 is valid; failed verification keeps its unique log and is not completion.
Use a read-only focused verifier: code changes during verification withhold
completion. No commit, worktree, review, or model change is required by these
helpers; dirty and untracked source files are included in checkout evidence.

For each task:
1. Start and read its brief; an unchanged `status: complete` resumes without
   rerunning implementation or verification just for bookkeeping.
2. Implement the approved steps, then pass the focused verification command to
   done. A named integration boundary, repository rule, or final-delivery
   requirement may require a full suite; do not repeat it after every task.
3. Mark complete only with successful evidence. A stale proof means stop and
   reconcile changed scope/evidence, not automatically rerun a completed task.
   Earlier task evidence remains historical when later tasks change the checkout.
   Ignored dependencies and external environment changes need separate judgment;
   checkout hashes do not prove them unchanged. Retain records, do not delete
   evidence to force a fresh run.

Ordinary conversational inline work without a plan file remains valid: use
superpowers:task-execution and record focused command/results in the conversation.
Do not create a plan merely to use these helpers or redirect that work to SDD.

For skill-behavior changes, the coordinator owns the separately approved,
finite-budget model validation (named cases, call/time/cost limits, and stop
condition). Local static checks alone do not establish behavioral success.
No model run is implied merely by selecting inline execution.

### Step 3: Complete Development

After all tasks complete and verified:
- If your human partner has already chosen the integration disposition (for
  example, keep changes in the current checkout without committing), honor it
  and report the results. Do not present another menu or commit/push.
- Otherwise, use superpowers:finishing-a-development-branch to present the
  remaining integration choices. Reuse fresh verification evidence rather than
  re-running unchanged tests just to enter that workflow.

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- A required verification gate cannot be met or its deadline/budget is exhausted

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent
