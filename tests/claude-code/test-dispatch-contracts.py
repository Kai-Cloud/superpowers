#!/usr/bin/env python3
"""Model-free source-contract regressions, not runtime behavior/routing proof."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
SDD = ROOT / "skills/subagent-driven-development"
SKILL = SDD / "SKILL.md"
IMPLEMENTER = SDD / "implementer-prompt.md"
TASK_REVIEWER = SDD / "task-reviewer-prompt.md"
RE_REVIEWER = SDD / "re-review-prompt.md"
REQUEST = ROOT / "skills/requesting-code-review/SKILL.md"
FINAL_REVIEWER = REQUEST.with_name("code-reviewer.md")
INLINE = ROOT / "skills/executing-plans/SKILL.md"
CODEX = ROOT / "skills/using-superpowers/references/codex-tools.md"
TEMPLATES = (IMPLEMENTER, TASK_REVIEWER, RE_REVIEWER, FINAL_REVIEWER)
REVIEWERS = (TASK_REVIEWER, RE_REVIEWER, FINAL_REVIEWER)


def normalized(path):
    return " ".join(path.read_text(encoding="utf-8").lower().replace("`", "").split())


class DispatchContracts(unittest.TestCase):
    def require(self, path, pattern, contract):
        with self.subTest(file=str(path.relative_to(ROOT)), contract=contract):
            self.assertIsNotNone(re.search(pattern, normalized(path)), contract)

    def forbid(self, path, pattern, contract):
        with self.subTest(file=str(path.relative_to(ROOT)), contract=contract):
            match = re.search(pattern, normalized(path))
            self.assertIsNone(match, f"{contract}: {match.group(0) if match else ''}")

    def test_no_cost_tier_routing_in_prose_diagrams_or_templates(self):
        tier_routing = (
            r"\b(?:cheap(?:est)?|mid[- ]tier|standard|strong(?:est)?|"
            r"(?:more|most) capable(?: available)?) model\b|"
            r"\b(?:cheap(?:est)?|mid)[- ]tier\b|\bcapability bump\b"
        )
        for path in (SKILL, CODEX, REQUEST, *TEMPLATES):
            self.forbid(path, tier_routing, "no cost/capability-based model routing")
        for path in TEMPLATES:
            self.forbid(path, r"model: \[model", "no task-specific model placeholder")

    def test_same_parent_model_policy_is_preserved(self):
        self.require(SKILL, r"parent session owns model selection", "parent owns model selection")
        for path in (SKILL, CODEX):
            self.require(
                path, r"inherit\w* (?:the )?parent(?: session's)? model|same (?:effective )?parent model",
                "all harnesses retain the same-parent-model policy",
            )

    def test_omitted_model_is_not_runtime_inheritance_proof(self):
        for path in (SKILL, CODEX):
            self.require(
                path, r"omit\w* .{0,80}model.{0,100}(?:not|cannot).{0,30}(?:proof|prove|guarantee)",
                "omitting model alone is not inheritance proof",
            )
            self.require(path, r"effective.{0,40}child.{0,40}model|child.{0,40}effective.{0,40}model",
                         "verify the effective child model")
            self.require(path, r"(?:rout\w*|inherit\w*|model).{0,100}\b(?:unverified|not verified)\b|"
                         r"\b(?:unverified|not verified)\b.{0,100}(?:rout\w*|inherit\w*|model)",
                         "unconfirmed routing stays unverified")

    def test_no_global_model_configuration_backstop(self):
        self.forbid(CODEX, r"default_subagent_model|default_subagent_reasoning_effort",
                    "do not prescribe machine-level model/effort overrides")
        self.forbid(SKILL, r"explicit model overrides are forbidden in this fork",
                    "same-model supported adapters must not be forbidden as model changes")

    def test_blocking_and_async_waits_are_distinct(self):
        self.forbid(SKILL, r"all sdd workers are foreground calls",
                    "foreground is a Claude adapter rule, not a universal API")
        self.require(SKILL, r"claude(?: code)?.{0,200}run_in_background: false",
                     "Claude foreground dispatch is explicitly scoped")
        self.require(SKILL, r"(?:blocking|foreground).{0,200}(?:return|directly)",
                     "blocking calls wait for their result directly")
        self.require(SKILL, r"async(?:hronous)?.{0,220}(?:event|notification|completion)",
                     "async adapters use supported completion events")
        self.require(SKILL, r"async(?:hronous)?.{0,350}bounded",
                     "async idle waiting is bounded")
        self.require(CODEX, r"event subscription", "Codex waits remain event-driven")
        self.require(CODEX, r"bounded stretches", "Codex idle waits remain bounded")

    def test_template_harness_parameters_are_labeled(self):
        for path in TEMPLATES:
            self.require(path, r"run_in_background: false", "Claude template is foreground")
            text = normalized(path)
            if "run_in_background:" in text:
                with self.subTest(file=str(path.relative_to(ROOT))):
                    self.assertRegex(text.split("run_in_background:", 1)[0], r"\bclaude(?: code)?\b",
                                     "label Claude-specific syntax before the example")

    def test_all_reviewers_are_read_only_without_skills_or_nested_agents(self):
        for path in REVIEWERS:
            self.require(path, r"read-only", "reviewers are read-only")
            self.require(path, r"do not mutate", "reviewers cannot change checkout or Git state")
            self.require(path, r"(?:do not|never).{0,35}(?:use|invoke).{0,35}skill",
                         "reviewers do not invoke Skill")
            self.require(path, r"(?:do not|never).{0,35}(?:spawn|dispatch).{0,40}(?:subagent|agent|reviewer)",
                         "reviewers do not dispatch nested agents")
            self.require(path, r"(?:do not|never).{0,35}(?:run|restart|re-enter|invoke).{0,40}workflow",
                         "reviewers do not restart workflows")

    def test_final_reviewer_has_no_worktree_creation_example(self):
        self.forbid(FINAL_REVIEWER, r"git worktree add", "read-only review must not create worktrees")

    def test_explicit_inline_is_not_redirected_to_sdd(self):
        self.require(INLINE, r"(?:explicit\w*|chosen|selected).{0,75}inline|inline.{0,75}(?:explicit\w*|chosen|selected)",
                     "explicit inline selection is honored")
        self.forbid(INLINE, r"if subagents are available, use superpowers:subagent-driven-development instead",
                    "tool availability does not override explicit inline execution")

    def test_inline_reuses_checkout_without_automatic_worktree(self):
        self.forbid(INLINE, r"ensure an isolated workspace: use superpowers:using-git-worktrees",
                    "inline selection does not require a new worktree")
        self.require(INLINE, r"(?:existing|current) (?:authori[sz]ed )?checkout",
                     "inline execution starts in the existing checkout")
        self.require(INLINE, r"worktree.{0,120}only.{0,160}(?:explicit|repository rule)",
                     "worktree creation needs explicit selection or a repository rule")
        self.require(INLINE, r"already.{0,100}(?:chosen|selected).{0,160}(?:integration|disposition)",
                     "completion preserves an already-chosen integration disposition")

    def test_standalone_audit_reports_and_stops_without_repair_authority(self):
        self.require(REQUEST, r"(?:standalone|independent|read-only|audit).{0,240}report.{0,60}(?:stop|end)",
                     "standalone audit ends after its report")
        self.require(REQUEST, r"\b(?:do not|never|no)\b.{0,40}\b(?:fix|repair|edit)\w*\b",
                     "standalone findings do not authorize edits")
        self.require(REQUEST, r"(?:already|explicitly).{0,45}(?:approved|authori[sz]ed).{0,80}implement|"
                     r"implement.{0,45}(?:already|explicitly).{0,45}(?:approved|authori[sz]ed)",
                     "repairs are confined to already-approved implementation")

    def test_workers_use_local_proof_unless_a_full_gate_is_named(self):
        self.forbid(IMPLEMENTER, r"run the full suite once before committing",
                    "a commit is not an automatic full-suite gate")
        self.require(IMPLEMENTER, r"(?:local|focused|affected).{0,60}(?:proof|test|check|verification)",
                     "workers run local affected-contract proof")
        self.require(IMPLEMENTER, r"(?:named|explicit\w*).{0,80}(?:full suite|full-suite|integration|gate)|"
                     r"(?:full suite|full-suite).{0,80}(?:named|explicit\w*)",
                     "broader verification needs a named gate")
        self.require(IMPLEMENTER, r"never spawn a subagent|do not dispatch (?:nested )?(?:subagents|agents)",
                     "workers do not start nested validators")

    def test_controller_owns_finite_model_validation(self):
        self.require(SKILL, r"(?:controller|coordinator).{0,200}(?:model|behavior).{0,100}(?:validation|smoke|test)",
                     "coordinator owns model-behavior validation")
        self.require(SKILL, r"(?:finite|bounded|budget).{0,160}(?:model|behavior).{0,100}(?:validation|smoke|test)|"
                     r"(?:model|behavior).{0,100}(?:validation|smoke|test).{0,160}(?:finite|bounded|budget)",
                     "model validation has a finite budget")

    def test_native_file_plan_evidence_is_bounded(self):
        for pattern, contract in (
            (r"scripts/task-start", "file plans use start evidence"),
            (r"scripts/task-done", "file plans use done evidence"),
            (r"without a plan file", "conversational inline remains valid"),
            (r"no commit.{0,90}required|commit.{0,50}not required", "no forced commit"),
            (r"stale.{0,120}(?:stop|reconcile)|reconcile.{0,100}stale", "stale proof is not blindly reused"),
        ):
            self.require(INLINE, pattern, contract)

    def test_existing_brief_ledger_and_repair_limits_remain(self):
        for pattern, contract in (
            (r"scripts/task-brief", "brief extraction remains"),
            (r"scripts/review-package", "review package remains"),
            (r"never make a subagent read the whole plan", "brief replaces whole-plan rediscovery"),
            (r"do not re-dispatch them", "completed ledger tasks are not repeated"),
            (r"five rounds maximum per task", "five-round repair cap remains"),
            (r"dispatch one fix subagent", "final findings use one fix wave"),
            (r"no second fix wave", "final repair does not restart indefinitely"),
        ):
            self.require(SKILL, pattern, contract)


if __name__ == "__main__":
    unittest.main(verbosity=2)
