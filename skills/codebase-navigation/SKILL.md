---
name: codebase-navigation
description: Use when working in a large or unfamiliar existing repository and the task lacks a known entry path, contract, state owner, or bounded evidence source.
---

# Codebase Navigation

## Purpose

A large repository is an executable dependency graph, not a book to read from
file one to file last. **Do not read or summarize the whole repository by
default.** The goal is not to claim that every file was seen. The goal is to
establish enough **current, evidence-backed context** to make one
requested change safely:

> Identify the requested behavior or symptom, its entry path, its owner and
> invariants, the direct risks that can change the decision, and the smallest
> proof that the result is correct.

Use existing code notes as a map when they exist. Current source, callers,
configuration, tests, and runtime evidence remain the authority.

## When to use

Use this skill when:

- a task targets a large or unfamiliar existing repository;
- a bug/feature request names an outcome but not the responsible module/path;
- the task may cross an API, state, queue, configuration, authorization, or
  persistence boundary;
- existing code notes are absent, stale, or do not cover the relevant path;
- an investigation is beginning to expand from one concrete question into
  unstructured repository exploration.

Do **not** use this skill when:

- the user explicitly requests a repository-wide inventory, audit, migration,
  or architecture map;
- a known local file and its direct test already establish a small task;
- the task is a pure explanation with no need to inspect code;
- a repository already has a current path card that identifies the exact
  entry, owner, invariant, and proof—read that card, then down-drill directly.

## The navigation contract

Before broadening beyond the first relevant file/path, write or be able to
state this contract:

```text
Requested behavior / observed symptom:
Entry or candidate path:
State owner / contract likely affected:
Direct callers, consumers, or named risk boundary to inspect:
Invariant(s) that must survive:
Proof expected:
Unknowns to resolve:
Stop condition:
```

This is not ceremony for its own sake. If the contract cannot be stated, the
next action is to identify the missing field—not to read random files until the
uncertainty feels smaller.

## Descent ladder

Use the smallest layer that can orient the task, then descend only when that
layer cannot establish a material fact:

```text
repository instructions / module card
  → relevant path card
    → contract, state, risk, test, and operations cards
      → current entry source, direct callers/consumers, config/schema, tests, trace
```

If no notes exist, create a **task map**, not an encyclopedia:

1. Read repository instructions, current branch/working-tree state, and the
   smallest root-level build/entry documentation that identifies the runtime.
2. Find one candidate entry using the symptom, public API, event, CLI command,
   test name, or error message.
3. Trace that candidate upstream to its trigger and downstream to its owner,
   side effect, failure boundary, and proof.
4. Record only the facts needed for this task. If the path will recur, promote
   them into a durable running note after the work is verified.

## Search contract

Before issuing `rg`, `grep`, or an equivalent repository search, define:

```text
Target:       exact symbol / API / event / config key / error / table
Scope:        first-party directories that can answer this task
Exclusions:   generated, vendor, build, fixture, or unrelated directories as applicable
Decision:     what a match or no-match will change
Stop:         when direct callers/consumers or the named risk boundary are enumerated
```

Example:

```text
Target: publishPaymentEvent
Scope: src/ and test/
Exclusions: generated/
Decision: find direct consumers before changing the event payload
Stop: inspect each direct producer/consumer path once
```

A broad keyword bundle such as `payment retry queue event`, or a repository-wide
search merely to feel safe, is not a valid search plan.

Expand a search only if current evidence identifies a new named boundary that
can change the next decision. Record why it expanded and the new stop condition.

## Boundary checks

For the selected path, inspect only concerns that apply. Do not mechanically
check every category in every task.

| Concern | Ask when applicable |
|---|---|
| Ownership | Who is the source of truth? Is state derived, cached, or replicated? |
| Authorization | Is access checked at every relevant ingress and asynchronous path? |
| Atomicity | What commits together? Can a side effect escape a failed transaction? |
| Idempotency | What happens on retry, duplicate event, or double submission? |
| Ordering | Are locks, versions, queues, or ordering assumptions involved? |
| Configuration | Which current flag/default/environment value controls this path? |
| Compatibility | Which direct consumer depends on this API/event/schema? |
| Failure | What error, retry, compensation, audit, or recovery path exists? |
| Proof | Which focused test, typecheck, trace, or controlled run proves the claim? |

## When evidence is insufficient

Do not convert uncertainty into an unlimited reading mission.

1. State `Unknown` precisely.
2. Name the missing evidence.
3. Name the cheapest verification that could change the next decision.
4. If that verification is unavailable or a product/architecture decision is
   genuinely required, ask one focused question or leave an explicit handoff.

Example:

```markdown
- **Unknown:** Whether the background consumer revalidates authorization.
- **Missing evidence:** Direct consumer source or an integration trace.
- **Next cheapest verification:** Read `workers/publish.ts` and run the denied-case test.
- **Do not change:** The event payload until that boundary is verified.
```

## Escalation

A large or unfamiliar repository by itself is not an architectural change.
Escalate scope only when evidence shows one of these:

- the requested change creates/restructures a cross-module public contract;
- a direct caller/consumer crosses a real API, event, schema, shared-state, or
  security boundary;
- the task introduces a new subsystem or durable state owner;
- a migration, authorization change, queue/retry rule, or irreversible effect
  genuinely changes deployment/recovery requirements;
- the user explicitly asks for a wider audit/map.

When escalating, state the evidence, expanded boundary, and decision it affects.
Do not treat “the repository is huge” or “I am not yet fully certain” as enough.

## Handoff

At the end of a bounded investigation or change, leave this record in an
existing project ledger/note or task report:

```markdown
## Navigation handoff — <task>

- **Revision / branch:** `<commit or branch>`
- **Path traced:** …
- **Facts verified:** …
- **Invariant(s) preserved:** …
- **Evidence actually run:** …
- **Unknowns / risks:** …
- **Exact next action:** Read `<card>` → inspect `<symbol>` → run `<command>`
```

## Common mistakes

| Mistake | Correct move |
|---|---|
| “The repo is large, so I should understand all of it first.” | Name one task path and trace it to a decision boundary. |
| “One more grep will make me confident.” | Search only if it resolves a named Unknown and has a stop condition. |
| “No notes means I must document every directory.” | Build the task map first; promote durable cards only for recurring paths. |
| “The note says this is true.” | Open the current source/test/config it references before changing behavior. |
| “I found a similar function, so this is the owner.” | Trace trigger, callers, state, and side effects before deciding. |
| “I cannot prove it, so I should keep reading.” | Record `Unknown`, next cheapest evidence, and stop or ask when needed. |

## Completion checklist

```markdown
- [ ] Requested behavior/symptom and task boundary are explicit
- [ ] Entry/candidate path and direct owner are identified or marked Unknown
- [ ] Search(es), if any, had target/scope/exclusions/decision/stop conditions
- [ ] Only applicable boundary risks were checked
- [ ] Current source/tests/config/trace evidence were used rather than notes alone
- [ ] Scope expansion, if any, has a named evidence trigger
- [ ] Proof is focused and proportional to the named claim
- [ ] Remaining Unknowns have next-cheapest verification and exact handoff
```
