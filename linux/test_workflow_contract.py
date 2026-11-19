"""Tests for the joint release workflow YAML contract; no execution."""
import json
import tempfile
import unittest
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).with_name('..') / '.github' / 'workflows' / 'hermes-joint-release.yml'
ANDROID_WORKFLOW = Path(__file__).with_name('..') / '.github' / 'workflows' / 'hermes-android.yml'


class WorkflowContractTests(unittest.TestCase):
    def workflow(self):
        return yaml.safe_load(WORKFLOW.read_text())

    def test_inputs_include_allocated_version_and_task(self):
        w = self.workflow()
        inputs = w[True]['workflow_dispatch']['inputs']
        self.assertIn('task_id', inputs)
        self.assertTrue(inputs['task_id']['required'])
        self.assertIn('version', inputs)
        self.assertIn('Ledger-allocated', inputs['version']['description'],
                        'version must come from the controller ledger, not manual entry')
        self.assertIn('android_code', inputs)
        self.assertIn('Ledger-allocated', inputs['android_code']['description'])
        self.assertNotIn('previous_android_code', inputs)

    def test_no_allocation_step_on_runner(self):
        w = self.workflow()
        admit = w['jobs']['admit']
        step_names = [s.get('name', '') for s in admit['steps']]
        self.assertNotIn('Allocate joint revision', step_names,
                         'ledger allocation happens on the controller, not the runner')
        self.assertIn('Validate ledger-allocated inputs', step_names)
        self.assertIn('Validate fixed inputs and committed version contract', step_names)
        validate_idx = step_names.index('Validate ledger-allocated inputs')
        contract_idx = step_names.index('Validate fixed inputs and committed version contract')
        self.assertLess(validate_idx, contract_idx, 'allocation validation must precede contract')

    def test_validate_step_checks_allocation_derivation(self):
        w = self.workflow()
        admit = w['jobs']['admit']
        step = next(s for s in admit['steps'] if s.get('name') == 'Validate ledger-allocated inputs')
        self.assertIn('revision_versions', step['run'])
        self.assertIn('versions_for_revision', step['run'])
        self.assertIn('image_tag', step['run'])

    def test_image_job_uses_allocated_version(self):
        w = self.workflow()
        image = w['jobs']['image']
        self.assertEqual(image['needs'], 'admit')
        steps = {s.get('name', ''): s for s in image['steps']}
        stamp = steps['Write install stamp and build image']['run']
        self.assertIn('display-version', stamp)
        self.assertIn('inputs.version', stamp)
        tag_check = steps['Resolve or verify existing version tag']
        env = tag_check.get('env', {})
        self.assertIn('needs.admit.outputs.image_tag', env.get('VERSION', ''))

    def test_android_job_receives_allocated_version(self):
        w = self.workflow()
        android = w['jobs']['android']
        self.assertEqual(android['uses'], './.github/workflows/hermes-android.yml')
        self.assertIn('version', android['with'])
        self.assertIn('inputs.version', android['with']['version'])
        self.assertIn('inputs.android_code', android['with']['android_code'])

    def test_package_job_records_allocated_version(self):
        w = self.workflow()
        package = w['jobs']['package']
        self.assertIn('needs', package)
        self.assertIn('admit', package['needs'])
        manifest = package['steps'][2]['run']
        self.assertIn("os.environ['VERSION']", manifest)
        self.assertIn("os.environ['ANDROID_CODE']", manifest)
        env = package['steps'][2].get('env', {})
        self.assertIn('inputs.version', env.get('VERSION', ''))
        self.assertIn('inputs.android_code', env.get('ANDROID_CODE', ''))

    def test_android_workflow_has_no_standalone_dispatch(self):
        w = yaml.safe_load(ANDROID_WORKFLOW.read_text())
        triggers = w[True]
        self.assertNotIn('workflow_dispatch', triggers,
                         'standalone Android dispatch would bypass revision allocation')
        self.assertIn('workflow_call', triggers)


if __name__ == '__main__':
    unittest.main()
