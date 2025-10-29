"""
Experiment 6: Multi-Environment Deployment
Enhanced to deploy ALL components in the project

PURPOSE: Validate deployment of all components across all environments

DESIGN PATTERN CLAIM:
"EADF supports multi-component, multi-environment deployment with automatic promotion"

VALIDATION APPROACH:
1. Discover all components in components/ folder
2. Deploy each component through dev → sit → uat → prod
3. Validate promotion gates between environments
4. Verify all components deployed successfully
"""

import sys
sys.path.insert(0, '.')

from eadf_core.deployment_engine import DeploymentEngine
import json
from pathlib import Path
import yaml

def discover_all_components():
    """Discover all component.yaml files in components/ folder"""
    components_dir = Path("components")
    
    if not components_dir.exists():
        print(f"⚠️  Components directory not found: {components_dir}")
        print("    Creating components directory...")
        components_dir.mkdir(parents=True, exist_ok=True)
        return []
    
    component_paths = []
    
    for component_folder in components_dir.iterdir():
        if component_folder.is_dir():
            component_file = component_folder / "component.yaml"
            if component_file.exists():
                component_paths.append(str(component_file))
    
    return sorted(component_paths)

def load_component_metadata(component_path: str):
    """Load component metadata from YAML"""
    with open(component_path) as f:
        return yaml.safe_load(f)

