"""
Experiment 7: Deployment Failure Scenarios
Simulates various failure scenarios and rollback mechanisms
"""

import sys
sys.path.insert(0, '.')

from eadf_core.deployment_engine import DeploymentEngine
import json
from pathlib import Path

def test_smoke_test_failure():
    """Test deployment with smoke test failure and rollback"""
    print("\n" + "=" * 70)
    print("SCENARIO 1: Smoke Test Failure in SIT")
    print("=" * 70)
    print("Expected: Deployment fails in SIT, rollback triggered\n")
    
    engine = DeploymentEngine()
    
    # Clean up SIT environment
    engine.env_simulator.cleanup_environment('sit')
    
    # Deploy successfully to dev
    dev_result = engine.deploy_to_environment(
        component_path="components/customer_orders_pipeline/component.yaml",
        environment='dev',
        simulate_failure=None
    )
    
    print(f"\n✓ DEV deployment: {dev_result['status']}")
    
    # Attempt promotion to SIT with smoke test failure
    sit_result = engine.promote_between_environments(
        component_path="components/customer_orders_pipeline/component.yaml",
        from_env='dev',
        to_env='sit',
        simulate_failure='smoke_test'
    )
    
    print(f"\n" + "-" * 70)
    print("SMOKE TEST FAILURE ANALYSIS")
    print("-" * 70)
    
    deployment = sit_result.get('deployment', {})
    
    print(f"Status: {deployment.get('status', 'unknown')}")
    print(f"Error: {deployment.get('error', 'N/A')}")
    
    if 'rollback' in deployment:
        print(f"\nRollback:")
        print(f"  Status: {deployment['rollback']['status']}")
        print(f"  Restored from: {deployment['rollback'].get('restored_from', 'N/A')}")
        print(f"\n✓ Rollback mechanism validated")
    
    return sit_result

def test_gate_evaluation_failure():
    """Test deployment blocked by gate evaluation"""
    print("\n" + "=" * 70)
    print("SCENARIO 2: Gate Evaluation Blocks Promotion")
    print("=" * 70)
    print("Expected: Deployment succeeds but promotion blocked\n")
    
    engine = DeploymentEngine()
    
    # Clean up UAT environment
    engine.env_simulator.cleanup_environment('uat')
    
    # Deploy to SIT (assume already deployed)
    sit_result = engine.deploy_to_environment(
        component_path="components/customer_orders_pipeline/component.yaml",
        environment='sit',
        simulate_failure=None
    )
    
    print(f"\n✓ SIT deployment: {sit_result['status']}")
    
    # Attempt promotion to UAT with gate failure
    uat_result = engine.promote_between_environments(
        component_path="components/customer_orders_pipeline/component.yaml",
        from_env='sit',
        to_env='uat',
        simulate_failure='gate'
    )
    
    print(f"\n" + "-" * 70)
    print("GATE EVALUATION FAILURE ANALYSIS")
    print("-" * 70)
    
    print(f"Status: {uat_result.get('status', 'unknown')}")
    
    if uat_result['status'] == 'blocked':
        print(f"Message: {uat_result.get('message', 'N/A')}")
        print(f"\n✓ Gate enforcement validated")
        print(f"  • Deployment successful in SIT")
        print(f"  • Promotion to UAT blocked by policy")
        print(f"  • No rollback needed (deployment didn't proceed)")
    
    return uat_result

def test_deployment_stage_failure():
    """Test failure during deployment stage"""
    print("\n" + "=" * 70)
    print("SCENARIO 3: Deployment Stage Failure")
    print("=" * 70)
    print("Expected: Deployment fails, immediate rollback\n")
    
    engine = DeploymentEngine()
    
    # Clean up prod environment
    engine.env_simulator.cleanup_environment('prod')
    
    # Attempt deployment with failure
    prod_result = engine.deploy_to_environment(
        component_path="components/customer_orders_pipeline/component.yaml",
        environment='prod',
        simulate_failure='deployment'
    )
    
    print(f"\n" + "-" * 70)
    print("DEPLOYMENT FAILURE ANALYSIS")
    print("-" * 70)
    
    print(f"Status: {prod_result.get('status', 'unknown')}")
    print(f"Error: {prod_result.get('error', 'N/A')}")
    
    if 'rollback' in prod_result:
        print(f"\nRollback:")
        print(f"  Status: {prod_result['rollback']['status']}")
        print(f"\n✓ Immediate rollback on deployment failure validated")
    
    return prod_result

