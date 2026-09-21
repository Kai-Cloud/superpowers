---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write comprehensive implementation plans within the named task boundary, assuming the engineer has no context for that path. This is not a requirement to understand or enumerate the whole repository. Document the files, contracts, code, focused testing, and relevant docs needed for each deliverable. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Commit only when authorized.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** If working in an isolated worktree, it should have been created via the `superpowers:using-git-worktrees` skill at execution time.

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Scope Check

A plan is not authorization to execute. A read-only audit, explanation, or known
local test/fixture/harness correction ends with its evidence report or focused
proof; it does not need a new implementation-plan workflow. Use this skill for
the requested multi-step implementation deliverable, preserving an already
approved design and explicit scope.

Use the known task path. If its entry, owner, or contract is unknown in an
existing repository, use `superpowers:codebase-navigation` for a bounded task map.
Record remaining `Unknown` facts and the next cheapest verification; do not fill
gaps by inventing interfaces or reading the entire repository.

If the spec covers multiple independent subsystems, suggest separate plans —
one per independently testable subsystem. Expand only for an evidenced boundary;
when new evidence reduces scope, narrow the plan rather than retaining ceremony.
Branches, worktrees, preparation, and dependency installation need task-scoped
user/project authorization, not merely a plan or a detected manifest.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Task Right-Sizing

A task is the smallest unit that carries its own test cycle and is worth a
fresh reviewer's gate. When drawing task boundaries: fold setup,
configuration, scaffolding, and documentation steps into the task whose
deliverable needs them; split only where a reviewer could meaningfully
reject one task while approving its neighbor. Each task ends with an
independently testable deliverable.

## Verification Scope

Each task names the affected contract, focused command, and expected evidence.
For a critical external dependency, plan early minimum real-boundary validation
within existing authorization, before dependent infrastructure accumulates.
Distinguish mock, model process, and actual service/broker evidence; none implies
another is live-verified. Simulation is valid when it is the explicit phase goal.
An unavailable or unauthorized boundary stays unverified/blocked, not permission
to access it or force production scope.
A full suite needs a named integration boundary, repository rule, or final
delivery gate. Place that gate where its evidence is needed, not after every
unrelated step. Reuse current proof for an unchanged tree and claim; rerun when
relevant code, inputs, or the integration result changes. Report unrun/blocked
checks accurately; a focused pass is not a whole-repository claim.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Execute only after your human partner selects execution. Use superpowers:executing-plans for explicit inline execution, or superpowers:subagent-driven-development for explicit SDD. Preserve an already-selected mode; tool availability does not select it. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [Current usable slice: entry, user action, observable acceptance, exclusions; reuse the existing brief when available]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Spec:** [path to the spec/design doc this plan implements — the plan
argues from the spec, so the spec travels with it; executors read both]

## Global Constraints

[The spec's project-wide requirements — version floors, dependency limits,
naming and copy rules, platform requirements — one line each, with exact
values copied verbatim from the spec. Every task's requirements implicitly
include this section.]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Interfaces:**
- Consumes: [what this task uses from earlier tasks — exact signatures]
- Produces: [what later tasks rely on — exact function names, parameter
  and return types. A task's implementer sees only their own task; this
  block is how they learn the names and types neighboring tasks use.]

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.

## Execution Handoff

After saving the plan, if your human partner already selected an execution
mode, honor that choice without re-selection. In particular, explicit inline
execution stays inline even when subagents are available. If only plan writing
was requested, report the plan and stop. Otherwise, offer the choice when no
mode has been explicitly selected:

**"Plan complete and saved to `docs/superpowers/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:executing-plans
- Batch execution with checkpoints for review
