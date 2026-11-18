"""Tests for the joint release orchestrator; no network, no real gh."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import delivery_task
import joint_release

GOOD = dict(target='115.190.243.21',
            source_sha='3b421578588243f920886e6fe79a6faa87ea026e',
            android_sha='187fc049225434642b85b93445a60e4ae2679e42',
            config_sha='06d610e7535daf28bc51754d095f2300838d046a',
            version='4.0.0', android_code=3049, previous_android_code=3048)


class ValidateRequestTests(unittest.TestCase):
    def test_good_request_passes(self):
        self.assertEqual(joint_release.validate_request(dict(GOOD)), GOOD)

    def test_short_sha_rejected(self):
        bad = dict(GOOD, source_sha='3b42157')
        with self.assertRaises(ValueError):
            joint_release.validate_request(bad)

    def test_uppercase_sha_rejected(self):
        bad = dict(GOOD, android_sha=str(GOOD['android_sha']).upper())
        with self.assertRaises(ValueError):
            joint_release.validate_request(bad)

    def test_nonsemver_version_rejected(self):
        with self.assertRaises(ValueError):
            joint_release.validate_request(dict(GOOD, version='v4.0'))
        with self.assertRaises(ValueError):
            joint_release.validate_request(dict(GOOD, version='4.0'))

    def test_version_code_must_increase(self):
        with self.assertRaises(ValueError):
            joint_release.validate_request(dict(GOOD, android_code=3048))
        with self.assertRaises(ValueError):
            joint_release.validate_request(dict(GOOD, android_code=3047))

    def test_unexpected_target_rejected(self):
        with self.assertRaises(ValueError):
            joint_release.validate_request(dict(GOOD, target='150.158.83.70'))

    def test_wrong_types_rejected(self):
        with self.assertRaises(ValueError):
            joint_release.validate_request(dict(GOOD, android_code='3049'))


class DispatchArgsTests(unittest.TestCase):
    def test_args_carry_fixed_inputs(self):
        args = joint_release.build_dispatch_args(GOOD)
        self.assertEqual(args[0:6], [joint_release.GH, 'workflow', 'run',
                                     joint_release.WORKFLOW, '--repo',
                                     'stevenzxs/hermes-config'])
        joined = ' '.join(args)
        for value in (GOOD['source_sha'], GOOD['android_sha'], GOOD['version'],
                      'android_code=3049', 'previous_android_code=3048'):
            self.assertIn(value, joined)
        self.assertNotIn('config_sha', joined,
                         'config SHA is pinned by the dispatched ref, not a field')

    def test_ref_is_main(self):
        self.assertIn('--ref main', ' '.join(joint_release.build_dispatch_args(GOOD)))


class FindRunTests(unittest.TestCase):
    def test_matches_head_sha(self):
        runs = [{'databaseId': 11, 'headSha': 'a' * 40},
                {'databaseId': 22, 'headSha': GOOD['config_sha']}]
        self.assertEqual(joint_release.find_run_id(runs, GOOD['config_sha']), 22)

    def test_no_match_refuses(self):
        with self.assertRaises(RuntimeError):
            joint_release.find_run_id([{'databaseId': 1, 'headSha': 'b' * 40}],
                                      GOOD['config_sha'])


class SecretLeakTests(unittest.TestCase):
    def test_token_like_record_refused(self):
        record = dict(GOOD, note='leak ghp_' + 'a' * 36)
        with self.assertRaises(ValueError):
            joint_release.check_record_safe(record)

    def test_clean_record_accepted(self):
        joint_release.check_record_safe(GOOD)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old = delivery_task.ROOT
        delivery_task.ROOT = self.root
        joint_release.delivery_task.ROOT = self.root

    def tearDown(self):
        delivery_task.ROOT = self.old
        joint_release.delivery_task.ROOT = self.old
        self.tmp.cleanup()

    def test_task_id_reuse_with_same_request(self):
        a = delivery_task.create_task(self.root, 'task-1', GOOD)
        b = delivery_task.create_task(self.root, 'task-1', dict(GOOD))
        self.assertEqual(a, b)

    def test_task_id_reuse_with_different_request_rejected(self):
        delivery_task.create_task(self.root, 'task-1', GOOD)
        with self.assertRaises(ValueError):
            delivery_task.create_task(self.root, 'task-1', dict(GOOD, version='4.0.1'))

    def test_published_requires_verified_evidence(self):
        delivery_task.create_task(self.root, 'task-1', GOOD)
        delivery_task.transition(self.root, 'task-1', 'building', {'run_id': 1})
        with self.assertRaises(ValueError):
            delivery_task.transition(self.root, 'task-1', 'published',
                                     {'run_conclusion': 'success'})
        evidence = {'run_conclusion': 'success', 'artifacts_verified': True,
                    'digest': 'sha256:' + 'c' * 64,
                    'source_sha': GOOD['source_sha'],
                    'config_sha': GOOD['config_sha'],
                    'android_sha': GOOD['android_sha']}
        record = delivery_task.transition(self.root, 'task-1', 'published', evidence)
        self.assertEqual(record['state'], 'published')

    def test_dispatch_refuses_non_prepared_state(self):
        delivery_task.create_task(self.root, 'task-1', GOOD)
        record = json.loads((self.root / 'task-1.json').read_text())
        self.assertEqual(record['state'], 'prepared')
        delivery_task.transition(self.root, 'task-1', 'failed', {'reason': 'x'})
        argv = ['x', 'dispatch', '--task-id', 'task-1']
        with mock.patch.object(joint_release, 'load_record') as load, \
                mock.patch.object(joint_release, 'run_gh') as gh:
            load.side_effect = lambda tid: delivery_task.transition(
                self.root, tid, 'failed', {'reason': 'y2'}) if False else json.loads(
                (self.root / 'task-1.json').read_text())
            with self.assertRaises(SystemExit):
                with mock.patch('sys.argv', argv):
                    joint_release.main()
            gh.assert_not_called()


if __name__ == '__main__':
    unittest.main()