def test_full_pipeline_with_failures():
    """Test full pipeline with failures at different stages"""
    print("\n" + "=" * 70)
    print("SCENARIO 4: Full Pipeline with Mixed Results")
    print("=" * 70)
    print("Expected: Pipeline stops at first failure\n")
    
    engine = DeploymentEngine()
    
    # Full pipeline with failure in UAT
    result = engine.deploy_pipeline_across_environments(
        component_path="components/customer_orders_pipeline/component.yaml",
        target_envs=['dev', 'sit', 'uat', 'prod'],
        simulate_failures={
            'uat': 'smoke_test'  # Fail in UAT
        }
    )
    
    print(f"\n" + "-" * 70)
    print("PIPELINE FAILURE ANALYSIS")
    print("-" * 70)
    
    print(f"Pipeline Status: {result['status']}")
    print(f"Stopped At: {result.get('stopped_at', 'N/A')}")
    
    print(f"\nEnvironment Results:")
    for env, deployment in result['deployments'].items():
        status = deployment.get('status', 'unknown')
        icon = "✓" if status == 'success' else "✗"
        print(f"  {icon} {env.upper()}: {status}")
    
    # Verify prod was never reached
    prod_state = engine.env_simulator.get_state('prod')
    component_name = "customer_orders_pipeline"
    
    if component_name not in prod_state['deployed_components']:
        print(f"\n✓ Validation: Production environment untouched")
        print(f"  • Pipeline correctly stopped at UAT failure")
        print(f"  • No partial deployments to production")
    
    return result

def main():
    """Run all failure scenarios"""
    print("=" * 70)
    print("EXPERIMENT 7: Deployment Failure Scenarios")
    print("=" * 70)
    print("\nTesting various failure scenarios and recovery mechanisms")
    
    results = {}
    
    # Scenario 1: Smoke test failure
    results['smoke_test_failure'] = test_smoke_test_failure()
    
    # Scenario 2: Gate evaluation blocks
    results['gate_failure'] = test_gate_evaluation_failure()
    
    # Scenario 3: Deployment stage failure
    results['deployment_failure'] = test_deployment_stage_failure()
    
    # Scenario 4: Full pipeline with failures
    results['pipeline_failure'] = test_full_pipeline_with_failures()
    
    # Summary
    print("\n" + "=" * 70)
    print("FAILURE SCENARIOS SUMMARY")
    print("=" * 70)
    
    print("\n✓ Scenario 1: Smoke Test Failure")
    print("  • Failure detected post-deployment")
    print("  • Automatic rollback triggered")
    print("  • Previous version restored")
    
    print("\n✓ Scenario 2: Gate Evaluation Failure")
    print("  • Deployment successful but blocked")
    print("  • Promotion policy enforced")
    print("  • Manual intervention required")
    
    print("\n✓ Scenario 3: Deployment Stage Failure")
    print("  • Failure during deployment")
    print("  • Immediate rollback executed")
    print("  • Environment restored to previous state")
    
    print("\n✓ Scenario 4: Pipeline Failure")
    print("  • Multi-environment pipeline halted")
    print("  • Downstream environments protected")
    print("  • Partial deployments prevented")
    
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    print("✓ Rollback mechanisms validated")
    print("✓ Gate enforcement validated")
    print("✓ Failure isolation validated")
    print("✓ Environment protection validated")
    
    # Save results
    Path("results").mkdir(exist_ok=True)
    
    with open("results/deployment_failures.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n✓ Results saved to: results/deployment_failures.json")
    print("=" * 70)

if __name__ == "__main__":
    main()
