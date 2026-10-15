#!/usr/bin/env python3
"""Model-free convergence contracts for the approved 6.3.5 scope.

Run directly with Python; no project runner, dependencies, subprocesses, or writes.
These checks cover published instructions, not actual model behavior. Selected
contracts reuse 5c48a53/c12edf8/dcf01b9, not their complete files or workflows.
Execution-worker/model-policy contracts are owned by separate tests.

The 6.4.3/6.4.4 additions name routing, evidence, and read-scheduling contracts,
not agent compliance. Focused RED/GREEN stops at these checks plus bounded offline
regression; no model evaluation is authorized or implied.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "router": "skills/using-superpowers/SKILL.md",
    "design": "skills/brainstorming/SKILL.md",
    "navigation": "skills/codebase-navigation/SKILL.md",
    "debugging": "skills/systematic-debugging/SKILL.md",
    "tracing": "skills/systematic-debugging/root-cause-tracing.md",
    "plans": "skills/writing-plans/SKILL.md",
    "execution": "skills/task-execution/SKILL.md",
    "verification": "skills/verification-before-completion/SKILL.md",
    "finishing": "skills/finishing-a-development-branch/SKILL.md",
    "worktrees": "skills/using-git-worktrees/SKILL.md",
}


class ConvergenceContracts(unittest.TestCase):
    def text(self, name):
        path = ROOT / FILES[name]
        self.assertTrue(path.is_file(), f"Missing required contract file: {path}")
        return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))

    def require(self, name, pattern):
        self.assertIsNotNone(
            re.search(pattern, self.text(name), re.IGNORECASE),
            f"{FILES[name]}: missing contract /{pattern}/",
        )

    def reject(self, name, pattern):
        self.assertIsNone(
            re.search(pattern, self.text(name), re.IGNORECASE),
            f"{FILES[name]}: conflicting instruction /{pattern}/",
        )

    def test_context_reads_are_relevant_excerpts_not_size_driven_sweeps(self):
        # Missing excerpt guidance permits whole-file reads even with a known path.
        for name in ("router", "navigation", "execution"):
            with self.subTest(skill=name):
                self.require(name, r"(?:relevant|missing|bounded) excerpts")
        self.require("navigation", r"repository size.{0,100}(?:not|never).{0,80}(?:sweep|read)")

    def test_goal_is_separate_from_suggested_diagnosis(self):
        # Authorization of an outcome must not validate the proposed cause.
        for name in ("router", "execution", "debugging"):
            with self.subTest(skill=name):
                self.require(name, r"(?:goal|outcome).{0,100}(?:suggested|proposed) (?:diagnosis|cause)")
                self.require(name, r"(?:unverified|unproven).{0,100}(?:premise|cause|diagnosis).{0,180}(?:before|prior to) (?:repair|fix)")

    def test_unverified_premise_needs_safe_current_baseline_not_repeat_ceremony(self):
        for name in ("execution", "debugging"):
            with self.subTest(skill=name):
                self.require(name, r"minimum safe current (?:baseline|reproduction)")
                self.require(name, r"reuse valid existing evidence")
        self.require("debugging", r"(?:unsafe|unavailable).{0,150}Unknown")
        self.require("debugging", r"production.{0,120}(?:authorization|permission)")
        self.require("debugging", r"(?:matches|covers).{0,100}(?:current|relevant).{0,80}(?:state|revision|environment)")

    def test_independent_known_reads_share_round_not_serial_focus(self):
        for name in ("router", "navigation", "execution", "debugging"):
            with self.subTest(skill=name):
                self.require(name, r"(?:batch|combine).{0,100}independent.{0,60}(?:known|relevant).{0,60}reads")
                self.require(name, r"same tool round.{0,60}(?:supported|available)")
        self.require("navigation", r"serial.{0,100}(?:actual|real) information dependenc")
        self.require("execution", r"focus.{0,60}(?:not|isn't).{0,30}serial")

    def test_read_batching_does_not_authorize_agents_or_mutations(self):
        for name in ("router", "navigation", "execution"):
            with self.subTest(skill=name):
                self.require(name, r"(?:batching|reads).{0,120}(?:not|no|neither).{0,80}(?:agents|delegation).{0,80}mutations")

    def test_routing_uses_evidence_not_bug_keywords(self):
        self.reject("router", r"bugs\s*→\s*systematic-debugging")
        self.require("router", r"evidence.{0,100}not.{0,40}keyword")
        self.require("router", r"unresolved.{0,70}(?:cause|failure).{0,80}systematic-debugging")
        self.require("router", r"unresolved design.{0,50}brainstorming")
        self.require("router", r"(?:untested|unresolved).{0,60}(?:code|production).{0,100}test-driven-development")

    def test_known_correction_has_no_mandatory_skill_or_ceremony(self):
        self.require("router", r"cause, target, and correction.{0,100}(?:evidence|established)")
        self.require("router", r"minimal authorized action.{0,80}focused verification")
        self.require("router", r"no skill.{0,30}required")
        self.reject("router", r"At an actual implementation boundary, use")
        self.require("router", r"confidence.{0,80}not.{0,40}evidence")
        self.require("router", r"explicit.{0,50}(?:requested|required).{0,80}(?:skill|workflow)")

    def test_misinvocation_can_exit_without_new_report_or_workflow(self):
        self.require("router", r"(?:misinvoked|mis.invocation).{0,100}(?:exit|narrow).{0,50}immediately")
        self.require("router", r"no.{0,40}(?:reflection|report).{0,60}(?:required|artifact)")
        for name in ("design", "debugging", "execution"):
            self.require(name, r"(?:exit|narrow).{0,60}(?:immediately|without.{0,30}(?:phase|ceremony))")

    def test_debugging_does_not_repeat_established_cause_phases(self):
        self.reject("debugging", r"description: Use when encountering any bug")
        self.reject("debugging", r"Use for ANY technical issue")
        self.reject("debugging", r"If you haven't completed Phase 1, you cannot propose fixes")
        self.reject("debugging", r"For an authorized fix, complete each phase before proceeding")
        self.require("debugging", r"existing evidence.{0,100}(?:satisf|reuse)")
        self.require("debugging", r"cause, target, and correction.{0,130}focused verification")

    def test_design_does_not_require_new_approval_for_resolved_correction(self):
        self.require("design", r"cause, target, and correction.{0,140}evidence")
        self.reject("design", r"a config change.{0,100}MUST present")
        self.require("design", r"unresolved design.{0,100}(?:paths|gate)|(?:paths|gate).{0,100}apply to unresolved design")

    def test_execution_and_tdd_scope_known_corrections_before_phase_rules(self):
        self.require("execution", r"description:.{0,200}(?:unresolved|untested)")
        for name, path in (("execution", FILES["execution"]),
                           ("tdd", "skills/test-driven-development/SKILL.md")):
            text = re.sub(r"\s+", " ", (ROOT / path).read_text(encoding="utf-8"))
            self.assertRegex(text, r"cause, target, and correction.{0,160}evidence")
            self.assertRegex(text, r"focused verification")
            self.assertRegex(text, r"(?:explicitly requested|required by).{0,100}(?:workflow|skill|TDD)")
        tdd = (ROOT / "skills/test-driven-development/SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("Never fix bugs without a test.", tdd)
        self.assertRegex(tdd, r"(?s)unresolved.*behavior.*failing test")

    def test_phase_slice_reuses_brief_without_quickfix_planning(self):
        for name in ("design", "plans", "execution"):
            for term in (r"current usable slice", r"entry", r"user action",
                         r"observable acceptance", r"exclusions", r"reuse.{0,60}brief"):
                self.require(name, term)
        self.require("execution", r"quick fixes.{0,100}full product planning")

    def test_external_boundary_is_early_authorized_and_truthfully_labeled(self):
        for name in ("plans", "execution"):
            for term in (r"critical external dependenc", r"early.{0,100}minimum.{0,60}real.boundary",
                         r"authoriz", r"mock", r"model process", r"broker",
                         r"simulation.{0,100}phase goal", r"live.verified"):
                self.require(name, term)
        self.require("execution", r"no unauthorized network.{0,30}trading")

    def test_repeated_infrastructure_or_fix_loop_reassesses_outcome_conditionally(self):
        for term in (r"if.{0,100}repeated infrastructure.only", r"same.fix loop",
                     r"next dependency.{0,100}user outcome", r"not a mechanical stop",
                     r"not.{0,30}autonomous scope change", r"existing authorization",
                     r"preserve.{0,80}tests.{0,80}safety"):
            self.require("execution", term)

    def test_delivery_status_uses_existing_summary_not_a_new_artifact(self):
        for term in (r"existing final summary", r"usable", r"simulated", r"unverified",
                     r"blocked", r"no separate.{0,30}(?:artifact|JSON)"):
            self.require("execution", term)

    def test_router_removes_hypothetical_and_every_response_triggers(self):
        self.reject("router", r"even a 1% chance.{0,100}MUST invoke")
        self.reject("router", r"requiring skill invocation before ANY response")
        self.reject("router", r"If a skill exists, use it|Simple things become complex\. Use it")
        self.require("router", r"(?:smallest|materially relevant|materially needed).{0,100}(?:skill|process)")

    def test_router_names_boundary_before_selecting_process(self):
        self.require("router", r"(?:task boundary|scope before process selection)")
        self.require("router", r"(?:named|requested).{0,60}(?:behavior|symptom|task)")
        self.require("router", r"(?:evidence|verified).{0,160}(?:expand|escalat|boundary)")
        self.require("router", r"Unknown.{0,180}(?:cheapest|next).{0,60}(?:verification|evidence)")

    def test_router_does_not_turn_audit_or_harness_fix_into_project(self):
        self.require("router", r"(?:audit|read.only).{0,180}(?:explanation|local correction)")
        self.require("router", r"(?:test|fixture|assertion).{0,100}harness")
        self.require("router", r"(?:not|does not|do not).{0,80}(?:implementation.plan workflow|project workflow)")
        self.require("router", r"(?:evidence report|focused proof)")

    def test_requested_skills_and_direct_user_priority_survive(self):
        self.require("router", r"(?:invoke.{0,40}requested skills|requested.{0,80}(?:MUST|always).{0,40}invoke)")
        self.require("router", r"User instructions.{0,160}(?:take precedence|override).{0,30}skills")
        self.require("router", r"<SUBAGENT-STOP>.{0,160}ignore this skill")
        for reference in ("codex-tools.md", "pi-tools.md", "antigravity-tools.md", "hermes-tools.md"):
            self.require("router", re.escape(reference))

    def test_direct_scope_can_narrow_workflow_without_overriding_authority(self):
        self.require("router", r"(?:User instructions|direct requests).{0,500}(?:task boundary|proof method|explicit scope)")
        self.require("router", r"(?:narrow|skip).{0,100}(?:workflow|process)")

    def test_design_discovery_is_not_every_creative_action(self):
        self.reject("design", r"MUST use this before any creative work")
        self.require("design", r"description:.{0,120}new project")
        self.require("design", r"description:.{0,240}(?:unresolved requirements|design decision|multiple valid approaches)")

    def test_design_exempts_evidence_only_and_local_harness_work(self):
        self.require("design", r"(?:audit|read.only).{0,200}explanation")
        self.require("design", r"(?:test|fixture|assertion).{0,100}harness")
        self.require("design", r"(?:not design work|non.escalating work)")
        self.require("design", r"(?:evidence report|focused proof)")

    def test_design_can_converge_when_evidence_reduces_scope(self):
        self.reject("design", r"When in doubt.{0,80}(?:heavier|heavy)")
        self.reject("design", r"Nothing downgrades|ratchet is one.way|take the heavier path")
        self.require("design", r"(?:Upgrade|Expand|Escalate) only when evidence")
        self.require("design", r"(?:evidence.{0,180}(?:downgrade|narrower|lighter)|(?:downgrade|narrower|lighter).{0,180}evidence)")
        self.require("design", r"(?:large|unfamiliar) repository.{0,100}(?:not|does not).{0,80}architectural")

    def test_real_feature_design_approval_is_preserved(self):
        text = self.text("design")
        gate = re.search(r"<HARD-GATE>(.*?)</HARD-GATE>", text, re.IGNORECASE)
        self.assertIsNotNone(gate, "Real feature design approval must remain a hard gate")
        self.assertIsNotNone(re.search(r"until.{0,180}approved", gate.group(1), re.IGNORECASE))
        self.require("design", r"Implementation starts only after.{0,140}(?:yes|approv)")
        self.require("design", r"User reviews written spec")

    def test_navigation_is_conditional_not_mandatory_for_known_files(self):
        self.require("navigation", r"description:.{0,180}(?:lacks|unknown|not known).{0,80}(?:entry|path|contract)")
        self.require("navigation", r"Do not use.{0,350}known local file.{0,140}(?:direct test|small task)")
        self.require("navigation", r"(?:task map|navigation contract)")

    def test_navigation_task_map_has_bounded_fields(self):
        for field in (
            r"Requested behavior.{0,30}observed symptom",
            r"Entry.{0,30}(?:candidate )?path",
            r"State owner.{0,40}contract",
            r"Direct callers.{0,70}(?:consumers|boundary)",
            r"Invariant", r"Proof", r"Unknown", r"Stop condition",
        ):
            self.require("navigation", field)

    def test_navigation_search_contract_and_evidence_expansion(self):
        for field in ("Target:", "Scope:", "Exclusions:", "Decision:", "Stop:"):
            self.require("navigation", re.escape(field))
        self.require("navigation", r"Expand.{0,80}only if.{0,100}evidence.{0,100}(?:named )?boundary")
        self.require("navigation", r"(?:Do not|not to).{0,60}(?:read|summarize).{0,80}whole repository")

    def test_navigation_unknowns_have_cheapest_evidence_and_stop(self):
        self.require("navigation", r"Unknown")
        self.require("navigation", r"(?:next )?cheapest verification")
        self.require("navigation", r"unavailable.{0,250}(?:ask|handoff|stop)")
        self.require("navigation", r"(?:stop or ask|stop condition)")

    def test_debugging_follows_failing_path_not_all_components(self):
        self.reject("debugging", r"For EACH component boundary:")
        self.require("debugging", r"(?:investigation|task) boundary")
        self.require("debugging", r"(?:failing|selected|suspected) path")
        self.require("debugging", r"(?:Never|Do not).{0,80}(?:every|all) component")
        self.require("debugging", r"superpowers:codebase-navigation")

    def test_debugging_does_not_demand_every_reference_line(self):
        self.reject("debugging", r"read reference implementation COMPLETELY|Don't skim - read every line")
        self.reject("debugging", r"Partial understanding guarantees bugs\. Read it completely")
        self.require("debugging", r"(?:relevant|selected|named).{0,90}(?:reference|contract|pattern)")
        self.require("debugging", r"Unknown.{0,180}(?:cheapest|next).{0,60}(?:verification|evidence)")

    def test_tracing_stops_at_source_or_explicit_unknown(self):
        self.require("tracing", r"(?:trace|task) boundary")
        self.require("tracing", r"Unknown")
        self.require("tracing", r"(?:next )?cheapest (?:verification|evidence)")
        self.require("tracing", r"(?:stop|handoff)")
        self.reject("tracing", r'"Fix at symptom point"')
        self.require("tracing", r"(?:original trigger|source of.{0,40}(?:value|state))")

    def test_tracing_example_uses_focused_test_not_default_full_suite(self):
        self.reject("tracing", r"npm test 2>&1\s*\|\s*grep")
        self.require("tracing", r"(?:focused|targeted).{0,30}test")
        self.require("tracing", r"(?:not|do not).{0,100}read every caller")

    def test_plans_are_complete_within_task_not_repository_inventory(self):
        self.require("plans", r"(?:task boundary|bounded task map)")
        self.require("plans", r"not.{0,120}(?:understand|enumerate|read).{0,40}whole repository")
        self.require("plans", r"Unknown")
        self.require("plans", r"Test: `tests/exact/path/to/test.py`")
        self.require("plans", r"## No Placeholders")

    def test_plan_is_not_execution_consent(self):
        self.require("plans", r"A plan is not authorization to execute")
        self.require("plans", r"(?:explicitly|explicit).{0,100}(?:select|choos|choice)")
        self.require("plans", r"If Inline Execution chosen:.{0,120}superpowers:executing-plans")

    def test_existing_inline_choice_is_honored_without_reselection(self):
        self.require("plans", r"(?:already|explicitly).{0,100}(?:selected|chosen|chose).{0,180}(?:honor|preserve|follow|do not re|without re|use that)")
        self.require("plans", r"Inline Execution")
        self.reject("plans", r"if.{0,50}subagents.{0,50}available.{0,100}(?:MUST|always).{0,40}(?:SDD|subagent.driven)")

    def test_verification_matches_named_claim_not_largest_suite(self):
        self.require("verification", r"(?:named|specific).{0,40}(?:claim|contract)")
        self.require("verification", r"(?:not the largest available suite|not.{0,70}(?:full|whole).{0,20}(?:suite|repository))")
        self.reject("verification", r"Partial proves nothing")
        self.require("verification", r"(?:unrun|unverified|not run|not verified).{0,160}(?:claim|report|scope|suite)|(?:report|claim).{0,160}(?:unrun|unverified|not run|not verified)")

    def test_verification_still_requires_real_current_evidence(self):
        self.require("verification", r"NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE")
        self.require("verification", r"check exit code")
        self.require("verification", r"State actual status with evidence")
        self.require("verification", r"Bug fixed.{0,60}Test original symptom")

    def test_full_verification_has_named_gate_and_avoids_redundancy(self):
        self.require("verification", r"(?:full|whole).{0,30}(?:suite|repository).{0,300}(?:integration|repository rule|final.{0,30}gate)")
        self.require("verification", r"(?:unchanged|same tree|same revision).{0,180}(?:reuse|repeat|rerun|redundan)|(?:reuse|repeat|rerun|redundan).{0,180}(?:unchanged|same tree|same revision)")

    def test_finishing_does_not_unconditionally_run_project_full_suite(self):
        self.reject("finishing", r"Run the project's full test suite")
        self.require("finishing", r"(?:named|scope|scoped).{0,100}integration|integration.{0,100}(?:named|scope|scoped)")
        self.require("finishing", r"(?:full|whole).{0,30}(?:suite|repository).{0,220}(?:require|gate|unrelated)")
        self.require("finishing", r"verification-before-completion|(?:required|scoped|focused) verification")

    def test_finishing_preserves_integration_and_discard_consent(self):
        self.require("finishing", r"Wait for their answer; the integration decision is theirs")
        self.require("finishing", r"Type 'discard' to confirm")
        self.require("finishing", r"Never `--force` on your own initiative")
        self.require("finishing", r"Tests fail on the merged result: stop")

    def test_finishing_honors_explicit_keep_without_menu(self):
        self.require("finishing", r"(?:explicitly|already).{0,100}(?:chose|chosen|selected|keep).{0,180}honor")
        self.require("finishing", r"keep.{0,300}(?:skip|without|do not).{0,40}(?:integration )?menu")
        self.require("finishing", r"(?:skip|without).{0,140}(?:integration.only|integration.only checks)")

    def test_worktree_discovery_and_creation_need_task_authority(self):
        self.reject("worktrees", r"description:.{0,240}or before executing implementation plans")
        self.require("worktrees", r"description:.{0,200}explicit(?:ly)?")
        self.require("worktrees", r"(?:human partner|user|project).{0,140}(?:authoriz|instruct|consent|request)")
        self.require("worktrees", r"(?:plan|subagent availability).{0,100}(?:not|no).{0,80}(?:consent|authoriz)")
        self.require("worktrees", r"(?:task scope|task boundary|named task)")

    def test_worktree_setup_is_not_manifest_driven_install(self):
        self.reject("worktrees", r"Auto-detect and run appropriate setup")
        self.reject("worktrees", r"if \[ -f (?:package\.json|Cargo\.toml|requirements\.txt|pyproject\.toml|go\.mod) \]; then (?:npm install|cargo build|pip install|poetry install|go mod download)")
        self.require("worktrees", r"(?:do not|not).{0,100}(?:install|download).{0,180}(?:manifest|ecosystem)")
        self.require("worktrees", r"(?:task|scoped|focused).{0,100}(?:proof|verification)")
        self.require("worktrees", r"(?:setup|install|preparation).{0,180}(?:authoriz|instruct|consent)|(?:authoriz|instruct|consent).{0,180}(?:setup|install|preparation)")

    def test_worktree_baseline_is_scoped_and_claims_are_accurate(self):
        self.require("worktrees", r"(?:baseline|verification).{0,120}(?:task|scope|claim)|(?:task|scope|claim).{0,120}baseline")
        self.require("worktrees", r"(?:not run|unverified|not verified|blocked)")
        self.require("worktrees", r"(?:full|whole).{0,30}(?:suite|repository).{0,240}(?:integration|require|gate)")
        self.require("worktrees", r"Do NOT create another worktree")
        self.require("worktrees", r"Native Worktree Tools")


if __name__ == "__main__":
    unittest.main(verbosity=2)
