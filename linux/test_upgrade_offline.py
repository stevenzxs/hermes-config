"""Tests for the offline upgrade script; no real Docker or target execution."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

UPGRADE = Path(__file__).with_name('upgrade-offline.sh')


class UpgradeOfflineTests(unittest.TestCase):
    def test_script_exists_and_has_shebang(self):
        self.assertTrue(UPGRADE.is_file())
        content = UPGRADE.read_text()
        self.assertTrue(content.startswith('#!/usr/bin/env bash'))
        self.assertIn('set -euo pipefail', content)

    def test_requires_sudo(self):
        content = UPGRADE.read_text()
        self.assertIn('id -u', content)
        self.assertIn('Run via sudo', content)

    def test_refuses_missing_existing_deployment(self):
        content = UPGRADE.read_text()
        self.assertIn('! -d "$target"', content)
        self.assertIn('No existing deployment', content)

    def test_refuses_first_install_mode(self):
        content = UPGRADE.read_text()
        self.assertIn('first-install', content)
        self.assertIn('upgrade', content)

    def test_preserves_runtime_env_and_data(self):
        content = UPGRADE.read_text()
        self.assertIn('runtime.env', content)
        self.assertIn('data', content)
        self.assertIn('backup', content)

    def test_updates_image_reference_only(self):
        content = UPGRADE.read_text()
        self.assertIn('.env', content)
        self.assertIn('HERMES_IMAGE', content)
        self.assertIn('docker compose', content)

    def test_does_not_delete_data_or_secrets(self):
        content = UPGRADE.read_text()
        forbidden = ['rm -rf', 'rm -fr', 'down -v', 'prune']
        for cmd in forbidden:
            self.assertNotIn(cmd, content, f'Forbidden destructive command: {cmd}')

    def test_uses_complete_compose_stack(self):
        content = UPGRADE.read_text()
        self.assertIn('compose.yml', content)
        self.assertIn('compose.*.yml', content,
                      'must include every existing compose override, not a fixed subset')
        self.assertIn('compose_args', content)

    def test_never_fixes_override_list(self):
        content = UPGRADE.read_text()
        self.assertNotIn('-f compose.yml -f compose.offline.yml config', content,
                         'hardcoded two-file stack would drop live overrides')

    def test_validates_image_before_stopping(self):
        content = UPGRADE.read_text()
        lines = content.splitlines()
        validate_idx = None
        stop_idx = None
        for i, line in enumerate(lines):
            if 'docker image inspect' in line or 'docker load' in line:
                validate_idx = i
            if 'compose "${compose_args[@]}" up' in line:
                stop_idx = i
                break
        self.assertIsNotNone(validate_idx, 'Image validation step missing')
        self.assertIsNotNone(stop_idx, 'Compose up step missing')
        self.assertLess(validate_idx, stop_idx, 'Image must be validated before compose up')

    def test_health_check_after_upgrade(self):
        content = UPGRADE.read_text()
        self.assertIn('/health', content)
        self.assertIn('curl', content)

    def test_rollback_instructions_present(self):
        content = UPGRADE.read_text()
        self.assertIn('rollback', content.lower())


if __name__ == '__main__':
    unittest.main()