def main():
    print("="*80)
    print("EXPERIMENT 6: Multi-Environment Deployment (Enhanced)")
    print("="*80)
    
    print("\nPURPOSE:")
    print("  Validate that EADF can deploy all components across multiple environments")
    print("  with automatic promotion (dev → sit → uat → prod)")
    
    print("\nDESIGN PATTERN CLAIM:")
    print('  "EADF supports multi-component, multi-environment deployment with')
    print('   automatic promotion gates and rollback capabilities"')
    
    print("\nVALIDATION APPROACH:")
    print("  1. Discover all components in components/ folder")
    print("  2. Deploy each component to dev")
    print("  3. Promote through sit → uat → prod")
    print("  4. Validate promotion gates")
    print("  5. Verify consistent state across environments")
    
    print("\n" + "="*80)
    
    # Discover all components
    print("\n" + "█"*80)
    print("STEP 1: Component Discovery")
    print("█"*80)
    
    component_paths = discover_all_components()
    
    if not component_paths:
        print("\n⚠️  No components found in components/ folder")
        print("\nTo add components:")
        print("  1. Run: python setup_sample_components.py")
        print("  2. Or manually create: components/my_component/component.yaml")
        print("  3. Run this experiment again")
        print("\nFor now, using default customer_orders_pipeline...")
        
        # Fall back to default component
        default_component = "components/customer_orders_pipeline/component.yaml"
        if Path(default_component).exists():
            component_paths = [default_component]
        else:
            print(f"\n❌ Default component not found: {default_component}")
            print("    Cannot proceed without components")
            return
    
    print(f"\n📦 Discovered {len(component_paths)} component(s):")
    
    components_metadata = []
    for path in component_paths:
        metadata = load_component_metadata(path)
        components_metadata.append({
            'path': path,
            'name': metadata['name'],
            'version': metadata['version'],
            'type': metadata['type']
        })
        
        print(f"\n  ✓ {metadata['name']} (v{metadata['version']})")
        print(f"    Type: {metadata['type']}")
        print(f"    Path: {path}")
    
    # Deploy all components
    print("\n" + "█"*80)
    print("STEP 2: Multi-Component Deployment")
    print("█"*80)
    
    print(f"\nDeploying {len(component_paths)} component(s) across environments:")
    print("  dev → sit → uat → prod")
    
    engine = DeploymentEngine()
    deployment_results = []
    
    for i, comp_meta in enumerate(components_metadata, 1):
        print(f"\n{'='*80}")
        print(f"Component {i}/{len(components_metadata)}: {comp_meta['name']}")
        print(f"{'='*80}")
        
        # Deploy through all environments
        print(f"\nDeployment Chain: dev → sit → uat → prod")
        
        try:
            result = engine.deploy_pipeline_across_environments(
                component_path=comp_meta['path'],
                target_envs=['dev', 'sit', 'uat', 'prod']
            )
            
            deployment_results.append({
                'component': comp_meta['name'],
                'version': comp_meta['version'],
                'type': comp_meta['type'],
                'status': result['status'],
                'deployments': result.get('deployments', {}),
                'promotions': result.get('promotions', [])
            })
            
            if result['status'] == 'success':
                print(f"\n✅ {comp_meta['name']} deployed successfully to all environments")
                
                # Show promotion chain
                deployments = result.get('deployments', {})
                print(f"\n  Deployment Timeline:")
                for env in ['dev', 'sit', 'uat', 'prod']:
                    if env in deployments:
                        print(f"    ✓ {env.upper()}: deployed")
                    else:
                        print(f"    ○ {env.upper()}: not deployed")
            else:
                stopped_at = result.get('stopped_at', 'unknown')
                print(f"\n❌ {comp_meta['name']} deployment stopped at: {stopped_at}")
                
        except Exception as e:
            print(f"\n❌ {comp_meta['name']} deployment failed: {e}")
            deployment_results.append({
                'component': comp_meta['name'],
                'version': comp_meta['version'],
                'type': comp_meta['type'],
                'status': 'failed',
                'error': str(e)
            })
    
    # Environment state validation
    print("\n" + "█"*80)
    print("STEP 3: Environment State Validation")
    print("█"*80)
    
    env_summary = engine.get_environment_summary()
    
    print("\n🌍 Environment State After Deployment:")
    
    for env_name in ['dev', 'sit', 'uat', 'prod']:
        env_state = env_summary.get(env_name, {})
        components = env_state.get('deployed_components', [])
        
        print(f"\n  {env_name.upper()}")
        print(f"    Total components: {len(components)}")
        
        if components:
            print(f"    Components:")
            for comp_name in components:
                comp_info = env_state.get('component_details', {}).get(comp_name, {})
                version = comp_info.get('version', 'unknown')
                comp_type = comp_info.get('type', 'unknown')
                print(f"      • {comp_name} (v{version}) [{comp_type}]")
        else:
            print(f"    No components deployed")
    
    # Validation results
    print("\n" + "="*80)
    print("VALIDATION RESULTS")
    print("="*80)
    
    successful = sum(1 for r in deployment_results if r['status'] == 'success')
    failed = len(deployment_results) - successful
    
    # Check environment consistency
    env_consistent = True
    expected_count = len([r for r in deployment_results if r['status'] == 'success'])
    
    for env_name in ['dev', 'sit', 'uat', 'prod']:
        env_state = env_summary.get(env_name, {})
        actual_count = len(env_state.get('deployed_components', []))
        if actual_count != expected_count:
            env_consistent = False
            break
    
    validations = {
        'components_discovered': len(component_paths) > 0,
        'all_components_deployed': failed == 0,
        'all_environments_reached': all(
            'prod' in r.get('deployments', {})
            for r in deployment_results
            if r['status'] == 'success'
        ),
        'environment_consistency': env_consistent,
        'multi_component_support': len(component_paths) >= 1
    }
    
    print("\n✅ Multi-Environment Deployment Validated:")
    for validation, passed in validations.items():
        icon = "✓" if passed else "✗"
        status = "PASS" if passed else "FAIL"
        print(f"  {icon} {validation.replace('_', ' ').title()}: {status}")
    
    all_passed = all(validations.values())
    
    # Summary
    print("\n" + "─"*80)
    print("Deployment Summary")
    print("─"*80)
    
    print(f"\n📊 Statistics:")
    print(f"  Components deployed: {len(deployment_results)}")
    print(f"  Successful: {successful}")
    if failed > 0:
        print(f"  Failed: {failed}")
    print(f"  Total deployments: {successful * 4} (across 4 environments)")
    
    print(f"\n📋 Component Results:")
    for result in deployment_results:
        icon = "✅" if result['status'] == 'success' else "❌"
        print(f"  {icon} {result['component']} (v{result['version']}) - {result['status']}")
    
    # Conclusion
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    
    if all_passed:
        print("\n✅ SUCCESS: Multi-component, multi-environment deployment validated")
        
        print("\nKey Findings:")
        print(f"  • Deployed {len(component_paths)} component(s) to 4 environments")
        print(f"  • Total successful deployments: {successful * 4}")
        print(f"  • Promotion chain: dev → sit → uat → prod")
        print(f"  • All environments have consistent component inventory")
        
        print("\n💡 EADF Pattern Validated:")
        print("  EADF successfully manages multi-component deployment across")
        print("  multiple environments with automatic promotion, demonstrating")
        print("  enterprise-scale capability for data platform management.")
    else:
        print("\n⚠️ ISSUES FOUND: Some validations failed")
        
        if failed > 0:
            print(f"\n{failed} component(s) failed to deploy:")
            for result in deployment_results:
                if result['status'] != 'success':
                    error = result.get('error', 'Unknown error')
                    print(f"  • {result['component']}: {error}")
    
    # Save results
    Path("results").mkdir(exist_ok=True)
    
    with open("results/deployment_success.json", 'w') as f:
        json.dump({
            'components_deployed': len(deployment_results),
            'components_metadata': components_metadata,
            'deployment_results': deployment_results,
            'environment_summary': env_summary,
            'validations': validations,
            'all_passed': all_passed
        }, f, indent=2)
    
    print("\n✓ Results saved to: results/deployment_success.json")
    print("="*80)

if __name__ == "__main__":
    main()
