import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import io
import tarfile

spec = importlib.util.spec_from_file_location('offline_bundle', Path(__file__).with_name('offline_bundle.py'))
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class VerificationTests(unittest.TestCase):
    def test_exported_config_is_image_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'image.tar.gz'
            data = b'{"architecture":"amd64","os":"linux"}'
            sha = hashlib.sha256(data).hexdigest()
            with tarfile.open(p, 'w:gz') as tar:
                for name, payload in [(sha + '.json', data),
                                      ('manifest.json', json.dumps([{'Config': sha + '.json'}]).encode())]:
                    info = tarfile.TarInfo(name); info.size = len(payload)
                    tar.addfile(info, io.BytesIO(payload))
            self.assertEqual(bundle.archive_image_id(p), 'sha256:' + sha)

    def fixture(self, root):
        for name in bundle.PAYLOAD:
            (root / name).write_text('fixture')
        manifest = dict(imageId='sha256:' + 'a' * 64, sourceCommit='e' * 40,
                        registryImage=bundle.REGISTRY + '@sha256:' + 'b' * 64,
                        buildConfigCommit='c' * 40, packagingConfigCommit='d' * 40,
                        platform='linux/amd64', localTag='hermes-offline:test')
        (root / 'manifest.json').write_text(json.dumps(manifest))
        bundle.write_checksums(root)

    def test_accept_complete(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); self.fixture(p)
            self.assertEqual(bundle.verify(p)['sourceCommit'], 'e' * 40)

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
