"""Instance policy checks without SSH, real credentials, Docker or commands."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).parent
TOOL = ROOT / 'runtime_approvals.py'
POLICY = ROOT / 'instances' / '150-approvals.json'
CONFIG = ('# preserve comments\nmodel: unchanged\napprovals:\n'
          '  mode: smart\n  cron_mode: deny  # cron policy\n  timeout: 300\n'
          'private_setting: never-print-this-value\n')


class RuntimeApprovalsTests(unittest.TestCase):
    def run_tool(self, path, *extra):
        return subprocess.run([sys.executable, str(TOOL), '--config', str(path),
                               '--policy', str(POLICY), *extra],
                              capture_output=True, text=True)

    def test_policy_is_instance_specific(self):
        self.assertTrue(POLICY.exists(), '150 approved instance policy missing')
        data = json.loads(POLICY.read_text())
        self.assertEqual(data['instance'], '150.158.83.70')
        self.assertEqual(data['approvals'], {'mode': 'smart', 'cron_mode': 'approve'})

    def test_check_does_not_mutate(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'config.yaml'
            p.write_text(CONFIG)
            r = self.run_tool(p)
            self.assertEqual(r.returncode, 1, r.stderr)
            self.assertEqual(p.read_text(), CONFIG)
            self.assertEqual(list(Path(d).iterdir()), [p])
            self.assertNotIn('never-print-this-value', r.stdout + r.stderr)

    def test_apply_preserves_other_bytes_and_backups(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'config.yaml'
            p.write_text(CONFIG)
            r = self.run_tool(p, '--apply')
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(p.read_text(), CONFIG.replace('cron_mode: deny', 'cron_mode: approve'))
            backups = list(Path(d).glob('config.yaml.before-cron-*'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), CONFIG)
            self.assertEqual(self.run_tool(p).returncode, 0)
            self.assertEqual(self.run_tool(p, '--apply').returncode, 0)
            self.assertEqual(len(list(Path(d).glob('config.yaml.before-cron-*'))), 1)
            self.assertNotIn('never-print-this-value', r.stdout + r.stderr)

    def test_refuses_non_smart_mode(self):
        self.assert_refused(CONFIG.replace('mode: smart', 'mode: off'))

    def test_refuses_duplicate_yaml_keys(self):
        self.assert_refused(CONFIG + 'approvals:\n  mode: smart\n  cron_mode: deny\n')

    def test_refuses_missing_cron_field(self):
        self.assert_refused(CONFIG.replace('  cron_mode: deny  # cron policy\n', ''))

    def test_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'config.yaml'
            p.write_text(CONFIG)
            link = Path(d) / 'link.yaml'
            try:
                link.symlink_to(p)
            except OSError:
                self.skipTest('symlink privilege unavailable')
            self.assertNotEqual(self.run_tool(link, '--apply').returncode, 0)
            self.assertEqual(p.read_text(), CONFIG)

    def assert_refused(self, content):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'config.yaml'
            p.write_text(content)
            r = self.run_tool(p, '--apply')
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(p.read_text(), content)
            self.assertEqual(list(Path(d).iterdir()), [p])
            self.assertNotIn('never-print-this-value', r.stdout + r.stderr)


if __name__ == '__main__':
    unittest.main()
