import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('offline_bundle', Path(__file__).with_name('offline_bundle.py'))
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class VerificationTests(unittest.TestCase):
    def fixture(self, root):
        for name in bundle.PAYLOAD:
            (root / name).write_text('fixture')
        manifest = dict(imageId='sha256:' + 'a' * 64, sourceCommit=bundle.SOURCE,
                        registryImage=bundle.REGISTRY + '@sha256:' + 'b' * 64,
                        buildConfigCommit='c' * 40, packagingConfigCommit='d' * 40,
                        platform='linux/amd64', localTag='hermes-offline:test')
        (root / 'manifest.json').write_text(json.dumps(manifest))
        bundle.write_checksums(root)

    def test_accept_complete(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); self.fixture(p)
            self.assertEqual(bundle.verify(p)['sourceCommit'], bundle.SOURCE)

    def test_reject_modified(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); self.fixture(p)
            (p / 'compose.yml').write_text('tampered')
            with self.assertRaises(ValueError): bundle.verify(p)

    def test_reject_missing_coverage(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); self.fixture(p)
            lines = (p / 'SHA256SUMS').read_text().splitlines()
            (p / 'SHA256SUMS').write_text('\n'.join(lines[1:]))
            with self.assertRaises(ValueError): bundle.verify(p)

    def test_reject_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); self.fixture(p)
            with (p / 'SHA256SUMS').open('a') as f: f.write('0' * 64 + '  ../secret\n')
            with self.assertRaises(ValueError): bundle.verify(p)

    def test_reject_invalid_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); self.fixture(p)
            m = json.loads((p / 'manifest.json').read_text()); m['imageId'] = 'latest'
            (p / 'manifest.json').write_text(json.dumps(m)); bundle.write_checksums(p)
            with self.assertRaises(ValueError): bundle.verify(p)


if __name__ == '__main__':
    unittest.main()
