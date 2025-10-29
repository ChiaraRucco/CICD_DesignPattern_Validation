"""
Experiment 8: Environment State Inspection
Inspect and verify environment states after deployments
"""

import sys
sys.path.insert(0, '.')

from eadf_core.environment_simulator import EnvironmentSimulator
import json
from pathlib import Path

def inspect_environment_states():
    """Inspect all environment states and deployment history"""
    print("=" * 70)
    print("EXPERIMENT 8: Environment State Inspection")
    print("=" * 70)
    
    env_sim = EnvironmentSimulator()
    
    # Inspect each environment
    for env in ['dev', 'sit', 'uat', 'prod']:
        print(f"\n{'='*70}")
        print(f"{env.upper()} ENVIRONMENT")
        print(f"{'='*70}")
        
        # Get state
        state = env_sim.get_state(env)
        
        print(f"\nDeployment Statistics:")
        print(f"  Total deployments: {state['deployment_count']}")
        print(f"  Last deployment: {state['last_deployment'] or 'Never'}")
        print(f"  Deployed components: {len(state['deployed_components'])}")
        
        # Show deployed components
        if state['deployed_components']:
            print(f"\nDeployed Components:")
            for comp_name, comp_info in state['deployed_components'].items():
                print(f"\n  • {comp_name}")
                print(f"      Version: {comp_info['version']}")
                print(f"      Status: {comp_info['status']}")
                print(f"      Deployed: {comp_info['deployed_at']}")
                print(f"      Location: {comp_info['artifact_path']}")
                
                # Check if file exists
                artifact_path = Path(comp_info['artifact_path'])
                if artifact_path.exists():
                    size = artifact_path.stat().st_size
                    print(f"      File size: {size} bytes")
                    print(f"      ✓ Artifact verified on disk")
                else:
                    print(f"      ✗ Artifact file not found")
        
        # Show deployment history
        history = env_sim.get_deployment_history(env)
        
        if history:
            print(f"\nRecent Deployment History ({len(history)} total):")
            for entry in history[-5:]:  # Last 5
                print(f"  • {entry['timestamp']}: {entry['action']} {entry['component']} v{entry['version']}")
        
        # Show directory contents
        env_path = Path(f"environments/{env}")
        pipelines_path = env_path / "pipelines"
        backups_path = env_path / "backups"
        
        print(f"\nDirectory Contents:")
        
        if pipelines_path.exists():
            pipeline_files = list(pipelines_path.glob("*.json"))
            print(f"  Pipelines: {len(pipeline_files)} file(s)")
            for f in pipeline_files:
                print(f"    • {f.name}")
        
        if backups_path.exists():
            backup_files = list(backups_path.glob("*.json"))
            print(f"  Backups: {len(backup_files)} file(s)")
            for f in backup_files:
                print(f"    • {f.name}")
    
    # Overall summary
    print(f"\n{'='*70}")
    print("OVERALL SUMMARY")
    print(f"{'='*70}")
    
    summary = env_sim.get_environment_summary()
    
    total_deployments = sum(s['total_deployments'] for s in summary.values())
    total_components = sum(s['deployed_components'] for s in summary.values())
    
    print(f"\nTotal deployments across all environments: {total_deployments}")
    print(f"Total deployed component instances: {total_components}")
    
    # Check promotion flow
    print(f"\nPromotion Flow Analysis:")
    
    component_name = "customer_orders_pipeline"
    promotion_chain = []
    
    for env in ['dev', 'sit', 'uat', 'prod']:
        state = env_sim.get_state(env)
        if component_name in state['deployed_components']:
            comp_info = state['deployed_components'][component_name]
            promotion_chain.append({
                'environment': env,
                'version': comp_info['version'],
                'status': comp_info['status']
            })
    
    if promotion_chain:
        print(f"\n  Component: {component_name}")
        print(f"  Promotion chain:")
        for entry in promotion_chain:
            icon = "✓" if entry['status'] == 'deployed' else "⚠"
            print(f"    {icon} {entry['environment'].upper()}: v{entry['version']} ({entry['status']})")
    
    # Save inspection results
    Path("results").mkdir(exist_ok=True)
    
    inspection_results = {
        'environments': {env: env_sim.get_state(env) for env in ['dev', 'sit', 'uat', 'prod']},
        'summary': summary,
        'total_deployments': total_deployments,
        'promotion_chain': promotion_chain
    }
    
    with open("results/environment_inspection.json", 'w') as f:
        json.dump(inspection_results, f, indent=2)
    
    print(f"\n✓ Inspection results saved to: results/environment_inspection.json")
    print("=" * 70)

if __name__ == "__main__":
    inspect_environment_states()
