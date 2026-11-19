"""Tests for the joint release workflow YAML contract; no execution."""
import json
import tempfile
import unittest
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).with_name('..') / '.github' / 'workflows' / 'hermes-joint-release.yml'


class WorkflowContractTests(unittest.TestCase):
    def test_manual_version_inputs_removed(self):
        w = yaml.safe_load(WORKFLOW.read_text())
        inputs = w[True]['workflow_dispatch']['inputs']
        self.assertNotIn('version', inputs, 'version must be allocated, not manual')
        self.assertNotIn('android_code', inputs, 'android_code must be allocated')
        self.assertNotIn('previous_android_code', inputs, 'previous code derived from ledger')

    def test_task_id_input_required(self):
        w = yaml.safe_load(WORKFLOW.read_text())
        inputs = w[True]['workflow_dispatch']['inputs']
        self.assertIn('task_id', inputs)
        self.assertTrue(inputs['task_id']['required'])

    def test_allocation_step_runs_before_build(self):
        w = yaml.safe_load(WORKFLOW.read_text())
        admit = w['jobs']['admit']
        step_names = [s.get('name', '') for s in admit['steps']]
        self.assertIn('Allocate joint revision', step_names)
        self.assertIn('Validate fixed inputs and committed version contract', step_names)
        alloc_idx = step_names.index('Allocate joint revision')
        validate_idx = step_names.index('Validate fixed inputs and committed version contract')
        self.assertLess(alloc_idx, validate_idx, 'allocation must precede validation')

    def test_image_job_uses_allocated_version(self):
        w = yaml.safe_load(WORKFLOW.read_text())
        image = w['jobs']['image']
        self.assertEqual(image['needs'], 'admit')
        steps = {s.get('name', ''): s for s in image['steps']}
        stamp = steps['Write install stamp and build image']['run']
        self.assertIn('display-version', stamp)
        self.assertIn('needs.admit.outputs.version', stamp)
        tag_check = steps['Resolve or verify existing version tag']
        env = tag_check.get('env', {})
        self.assertIn('needs.admit.outputs.image_tag', env.get('VERSION', ''))
        self.assertIn('needs.admit.outputs.version', env.get('ALLOCATED_VERSION', ''))

    def test_android_job_receives_allocated_version(self):
        w = yaml.safe_load(WORKFLOW.read_text())
        android = w['jobs']['android']
        self.assertEqual(android['uses'], './.github/workflows/hermes-android.yml')
        self.assertIn('version', android['with'])
        self.assertIn('needs.admit.outputs.version', android['with']['version'])
        self.assertIn('needs.admit.outputs.android_code', android['with']['android_code'])

    def test_package_job_records_allocated_version(self):
        w = yaml.safe_load(WORKFLOW.read_text())
        package = w['jobs']['package']
        self.assertIn('needs', package)
        self.assertIn('admit', package['needs'])
        manifest = package['steps'][2]['run']
        self.assertIn('needs.admit.outputs.version', manifest)

    def test_allocation_uses_ledger_cli(self):
        w = yaml.safe_load(WORKFLOW.read_text())
        admit = w['jobs']['admit']
        alloc_step = next(s for s in admit['steps'] if s.get('name') == 'Allocate joint revision')
        self.assertIn('revision_ledger.py', alloc_step['run'])
        self.assertIn('allocate', alloc_step['run'])
        self.assertIn('--task-id', alloc_step['run'])


if __name__ == '__main__':
    unittest.main()
