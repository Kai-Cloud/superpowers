#!/usr/bin/env python3
"""Offline hook execution and static instruction contracts, not agent behavior.

Run: python tests/hooks/test-capability-profiles.py
Temporary fixtures run the real Bash hook; no model calls or dependencies.
"""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
TIERS = ("compact", "standard", "complex")


class ProfileHookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="superpowers profiles ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "hooks/profiles").mkdir(parents=True)
        (self.root / "skills/using-superpowers").mkdir(parents=True)
        shutil.copyfile(ROOT / "hooks/session-start", self.root / "hooks/session-start")
        self.core = 'CORE fixture "quoted" \\path\nnext\tcolumn\rreturn'
        (self.root / "skills/using-superpowers/SKILL.md").write_text(self.core, encoding="utf-8", newline="")
        for tier in TIERS:
            (self.root / f"hooks/profiles/{tier}.md").write_text(
                f'PROFILE {tier} "quoted" \\path\nnext\tcolumn', encoding="utf-8", newline="")

    def run_hook(self, tier=None, platform=None, extra=None):
        env = {key: value for key, value in os.environ.items()
               if key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP")}
        if tier is not None:
            env["SUPERPOWERS_CAPABILITY_TIER"] = tier
        env.update(platform or {})
        env.update(extra or {})
        result = subprocess.run(["bash", self.root.joinpath("hooks/session-start").as_posix()],
                                env=env, capture_output=True, encoding="utf-8", timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        if "hookSpecificOutput" in payload:
            self.assertEqual(set(payload), {"hookSpecificOutput"})
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
            context = payload["hookSpecificOutput"]["additionalContext"]
        else:
            self.assertEqual(len(payload), 1)
            context = next(iter(payload.values()))
        return payload, context, result.stderr

    def test_selected_text_and_platform_priority(self):
        platforms = [({}, "additionalContext"),
                     ({"CLAUDE_PLUGIN_ROOT": "x"}, "hookSpecificOutput"),
                     ({"CLAUDE_PLUGIN_ROOT": "x", "COPILOT_CLI": "1"}, "additionalContext"),
                     ({"CURSOR_PLUGIN_ROOT": "x", "CLAUDE_PLUGIN_ROOT": "x", "COPILOT_CLI": "1"}, "additional_context")]
        for tier in TIERS:
            for platform, key in platforms:
                with self.subTest(tier=tier, key=key):
                    payload, context, stderr = self.run_hook(tier, platform)
                    self.assertEqual(set(payload), {key})
                    self.assertIn(self.core, context)
                    self.assertIn(f'PROFILE {tier} "quoted" \\path\nnext\tcolumn', context)
                    self.assertEqual(sum(f"PROFILE {t}" in context for t in TIERS), 1)
                    self.assertEqual(stderr, "")

    def test_default_and_unknown_environment(self):
        for tier in (None, ""):
            with self.subTest(tier=tier):
                _, context, stderr = self.run_hook(tier, extra={"SUPERPOWERS_UNKNOWN": "$(exit 17)"})
                self.assertIn("PROFILE standard", context)
                self.assertNotIn("INVALID_CAPABILITY_TIER", context)
                self.assertEqual(stderr, "")

    def test_invalid_values_fall_back_without_execution_or_value_echo(self):
        marker = self.root / "executed"
        for tier in ("COMPACT", "../compact", " complex", f'$(touch "{marker.as_posix()}")',
                     f'; touch "{marker.as_posix()}"; #', '`exit 19`', 'bad"\n\x01'):
            with self.subTest(tier=tier):
                _, context, stderr = self.run_hook(tier)
                self.assertIn("PROFILE standard", context)
                self.assertIn("SUPERPOWERS_INVALID_CAPABILITY_TIER", context + stderr)
                self.assertNotIn(tier, context + stderr)
                self.assertFalse(marker.exists())

    def test_missing_and_empty_profile_are_explicitly_degraded(self):
        path = self.root / "hooks/profiles/compact.md"
        for mode in ("missing", "empty"):
            with self.subTest(mode=mode):
                if mode == "missing":
                    path.unlink()
                else:
                    path.write_text("", encoding="utf-8", newline="")
                _, context, stderr = self.run_hook("compact")
                self.assertIn(self.core, context)
                self.assertIn("SUPERPOWERS_PROFILE_UNAVAILABLE", context)
                self.assertIn("SUPERPOWERS_PROFILE_UNAVAILABLE", stderr)
                self.assertNotIn("PROFILE compact", context)

    def test_missing_core_does_not_claim_full_skill_loaded(self):
        (self.root / "skills/using-superpowers/SKILL.md").unlink()
        _, context, stderr = self.run_hook()
        self.assertIn("SUPERPOWERS_CORE_UNAVAILABLE", context)
        self.assertIn("SUPERPOWERS_CORE_UNAVAILABLE", stderr)
        self.assertNotIn("Below is the full content", context)
        self.assertIn("PROFILE standard", context)


class InstructionContracts(unittest.TestCase):
    def text(self, relative):
        path = ROOT / relative
        self.assertTrue(path.is_file(), f"Missing contract: {relative}")
        return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))

    def test_shared_core_budget_and_finite_recipe(self):
        text = self.text("skills/using-superpowers/SKILL.md")
        self.assertLessEqual(len(text.split()), 450)
        for pattern in (r"Goal.*Target context.*Implementation.*Target tests.*Truthful final",
                        r"Stop.*(?:tool|done)", r"context budget", r"repeated full reads"):
            self.assertRegex(text, pattern)

    def test_parent_selection_and_existing_approval_take_priority(self):
        core = self.text("skills/using-superpowers/SKILL.md")
        self.assertIn("Invoke requested skills", core)
        self.assertRegex(core, r"User instructions.*take precedence.*skills")
        self.assertIn("<SUBAGENT-STOP>", core)
        task = self.text("skills/task-execution/SKILL.md")
        self.assertRegex(task, r"parent.*(?:selection|workflow).*(?:unchanged|preserve)")
        self.assertRegex(task, r"already.approved.*(?:not|no).*(?:approval|approve)")
        self.assertRegex(task, r"(?:not|Do not).*(?:every question|questions)")
        compact = self.text("hooks/profiles/compact.md")
        self.assertRegex(compact, r"single.agent.*default")
        self.assertRegex(compact, r"explicit.*(?:SDD|subagent-driven-development).*overrides")

    def test_noop_and_unchanged_retry_contracts(self):
        task = self.text("skills/task-execution/SKILL.md")
        self.assertIn("old == new", task)
        self.assertRegex(task, r"(?i)never retry.*unchanged parameters")
        self.assertRegex(task, r"(?i)no.op.*(?:not|isn't).*(?:success|progress)")
        self.assertRegex(task, r"(?i)(?:blocked|unknown).*stop")
        self.assertRegex(task, r"(?i)one task.*test evidence.*time")

    def test_profiles_are_short_advisory_not_authority(self):
        for tier in TIERS:
            text = self.text(f"hooks/profiles/{tier}.md")
            with self.subTest(tier=tier):
                self.assertGreaterEqual(len(text.split()), 100)
                self.assertLessEqual(len(text.split()), 200)
                self.assertRegex(text, r"(?:authorization|permission)")
        complex_text = self.text("hooks/profiles/complex.md")
        self.assertIn("risk ledger", complex_text)
        self.assertIn("named contracts", complex_text)
        self.assertRegex(complex_text, r"one risk.led review.*authorized")
        self.assertRegex(complex_text, r"(?:No|no) autonomous.*review loops")


if __name__ == "__main__":
    unittest.main(verbosity=2)
