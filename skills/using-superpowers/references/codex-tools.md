## Subagent dispatch requires multi-agent support

Add to your Codex config (`~/.codex/config.toml`):

```toml
[features]
multi_agent = true
```

This enables the multi-agent tools that skills like
`dispatching-parallel-agents` and `subagent-driven-development` use.
Which tools you get depends on the multi-agent version your model
preset selects (current presets run V2; older ones run V1). Trust your
actual tool list over any table — including this one — when they
disagree.

- **Spawning:** give children a clean context with
  `spawn_agent {fork_turns: "none"}`; the default `"all"` copies your
  entire transcript into the child. On Codex 0.145+, role files under
  `~/.codex/agents/` attach to isolated forks via `agent_type`.
  Some tool versions expose `model` and `reasoning_effort` on full-history
  forks (only `agent_type` is refused there). Supported fields do not
  authorize changing the parent model. SDD uses isolated context for
  hygiene; verify routing separately as described below.
- **Fix rounds:** resume the implementer with `followup_task` — it
  delivers your message, triggers a turn, and transparently reloads a
  child the harness evicted. Never dispatch a fresh implementer on the
  theory that a spawned agent cannot be messaged again; on V2 it
  always can.
- **Lifecycle:** V2 has no `close_agent`. Finished children are
  evicted automatically when slots are needed; leaving them unclosed
  costs nothing. Only V1 sessions have `close_agent` — there, close
  reviewers when their review returns, and close each implementer
  after its task's review passes.
- **Model names:** never copy a model name from a skill, table, or old
  session into `spawn_agent` without checking it against your current
  spawn allowlist — V2 accepts only V2-capable presets and hard-errors
  on the rest.

## Waiting on children

Codex's asynchronous adapter is not Claude Code's blocking foreground call.
Do not copy `run_in_background` into `spawn_agent`.

When exposed by the current tool list, `wait_agent` is an event subscription,
not a poll: a long wait wakes on child mailbox activity. Other versions use
their documented completion/wait interface, not invented fields.

- While independent local work remains, consume delivered completion events
  and keep working. Do not duplicate a child's assignment or dispatch.
- When genuinely idle, wait in bounded stretches within the tool's supported
  timeout range (5-10 minutes where allowed). On completion or timeout,
  reconcile outstanding children once and recover any completed report.
  Never replace completion events with repeated short polls.
- Record a finite task deadline before dispatch. If it expires without a
  usable result, report BLOCKED and stop further dispatch. Do not renew
  waits forever, fabricate the result, or replace a still-running child.
- If the harness delivers mailbox messages without waking an idle controller,
  the supported event wait covers that idle interval. If completion already
  wakes the controller, use that notification rather than another wait loop.

## Model routing on spawns

For SDD and review dispatches, preserve the same effective parent model for
implementers, task reviewers, re-reviewers, fix workers, and final reviewers.
Worker/reviewer role restrictions still apply: this adapter does not authorize
a spawned worker to start its own fan-out.

Use the current harness's documented inheritance mechanism, or pass the same
parent model explicitly only when the actual tool schema and spawn allowlist
support it. Never infer an API from a different harness or invent a model ID.
Where an explicit model resets effort, preserve the parent's effort using the
supported field if available; otherwise report the limitation. Do not silently
substitute a different model or effort as a fix for dispatch failure.

Omitting `model` alone is not proof of inheritance. Role files, subagent
defaults, and provider routing may change the effective child model. Check
available runtime metadata against the effective parent route; when that
cannot be confirmed, routing remains **unverified**, not passed or a proven
mismatch. A required route-verification gate stops on missing evidence; do not
launch extra probes outside the coordinator's finite validation budget.

Do not change or prescribe global model/effort configuration as a backstop.
Keep the parent's model intent at dispatch, using supported parameters only;
configuration changes require a separate request from your human partner.

## Environment Detection

Skills that create worktrees or finish branches should detect their
environment with read-only git commands before proceeding:

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

- `GIT_DIR != GIT_COMMON` → already in a linked worktree (skip creation)
- `BRANCH` empty → detached HEAD (cannot branch/push/PR from sandbox)

See `using-git-worktrees` Step 0 and `finishing-a-development-branch`
Step 1 for how each skill uses these signals.

## Codex App Finishing

When the sandbox blocks branch/push operations (detached HEAD in an
externally managed worktree), the agent commits all work and informs
the user to use the App's native controls:

- **"Create branch"** — names the branch, then commit/push/PR via App UI
- **"Hand off to local"** — transfers work to the user's local checkout

The agent can still run tests, stage files, and output suggested branch
names, commit messages, and PR descriptions for the user to copy.
