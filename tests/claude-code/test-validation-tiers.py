#!/usr/bin/env python3
"""Offline instruction-contract lint, NOT consuming-agent behavior validation.

Only reads the five scoped documents; no model, evaluator, subprocess, or network.
Real behavior evidence remains the coordinator's separately authorized work.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
WRITING = "skills/writing-skills/SKILL.md"
PRESSURE = "skills/writing-skills/testing-skills-with-subagents.md"
TDD = "skills/test-driven-development/SKILL.md"
GOOD_TESTS = "skills/test-driven-development/writing-good-tests.md"
CONTRIBUTOR = "CLAUDE.md"


def plain(text):
    return re.sub(r"\s+", " ", text.replace("**", "").replace("`", "")).strip()


class ValidationTierContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = {name: (ROOT / name).read_text(encoding="utf-8")
                    for name in (WRITING, PRESSURE, TDD, GOOD_TESTS, CONTRIBUTOR)}

    def require(self, text, patterns, reason):
        missing = [pattern for pattern in patterns if not re.search(pattern, plain(text), re.I)]
        self.assertFalse(missing, f"{reason}; missing contract(s): {missing}")

    def section(self, name, title):
        text = self.docs[name]
        match = re.search(r"(?im)^(#{2,3})[ \t]+" + title + r"\b[^\n]*\n", text)
        self.assertIsNotNone(match, f"{name}: missing {title} section")
        rest = text[match.end():]
        next_heading = re.search(r"(?m)^#{1," + str(len(match[1])) + r"}[ \t]+", rest)
        return match[0] + (rest[:next_heading.start()] if next_heading else rest)

    def test_focused_defaults_to_deterministic_local_proof(self):
        focused = self.section(WRITING, "Focused")
        self.require(focused, (
            r"default", r"(?:local|deterministic)", r"(?:fixture|contract)",
            r"(?:no|do not|never|without)\b[^.]{0,100}\b(?:model|llm|live)\b",
        ), "Focused must be the offline default, not a default real-model test")

    def test_targeted_requires_real_before_after_behavior_evidence(self):
        targeted = self.section(WRITING, "Targeted(?: Behavior)?")
        self.require(targeted, (
            r"explicit(?:ly)?\b[^.]{0,60}(?:approv|authoriz|opt[- ]in)",
            r"(?:real|live)\b[^.]{0,90}(?:behavior|agent|model|scenario)",
            r"(?:before/after|before[- ]and[- ]after|baseline.{0,60}candidate)",
        ), "Targeted must exercise the consuming agent, not merely grep guidance")

    def test_static_success_cannot_be_claimed_as_behavior_validated(self):
        tiers = self.section(WRITING, "Validation Tiers")
        self.require(tiers, (
            r"(?:static|local|focused)\b[^.]{0,110}(?:does not|cannot|is not)\b[^.]{0,90}behavior",
            r"(?:before claiming|to claim|claims?\b[^.]{0,45}(?:requires?|needs?))\b[^.]{0,140}(?:targeted|real|live)",
        ), "Behavior-validation claims require real Targeted evidence or stronger")

    def test_full_pressure_is_a_separate_explicit_bounded_choice(self):
        full = self.section(WRITING, "Full(?: Pressure)?")
        self.require(full, (
            r"explicit(?:ly)?\b[^.]{0,60}(?:approv|authoriz|opt[- ]in)",
            r"separate", r"(?:bounded|fixed)\b[^.]{0,60}budget",
            r"pressure",
        ), "Targeted approval must not silently authorize Full Pressure")

    def test_all_live_evaluation_requires_authorization_and_complete_budget(self):
        tiers = self.section(WRITING, "Validation Tiers")
        # One authoritative budget paragraph avoids duplicating caps in every file.
        budgets = [paragraph for paragraph in re.split(r"\n\s*\n", tiers)
                   if re.search(r"(?:all|every|any|before)\b.{0,80}(?:live|model|llm)\b.{0,50}(?:evaluat|run|call)",
                                plain(paragraph), re.I)]
        self.assertTrue(budgets, "State the prerequisite for ALL live evaluation, including micro-tests")
        self.require("\n".join(budgets), (
            r"explicit(?:ly)?\b[^.]{0,60}(?:approv|authoriz)",
            r"(?:before|requires?|must|without)\b[^.]{0,180}(?:budget|caps?)",
            r"scenario (?:list|set|matrix)", r"\bmodel\b",
            r"(?:call (?:count|cap|limit)|max(?:imum)? (?:model )?calls)",
            r"(?:time|wall[- ]clock) (?:cap|limit|budget)",
            r"(?:cost|usd) (?:cap|limit|budget)",
            r"(?:zero|0|no) automatic (?:expansion|escalation)",
        ), "A model run requires scenarios, model, calls, time, cost and zero automatic expansion")

    def test_budget_exhaustion_stops_instead_of_retrying_or_escalating(self):
        tiers = self.section(WRITING, "Validation Tiers")
        self.require(tiers, (
            r"stop\b[^.]{0,100}(?:cap|budget|limit)",
            r"(?:report|record)\b[^.]{0,100}(?:fail|incomplete|not.verified|variance)",
            r"(?:do not|never|no)\b[^.]{0,80}(?:automatically.{0,20}escalat|escalat.{0,40}automatically|automatic escalation)",
        ), "A failed or exhausted tier reports its evidence without widening evaluation")

    def test_coordinator_owns_existing_budget_workers_do_not_nest_evaluation(self):
        tiers = self.section(WRITING, "Validation Tiers")
        self.require(tiers, (
            r"coordinator\b[^.]{0,80}(?:owns|runs|manages|responsible)\b[^.]{0,50}evaluation",
            r"(?:already[- ]authorized|existing(?:ly)?[- ]approved|existing authorization)",
            r"workers?\b[^.]{0,100}(?:do not|must not|never|no)\b[^.]{0,80}(?:nested|spawn|launch|evaluation)",
        ), "Dispatch is not authorization for workers to launch nested validation")

    def test_unconditional_sampling_and_open_ended_retesting_are_removed(self):
        forbidden = (
            r"5\+ reps", r"re[- ]?test until bulletproof",
            r"continue (?:the )?refactor cycle until no new rationalizations",
            r"if agent finds new rationalization.{0,15}continue refactor cycle",
            r"full pressure[- ]scenario runs are the final gate",
        )
        for name in (WRITING, PRESSURE):
            with self.subTest(document=name):
                text = plain(self.docs[name])
                hits = [pattern for pattern in forbidden if re.search(pattern, text, re.I)]
                self.assertFalse(hits, f"{name}: unbounded or unconditional model instruction(s): {hits}")

    def test_pressure_reference_uses_authorized_tiers_without_losing_real_pressure(self):
        text = self.docs[PRESSURE]
        opening = text.split("## TDD Mapping", 1)[0]
        self.require(opening, (
            r"(?:targeted|full pressure)",
            r"explicit(?:ly)?\b[^.]{0,80}(?:approv|authoriz)",
            r"(?:writing-skills|SKILL\.md)", r"budget",
        ), "The reference must inherit the shared authorization gate, not start a campaign")
        self.require(text, (
            r"realistic scenarios", r"(?:combined|multiple) pressures",
            r"without (?:the )?skill", r"with (?:the )?skill",
            r"(?:choices|decisions|rationalizations)",
        ), "Bounded pressure validation still needs observed baseline/candidate decisions")

    def test_nonbehavioral_work_is_outside_skill_authoring_workflow(self):
        text = self.section(WRITING, "Behavior-Shaping Changes")
        self.require(text, (
            r"(?:do not|not)\b[^.]{0,60}(?:invoke|use|apply)",
            r"test", r"fixture", r"(?:harness|runner)",
            r"(?:non[- ]behavioral|format[- ]only)", r"focused local",
        ), "Test/fixture/harness corrections must not trigger skill behavior validation")

    def test_test_only_corrections_do_not_require_deleting_working_production(self):
        text = self.docs[TDD]
        self.require(text, (
            r"(?:test[- ]only|test/fixture|tests?, fixtures?)",
            r"(?:correction|non[- ]behavioral)",
            r"(?:do not|never)\b[^.]{0,90}delete\b[^.]{0,90}(?:working|correct|unchanged)\b[^.]{0,50}(?:production|code)",
        ), "Correcting only an assertion/fixture must preserve correct production code")
        for phrase in (
            "Write code before the test? Delete it. Start over.",
            "All of these mean: Delete code. Start over with TDD.",
            "Can't check all boxes? You skipped TDD. Start over.",
            "Test passes? You're testing existing behavior. Fix test.",
            "Test fails? Fix code, not test.",
        ):
            self.assertNotIn(phrase, plain(text), "Scope production rules separately from test corrections")

    def test_production_changes_still_require_real_red_green_tdd(self):
        # This preservation guard should already pass on the baseline.
        text = self.docs[TDD]
        self.require(text, (
            r"NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST",
            r"(?:new|production) (?:features?|behavior)", r"(?:bug ?fix|bug fixes)",
            r"refactor", r"behavior changes?",
            r"(?:real code|real implementation|real behavior)",
            r"fails? \(not errors\)", r"(?:watch it pass|verify green)",
        ), "Tiered documentation validation must not weaken production TDD")

    def test_good_tests_distinguishes_contract_lint_from_behavior_proof(self):
        text = self.docs[GOOD_TESTS]
        self.require(text, (
            r"(?:static|deterministic)\b[^.]{0,100}(?:contract|fixture)",
            r"(?:static|contract|fixture)\b[^.]{0,100}(?:does not|cannot|is not)\b[^.]{0,100}behavior",
            r"(?:writing-skills|validation tiers)",
        ), "Static instruction contracts are valid narrow evidence, not behavior evaluation")
        for phrase in ("never grep its text", "prose for humans earns no test at all"):
            self.assertNotIn(phrase, plain(text).lower(), "Remove blanket ban contradicting static-contract tier")

    def test_contributor_validation_section_uses_shared_policy_not_unconditional_campaign(self):
        text = self.section(CONTRIBUTOR, "Skill Changes Require Evaluation")
        self.require(text, (
            r"writing-skills", r"focused", r"targeted", r"full pressure",
            r"explicit(?:ly)?\b[^.]{0,80}(?:approv|authoriz)", r"budget",
        ), "Contributor validation must agree with the canonical tier/budget policy")
        self.assertNotIn("Run adversarial pressure testing across multiple sessions", text,
                         "Pressure campaigns cannot be an unconditional contributor requirement")


if __name__ == "__main__":
    unittest.main(verbosity=2)
