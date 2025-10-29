"""
Enhanced Deployment Engine with Multi-Environment Support
Includes failure scenarios and rollback logic
"""

import sys
sys.path.insert(0, '.')

from eadf_core.resolver import EADFResolver
from eadf_core.environment_simulator import EnvironmentSimulator
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import random
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentEngine:
    """
    Enhanced deployment engine with multi-environment support
    """
    
    def __init__(self):
        self.env_simulator = EnvironmentSimulator()
        self.deployment_log = []
    
    def deploy_to_environment(self,
                             component_path: str,
                             environment: str,
                             simulate_failure: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute full deployment to environment with optional failure simulation
        
        Args:
            component_path: Path to component.yaml
            environment: Target environment (dev/sit/uat/prod)
            simulate_failure: Optional failure type ('smoke_test', 'gate', 'deployment')
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"DEPLOYMENT: {Path(component_path).parent.name} → {environment}")
        logger.info(f"{'='*70}")
        
        deployment_record = {
            'component_path': component_path,
            'environment': environment,
            'start_time': datetime.now().isoformat(),
            'stages': {}
        }
        
        try:
            # Initialize resolver
            resolver = EADFResolver(component_path, environment)
            component_name = resolver.component['name']
            version = resolver.component['version']
            
            # Stage 1-3: Binding, Build, Validation
            logger.info(f"\n[Stages 1-3] Binding → Build → Validation")
            resolver.stage_binding()
            resolver.stage_build()
            resolver.stage_validation()
            
            deployment_record['stages']['pre_deployment'] = 'success'
            
            # Stage 4: Deployment (with optional failure)
            logger.info(f"\n[Stage 4] Deployment to {environment}")
            
            if simulate_failure == 'deployment':
                raise RuntimeError("Simulated deployment failure")
            
            # Create artifact file (simulate actual pipeline JSON)
            artifact_path = self._create_artifact(component_name, version)
            
            # Deploy to environment
            deploy_result = self.env_simulator.deploy_artifact(
                component_name=component_name,
                artifact_path=artifact_path,
                environment=environment,
                version=version
            )
            
            resolver.stage_deployment()
            deployment_record['stages']['deployment'] = 'success'
            deployment_record['artifact_location'] = deploy_result['artifact_location']
            
            # Stage 5: Smoke Test (with optional failure)
            logger.info(f"\n[Stage 5] Smoke Test")
            
            if simulate_failure == 'smoke_test':
                logger.error(f"  ✗ Smoke test failed (simulated)")
                raise RuntimeError("Smoke test failed: Row count check returned 0 rows")
            
            resolver.stage_smoke_test()
            deployment_record['stages']['smoke_test'] = 'success'
            
            # Verify deployment
            if not self.env_simulator.verify_deployment(component_name, environment):
                raise RuntimeError("Deployment verification failed")
            
            # Stage 6: Gate Evaluation (with optional failure)
            logger.info(f"\n[Stage 6] Gate Evaluation")
            
            if simulate_failure == 'gate':
                logger.error(f"  ✗ Gate evaluation failed (simulated)")
                deployment_record['stages']['gate_evaluation'] = 'blocked'
                deployment_record['status'] = 'success_but_blocked'
                deployment_record['message'] = 'Deployment successful but promotion blocked by gate'
                return deployment_record
            
            resolver.stage_gate_evaluation()
            deployment_record['stages']['gate_evaluation'] = 'passed'
            
            # Stage 7: Provenance
            logger.info(f"\n[Stage 7] Provenance")
            resolver.stage_provenance()
            deployment_record['stages']['provenance'] = 'recorded'
            
            # Success
            deployment_record['status'] = 'success'
            deployment_record['end_time'] = datetime.now().isoformat()
            deployment_record['eligible_for_promotion'] = True
            
            logger.info(f"\n✓ Deployment successful to {environment}")
            
        except Exception as e:
            # Handle failure
            logger.error(f"\n✗ Deployment failed: {e}")
            
            deployment_record['status'] = 'failed'
            deployment_record['error'] = str(e)
            deployment_record['end_time'] = datetime.now().isoformat()
            
            # Attempt rollback if deployment stage completed
            if 'deployment' in deployment_record['stages']:
                logger.info(f"\n🔄 Initiating rollback...")
                try:
                    rollback_result = self.env_simulator.rollback_artifact(
                        component_name=component_name,
                        environment=environment
                    )
                    deployment_record['rollback'] = rollback_result
                    logger.info(f"  ✓ Rollback successful")
                except Exception as rollback_error:
                    logger.error(f"  ✗ Rollback failed: {rollback_error}")
                    deployment_record['rollback_error'] = str(rollback_error)
        
        finally:
            self.deployment_log.append(deployment_record)
        
        return deployment_record
    
    def promote_between_environments(self,
                                     component_path: str,
                                     from_env: str,
                                     to_env: str,
                                     simulate_failure: Optional[str] = None) -> Dict[str, Any]:
        """
        Promote component from one environment to another
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"PROMOTION: {from_env.upper()} → {to_env.upper()}")
        logger.info(f"{'='*70}")
        
        # Load component
        import yaml
        with open(component_path) as f:
            component = yaml.safe_load(f)
        
        component_name = component['name']
        
        promotion_record = {
            'component': component_name,
            'from_environment': from_env,
            'to_environment': to_env,
            'start_time': datetime.now().isoformat()
        }
        
        try:
            # Verify source deployment exists
            source_state = self.env_simulator.get_state(from_env)
            
            if component_name not in source_state['deployed_components']:
                raise ValueError(f"Component {component_name} not found in {from_env}")
            
            logger.info(f"  ✓ Component verified in {from_env}")
            
            # Check promotion gates
            promotion_key = f"{from_env}_to_{to_env}"
            logger.info(f"  📋 Evaluating promotion policy: {promotion_key}")
            
            # Simulate gate checks
            gates_passed = self._evaluate_promotion_gates(promotion_key, simulate_failure)
            
            if not gates_passed:
                promotion_record['status'] = 'blocked'
                promotion_record['message'] = 'Promotion blocked by gates'
                logger.error(f"  ✗ Promotion blocked by gates")
                return promotion_record
            
            logger.info(f"  ✓ All gates passed")
            
            # Promote artifact
            promote_result = self.env_simulator.promote_artifact(
                component_name=component_name,
                from_environment=from_env,
                to_environment=to_env
            )
            
            # Deploy to target environment
            deploy_result = self.deploy_to_environment(
                component_path=component_path,
                environment=to_env,
                simulate_failure=simulate_failure
            )
            
            promotion_record['status'] = deploy_result['status']
            promotion_record['deployment'] = deploy_result
            promotion_record['end_time'] = datetime.now().isoformat()
            
            if deploy_result['status'] == 'success':
                logger.info(f"\n✓ Promotion successful: {from_env} → {to_env}")
            else:
                logger.error(f"\n✗ Promotion failed")
            
        except Exception as e:
            logger.error(f"\n✗ Promotion failed: {e}")
            promotion_record['status'] = 'failed'
            promotion_record['error'] = str(e)
            promotion_record['end_time'] = datetime.now().isoformat()
        
        return promotion_record
    
    def deploy_pipeline_across_environments(self,
                                           component_path: str,
                                           target_envs: Optional[List[str]] = None,
                                           simulate_failures: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Deploy component across multiple environments (dev → sit → uat → prod)
        
        Args:
            component_path: Path to component.yaml
            target_envs: List of environments (default: ['dev', 'sit', 'uat', 'prod'])
            simulate_failures: Dict mapping env to failure type, e.g. {'sit': 'smoke_test'}
        """
        if target_envs is None:
            target_envs = ['dev', 'sit', 'uat', 'prod']
        
        if simulate_failures is None:
            simulate_failures = {}
        
        logger.info(f"\n{'='*70}")
        logger.info(f"MULTI-ENVIRONMENT DEPLOYMENT PIPELINE")
        logger.info(f"Environments: {' → '.join(target_envs)}")
        logger.info(f"{'='*70}")
        
        pipeline_record = {
            'component_path': component_path,
            'environments': target_envs,
            'deployments': {},
            'start_time': datetime.now().isoformat()
        }
        
        # Deploy to first environment
        first_env = target_envs[0]
        failure_type = simulate_failures.get(first_env)
        
        first_deployment = self.deploy_to_environment(
            component_path=component_path,
            environment=first_env,
            simulate_failure=failure_type
        )
        
        pipeline_record['deployments'][first_env] = first_deployment
        
        if first_deployment['status'] != 'success':
            logger.error(f"\n✗ Pipeline stopped: Initial deployment to {first_env} failed")
            pipeline_record['status'] = 'failed'
            pipeline_record['stopped_at'] = first_env
            return pipeline_record
        
        # Promote through remaining environments
        for i in range(len(target_envs) - 1):
            from_env = target_envs[i]
            to_env = target_envs[i + 1]
            failure_type = simulate_failures.get(to_env)
            
            promotion = self.promote_between_environments(
                component_path=component_path,
                from_env=from_env,
                to_env=to_env,
                simulate_failure=failure_type
            )
            
            pipeline_record['deployments'][to_env] = promotion
            
            if promotion['status'] != 'success':
                logger.error(f"\n✗ Pipeline stopped: Promotion to {to_env} failed")
                pipeline_record['status'] = 'failed'
                pipeline_record['stopped_at'] = to_env
                return pipeline_record
        
        # Success
        pipeline_record['status'] = 'success'
        pipeline_record['end_time'] = datetime.now().isoformat()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"✓ PIPELINE COMPLETE: Deployed to all environments")
        logger.info(f"{'='*70}")
        
        return pipeline_record
    
    def _create_artifact(self, component_name: str, version: str) -> Path:
        """Create simulated artifact file"""
        artifacts_path = Path("artifacts")
        artifacts_path.mkdir(exist_ok=True)
        
        artifact_path = artifacts_path / f"{component_name}_v{version}.json"
        
        # Create mock ADF pipeline JSON
        artifact_content = {
            "name": component_name,
            "properties": {
                "activities": [
                    {
                        "name": "Extract",
                        "type": "Copy"
                    },
                    {
                        "name": "Transform",
                        "type": "DataFlow"
                    }
                ],
                "version": version
            }
        }
        
        with open(artifact_path, 'w') as f:
            json.dump(artifact_content, f, indent=2)
        
        return artifact_path
    
    def _evaluate_promotion_gates(self, promotion_key: str, simulate_failure: Optional[str]) -> bool:
        """Evaluate promotion gates"""
        if simulate_failure == 'gate':
            logger.error(f"    ✗ Gate: manual_approval - FAILED (simulated)")
            return False
        
        # Simulate gate evaluation
        gates = ['automated_tests', 'code_review', 'manual_approval']
        
        for gate in gates:
            # Simulate gate check
            passed = random.random() > 0.05  # 95% pass rate
            icon = "✓" if passed else "✗"
            logger.info(f"    {icon} Gate: {gate}")
            
            if not passed:
                return False
        
        return True
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """Get summary of all environments"""
        return self.env_simulator.get_environment_summary()
    
    def save_deployment_log(self, filepath: str):
        """Save complete deployment log"""
        with open(filepath, 'w') as f:
            json.dump(self.deployment_log, f, indent=2)
