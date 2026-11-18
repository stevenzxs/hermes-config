import tempfile
import unittest
from pathlib import Path

from delivery_task import create_task, transition


class TaskTests(unittest.TestCase):
    def test_create_is_idempotent_but_rejects_changed_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = {'version': '0.23.1-stevenzxs.1', 'target': '115.190.243.21'}
            first = create_task(root, 'acceptance-1', request)
            self.assertEqual(first, create_task(root, 'acceptance-1', request))
            with self.assertRaises(ValueError):
                create_task(root, 'acceptance-1', dict(request, target='150.158.83.70'))

    def test_publish_requires_successful_build_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_task(root, 'test-1', {'target': '115.190.243.21'})
            with self.assertRaises(ValueError):
                transition(root, 'test-1', 'published', {})
            transition(root, 'test-1', 'building', {'run_id': 123})
            with self.assertRaises(ValueError):
                transition(root, 'test-1', 'published', {'digest': 'latest'})
            result = transition(root, 'test-1', 'published', {
                'run_conclusion': 'success', 'digest': 'sha256:' + 'a' * 64,
                'source_sha': 'b' * 40, 'config_sha': 'c' * 40,
                'android_sha': 'd' * 40, 'artifacts_verified': True})
            self.assertEqual(result['state'], 'published')


if __name__ == '__main__':
    unittest.main()
