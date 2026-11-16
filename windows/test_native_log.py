import pathlib
import subprocess
import sys
import tempfile
import unittest


class NativeLogTests(unittest.TestCase):
    def test_stderr_progress_is_not_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            log = pathlib.Path(directory) / 'build.log'
            result = subprocess.run([
                sys.executable, str(pathlib.Path(__file__).with_name('native_log.py')),
                str(log), sys.executable, '-c',
                "import sys; print('progress', file=sys.stderr); print('done')",
            ], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b'progress', log.read_bytes())
            self.assertIn(b'done', log.read_bytes())

    def test_child_failure_is_propagated(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([
                sys.executable, str(pathlib.Path(__file__).with_name('native_log.py')),
                str(pathlib.Path(directory) / 'build.log'), sys.executable,
                '-c', 'raise SystemExit(7)',
            ], capture_output=True)
            self.assertEqual(result.returncode, 7, result.stderr)


if __name__ == '__main__':
    unittest.main()
