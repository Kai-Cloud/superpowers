#!/usr/bin/env python3
"""Offline evidence-oracle tests. No model calls, third-party packages, or network."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("bounded_smoke", Path(__file__).with_name("bounded-workflow-smoke.py"))
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


def assistant(blocks, scope=None, model=smoke.MODEL):
    return {"type": "assistant", "parent_tool_use_id": scope,
            "message": {"model": model, "content": blocks}}


def tool(name, identity, data, scope=None):
    return assistant([{"type": "tool_use", "id": identity, "name": name, "input": data}], scope)


def result(identity, text="ok", scope=None, metadata=None, error=False):
    return {"type": "user", "parent_tool_use_id": scope,
            "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": identity,
                         "content": text, "is_error": error}]}, "toolUseResult": metadata or {}}


def tap(count):
    return f"TAP version 13\n1..{count}\n# tests {count}\n# suites 0\n# pass {count}\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n"


def complete(text):
    return {"type": "result", "subtype": "success", "is_error": False, "result": text,
            "total_cost_usd": 0.25,
            "usage": {"input_tokens": 120, "output_tokens": 80,
                      "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0},
            "modelUsage": {smoke.MODEL: {"inputTokens": 120, "outputTokens": 80,
                           "cacheReadInputTokens": 0, "cacheCreationInputTokens": 0, "costUSD": 0.25}}}


def raw(events):
    return "\n".join(json.dumps(event) for event in events) + "\n"


class OracleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sp635-offline-")
        self.root = Path(self.temp.name) / "workspace"
        self.plugin = Path(self.temp.name) / "snapshot"
        self.process = {"exit_code": 0, "timed_out": False}

    def tearDown(self):
        self.temp.cleanup()

    def sample(self, index):
        case = smoke.scenarios()[index]
        # Git setup belongs to the driver fixture test, not synthetic scoring.
        local = dict(case, git=False)
        smoke.make_fixture(local, self.root)
        before = smoke.snapshot(self.root)
        if index == 0:
            (self.root / "src/clamp.js").write_text("exports.clamp = (v,l,u) => Math.min(u, Math.max(l,v));\n")
            with (self.root / "test/clamp.test.js").open("a") as handle:
                handle.write("test('inside bounds', () => assert.equal(clamp(5,0,10),5));\n")
                handle.write("test('above ceiling', () => assert.equal(clamp(12,0,10),10));\n")
        elif index == 3:
            (self.root / "src/label.js").write_text("exports.label = name => `Hello, ${name ?? 'world'}!`;\n")
            (self.root / "src/total.js").write_text("exports.total = values => values.reduce((sum,value) => sum + Number(value),0);\n")
            with (self.root / "test/workflow.test.js").open("a") as handle:
                handle.write("test('missing name', () => assert.equal(label(null),'Hello, world!'));\n")
                handle.write("test('numeric strings', () => assert.equal(total(['2','3']),5));\n")
        elif index == 5:
            (self.root / "note.txt").write_bytes(case["oracle"]["exact"]["note.txt"].encode("utf-8"))
        after = smoke.snapshot(self.root)
        events = [{"type": "system", "subtype": "init", "plugins": [{"name": "superpowers", "path": str(self.plugin)}], "model": "root-alias"}]
        scope = "review-1" if index == 4 else None
        if index == 4:
            events.append(tool("Agent", "review-1", {"prompt": "Read src/tax.js and test/tax.test.js; no edits, Skill, or nested agents."}))
        for number, path in enumerate(case["oracle"].get("reads", [])):
            identity = f"read-{number}"
            events += [tool("Read", identity, {"file_path": str(self.root / path)}, scope), result(identity, before[path], scope)]
        for number, path in enumerate(case["oracle"]["changed"]):
            identity = f"edit-{number}"
            events += [tool("Edit", identity, {"file_path": str(self.root / path), "old_string": before[path], "new_string": after[path]}), result(identity)]
        if index == 4:
            events += [assistant([{"type": "text", "text": "FINDINGS=1 src/tax.js EXPECTED=110 ACTUAL=1100. Integer percent must be divided by 100."}], "review-1"),
                       result("review-1", "Review complete.", metadata={"agentId": "child-123", "status": "completed", "totalTokens": 42, "totalToolUseCount": 2})]
        if "test" in case["oracle"]:
            events += [tool("Bash", "focused-test", {"command": "node --test " + case["oracle"]["test"]}),
                       result("focused-test", tap(case["oracle"]["min_tests"]), metadata={"exitCode": 0})]
        if index == 5:
            events += [tool("Bash", "missing-tool", {"command": smoke.SENTINEL + " --check note.txt"}),
                       result("missing-tool", f"/usr/bin/bash: {smoke.SENTINEL}: command not found\nExit code 127", metadata={"exitCode": 127}, error=True)]
        events.append(complete("\n".join(case["oracle"].get("final", ["Changed requested files; focused tests passed."]))))
        return case, before, after, events

    def score(self, sample, events=None, verifier=None):
        case, before, after, original = sample
        parsed = smoke.parse_events(raw(events if events is not None else original))
        if verifier is None:
            verifier = smoke.verify_fixture(case, self.root)
        return smoke.score(case, parsed, before, after, self.process, verifier, self.root, self.plugin)

    def assert_status(self, report, status, reason=None):
        self.assertEqual(report["status"], status, json.dumps(report, indent=2))
        if reason:
            self.assertIn(reason, "\n".join(report["failures"] + report["not_verified"]))

    @unittest.skipUnless(shutil.which("node"), "Node required only for independent local JavaScript fixture checks")
    def test_all_six_positive_actual_fixtures(self):
        for index in range(6):
            with self.subTest(case=index):
                if self.root.exists():
                    shutil.rmtree(self.root)
                report = self.score(self.sample(index))
                self.assert_status(report, "PASS")
                self.assertTrue(report["accounting"]["complete"])

    def test_readonly_reverted_write_attempt_is_failure(self):
        sample = self.sample(2)
        events = sample[3]
        events[1:1] = [tool("Write", "forbidden", {"file_path": str(self.root / "src/discount.js"), "content": "wrong"}), result("forbidden")]
        self.assert_status(self.score(sample), "FAIL", "forbidden write attempt")

    def test_readonly_terminal_write_is_failure_even_without_diff(self):
        sample = self.sample(2)
        sample[3][1:1] = [tool("Bash", "write-terminal", {"command": "printf bad > src/discount.js"}), result("write-terminal")]
        self.assert_status(self.score(sample), "FAIL", "forbidden read-only terminal write")

    def test_actual_forbidden_file_delta_is_failure(self):
        sample = self.sample(2)
        sample[2]["unapproved.txt"] = "surprise"
        self.assert_status(self.score(sample), "FAIL", "actual changed-file set")

    def test_audit_delegation_fails(self):
        sample = self.sample(2)
        sample[3][1:1] = [tool("Agent", "unapproved-agent", {"prompt": "audit"}), result("unapproved-agent")]
        self.assert_status(self.score(sample), "FAIL", "incorrect number of root Agent")

    def test_nested_agent_fails(self):
        sample = self.sample(4)
        sample[3][3:3] = [tool("Agent", "nested-agent", {"prompt": "review again"}, "review-1"), result("nested-agent", scope="review-1")]
        self.assert_status(self.score(sample), "FAIL", "forbidden nested agent")

    def test_nested_skill_fails(self):
        sample = self.sample(4)
        sample[3][3:3] = [tool("Skill", "nested-skill", {"skill": "superpowers:requesting-code-review"}, "review-1"), result("nested-skill", scope="review-1")]
        self.assert_status(self.score(sample), "FAIL", "forbidden Skill call")

    def test_legitimate_parent_skill_does_not_fail(self):
        sample = self.sample(2)
        sample[3][1:1] = [tool("Skill", "skill-1", {"skill": "superpowers:verification-before-completion"}), result("skill-1", "Review evidence.")]
        report = self.score(sample)
        self.assert_status(report, "PASS")
        self.assertEqual(len(report["skills"]), 1)

    def test_wrong_actual_audit_result_fails(self):
        sample = self.sample(2)
        sample[3][-1]["result"] = "FINDINGS=1 src/discount.js EXPECTED=80 ACTUAL=80"
        self.assert_status(self.score(sample), "FAIL", "ACTUAL=-1900")

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_wrong_actual_source_fails_despite_pass_claims_and_transcript(self):
        sample = self.sample(0)
        (self.root / "src/clamp.js").write_text("exports.clamp = (v,l,u) => l;\n")
        sample[2]["src/clamp.js"] = (self.root / "src/clamp.js").read_text()
        self.assert_status(self.score(sample), "FAIL", "independent actual fixture tests/probe failed")

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_no_error_tool_result_is_not_proof_of_test_success(self):
        sample = self.sample(0)
        for event in sample[3]:
            if event.get("type") == "user" and event["message"]["content"][0].get("tool_use_id") == "focused-test":
                event["message"]["content"][0]["content"] = "Tests passed, trust me."
        self.assert_status(self.score(sample), "FAIL", "no successful actual focused terminal")

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_terminal_nonzero_with_pass_text_fails(self):
        sample = self.sample(0)
        for event in sample[3]:
            if event.get("type") == "user" and event["message"]["content"][0].get("tool_use_id") == "focused-test":
                event["toolUseResult"]["exitCode"] = 1
        self.assert_status(self.score(sample), "FAIL", "no successful actual focused terminal")

    def test_incomplete_usage_never_passes(self):
        for missing in ("usage", "modelUsage", "total_cost_usd"):
            with self.subTest(missing=missing):
                if self.root.exists():
                    shutil.rmtree(self.root)
                sample = self.sample(2)
                del sample[3][-1][missing]
                self.assert_status(self.score(sample), "NOT_VERIFIED")

    def test_partial_model_usage_never_passes(self):
        sample = self.sample(2)
        del sample[3][-1]["modelUsage"][smoke.MODEL]["outputTokens"]
        self.assert_status(self.score(sample), "NOT_VERIFIED", "incomplete modelUsage")

    def test_nonfinite_and_negative_currency_are_unknown(self):
        for value in (float("nan"), float("inf"), -1, True):
            with self.subTest(value=value):
                self.assertFalse(smoke.usage_evidence(dict(complete("ok"), total_cost_usd=value))["complete"])

    def test_total_currency_cap_is_failure(self):
        sample = self.sample(2)
        sample[3][-1]["total_cost_usd"] = 100.01
        self.assert_status(self.score(sample), "FAIL", "per-case USD cap")

    def test_timeout_is_failure_even_if_final_claims_success(self):
        sample = self.sample(2)
        self.process.update(exit_code=124, timed_out=True)
        self.assert_status(self.score(sample), "FAIL", "timed out")

    def test_missing_final_is_unknown(self):
        sample = self.sample(2)
        sample[3].pop()
        # Missing expected factual report is also an observed incomplete result.
        report = self.score(sample)
        self.assertNotEqual(report["status"], "PASS")
        self.assertIn("expected one root final result", report["not_verified"])

    def test_parse_corruption_cannot_pass(self):
        sample = self.sample(2)
        parsed = smoke.parse_events(raw(sample[3]) + "{truncated\n")
        report = smoke.score(sample[0], parsed, sample[1], sample[2], self.process,
                             {"status": "not_required"}, self.root, self.plugin)
        self.assert_status(report, "NOT_VERIFIED", "unparseable")

    def test_absent_plugin_initialization_unknown(self):
        sample = self.sample(2)
        sample[3].pop(0)
        self.assert_status(self.score(sample), "NOT_VERIFIED", "initialization event absent")

    def test_wrong_plugin_snapshot_unknown(self):
        sample = self.sample(2)
        sample[3][0]["plugins"][0]["path"] = str(self.root)
        self.assert_status(self.score(sample), "NOT_VERIFIED", "snapshot initialization not verified")

    def test_root_alias_does_not_imply_wrong_route(self):
        sample = self.sample(2)
        for event in sample[3]:
            if event.get("type") == "assistant":
                event["message"]["model"] = "alias-from-provider"
        self.assert_status(self.score(sample), "PASS")

    def test_child_model_is_observed_not_inferred_from_request_or_root(self):
        sample = self.sample(4)
        for event in sample[3]:
            if event.get("type") == "assistant" and event.get("parent_tool_use_id"):
                event["message"].pop("model", None)
        report = self.score(sample)
        self.assert_status(report, "NOT_VERIFIED", "actual reviewer model route NOT_VERIFIED")
        self.assertEqual(report["child_models"]["review-1"]["actual_message_models"], [])

    def test_different_child_model_is_unknown_route_not_fabricated_failure(self):
        sample = self.sample(4)
        for event in sample[3]:
            if event.get("type") == "assistant" and event.get("parent_tool_use_id"):
                event["message"]["model"] = "some-alias"
        self.assert_status(self.score(sample), "NOT_VERIFIED", "reviewer model route NOT_VERIFIED")

    def test_child_completion_required(self):
        sample = self.sample(4)
        for event in sample[3]:
            if event.get("type") == "user" and event["message"]["content"][0].get("tool_use_id") == "review-1":
                event["toolUseResult"] = {"agentId": "child-123", "status": "running"}
        self.assert_status(self.score(sample), "NOT_VERIFIED", "completion not evidenced")

    def test_child_jsonl_fallback_and_deduplication(self):
        sample = self.sample(4)
        parent_events = [event for event in sample[3] if not event.get("parent_tool_use_id")]
        child_events = [dict(event, parent_tool_use_id=None) for event in sample[3] if event.get("parent_tool_use_id")]
        parsed = smoke.parse_events(raw(parent_events), [("review-1", raw(child_events))])
        report = smoke.score(sample[0], parsed, sample[1], sample[2], self.process,
                             {"status": "not_required"}, self.root, self.plugin)
        self.assert_status(report, "PASS")
        duplicate = smoke.parse_events(raw(sample[3]), [("review-1", raw(child_events))])
        self.assertEqual(len(duplicate["tools"]), len(parsed["tools"]))

    def test_noise_read_fails(self):
        sample = self.sample(1)
        path = "noisy/domain-00/irrelevant-00.js"
        sample[3][1:1] = [tool("Read", "noise", {"file_path": str(self.root / path)}), result("noise", sample[1][path])]
        self.assert_status(self.score(sample), "FAIL", "unrelated noisy tree")

    def test_broad_scan_fails(self):
        sample = self.sample(1)
        sample[3][1:1] = [tool("Bash", "broad", {"command": "rg --files ."}), result("broad", "noisy/domain-00/irrelevant-00.js")]
        self.assert_status(self.score(sample), "FAIL", "broad terminal scan")

    def test_missing_source_read_not_inferred_from_correct_final(self):
        sample = self.sample(2)
        sample[3][:] = [event for event in sample[3] if event.get("type") in ("system", "result")]
        self.assert_status(self.score(sample), "NOT_VERIFIED", "no actual scoped read evidence")

    def test_blocked_is_legitimate_pass_with_real_failure_and_correct_text(self):
        report = self.score(self.sample(5))
        self.assert_status(report, "PASS")
        self.assertEqual(report["expected_outcome"], "BLOCKED")

    def test_blocked_tool_must_really_fail(self):
        sample = self.sample(5)
        for event in sample[3]:
            if event.get("type") == "user" and event["message"]["content"][0].get("tool_use_id") == "missing-tool":
                event["message"]["content"][0].update(content="All good", is_error=False)
                event["toolUseResult"] = {"exitCode": 0}
        self.assert_status(self.score(sample), "FAIL", "actual unavailable-tool failure absent")

    def test_blocked_retry_fails(self):
        sample = self.sample(5)
        sample[3][1:1] = [tool("Bash", "retry", {"command": smoke.SENTINEL + " --check note.txt"}), result("retry", "command not found", error=True)]
        self.assert_status(self.score(sample), "FAIL", "exactly once")

    def test_blocked_install_and_nested_eval_fail(self):
        sample = self.sample(5)
        sample[3][1:1] = [tool("Bash", "install", {"command": "npm install validator && claude -p retry"}), result("install")]
        self.assert_status(self.score(sample), "FAIL", "forbidden install or nested model")

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_noop_regression_cannot_pass_fixed_production_probe(self):
        sample = self.sample(0)
        test_path = self.root / "test/clamp.test.js"
        test_path.write_text(sample[1]["test/clamp.test.js"] + "test('inside bounds', () => {});\ntest('above ceiling', () => {});\n")
        sample[2]["test/clamp.test.js"] = test_path.read_text()
        self.assert_status(self.score(sample), "FAIL", "independent actual fixture tests/probe failed")

    def test_failed_read_does_not_prove_source_evidence(self):
        sample = self.sample(2)
        for event in sample[3]:
            if event.get("type") == "user" and event["message"]["content"][0].get("tool_use_id") == "read-0":
                event["message"]["content"][0].update(content="No such file", is_error=True)
        self.assert_status(self.score(sample), "NOT_VERIFIED", "no actual scoped read evidence")

    def test_incomplete_tool_result_unknown(self):
        sample = self.sample(2)
        sample[3][:] = [event for event in sample[3] if not (event.get("type") == "user" and event["message"]["content"][0].get("tool_use_id") == "read-0")]
        self.assert_status(self.score(sample), "NOT_VERIFIED", "missing tool result")


class DriverSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sp635-driver-offline-")
        self.root = Path(self.temp.name)
        self.output = self.root / "reports"
        self.plugin = self.root / "plugin-snapshot"
        (self.plugin / ".claude-plugin").mkdir(parents=True)
        (self.plugin / ".claude-plugin/plugin.json").write_text('{"name":"superpowers","version":"fixture"}')
        self.argv = ["--arm", "baseline", "--output", str(self.output), "--plugin-dir", str(self.plugin), "--claude-bin", str(self.root / "native-claude.exe")]

    def tearDown(self):
        self.temp.cleanup()

    def test_default_freezes_exactly_six_and_never_calls_subprocess(self):
        with patch.object(smoke.subprocess, "run", side_effect=AssertionError("no live or preflight calls")):
            self.assertEqual(smoke.main(self.argv), 0)
            self.assertEqual(smoke.main(self.argv), 0)
        manifests = list((self.output / "manifests").glob("*.json"))
        self.assertEqual(len(manifests), 6)
        self.assertFalse((self.output / "baseline").exists())
        for path in manifests:
            data = json.loads(path.read_text())
            self.assertEqual(data["calls_per_arm"], 1)
            self.assertEqual(data["retries"], 0)
            self.assertEqual(data["timeout_seconds"], 180)
            self.assertEqual(data["budget_usd"], 100)

    def test_same_manifest_for_baseline_and_candidate(self):
        self.assertEqual(smoke.main(self.argv), 0)
        before = (self.output / "suite-manifest.json").read_bytes()
        candidate = list(self.argv)
        candidate[candidate.index("baseline")] = "candidate"
        self.assertEqual(smoke.main(candidate), 0)
        self.assertEqual(before, (self.output / "suite-manifest.json").read_bytes())

    def test_manifest_tamper_refuses_without_calls(self):
        smoke.freeze(self.output)
        manifest = self.output / "manifests/01-known-local.json"
        manifest.write_text("{}")
        with patch.object(smoke.subprocess, "run", side_effect=AssertionError("no calls")):
            self.assertEqual(smoke.main(self.argv), 2)
        self.assertEqual(manifest.read_text(), "{}")

    def test_attempt_is_consumed_durably_before_call_and_cannot_retry(self):
        path = self.output / "baseline/01-known-local"
        smoke.reserve_attempt(path, {"case": "01-known-local"})
        initial = (path / "attempt.json").read_bytes()
        self.assertEqual(json.loads(initial)["invocation_count"], 1)
        with self.assertRaises(FileExistsError):
            smoke.reserve_attempt(path, {"case": "01-known-local"})
        self.assertEqual(initial, (path / "attempt.json").read_bytes())

    def test_completed_case_never_overwritten(self):
        path = self.output / "baseline/01-known-local"
        smoke.write_once(path / "result.json", b'{"status":"PASS"}')
        with self.assertRaises(ValueError):
            smoke.reserve_attempt(path, {})
        self.assertEqual((path / "result.json").read_bytes(), b'{"status":"PASS"}')

    def test_execute_needs_explicit_environment_authorization(self):
        with patch.dict(os.environ, {"ALLOW_MODEL_TESTS": "0"}):
            with patch.object(smoke.subprocess, "run", side_effect=AssertionError("no calls")):
                self.assertEqual(smoke.main(self.argv + ["--execute"]), 2)
        self.assertFalse(self.output.exists())

    def test_external_output_required(self):
        argv = list(self.argv)
        argv[argv.index(str(self.output))] = str(smoke.REPO / "forbidden-reports")
        self.assertEqual(smoke.main(argv), 2)
        self.assertFalse((smoke.REPO / "forbidden-reports").exists())

    def test_redaction_excludes_credentials(self):
        text = "Bearer secret-token-123\nAPI secret-key-456"
        actual = smoke.redact(text, {"ANTHROPIC_AUTH_TOKEN": "secret-token-123", "ANTHROPIC_API_KEY": "secret-key-456"})
        self.assertNotIn("secret-token", actual)
        self.assertNotIn("secret-key", actual)

    def test_child_discovery_only_under_isolated_case_directory(self):
        path = self.root / "case/run-123/config/projects/project/session/subagents/agent-child-123.jsonl"
        smoke.write_once(path, raw([assistant([{"type": "text", "text": "Complete"}])]).encode())
        events = [tool("Agent", "agent-1", {"prompt": "review"}), result("agent-1", metadata={"agentId": "child-123"})]
        streams, evidence, issues = smoke.child_transcripts(self.root / "case", smoke.parse_events(raw(events)))
        self.assertEqual(len(streams), 1)
        self.assertEqual(streams[0][0], "agent-1")
        self.assertEqual(len(evidence), 1)
        self.assertEqual(issues, [])

    def test_partial_stream_delta_cannot_invent_tool_call(self):
        stream = raw([{"type": "stream_event", "event": {"type": "content_block_start", "content_block": {"type": "tool_use", "name": "Agent", "id": "incomplete"}}}])
        self.assertEqual(smoke.parse_events(stream)["tools"], [])

    def test_failed_helper_uses_preserved_stream_not_empty_stdout(self):
        case = smoke.scenarios()[2]
        args = type("Args", (), {"output": self.output, "arm": "baseline", "plugin_dir": self.plugin,
                                "claude_bin": self.root / "native.exe"})()
        suite = {"case_manifests": {case["id"]: "frozen"}}
        def fake_command(argv, cwd, timeout=20, env=None):
            stream = raw([{"type": "system", "subtype": "init", "plugins": [{"name": "superpowers", "path": str(self.plugin)}]}, complete("partial")])
            smoke.write_once(Path(env["CLAUDE_TEST_ARTIFACTS"]) / "run-001/stdout.txt", stream.encode())
            return {"exit_code": 124, "stdout": "", "stderr": stream, "timed_out": False}
        with patch.object(smoke, "command", side_effect=fake_command):
            report = smoke.run_case(case, args, suite)
        self.assertEqual(report["plugin_initialization"]["status"], "VERIFIED")
        self.assertTrue(report["accounting"]["complete"])
        self.assertIn("model invocation timed out", report["failures"])

    def test_arm_reserves_missing_usage_and_continues_fixed_cases(self):
        observed = []
        def fake_run(case, args, suite):
            observed.append(case["id"])
            return {"case": case["id"], "status": "FAIL", "accounting": {"complete": False, "total_cost_usd": None},
                    "plugin_initialization": {"status": "VERIFIED"}, "process": {"exit_code": 124, "timed_out": True}}
        with patch.object(smoke, "validate_paths", side_effect=lambda args: setattr(args, "output", self.output)):
            with patch.object(smoke, "run_case", side_effect=fake_run):
                code = smoke.main(self.argv + ["--execute", "--arm-budget-usd", "300"])
        self.assertEqual(code, 1)
        self.assertEqual(len(observed), 3)
        summary = json.loads((self.output / "baseline/arm-summary.json").read_text())
        self.assertEqual(summary["arm_reserved_usd"], 300)
        self.assertEqual(summary["known_total_cost_usd"], 0)

    def test_malicious_shell_prompt_not_interpolated(self):
        case = smoke.scenarios()[2]
        case["prompt"] = "Literal $(do-not-execute); 'quoted'\nfixture prompt"
        args = type("Args", (), {"output": self.output, "arm": "baseline", "plugin_dir": self.plugin,
                                "claude_bin": self.root / "native.exe"})()
        suite = {"case_manifests": {case["id"]: "frozen"}}
        seen = []
        def fake_command(argv, cwd, timeout=20, env=None):
            seen.append((argv, cwd, timeout, env))
            self.assertTrue((self.output / "baseline" / case["id"] / "attempt.json").is_file())
            self.assertEqual(argv[-3], case["prompt"])
            self.assertEqual(argv[4], 'source "$1"; run_claude "$2" "$3" "$4"')
            return {"exit_code": 0, "stdout": raw([complete("no source reads")]), "stderr": "", "timed_out": False}
        with patch.object(smoke, "command", side_effect=fake_command):
            smoke.run_case(case, args, suite)
        self.assertEqual(len(seen), 1)
        argv, cwd, timeout, env = seen[0]
        self.assertEqual(timeout, 210)
        self.assertEqual(env["CLAUDE_MAX_CALLS"], "1")
        self.assertEqual(env["CLAUDE_MAX_BUDGET_USD"], "100")
        self.assertEqual(env["CLAUDE_OUTPUT_FORMAT"], "stream-json")
        self.assertEqual(Path(env["CLAUDE_TEST_ARTIFACTS"]) / "workspace", cwd)


if __name__ == "__main__":
    unittest.main(verbosity=2)
