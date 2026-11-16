import importlib.util
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('restore', Path(__file__).with_name('restore-user-state.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RestoreTests(unittest.TestCase):
    def test_preserves_state_and_workspace_without_old_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            backup, target = root / 'backup', root / 'target'
            (backup / 'home/bin').mkdir(parents=True)
            (backup / 'workspace/bin').mkdir(parents=True)
            (backup / 'home/bin/old.exe').write_bytes(b'old')
            (backup / 'home/auth.lock').write_text('stale')
            (backup / 'home/.env').write_text('fixture')
            (backup / 'workspace/bin/user.txt').write_text('user')
            with closing(sqlite3.connect(backup / 'home/state.db')) as db:
                db.execute('create table messages (value text)')
                db.execute("insert into messages values ('saved')")
                db.commit()
            result = module.restore(backup, target)
            self.assertEqual(result['home/state.db'], 'ok')
            self.assertFalse((target / 'home/bin').exists())
            self.assertFalse((target / 'home/auth.lock').exists())
            self.assertEqual((target / 'workspace/bin/user.txt').read_text(), 'user')
            self.assertEqual((target / 'home/.env').read_text(), 'fixture')
            self.assertTrue((backup / 'home/auth.lock').exists())
            with closing(sqlite3.connect(target / 'home/state.db')) as db:
                self.assertEqual(db.execute('select value from messages').fetchone(), ('saved',))
            with self.assertRaises(ValueError):
                module.restore(backup, target)


if __name__ == '__main__':
    unittest.main()
