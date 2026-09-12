---
name: codebase-navigation
description: Use when working in a large or unfamiliar existing repository and the task lacks a known entry path, contract, state owner, or bounded evidence source.
---

# Codebase Navigation

## Purpose and Trigger

Establish current, evidence-backed context for one requested behavior or symptom.
Do not read or summarize the whole repository by default. Repository size is not
an architectural decision and missing notes are not a documentation assignment.

Use this skill when the relevant entry, state owner, contract, or proof is
unknown, or an investigation is expanding without a decision boundary.

Do not use it when a known local file and its direct test already establish a
small task, a current path card supplies the needed evidence links, or a pure
explanation needs no code inspection. A user-requested repository-wide map or
audit has its own explicit wider boundary; do not silently narrow that request.

## Task Map

Before broadening beyond the first relevant path, state the needed fields in
chat or the existing task record; a separate document is not required:

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

1. Read repository instructions and the smallest relevant entry/path note.
2. Find one candidate using an exact API, event, symbol, error, CLI command, or
   test name. If notes are absent, build this task map rather than an inventory.
3. Trace its trigger, direct owner, side effect, and proof. Inspect current
   source, tests, configuration/schema, or runtime evidence; notes are a map,
   not authority for what the code does today.
4. Inspect applicable boundaries only: authorization, atomicity, retry/order,
   compatibility, configuration, or recovery when the selected path involves
   them. Do not turn these categories into a checklist for every subsystem.

## Search Contract

For a search beyond the known file, define:

```text
Target:       exact symbol / API / event / config key / error / table
Scope:        first-party directories that can answer this task
Exclusions:   generated, vendor, build, fixture, or unrelated paths as applicable
Decision:     what a match or no-match will change
Stop:         when direct callers/consumers or the named risk boundary are enumerated
```

For example, search `publishPaymentEvent` in its source and tests, excluding
generated files, to enumerate direct consumers before changing its payload.
Read each relevant producer/consumer path once; unrelated keyword matches do
not create more work.

Expand a search only if current evidence identifies a new named boundary that
can change the decision. State the evidence, expanded scope, and new stop
condition. When evidence resolves a suspected crossing, narrow the map again.
A new public contract, subsystem, or irreversible effect may need design
approval; navigation itself does not authorize implementation or wider work.

## Unknown and Stop

When evidence is insufficient, state `Unknown`, the missing fact, and the next
cheapest verification. If that evidence is unavailable, stop or ask one focused
question; do not substitute an unlimited reading mission.

Example: `Unknown: whether the async consumer rechecks authorization. Next
cheapest verification: read workers/publish.ts and its denied-case test. Leave
the event contract unchanged until verified.`

Stop when the named decision and direct boundary are supported, or the missing
evidence has an explicit handoff. Report the path traced, verified facts and
invariants, proof actually run, remaining Unknowns, and exact next action.
Use the existing task report; durable notes are optional for recurring paths.
