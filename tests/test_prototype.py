"""
Tests for the EADF prototype resolver.

Run from the repository root:
    python -m unittest discover -s tests -v

These tests check the behavior fixed in the evidence-based revision: gates and
smoke tests fail closed without evidence, promotion rules come from
promotion.yaml, validation checks are real, and runs are reproducible.
Determinism tests write provenance files; they are removed afterwards.
"""

import copy
import io
import json
import logging
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
logging.disable(logging.CRITICAL)

import yaml  # noqa: E402

from eadf_core.resolver import EADFResolver  # noqa: E402

COMPONENT = 'components/customer_orders_pipeline/component.yaml'


class ResolverTestCase(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        os.chdir(ROOT)

    def tearDown(self):
        os.chdir(self._cwd)


class GateTests(ResolverTestCase):
    def test_promotion_key_comes_from_policy(self):
        resolver = EADFResolver(COMPONENT, 'dev')
        self.assertEqual(resolver._get_promotion_key('dev'), 'dev_to_sit')
        self.assertEqual(resolver._get_promotion_key('sit'), 'sit_to_uat')
        self.assertIsNone(resolver._get_promotion_key('prod'))

    def test_automated_gate_fails_closed_without_evidence(self):
        resolver = EADFResolver(COMPONENT, 'dev')
        resolver.env_evidence = {}
        gate = {'name': 'smoke_tests_passed', 'type': 'automated'}
        result = resolver._evaluate_gate(gate)
        self.assertFalse(result['passed'])
        self.assertEqual(result['status'], 'not_evaluated')

    def test_automated_gate_passes_only_when_evidence_says_passed(self):
        resolver = EADFResolver(COMPONENT, 'dev')
        gate = {'name': 'smoke_tests_passed', 'type': 'automated'}
        resolver.env_evidence = {'smoke_tests_passed': 'failed'}
        self.assertFalse(resolver._evaluate_gate(gate)['passed'])
        resolver.env_evidence = {'smoke_tests_passed': 'passed'}
        self.assertTrue(resolver._evaluate_gate(gate)['passed'])

    def test_manual_gate_needs_a_named_approver(self):
        resolver = EADFResolver(COMPONENT, 'dev')
        gate = {'name': 'code_review_approved', 'type': 'manual'}
        resolver.env_evidence = {}
        self.assertEqual(resolver._evaluate_gate(gate)['status'], 'pending_approval')
        resolver.env_evidence = {'code_review_approved': 'alice'}
        self.assertTrue(resolver._evaluate_gate(gate)['passed'])

    def test_gate_outcomes_do_not_depend_on_random_state(self):
        resolver = EADFResolver(COMPONENT, 'dev')
        gate = {'name': 'unit_tests_passed', 'type': 'automated'}
        resolver.env_evidence = {'unit_tests_passed': 'passed'}
        outcomes = {resolver._evaluate_gate(gate)['passed'] for _ in range(50)}
        self.assertEqual(outcomes, {True})


class SmokeTestTests(ResolverTestCase):
    def test_row_count_not_recorded_is_not_run(self):
        resolver = EADFResolver(COMPONENT, 'dev')
        resolver.env_evidence = {}
        result = resolver._smoke_test_row_count({'expected_min': 1})
        self.assertFalse(result['passed'])
        self.assertEqual(result['status'], 'not_run')

    def test_row_count_compared_with_expected_minimum(self):
        resolver = EADFResolver(COMPONENT, 'dev')
        resolver.env_evidence = {'row_count': 0}
        self.assertFalse(resolver._smoke_test_row_count({'expected_min': 1})['passed'])
        resolver.env_evidence = {'row_count': 5}
        self.assertTrue(resolver._smoke_test_row_count({'expected_min': 1})['passed'])


class ValidationTests(ResolverTestCase):
    def test_out_of_repo_dependency_fails_validation(self):
        resolver = EADFResolver('components/inventory_sync_pipeline/component.yaml', 'dev')
        resolver.stage_binding()
        with self.assertRaisesRegex(ValueError, 'not verifiable'):
            resolver._check_dependencies()

    def test_undeclared_target_cloud_fails_compatibility(self):
        resolver = EADFResolver(COMPONENT, 'dev')
        resolver.stage_binding()
        resolver.bindings['environment'] = dict(resolver.bindings['environment'], cloud='gcp')
        with self.assertRaisesRegex(ValueError, 'not declared'):
            resolver._verify_compatibility()

    def test_provenance_lists_only_checks_that_ran(self):
        resolver = EADFResolver(COMPONENT, 'dev')
        resolver.stage_binding()
        resolver.stage_build()
        resolver.stage_validation()
        record = resolver.provenance['stages']['validation']
        self.assertEqual(record['checks_passed'], ['schema', 'dependencies', 'compatibility'])
        self.assertEqual(record['checks']['dependencies'], 'passed')


class DeterminismTests(ResolverTestCase):
    def _strip(self, obj):
        if isinstance(obj, dict):
            return {k: self._strip(v) for k, v in obj.items()
                    if not re.search(r'timestamp|time|run_id|deployment_id|duration', k)}
        if isinstance(obj, list):
            return [self._strip(x) for x in obj]
        return obj

    def test_same_promotion_twice_gives_same_outcome(self):
        provenance_dir = ROOT / 'results' / 'provenance'
        before = set(provenance_dir.glob('*.json'))
        try:
            for component in ['components/customer_orders_pipeline/component.yaml',
                              'components/analytics_dbt/component.yaml']:
                for env in ['dev', 'sit', 'uat', 'prod']:
                    runs = []
                    for _ in range(2):
                        with redirect_stdout(io.StringIO()):
                            outcome = EADFResolver(component, env).execute()
                        runs.append(json.dumps(self._strip(outcome), sort_keys=True, default=str))
                    self.assertEqual(runs[0], runs[1], f'{component} {env} differs between runs')
        finally:
            for path in set(provenance_dir.glob('*.json')) - before:
                path.unlink()


if __name__ == '__main__':
    unittest.main()
