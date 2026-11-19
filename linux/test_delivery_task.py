import json
import tempfile
import unittest
from pathlib import Path

from delivery_task import create_task, transition, set_deployment

BUILD_REQUEST = dict(source_sha='3b421578588243f920886e6fe79a6faa87ea026e',
                     android_sha='187fc049225434642b85b93445a60e4ae2679e42',
                     config_sha='06d610e7535daf28bc51754d095f2300838d046a',
                     version='4.0.0', android_code=3049, previous_android_code=3048)
PUBLISHED_EVIDENCE = {'run_conclusion': 'success', 'artifacts_verified': True,
                      'digest': 'sha256:' + 'c' * 64,
                      'source_sha': '3b421578588243f920886e6fe79a6faa87ea026e',
                      'config_sha': '06d610e7535daf28bc51754d095f2300838d046a',
                      'android_sha': '187fc049225434642b85b93445a60e4ae2679e42'}


class TaskTests(unittest.TestCase):
    def test_create_is_idempotent_but_rejects_changed_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = create_task(root, 'acceptance-1', BUILD_REQUEST)
            self.assertEqual(first, create_task(root, 'acceptance-1', BUILD_REQUEST))
            self.assertIsNone(first['deployment'])
            with self.assertRaises(ValueError):
                create_task(root, 'acceptance-1', dict(BUILD_REQUEST, target='150.158.83.70'))

    def test_build_request_rejects_target_in_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                create_task(root, 't1', dict(BUILD_REQUEST, target='115.190.243.21'))
            self.assertFalse((root / 't1.json').exists())

    def test_publish_requires_successful_build_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_task(root, 'test-1', BUILD_REQUEST)
            with self.assertRaises(ValueError):
                transition(root, 'test-1', 'published', {})
            transition(root, 'test-1', 'building', {'run_id': 123})
            with self.assertRaises(ValueError):
                transition(root, 'test-1', 'published', {'digest': 'latest'})
            result = transition(root, 'test-1', 'published', PUBLISHED_EVIDENCE)
            self.assertEqual(result['state'], 'published')

    def test_published_task_cannot_deploy_without_explicit_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_task(root, 't2', BUILD_REQUEST)
            transition(root, 't2', 'building', {'run_id': 123})
            transition(root, 't2', 'published', PUBLISHED_EVIDENCE)
            with self.assertRaises(ValueError):
                transition(root, 't2', 'deploying', {})
            record = set_deployment(root, 't2', {'target': '150.158.83.70', 'mode': 'upgrade'})
            self.assertEqual(record['deployment']['target'], '150.158.83.70')
            self.assertEqual(record['deployment']['mode'], 'upgrade')
            result = transition(root, 't2', 'deploying', {})
            self.assertEqual(result['state'], 'deploying')

    def test_deployment_selection_cannot_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_task(root, 't3', BUILD_REQUEST)
            set_deployment(root, 't3', {'target': '150.158.83.70', 'mode': 'first-install'})
            with self.assertRaises(ValueError):
                set_deployment(root, 't3', {'target': '115.190.243.21', 'mode': 'upgrade'})
            record = set_deployment(root, 't3', {'target': '150.158.83.70', 'mode': 'first-install'})
            self.assertEqual(record['deployment']['mode'], 'first-install')

    def test_deployment_requires_valid_ip_and_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_task(root, 't4', BUILD_REQUEST)
            for bad in ({'target': 'not-an-ip', 'mode': 'upgrade'},
                        {'target': '150.158.83.70', 'mode': 'unknown'},
                        {'target': '150.158.83.70', 'mode': ''}):
                with self.assertRaises(ValueError):
                    set_deployment(root, 't4', bad)
            record = json.loads((root / 't4.json').read_text())
            self.assertIsNone(record['deployment'])


if __name__ == '__main__':
    unittest.main()
