import pathlib
import hashlib
import tempfile
import unittest
from unittest.mock import patch
from prepare_signing import prepare


class SigningTests(unittest.TestCase):
    def test_authorized_certificate_writes_escaped_properties(self):
        with tempfile.TemporaryDirectory() as root:
            env = dict(KEYSTORE_BASE64='a2V5', STORE_PASSWORD='a b\\c', KEY_PASSWORD='p:=', KEY_ALIAS='release')
            with patch('prepare_signing.subprocess.run') as run, patch('prepare_signing.EXPECTED_CERT', hashlib.sha256(b'certificate').hexdigest()):
                run.return_value.stdout = b'certificate'
                prepare(root, root, env)
            text = (pathlib.Path(root) / 'key.properties').read_text()
            self.assertIn('storePassword=a\\u0020b\\u005cc', text)
            self.assertIn('keyPassword=p\\u003a\\u003d', text)

    def test_missing_secrets_fail_before_writing(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                prepare(root, root, {})
            self.assertEqual(list(pathlib.Path(root).iterdir()), [])

    def test_wrong_certificate_is_rejected_and_removed(self):
        with tempfile.TemporaryDirectory() as root:
            env = dict(KEYSTORE_BASE64='a2V5', STORE_PASSWORD='test', KEY_PASSWORD='test', KEY_ALIAS='test')
            with patch('prepare_signing.subprocess.run') as run:
                run.return_value.stdout = b'wrong certificate'
                with self.assertRaises(ValueError):
                    prepare(root, root, env)
            self.assertEqual(list(pathlib.Path(root).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
