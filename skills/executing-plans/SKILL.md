---
name: executing-plans
description: Use when a human partner explicitly selects inline execution of a named, approved multi-task implementation plan
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## Eligibility

Use this skill only when a named, approved, multi-task implementation plan exists and your human partner explicitly selected inline execution. A plan file, available subagents, or a request that could become implementation is not enough. If either condition is missing, report or finish the plan; do not create a worktree, dispatch workers, or begin task execution.

**Note:** Subagent-driven development can be appropriate for independent tasks only when your human partner explicitly selects subagent-driven-development. Subagent availability never substitutes for that selection.

## The Process

### Step 1: Load and Review Plan
1. Ensure an isolated workspace: use superpowers:using-git-worktrees to create one or verify the existing one
2. Read plan file
3. For each task, identify its entry/path, owner, direct contract/risk boundary, and proof. If a large or unfamiliar existing repository lacks those facts, invoke `superpowers:codebase-navigation` once to create a bounded task map; do not solve missing context by reading the whole repository.
4. Review critically - identify questions or concerns that can change a task decision
5. If a material fact remains Unknown: state the missing evidence and next cheapest verification; raise a focused question only when it genuinely blocks the task
6. If no blocking concern: Create todos for the plan items and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has a critical gap after its named path/boundary was checked
- A material entry, owner, or contract remains Unknown and the next cheapest verification is unavailable
- Verification fails repeatedly

**Ask for clarification rather than guessing or broadening into unbounded repository exploration.**

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
