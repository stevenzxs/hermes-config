import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('kb', Path(__file__).with_name('knowledgebase_git.py'))
kb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kb)


class KnowledgebaseTests(unittest.TestCase):
    def test_credentials_exact_scope(self):
        self.assertTrue(kb.allowed_credential(dict(protocol='https', host='github.com', path='stevenzxs/knowledgebase.git')))
        for fields in [dict(protocol='http', host='github.com', path=kb.REPO),
                       dict(protocol='https', host='github.com.evil.test', path=kb.REPO),
                       dict(protocol='https', host='github.com', path='stevenzxs/cloudmeet'),
                       dict(protocol='https', host='github.com')]:
            self.assertFalse(kb.allowed_credential(fields))

    def test_branches(self):
        self.assertTrue(kb.safe_branch('hermes/audit-20261116'))
        for branch in ['main', 'master', 'hermes/../main', 'hermes/x.lock', 'hermes/', '-main']:
            self.assertFalse(kb.safe_branch(branch))

    def test_missing_token_fails_closed(self):
        with tempfile.TemporaryDirectory() as d, patch.object(kb, 'AUTH', Path(d)):
            with self.assertRaises(ValueError):
                kb.token()


if __name__ == '__main__':
    unittest.main()
