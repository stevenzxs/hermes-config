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

    def test_submit_keeps_default_branch_blocked(self):
        with patch.object(kb, 'check_origin'), patch.object(kb, 'git', return_value='main'), patch.object(kb, 'api') as api:
            with self.assertRaises(ValueError):
                kb.submit('test')
            api.assert_not_called()

    def test_submit_without_branch_rule_attestation(self):
        with patch.object(kb, 'check_origin'), patch.object(kb, 'git', side_effect=['hermes/test', '']), patch.object(kb, 'token', return_value='test'), patch.object(kb, 'api', side_effect=[{'default_branch': 'main'}, [{'html_url': 'https://github.com/stevenzxs/knowledgebase/pull/1'}]]) as api, patch.object(kb.subprocess, 'run') as run:
            kb.submit('test')
            self.assertEqual(api.call_count, 2)
            self.assertIn('HEAD:refs/heads/hermes/test', run.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
