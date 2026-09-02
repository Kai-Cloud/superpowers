---
name: using-superpowers
description: Use when starting a conversation with Superpowers installed, or when choosing which Superpowers skill applies to a substantive task.
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
A skill explicitly requested by your human partner MUST be invoked. Before a
substantive action, invoke the smallest skill whose process is materially
needed for that action.

Do NOT invoke or chain skills because there is a merely hypothetical 1% chance
they might help. A task needs a bounded path, not every process in the library.
</EXTREMELY-IMPORTANT>

## The Rule

**Invoke requested skills, and invoke materially relevant skills before the
substantive action they govern.** A pure explanation, a known local edit, or a
single targeted inspection does not automatically require a process ceremony.

**Before entering plan mode:** invoke brainstorming only when design work is
actually needed. In a large or unfamiliar existing repository whose relevant
path is not yet known, invoke `superpowers:codebase-navigation` first to establish that
path; do not replace navigation with a generic plan.

Then announce "Using [skill] to [purpose]" and follow the selected skill
exactly. If it has a checklist, create a todo per item.

## Scope Before Process Selection

For work in an existing repository, decide scope before selecting a heavyweight
process skill:

1. Name the requested behavior or observed symptom.
2. Identify the known entry/path, or name the exact missing fact.
3. If the repository is large or unfamiliar and that path is unknown, use
   `superpowers:codebase-navigation` to establish a bounded task map.
4. Select brainstorming, systematic-debugging, planning, TDD, review, or an
   implementation skill only when its process is needed by the named task.
5. Do not chain process skills merely because a task exists, a repository is
   large, or uncertainty feels uncomfortable.

If evidence remains insufficient, record `Unknown` and the next cheapest
verification. Do not turn uncertainty into an unbounded repository-reading
mission.

## Skill Priority

When multiple skills materially apply, process skills set the approach before
implementation skills. Use only the process skills required by the current
bounded task.

- "Let's build X" → `brainstorming` when design choices remain; in a large
  existing repository with no known target flow, `superpowers:codebase-navigation` first.
- "Fix this bug" → `systematic-debugging`; when the failing path is unknown in
  a large repository, establish its task map with `superpowers:codebase-navigation` first.
- "Read / map this repository" → `superpowers:codebase-navigation`.

## Red Flags

These thoughts mean STOP and re-scope:

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | A pure explanation may not need a process skill; an action still needs the smallest relevant one. |
| "I need more context first" | Name what context is missing and use the narrowest skill/path that can obtain it. |
| "Let me explore the whole codebase first" | Establish a task boundary and descend only through named paths and risks. |
| "I can check every git/file/test result quickly" | Check the evidence that can change this task's decision, not every artifact for reassurance. |
| "Let me gather more information" | State the Unknown and next cheapest verification before searching. |
| "This doesn't need a formal skill" | Use a materially relevant or requested skill; do not add unrelated ceremony. |
| "I remember this skill" | Skills evolve. Read the current selected skill before relying on it. |
| "This doesn't count as a task" | If an action changes code, state, or an external system, identify its bounded task path. |
| "The skill is overkill" | Choose the smallest applicable skill or record why a skill is not needed. |
| "I'll just do this one thing first" | Check repository instructions and the task boundary before a substantive action. |
| "This feels productive" | Evidence-driven progress beats unbounded browsing or ritual. |
| "I know what that means" | Knowing a concept does not replace checking current instructions or evidence. |

## Platform Adaptation

If your harness appears here, read its reference file for special instructions:

- Codex: `references/codex-tools.md`
- Pi: `references/pi-tools.md`
- Antigravity: `references/antigravity-tools.md`
- Hermes Agent: `references/hermes-tools.md`

## User Instructions

User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take precedence over skills, which in turn override default behavior. They may narrow or skip an otherwise applicable workflow when they give a clear task boundary, proof method, or contrary process instruction. Never use a plugin rule to override explicit safety, authorization, or deployment constraints.
