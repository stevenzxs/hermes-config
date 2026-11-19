"""Tests for the deterministic Android joint version commit; no real repo."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import version_commit


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root)] + list(args), text=True).strip()


def make_repo(root):
    root.mkdir(parents=True)
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    subprocess.run(['git', '-C', str(root), 'config', 'user.email', 't@example.com'], check=True)
    subprocess.run(['git', '-C', str(root), 'config', 'user.name', 'test'], check=True)
    (root / 'pubspec.yaml').write_text('name: hermes_android\nversion: 4.0.0+3049\n\nenvironment:\n  sdk: ^3.12.0\n')
    (root / 'other.txt').write_text('untouched')
    subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
    env = dict(os.environ, GIT_AUTHOR_DATE='2026-01-01T00:00:00Z', GIT_COMMITTER_DATE='2026-01-01T00:00:00Z')
    subprocess.run(['git', '-C', str(root), 'commit', '-q', '-m', 'baseline'], check=True, env=env)
    return git(root, 'rev-parse', 'HEAD')


class VersionCommitTests(unittest.TestCase):
    def test_creates_deterministic_commit_changing_only_pubspec(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'repo'
            baseline = make_repo(root)
            record = version_commit.create(root, '4.0.0+r1', 30491)
            head = git(root, 'rev-parse', 'HEAD')
            self.assertEqual(record['commit'], head)
            self.assertEqual(record['parent'], baseline)
            self.assertEqual(record['version'], '4.0.0+r1')
            self.assertEqual(record['android_code'], 30491)
            self.assertEqual(git(root, 'diff', '--name-only', 'HEAD^', 'HEAD'), 'pubspec.yaml')
            # pubspec keeps the pub-compatible numeric form; display 4.0.0+r1 comes
            # from the build's --build-name override.
            self.assertIn('version: 4.0.0+30491', (root / 'pubspec.yaml').read_text())
            self.assertEqual((root / 'other.txt').read_text(), 'untouched')
            # Determinism: a fresh repo with identical inputs produces the same SHA.
            root2 = Path(d) / 'repo2'
            baseline2 = make_repo(root2)
            self.assertEqual(baseline2, baseline)
            record2 = version_commit.create(root2, '4.0.0+r1', 30491)
            self.assertEqual(record2['commit'], record['commit'])

    def test_different_inputs_change_commit(self):
        with tempfile.TemporaryDirectory() as d:
            root1 = Path(d) / 'r1'; make_repo(root1)
            root2 = Path(d) / 'r2'; make_repo(root2)
            r1 = version_commit.create(root1, '4.0.0+r1', 30491)
            r2 = version_commit.create(root2, '4.0.0+r2', 30492)
            self.assertNotEqual(r1['commit'], r2['commit'])

    def test_refuses_dirty_or_mismatched_repo(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'repo'
            make_repo(root)
            (root / 'pubspec.yaml').write_text('dirty')
            with self.assertRaises(ValueError):
                version_commit.create(root, '4.0.0+r1', 30491)

    def test_refuses_invalid_version_or_code(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'repo'
            make_repo(root)
            for version, code in [('4.0.0', 30491), ('4.0.0+r1', 3049),
                                  ('x; rm -rf /', 30491), ('4.0.0+r1', '30491')]:
                with self.assertRaises(ValueError):
                    version_commit.create(root, version, code)

    def test_refuses_when_head_already_version_commit(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'repo'
            make_repo(root)
            version_commit.create(root, '4.0.0+r1', 30491)
            with self.assertRaises(ValueError):
                version_commit.create(root, '4.0.0+r2', 30492)

    def test_version_must_match_ledger_mapping(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'repo'
            make_repo(root)
            with self.assertRaises(ValueError):
                version_commit.create(root, '4.0.0+r1', 30492)


if __name__ == '__main__':
    unittest.main()
