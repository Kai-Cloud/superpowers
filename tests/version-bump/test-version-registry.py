#!/usr/bin/env python3
"""No-model version invariants; Python standard library only.

Usage:
  python tests/version-bump/test-version-registry.py
      Run regression tests, mutating only external temporary manifest copies.
  python tests/version-bump/test-version-registry.py --check [REPO_ROOT]
      Read-only check of every manifest declared in .version-bump.json.
      REPO_ROOT defaults to this script's repository, not the working directory.

JSON fields use dotted object keys and zero-based list indices. YAML support is
intentionally NOT a general YAML parser: only one top-level `version: X.Y.Z`
line, with optional single/double quotes around X.Y.Z and trailing whitespace.
No comments, escapes, aliases, tags, flow/block values, or nested version fields
are accepted for that scalar. Other YAML fields are not parsed. Versions must
be strings containing a numeric X.Y.Z release; no release number is pinned.
"""

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]


class VersionCheckError(ValueError):
    """An unreadable, unsupported, missing, or inconsistent registered version."""


def read_version(path, field):
    try:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            value = json.loads(text)
            for key in field.split("."):
                if isinstance(value, dict):
                    value = value[key]
                elif isinstance(value, list) and re.fullmatch(r"[0-9]+", key):
                    value = value[int(key)]
                else:
                    raise ValueError(f"cannot resolve field {field}")
        elif path.suffix == ".yaml" and field == "version":
            candidates = [
                line for line in text.splitlines()
                if re.match(r"\s*(?:version|'version'|\"version\")\s*:", line)
            ]
            if len(candidates) != 1:
                raise ValueError("expected exactly one top-level version scalar")
            match = re.fullmatch(
                r"version:[ \t]+(['\"]?)([0-9]+\.[0-9]+\.[0-9]+)\1[ \t]*", candidates[0]
            )
            if match is None:
                raise ValueError("unsupported YAML version syntax (see --help)")
            value = match.group(2)
        else:
            raise ValueError(f"unsupported manifest format or field: {field}")
        if not isinstance(value, str) or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value) is None:
            raise ValueError(f"{field} must be an X.Y.Z version string")
        return value
    except (OSError, ValueError, KeyError, IndexError) as error:
        raise VersionCheckError(f"{path.as_posix()} ({field}): {error}") from error


def check_versions(root):
    root = Path(root)
    registry_path = root / ".version-bump.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise VersionCheckError(f"{registry_path}: {error}") from error
    entries = registry.get("files") if isinstance(registry, dict) else None
    if not isinstance(entries, list) or not entries:
        raise VersionCheckError(f"{registry_path}: files must be a nonempty list")

    versions = {}
    for entry in entries:
        path = entry.get("path") if isinstance(entry, dict) else None
        field = entry.get("field") if isinstance(entry, dict) else None
        if not isinstance(path, str) or not path or not isinstance(field, str) or not field:
            raise VersionCheckError(f"{registry_path}: each entry needs a path and field string")
        if path in versions:
            raise VersionCheckError(f"{registry_path}: duplicate manifest {path}")
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise VersionCheckError(f"{registry_path}: manifest path must be repo-relative: {path}")
        versions[path] = read_version(root / path, field)

    if len(set(versions.values())) != 1:
        details = ", ".join(f"{path}={version}" for path, version in versions.items())
        raise VersionCheckError(f"registered versions disagree: {details}")
    return versions


class VersionRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="superpowers version registry ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = json.loads((REPO_ROOT / ".version-bump.json").read_text(encoding="utf-8"))
        self.entries = self.registry["files"]
        self.save_registry()
        for entry in self.entries:
            source = REPO_ROOT / entry["path"]
            target = self.root / entry["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def save_registry(self):
        (self.root / ".version-bump.json").write_text(json.dumps(self.registry), encoding="utf-8")

    def set_version(self, entry, version, delete=False):
        path = self.root / entry["path"]
        if path.suffix == ".yaml":
            lines = path.read_text(encoding="utf-8").splitlines()
            lines = [line for line in lines if not line.startswith("version:")]
            if not delete:
                lines.insert(1, f"version: {version}")
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
        document = json.loads(path.read_text(encoding="utf-8"))
        keys = entry["field"].split(".")
        parent = document
        for key in keys[:-1]:
            parent = parent[int(key)] if isinstance(parent, list) else parent[key]
        if delete:
            del parent[keys[-1]]
        else:
            parent[keys[-1]] = version
        path.write_text(json.dumps(document), encoding="utf-8")

    def sync(self, version):
        for entry in self.entries:
            self.set_version(entry, version)

    def assert_rejected(self, text):
        with self.assertRaises(VersionCheckError) as caught:
            check_versions(self.root)
        self.assertIn(text, str(caught.exception))

    def test_live_registry_has_eight_json_and_one_yaml_manifest(self):
        self.assertEqual(len(self.entries), 9)
        self.assertEqual(sum(Path(entry["path"]).suffix == ".json" for entry in self.entries), 8)
        self.assertEqual(sum(Path(entry["path"]).suffix == ".yaml" for entry in self.entries), 1)
        self.assertEqual(len(check_versions(REPO_ROOT)), 9)

    def test_synchronized_release_changes_pass(self):
        for version in ("6.3.5", "12.34.56"):
            with self.subTest(version=version):
                self.sync(version)
                versions = check_versions(self.root)
                self.assertEqual(len(versions), 9)
                self.assertEqual(set(versions.values()), {version})

    def test_each_manifest_mismatch_fails(self):
        self.sync("6.3.5")
        for entry in self.entries:
            with self.subTest(path=entry["path"]):
                self.set_version(entry, "6.3.6")
                self.assert_rejected(entry["path"])
                self.set_version(entry, "6.3.5")

    def test_each_missing_manifest_fails(self):
        for entry in self.entries:
            with self.subTest(path=entry["path"]):
                path = self.root / entry["path"]
                original = path.read_bytes()
                path.unlink()
                self.assert_rejected(entry["path"])
                path.write_bytes(original)

    def test_each_missing_version_field_fails(self):
        for entry in self.entries:
            with self.subTest(path=entry["path"]):
                path = self.root / entry["path"]
                original = path.read_bytes()
                self.set_version(entry, None, delete=True)
                self.assert_rejected(entry["path"])
                path.write_bytes(original)

    def test_checker_follows_registry_path_and_nested_field(self):
        self.sync("6.3.5")
        entry = next(entry for entry in self.entries if ".0." in entry["field"])
        (self.root / entry["path"]).unlink()
        entry.update(path="renamed manifest.json", field="release.plugins.1.version")
        (self.root / entry["path"]).write_text(
            json.dumps({"release": {"plugins": [{"version": "unrelated"}, {"version": "6.3.5"}]}}),
            encoding="utf-8",
        )
        self.save_registry()
        versions = check_versions(self.root)
        self.assertEqual(len(versions), 9)
        self.assertEqual(versions[entry["path"]], "6.3.5")

    def test_invalid_json_versions_fail(self):
        entry = next(entry for entry in self.entries if Path(entry["path"]).suffix == ".json")
        for value in (None, 635, True, "", "6.3", " 6.3.5 ", [], {}):
            with self.subTest(value=value):
                self.set_version(entry, value)
                self.assert_rejected(entry["path"])

    def test_malformed_json_fails(self):
        entry = next(entry for entry in self.entries if Path(entry["path"]).suffix == ".json")
        (self.root / entry["path"]).write_text("{", encoding="utf-8")
        self.assert_rejected(entry["path"])

    def test_yaml_supported_scalar_forms_pass(self):
        self.sync("6.3.5")
        entry = next(entry for entry in self.entries if Path(entry["path"]).suffix == ".yaml")
        for scalar in ("6.3.5", "'6.3.5'", '"6.3.5"', '"6.3.5"   '):
            with self.subTest(scalar=scalar):
                (self.root / entry["path"]).write_text(
                    f"name: fixture\nversion: {scalar}\nprovides_hooks:\n  - pre_llm_call\n",
                    encoding="utf-8",
                )
                self.assertEqual(set(check_versions(self.root).values()), {"6.3.5"})

    def test_yaml_unsupported_or_ambiguous_scalars_fail(self):
        self.sync("6.3.5")
        entry = next(entry for entry in self.entries if Path(entry["path"]).suffix == ".yaml")
        bodies = (
            "version: 635", "version: null", "version: true", "version:",
            "version: [6.3.5]", "version: !!str 6.3.5", "version: *release",
            "version: &release 6.3.5", "version: |\n  6.3.5", "version: 6.3.5 # comment",
            "version: '6.3.5\"", 'version: "6.3.\\x35"', "  version: 6.3.5",
            "version: 6.3.5\nversion: 6.3.5", 'version: 6.3.5\n"version": 6.3.6',
        )
        for body in bodies:
            with self.subTest(body=body):
                (self.root / entry["path"]).write_text(body + "\n", encoding="utf-8")
                self.assert_rejected(entry["path"])

    def test_registry_missing_or_malformed_fails(self):
        path = self.root / ".version-bump.json"
        path.unlink()
        self.assert_rejected(".version-bump.json")
        for body in ("{", "null", "{}", '{"files": []}'):
            with self.subTest(body=body):
                path.write_text(body, encoding="utf-8")
                self.assert_rejected(".version-bump.json")

    def test_check_is_read_only(self):
        paths = [self.root / ".version-bump.json"] + [self.root / entry["path"] for entry in self.entries]
        before = {path: path.read_bytes() for path in paths}
        check_versions(self.root)
        self.assertEqual(before, {path: path.read_bytes() for path in paths})

    def test_check_cli_exit_codes_and_default_root(self):
        command = [sys.executable, str(Path(__file__).resolve()), "--check"]

        def run(*arguments):
            return subprocess.run(
                command + list(arguments), cwd=self.root, capture_output=True, text=True, timeout=30
            )

        result = run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("9 registered manifests agree", result.stdout)

        self.sync("6.3.5")
        result = run(str(self.root))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("9 registered manifests agree at 6.3.5", result.stdout)

        for entry in self.entries:
            with self.subTest(path=entry["path"]):
                self.set_version(entry, "6.3.6")
                result = run(str(self.root))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(entry["path"], result.stderr)
                self.set_version(entry, "6.3.5")

        missing = self.entries[0]["path"]
        (self.root / missing).unlink()
        result = run(str(self.root))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(missing, result.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", nargs="?", const=REPO_ROOT, type=Path, metavar="REPO_ROOT")
    args = parser.parse_args()
    if args.check is None:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(VersionRegistryTests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    try:
        versions = check_versions(args.check)
    except VersionCheckError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    for path, version in versions.items():
        print(f"  {path}: {version}")
    print(f"[PASS] {len(versions)} registered manifests agree at {next(iter(versions.values()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
