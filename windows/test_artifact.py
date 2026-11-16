import json
import pathlib
import tempfile
import unittest

from artifact import inspect_artifact


class ArtifactTests(unittest.TestCase):
    def fixture(self, root):
        payload = root / 'resources/agent-payload'
        (payload / 'bin').mkdir(parents=True)
        (payload / 'bin/hermes-abc.exe').write_bytes(b'cli')
        (root / 'hermes-abc.exe').write_bytes(b'desktop')
        runtime = {'commands': {'hermes': 'bin/hermes-abc.exe'}}
        stamp = {'commit': 'a' * 40, 'dirty': False, 'payload': 'bundled', 'runtime': runtime}
        (root / 'resources/install-stamp.json').write_text(json.dumps(stamp))
        (payload / 'manifest.json').write_text(json.dumps({'ref': 'a' * 40, 'runtime': runtime}))

    def test_commit_named_executable_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self.fixture(root)
            result = inspect_artifact(root, 'a' * 40)
            self.assertEqual(result['desktop'], 'hermes-abc.exe')
            self.assertEqual(result['cli'], 'resources/agent-payload/bin/hermes-abc.exe')

    def test_wrong_source_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self.fixture(root)
            with self.assertRaises(ValueError):
                inspect_artifact(root, 'b' * 40)

    def test_command_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self.fixture(root)
            stamp_path = root / 'resources/install-stamp.json'
            stamp = json.loads(stamp_path.read_text())
            stamp['runtime']['commands']['hermes'] = '../../../outside.exe'
            stamp_path.write_text(json.dumps(stamp))
            with self.assertRaises(ValueError):
                inspect_artifact(root, 'a' * 40)


if __name__ == '__main__':
    unittest.main()
