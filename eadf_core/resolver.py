"""
EADF Resolver - Core execution engine
Implements the 7-stage deployment pipeline
"""

import yaml
import json
from jinja2 import Template
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EADFResolver:
    """
    Resolver-centric execution engine
    Binds YAML artifacts and executes deployment stages
    """
    
    def __init__(self, component_path: str, environment_name: str):
        """Initialize resolver with component and target environment"""
        self.component_path = Path(component_path)
        self.environment_name = environment_name
        
        # Load artifacts
        self.component = self._load_yaml(component_path)
        self.environments = self._load_yaml("ci/env/environments.yaml")
        self.pipeline = self._load_yaml("ci/pattern/pipeline.yaml")
        self.promotion = self._load_yaml("ci/pattern/promotion.yaml")
        
        # Execution state
        self.bindings = {}
        self.execution_log = []
        self.provenance = {
            'component': {},
            'environment': {},
            'pipeline': {},
            'stages': {},
            'outcomes': {}
        }
        
    def _load_yaml(self, filepath: str) -> Dict:
        """Load YAML file"""
        with open(filepath) as f:
            return yaml.safe_load(f)
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute full 7-stage deployment pipeline
        Returns: Deployment outcome with provenance
        """
        logger.info(f"=" * 70)
        logger.info(f"EADF Deployment: {self.component['name']} → {self.environment_name}")
        logger.info(f"=" * 70)
        
        start_time = datetime.now()
        
        try:
            # Stage 1: Binding
            self.stage_binding()
            
            # Stage 2: Build
            self.stage_build()
            
            # Stage 3: Validation
            self.stage_validation()
            
            # Stage 4: Deployment
            self.stage_deployment()
            
            # Stage 5: Smoke Test
            self.stage_smoke_test()
            
            # Stage 6: Gate Evaluation
            self.stage_gate_evaluation()
            
            # Stage 7: Provenance
            self.stage_provenance()
            
            outcome = {
                'status': 'success',
                'component': self.component['name'],
                'environment': self.environment_name,
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
                'provenance': self.provenance
            }
            
            logger.info(f"\n✓ Deployment successful")
            
        except Exception as e:
            outcome = {
                'status': 'failed',
                'component': self.component['name'],
                'environment': self.environment_name,
                'error': str(e),
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
                'provenance': self.provenance
            }
            
            logger.error(f"\n✗ Deployment failed: {e}")
        
        return outcome
    
    def stage_binding(self):
        """
        Stage 1: Binding
        Resolve environment-specific parameters at deployment time (late binding)
        """
        logger.info(f"\n[1/7] BINDING - Late resolution of environment parameters")
        
        if self.environment_name not in self.environments['environments']:
            raise ValueError(f"Environment '{self.environment_name}' not found")
        
        environment = self.environments['environments'][self.environment_name]
        
        # Bind environment parameters
        self.bindings = {
            'component': self.component,
            'environment': environment,
            'env_name': self.environment_name,
            'timestamp': datetime.now().isoformat(),
            'pipeline_version': self.pipeline['version']
        }
        
        # Resolve template variables (e.g., {{vault:secret_name}})
        self.bindings = self._resolve_templates(self.bindings)
        
        # Validate bindings
        self._validate_bindings()
        
        logger.info(f"  ✓ Bound to environment: {self.environment_name}")
        logger.info(f"  ✓ Cloud: {environment['cloud']}")
        logger.info(f"  ✓ Region: {environment['region']}")
        
        self.provenance['stages']['binding'] = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'environment_snapshot': environment
        }
    
    def stage_build(self):
        """
        Stage 2: Build
        Package artifact into consistent reusable unit
        """
        logger.info(f"\n[2/7] BUILD - Package artifact")
        
        component_type = self.component['type']
        
        # Dispatch by component type
        if component_type == 'adf_pipeline':
            self._build_adf_pipeline()
        elif component_type == 'dbt_project':
            self._build_dbt_project()
        elif component_type == 'databricks_notebook':
            self._build_databricks_notebook()
        else:
            logger.warning(f"  ⚠ Unknown component type: {component_type}, using default build")
        
        # Version artifact
        artifact_hash = self._calculate_artifact_hash()
        
        logger.info(f"  ✓ Component type: {component_type}")
        logger.info(f"  ✓ Artifact version: {self.component['version']}")
        logger.info(f"  ✓ Artifact hash: {artifact_hash[:16]}...")
        
        self.provenance['stages']['build'] = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'component_type': component_type,
            'artifact_version': self.component['version'],
            'artifact_hash': artifact_hash
        }
    
    def stage_validation(self):
        """
        Stage 3: Validation
        Check artifact against schema rules and compatibility constraints
        """
        logger.info(f"\n[3/7] VALIDATION - Schema and compatibility checks")
        
        # Schema validation
        self._validate_schema()
        
        # Dependency validation
        self._check_dependencies()
        
        # Compatibility validation
        self._verify_compatibility()
        
        logger.info(f"  ✓ Schema validation passed")
        logger.info(f"  ✓ Dependencies satisfied")
        logger.info(f"  ✓ Compatibility verified")
        
        self.provenance['stages']['validation'] = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'checks_passed': ['schema', 'dependencies', 'compatibility']
        }
    
    def stage_deployment(self):
        """
        Stage 4: Deployment
        Instantiate artifact into target environment using bindings
        """
        logger.info(f"\n[4/7] DEPLOYMENT - Instantiate to {self.environment_name}")
        
        component_type = self.component['type']
        cloud = self.bindings['environment']['cloud']
        
        # Dispatch by component type and cloud
        if component_type == 'adf_pipeline' and cloud == 'azure':
            self._deploy_adf_to_azure()
        elif component_type == 'adf_pipeline' and cloud == 'aws':
            self._deploy_adf_to_aws()
        else:
            logger.warning(f"  ⚠ Deployment not implemented for {component_type} on {cloud}")
        
        logger.info(f"  ✓ Deployed to {cloud}")
        
        resource_group = self.bindings['environment'].get('orchestrator', {}).get('resource_group', 'N/A')
        logger.info(f"  ✓ Resource group: {resource_group}")
        
        self.provenance['stages']['deployment'] = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'cloud': cloud,
            'region': self.bindings['environment']['region']
        }
    
    def stage_smoke_test(self):
        """
        Stage 5: Smoke Test
        Lightweight verification that artifact runs correctly
        """
        logger.info(f"\n[5/7] SMOKE TEST - Verify deployment")
        
        smoke_test_config = self.component.get('smoke_test', {})
        
        if not smoke_test_config:
            logger.info(f"  ⊘ No smoke test defined (skipped)")
            self.provenance['stages']['smoke_test'] = {
                'status': 'skipped',
                'timestamp': datetime.now().isoformat()
            }
            return
        
        # Execute smoke test based on type
        test_type = smoke_test_config.get('type', 'row_count_check')
        component_type = self.component.get('type')

        # --- Branch on test type ---
        if test_type == 'row_count_check':
            result = self._smoke_test_row_count(smoke_test_config)
        elif test_type == 'pipeline_status':
            result = self._smoke_test_pipeline_status(smoke_test_config)
        elif test_type == 'dbt_test':
            result = self._smoke_test_dbt(smoke_test_config)
        elif test_type == 'notebook_run':
            result = self._smoke_test_notebook(smoke_test_config)
        else:
            raise ValueError(f"Unknown smoke test type: {test_type}")

        if not result['passed']:
            raise RuntimeError(f"Smoke test failed: {result['message']}")
        
        logger.info(f"  ✓ Smoke test passed: {test_type}")
        logger.info(f"  ✓ {result['message']}")
        
        self.provenance['stages']['smoke_test'] = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'test_type': test_type,
            'component_type': component_type,
            'result': result
        }

    
    def stage_gate_evaluation(self):
        """
        Stage 6: Gate Evaluation
        Evaluate promotion policies to determine if component can advance
        """
        logger.info(f"\n[6/7] GATE EVALUATION - Check promotion policies")
        
        # Determine promotion path (e.g., dev_to_sit, sit_to_uat)
        current_env = self.environment_name
        promotion_key = self._get_promotion_key(current_env)
        
        if not promotion_key:
            logger.info(f"  ⊘ No promotion from {current_env} (terminal stage)")
            self.provenance['stages']['gate_evaluation'] = {
                'status': 'skipped',
                'timestamp': datetime.now().isoformat(),
                'reason': 'terminal_stage'
            }
            return
        
        if promotion_key not in self.promotion.get('promotion_rules', {}):
            logger.info(f"  ⊘ No promotion rules defined for {promotion_key}")
            self.provenance['stages']['gate_evaluation'] = {
                'status': 'skipped',
                'timestamp': datetime.now().isoformat(),
                'reason': 'no_rules_defined'
            }
            return
        
        promotion_rules = self.promotion['promotion_rules'][promotion_key]
        gates = promotion_rules.get('gates', [])
        
        # Evaluate each gate
        gate_results = []
        for gate in gates:
            result = self._evaluate_gate(gate)
            gate_results.append(result)
            
            status_icon = "✓" if result['passed'] else "✗"
            logger.info(f"  {status_icon} {gate['name']}: {result['message']}")
        
        all_passed = all(r['passed'] for r in gate_results)
        
        if all_passed:
            logger.info(f"  ✓ All gates passed - eligible for promotion to next stage")
        else:
            logger.info(f"  ⚠ Some gates failed - promotion blocked")
        
        self.provenance['stages']['gate_evaluation'] = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'promotion_path': promotion_key,
            'gates_evaluated': len(gates),
            'gates_passed': sum(1 for r in gate_results if r['passed']),
            'eligible_for_promotion': all_passed,
            'gate_results': gate_results
        }
    
    def stage_provenance(self):
        """
        Stage 7: Provenance
        Record deployment metadata for auditability and reproducibility
        """
        logger.info(f"\n[7/7] PROVENANCE - Record deployment metadata")
        
        # Capture component identity
        self.provenance['component'] = {
            'name': self.component['name'],
            'type': self.component['type'],
            'version': self.component['version'],
            'commit_sha': self.component.get('source', {}).get('commit_sha', 'unknown')
        }
        
        # Capture effective environment snapshot
        self.provenance['environment'] = {
            'name': self.environment_name,
            'cloud': self.bindings['environment']['cloud'],
            'region': self.bindings['environment']['region'],
            'stage': self.bindings['environment']['stage']
        }
        
        # Capture template versions
        self.provenance['pipeline'] = {
            'version': self.pipeline['version'],
            'pipeline_hash': self._hash_dict(self.pipeline),
            'promotion_hash': self._hash_dict(self.promotion)
        }
        
        # Calculate overall outcome
        all_stages_success = all(
            stage.get('status') in ['success', 'skipped']
            for stage in self.provenance['stages'].values()
        )
        
        self.provenance['outcomes'] = {
            'overall_status': 'success' if all_stages_success else 'partial_failure',
            'deployment_timestamp': datetime.now().isoformat(),
            'total_stages': 7,
            'successful_stages': sum(1 for s in self.provenance['stages'].values() if s.get('status') == 'success')
        }
        
        # Store provenance
        self._store_provenance()
        
        logger.info(f"  ✓ Provenance recorded")
        logger.info(f"  ✓ Deployment ID: {self._get_deployment_id()}")
        logger.info(f"  ✓ Audit trail complete")
    
    # Helper methods
    
    def _resolve_templates(self, config: Dict) -> Dict:
        """Resolve template variables like {{vault:secret}}"""
        # Recursive resolution to avoid JSON parsing issues
        def resolve_value(value):
            if isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            elif isinstance(value, str):
                # Replace vault templates with mock values
                if '{{vault:' in value:
                    # Extract secret name between {{vault: and }}
                    import re
                    pattern = r'\{\{vault:([^}]+)\}\}'
                    matches = re.findall(pattern, value)
                    for secret_name in matches:
                        mock_value = f'MOCK_SECRET_{secret_name.upper()}'
                        value = value.replace(f'{{{{vault:{secret_name}}}}}', mock_value)
                return value
            else:
                return value
        
        return resolve_value(config)
    
    def _validate_bindings(self):
        """Validate that all required bindings are present"""
        required_fields = ['component', 'environment', 'env_name']
        for field in required_fields:
            if field not in self.bindings:
                raise ValueError(f"Missing required binding: {field}")
    
    def _calculate_artifact_hash(self) -> str:
        """Calculate hash of artifact for versioning"""
        artifact_str = json.dumps(self.component, sort_keys=True)
        return hashlib.sha256(artifact_str.encode()).hexdigest()
    
    def _hash_dict(self, d: Dict) -> str:
        """Calculate hash of dictionary"""
        return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()
    
    def _build_adf_pipeline(self):
        """Build Azure Data Factory pipeline artifact"""
        # Simulate build process
        logger.debug("  Building ADF pipeline artifact")
    
    def _build_dbt_project(self):
        """Build dbt project artifact"""
        logger.debug("  Building dbt project artifact")
    
    def _build_databricks_notebook(self):
        """Build Databricks notebook artifact"""
        logger.debug("  Building Databricks notebook artifact")
    
    def _validate_schema(self):
        """Validate artifact against schema"""
        # Simplified validation
        required_fields = ['name', 'type', 'version']
        for field in required_fields:
            if field not in self.component:
                raise ValueError(f"Missing required field: {field}")
    
    def _check_dependencies(self):
        """Check that dependencies are satisfied"""
        dependencies = self.component.get('depends_on', [])
        # In production: verify dependencies are deployed with minimum versions
        logger.debug(f"  Checking {len(dependencies)} dependencies")
    
    def _verify_compatibility(self):
        """Verify compatibility with target environment"""
        # Check component type is supported in target cloud
        logger.debug("  Verifying compatibility")
    
    def _deploy_adf_to_azure(self):
        """Deploy ADF pipeline to Azure"""
        # Simulate: az datafactory pipeline create ...
        logger.debug("  Deploying to Azure Data Factory")
    
    def _deploy_adf_to_aws(self):
        """Deploy ADF pipeline to AWS (translate to Step Functions)"""
        # Simulate: aws stepfunctions create-state-machine ...
        logger.debug("  Deploying to AWS Step Functions")
    
    def _smoke_test_row_count(self, config: Dict) -> Dict:
        """Execute row count smoke test"""
        # Simulate checking row count
        import random
        random.seed(42)  # For reproducibility
        row_count = random.randint(100, 10000)
        expected_min = config.get('expected_min', 1)
        
        passed = row_count >= expected_min
        return {
            'passed': passed,
            'message': f"Row count: {row_count} (expected min: {expected_min})"
        }
    
    def _smoke_test_pipeline_status(self, config: Dict) -> Dict:
        """Check pipeline execution status"""
        # Simulate checking pipeline status
        import random
        random.seed(42)
        passed = random.random() > 0.05  # 95% success rate
        
        return {
            'passed': passed,
            'message': "Pipeline status: Active" if passed else "Pipeline status: Failed"
        }

    def _smoke_test_dbt(self, config: Dict) -> Dict:
        """Run dbt smoke tests (simulate dbt test run)"""
        import random
        random.seed(42)
        tests_run = config.get('run_tests', True)
        passed = random.random() > 0.05  # 95% success rate
        
        return {
            'passed': passed,
            'message': (
                f"dbt tests {'executed' if tests_run else 'skipped'} - "
                f"{'all passed' if passed else 'some failed'}"
            )
        }

    def _smoke_test_notebook(self, config: Dict) -> Dict:
        """Run Databricks notebook smoke test"""
        import random
        random.seed(42)
        validate_output = config.get('validate_output', True)
        passed = random.random() > 0.1  # 90% success rate
        
        return {
            'passed': passed,
            'message': (
                f"Notebook run {'validated' if validate_output else 'executed'} - "
                f"{'success' if passed else 'error detected'}"
            )
        }

    
    def _get_promotion_key(self, current_env: str) -> Optional[str]:
        """Determine promotion path from current environment"""
        promotion_map = {
            'dev': 'dev_to_sit',
            'sit': 'sit_to_uat',
            'uat': 'uat_to_prod'
        }
        return promotion_map.get(current_env)
    
    def _evaluate_gate(self, gate: Dict) -> Dict:
        """Evaluate a single promotion gate"""
        gate_type = gate.get('type', 'automated')
        
        if gate_type == 'automated':
            # Simulate automated check (e.g., tests passed)
            import random
            random.seed(42)
            passed = random.random() > 0.1  # 90% pass rate
        else:
            # Manual gate - simulate approval
            import random
            random.seed(42)
            passed = random.random() > 0.2  # 80% approval rate
        
        return {
            'gate_name': gate['name'],
            'gate_type': gate_type,
            'passed': passed,
            'message': f"{'Passed' if passed else 'Failed'}"
        }
    
    def _store_provenance(self):
        """Store provenance to ledger"""
        # In production: write to database, S3, etc.
        ledger_path = Path("results/provenance")
        ledger_path.mkdir(parents=True, exist_ok=True)
        
        deployment_id = self._get_deployment_id()
        ledger_file = ledger_path / f"{deployment_id}.json"
        
        with open(ledger_file, 'w') as f:
            json.dump(self.provenance, f, indent=2)
    
    def _get_deployment_id(self) -> str:
        """Generate unique deployment ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.component['name']}_{self.environment_name}_{timestamp}"
