"""Version policy tests; no builds, credentials or remote writes."""
import unittest

from revision_versions import versions_for_revision, next_revision


class RevisionVersionsTests(unittest.TestCase):
    def test_shared_revision_preserves_baselines(self):
        for revision in (1, 2, 9, 10, 99, 100, 101):
            value = versions_for_revision(revision)
            self.assertEqual(value['agent_version'], f'0.23.1+r{revision}')
            self.assertEqual(value['android_version'], f'4.0.0+r{revision}')
            self.assertEqual(value['android_code'], int(f'3049{revision}'))
            self.assertEqual(value['image_tag'], f'0.23.1-r{revision}')

    def test_invalid_and_split_overflow_fail_closed(self):
        for value in (0, -1, True, '1', 100000):
            with self.assertRaises(ValueError):
                versions_for_revision(value)

    def test_new_run_increments_and_retry_reuses_assignment(self):
        records = [{'run_id': '100', 'revision': 1},
                   {'run_id': '101', 'revision': 2}]
        self.assertEqual(next_revision(records, '102'), 3)
        self.assertEqual(next_revision(records, '100'), 1)

    def test_corrupt_or_duplicate_ledger_rejected(self):
        for records in ([{'run_id': '1', 'revision': 0}],
                        [{'run_id': '1', 'revision': 1},
                         {'run_id': '2', 'revision': 1}]):
            with self.assertRaises(ValueError):
                next_revision(records, '3')


if __name__ == '__main__':
    unittest.main()
