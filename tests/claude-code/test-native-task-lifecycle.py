#!/usr/bin/env python3
"""Offline real-helper contracts; fixtures live outside the checkout."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SDD = ROOT / 'skills/subagent-driven-development/scripts'
NATIVE = ROOT / 'skills/executing-plans/scripts'


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix='native-', dir=os.environ.get('SP_TEST_ROOT')))
        self.git('init', '-q', '-b', 'main')
        self.plan = self.repo / 'plan.md'
        self.plan.write_text('# Plan\n\n## Task 1: First\nDo it.\n\n## Task 2: Second\nCheck it.\n', encoding='utf-8')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'base')
        self.base = self.git('rev-parse', 'HEAD').stdout.strip()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], text=True, capture_output=True, check=True)

    def helper(self, name, *args, ok=True):
        folder = NATIVE if name.startswith('task-') and name != 'task-brief' else SDD
        p = subprocess.run(['bash', str(folder / name), *map(str, args)], cwd=self.repo, text=True, capture_output=True)
        if ok:
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        else:
            self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)
        return p

    def workspace(self):
        p = self.helper('sdd-workspace', self.plan).stdout.strip()
        if os.name == 'nt' and p.startswith('/'):
            p = subprocess.check_output(['cygpath', '-w', p], text=True).strip()
        return Path(p)

    def start(self):
        return self.helper('task-start', self.plan, '1')

    def done(self, *command, ok=True):
        return self.helper('task-done', self.plan, '1', self.base, '--', *command, ok=ok)

    def test_collision_and_alias_identity(self):
        a = self.workspace()
        self.assertEqual(a, self.workspace())
        other = self.repo / 'other' / 'plan.md'
        other.parent.mkdir()
        other.write_text(self.plan.read_text(), encoding='utf-8')
        b = self.helper('sdd-workspace', other).stdout.strip()
        self.assertNotEqual(b, self.helper('sdd-workspace', self.plan).stdout.strip())
        self.assertTrue((a / 'plan-path').is_file())
        self.assertEqual(self.helper('sdd-workspace', 'other/../plan.md').stdout, self.helper('sdd-workspace', self.plan).stdout)

    def test_unknown_legacy_is_not_claimed(self):
        d = self.repo / '.superpowers/sdd/plan'
        d.mkdir(parents=True)
        (d / 'artifact').write_text('keep')
        self.helper('sdd-workspace', self.plan, ok=False)
        self.assertEqual(list(d.iterdir()), [d / 'artifact'])

    def test_missing_marker_and_foreign_legacy_preserve_artifacts(self):
        d = self.repo / '.superpowers/sdd/plan'
        d.mkdir(parents=True)
        text = '# SDD ledger — plan: absent-plan.md\nTask 1: complete\n'
        (d / 'progress.md').write_text(text, encoding='utf-8')
        self.helper('sdd-workspace', self.plan, ok=False)
        self.helper('task-done', self.plan, '1', self.base, '--', 'bash', '-c', 'touch EXECUTED', ok=False)
        self.assertEqual((d / 'progress.md').read_text(encoding='utf-8'), text)
        self.assertFalse((d / 'plan-path').exists())
        self.assertFalse((self.repo / 'EXECUTED').exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows path spellings')
    def test_windows_drive_case_slash_spellings(self):
        expected = self.helper('sdd-workspace', self.plan).stdout
        self.assertEqual(self.helper('sdd-workspace', str(self.plan).upper()).stdout, expected)
        self.assertEqual(self.helper('sdd-workspace', self.plan.as_posix()).stdout, expected)

    def test_matching_legacy_ledger_only(self):
        d = self.repo / '.superpowers/sdd/plan'
        d.mkdir(parents=True)
        ledger = '# SDD ledger — plan: plan.md\nTask 1: complete (old evidence)\n'
        (d / 'progress.md').write_text(ledger, encoding='utf-8')
        self.workspace()
        self.assertEqual((d / 'progress.md').read_text(encoding='utf-8'), ledger)
        self.assertTrue((d / 'plan-path').exists())

    def test_bad_ranges_preserve_output_and_create_no_workspace(self):
        out = self.repo / 'review.diff'
        out.write_text('keep')
        for base, head in [(self.base, self.base), ('missing', 'HEAD'), ('HEAD', 'missing')]:
            self.helper('review-package', self.plan, base, head, out, ok=False)
            self.assertEqual(out.read_text(), 'keep')
        self.assertFalse((self.repo / '.superpowers').exists())

    def test_silent_success_no_commit_and_resume_no_rerun(self):
        self.start()
        (self.repo / 'dirty.txt').write_text('uncommitted')
        self.done('bash', '-c', 'exit 0')
        ledger = (self.workspace() / 'progress.md').read_text(encoding='utf-8')
        self.assertIn('Task 1: complete', ledger)
        self.assertIn('exit=0', ledger)
        self.assertIn('checkout=', ledger)
        self.start()
        self.done('bash', '-c', 'touch SHOULD_NOT_EXIST')
        self.assertFalse((self.repo / 'SHOULD_NOT_EXIST').exists())
        self.assertEqual(self.git('rev-parse', 'HEAD').stdout.strip(), self.base)

    def test_failure_retained_then_explicit_retry(self):
        self.start()
        self.done('bash', '-c', 'printf failed; exit 7', ok=False)
        d = self.workspace()
        before = list(d.glob('task-1-tests-*.log'))
        self.assertEqual(len(before), 1)
        self.assertEqual(before[0].read_text(), 'failed')
        self.assertNotIn('Task 1: complete', (d / 'progress.md').read_text(encoding='utf-8'))
        self.done('bash', '-c', 'exit 0')
        self.assertEqual(before[0].read_text(), 'failed')

    def test_invalid_inputs_never_execute_or_write(self):
        for task, base in [('1; touch INJECTED', self.base), ('99', self.base), ('1', 'missing')]:
            self.helper('task-done', self.plan, task, base, '--', 'bash', '-c', 'touch EXECUTED', ok=False)
        self.assertFalse((self.repo / 'EXECUTED').exists())
        self.assertFalse((self.repo / '.superpowers').exists())

    def test_foreign_ledger_never_runs(self):
        self.start()
        d = self.workspace()
        (d / 'progress.md').write_text('# SDD ledger — plan: foreign.md\n', encoding='utf-8')
        self.done('bash', '-c', 'touch EXECUTED', ok=False)
        self.assertFalse((self.repo / 'EXECUTED').exists())

    def test_stale_untracked_content_cannot_reuse_completion(self):
        self.start()
        f = self.repo / 'new.txt'
        f.write_text('first')
        self.done('bash', '-c', 'exit 0')
        f.write_text('other')
        self.done('bash', '-c', 'touch EXECUTED', ok=False)
        self.helper('task-start', self.plan, '1', ok=False)
        self.assertFalse((self.repo / 'EXECUTED').exists())

    def test_reversed_nonancestor_and_zero_net_diff(self):
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=f@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-qm', 'empty diff real commit')
        self.helper('review-package', self.plan, self.base, 'HEAD')
        self.helper('review-package', self.plan, 'HEAD', self.base, ok=False)
        self.git('checkout', '-q', '--orphan', 'unrelated')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=f@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'other root')
        self.helper('review-package', self.plan, self.base, 'HEAD', ok=False)

    def test_missing_task_brief_preserves_output(self):
        out = self.repo / 'keep.txt'
        out.write_text('keep')
        self.helper('task-brief', self.plan, '99', out, ok=False)
        self.helper('task-brief', self.plan, '../oops', out, ok=False)
        self.assertEqual(out.read_text(), 'keep')
        self.assertFalse((self.repo / '.superpowers').exists())

    def test_explicit_argv_preserves_quoting(self):
        self.start()
        self.done('bash', '-c', 'printf "%s" "$1"', 'arg0', 'space ; $(touch INJECTED) "quote"')
        log = next(self.workspace().glob('task-1-tests-*.log'))
        self.assertEqual(log.read_text(), 'space ; $(touch INJECTED) "quote"')
        self.assertFalse((self.repo / 'INJECTED').exists())

    def test_verifier_mutation_not_complete(self):
        self.start()
        self.done('bash', '-c', 'printf changed > source.txt', ok=False)
        self.assertNotIn('Task 1: complete', (self.workspace() / 'progress.md').read_text(encoding='utf-8'))

    def test_dirty_tracked_and_plan_change_invalidate(self):
        self.start()
        self.done('bash', '-c', 'exit 0')
        self.plan.write_text(self.plan.read_text() + '\nchanged\n')
        self.done('bash', '-c', 'touch EXECUTED', ok=False)
        self.assertFalse((self.repo / 'EXECUTED').exists())

    def test_missing_log_invalidates_success(self):
        self.start()
        self.done('bash', '-c', 'exit 0')
        log = next(self.workspace().glob('task-1-tests-*.log'))
        log.rename(log.with_suffix('.saved'))
        self.done('bash', '-c', 'touch EXECUTED', ok=False)
        self.assertFalse((self.repo / 'EXECUTED').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
