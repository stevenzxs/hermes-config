"""Real SQLite/filesystem tests; no product build or allocation of real versions."""
from concurrent.futures import ThreadPoolExecutor
import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

import revision_ledger as ledger


REQUEST = dict(repository='stevenzxs/hermes-config', workflow='hermes-joint-release.yml',
               task_id='reasoning-fix', source_sha='a' * 40,
               android_sha='b' * 40, config_sha='c' * 40)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / 'primary' / 'ledger.sqlite'
        self.backups = self.root / 'independent'

    def tearDown(self):
        self.tmp.cleanup()

    def initialize(self):
        ledger.initialize(self.db, self.backups, history_sha256='d' * 64)

    def allocate(self, **kwargs):
        request = dict(REQUEST, **kwargs)
        return ledger.allocate(self.db, self.backups, request)

    def test_missing_ledger_never_recreated(self):
        with self.assertRaisesRegex(ValueError, 'initializ'):
            self.allocate()
        self.assertFalse(self.db.exists())

    def test_initialize_is_explicit_and_cannot_overwrite(self):
        with self.assertRaises(ValueError):
            ledger.initialize(self.db, self.backups, history_sha256='')
        self.initialize()
        with self.assertRaises((ValueError, FileExistsError)):
            self.initialize()

    def test_new_tasks_increment_and_task_reuse_is_idempotent(self):
        self.initialize()
        a = self.allocate()
        self.assertEqual(a['versions']['agent_version'], '0.23.1+r1')
        self.assertEqual(a['versions']['android_version'], '4.0.0+r1')
        self.assertEqual(a['versions']['android_code'], 30491)
        before = sorted(p.name for p in self.backups.iterdir())
        self.assertEqual(a, self.allocate())
        self.assertEqual(before, sorted(p.name for p in self.backups.iterdir()),
                         'idempotent reuse must not append snapshots')
        self.assertEqual(self.allocate(task_id='other-task')['versions']['revision'], 2)

    def test_failure_or_cancel_does_not_reclaim_revision(self):
        self.initialize()
        self.allocate()  # No successful publication is needed to consume r1.
        self.assertEqual(self.allocate(task_id='t2')['versions']['revision'], 2)

    def test_changed_input_on_same_task_is_rejected(self):
        self.initialize()
        self.allocate()
        for key in ('source_sha', 'android_sha', 'config_sha'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.allocate(**{key: 'e' * 40})

    def test_wrong_namespace_types_refused(self):
        self.initialize()
        for changes in ({'repository': 'other/project'}, {'task_id': '../x'},
                        {'config_sha': 'main'}, {'run_id': '1'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.allocate(**changes)

    def test_bind_run_records_dispatch_and_attempts(self):
        self.initialize()
        self.allocate()
        ledger.bind_run(self.db, self.backups, 'reasoning-fix', 12345, 1)
        # Rerun of the same run reuses inputs; binding again is idempotent per attempt.
        ledger.bind_run(self.db, self.backups, 'reasoning-fix', 12345, 1)
        ledger.bind_run(self.db, self.backups, 'reasoning-fix', 12345, 2)
        with closing(sqlite3.connect(self.db)) as con:
            rows = con.execute('SELECT task_id,run_id,attempt FROM dispatches ORDER BY attempt').fetchall()
        self.assertEqual(rows, [('reasoning-fix', 12345, 1), ('reasoning-fix', 12345, 2)])

    def test_bind_requires_existing_allocation_and_valid_run(self):
        self.initialize()
        with self.assertRaises(ValueError):
            ledger.bind_run(self.db, self.backups, 'unknown-task', 1, 1)
        self.allocate()
        for run_id in (0, -1, 'abc'):
            with self.assertRaises((ValueError, sqlite3.Error)):
                ledger.bind_run(self.db, self.backups, 'reasoning-fix', run_id, 1)

    def test_allocations_and_dispatches_are_append_only(self):
        self.initialize()
        self.allocate()
        ledger.bind_run(self.db, self.backups, 'reasoning-fix', 12345, 1)
        with closing(sqlite3.connect(self.db)) as con:
            for sql in ('DELETE FROM allocations', 'UPDATE allocations SET revision=9',
                        'DELETE FROM dispatches', 'UPDATE dispatches SET attempt=9'):
                with self.subTest(sql=sql), self.assertRaises(sqlite3.IntegrityError):
                    con.execute(sql)

    def test_concurrent_allocations_are_unique(self):
        self.initialize()
        def allocate(index):
            return ledger.allocate(self.db, self.backups,
                                   dict(REQUEST, task_id=f'task-{index}'))
        with ThreadPoolExecutor(max_workers=4) as pool:
            records = list(pool.map(allocate, range(8)))
        self.assertEqual(sorted(r['versions']['revision'] for r in records), list(range(1, 9)))

    def test_missing_or_tampered_backup_refused(self):
        self.initialize()
        self.allocate()
        snapshot = sorted(self.backups.glob('*.sqlite'))[-1]
        snapshot.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'backup|witness'):
            self.allocate(task_id='t2')

    def test_stale_primary_refused_and_explicit_recovery_verified(self):
        self.initialize()
        old = self.db.read_bytes()
        self.allocate()
        self.db.write_bytes(old)
        with self.assertRaisesRegex(ValueError, 'stale|witness'):
            self.allocate(task_id='t2')
        ledger.recover(self.db, self.backups)
        self.assertEqual(self.allocate(task_id='t2')['versions']['revision'], 2)

    def test_lost_primary_can_only_be_explicitly_recovered(self):
        self.initialize()
        self.allocate()
        self.db.unlink()
        with self.assertRaises(ValueError):
            self.allocate()
        ledger.recover(self.db, self.backups)
        self.assertEqual(self.allocate()['versions']['revision'], 1)

    def test_missing_backup_chain_or_policy_drift_refused(self):
        self.initialize()
        self.allocate()
        (self.backups / '00000000.json').unlink()
        with self.assertRaises(ValueError):
            self.allocate(task_id='t2')

    def test_helper_cli_does_not_auto_create_lost_state(self):
        import subprocess
        result = subprocess.run(['python', 'linux/revision_versions.py', str(self.root / 'lost.json'),
                                 '--run-id', '12345', '--output', str(self.root / 'out.json')],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / 'lost.json').exists())


if __name__ == '__main__':
    unittest.main()
