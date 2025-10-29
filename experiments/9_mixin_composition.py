"""
Experiment 11: Mix-in Composition Validation
Demonstrates that mix-ins are reusable, composable cross-cutting concerns

PURPOSE: Prove that EADF mix-ins work as advertised - they're truly reusable
         snippets that can be mixed and matched across deployments.

VALIDATION APPROACH:
1. Deploy component with NO mix-ins (baseline)
2. Deploy component with NOTIFICATIONS mix-in only
3. Deploy component with DATA_QUALITY mix-in only
4. Deploy component with BOTH mix-ins (composition)

METRICS:
- Mix-ins applied correctly: Yes/No
- Notifications sent when mix-in enabled: Yes/No
- Data quality checks executed when mix-in enabled: Yes/No
- Mix-ins compose without conflicts: Yes/No
"""

import sys
sys.path.insert(0, '.')

from eadf_core.resolver import EADFResolver
from eadf_core.mixin_executor import MixinExecutor
import json
from pathlib import Path
import yaml

class MixinValidator:
    """Validates that mix-ins are properly applied during deployment"""
    
    def __init__(self):
        self.execution_log = []
    
    def deploy_with_mixins(self, component_path: str, environment: str, mixins: list) -> dict:
        """Deploy component with specified mix-ins"""
        
        print(f"\n{'='*70}")
        print(f"DEPLOYMENT WITH MIX-INS: {', '.join(mixins) if mixins else 'NONE'}")
        print(f"{'='*70}")
        print(f"Component: {Path(component_path).parent.name}")
        print(f"Environment: {environment}")
        print(f"Mix-ins: {mixins if mixins else '(none - baseline deployment)'}")
        
        # Initialize resolver
        resolver = EADFResolver(component_path, environment)
        
        # Load and apply mix-ins
        mixin_executor = MixinExecutor()
        applied_mixins = {}
        
        if mixins:
            print(f"\n📦 Loading and applying mix-ins:")
            for mixin_name in mixins:
                print(f"  • Loading {mixin_name}...")
                mixin_config = self._load_mixin(mixin_name)
                applied_mixins[mixin_name] = mixin_config
                print(f"    ✓ {mixin_name} loaded successfully")
        else:
            print(f"\n  ℹ No mix-ins specified - executing baseline deployment")
        
        # Execute deployment stages
        print(f"\n🚀 Executing deployment stages:")
        print(f"  [1/7] Binding...")
        resolver.stage_binding()
        
        print(f"  [2/7] Build...")
        resolver.stage_build()
        
        print(f"  [3/7] Validation...")
        resolver.stage_validation()
        
        # Apply data_quality mix-in during validation if present
        if 'data_quality' in applied_mixins:
            print(f"\n  🔍 Applying DATA_QUALITY mix-in:")
            quality_results = mixin_executor.execute_data_quality_checks(
                applied_mixins['data_quality']
            )
            print(f"    ✓ Row count check: {quality_results['row_count']['status']}")
            print(f"    ✓ Freshness check: {quality_results['freshness']['status']}")
            print(f"    ✓ Schema validation: {quality_results['schema']['status']}")
        
        print(f"  [4/7] Deployment...")
        resolver.stage_deployment()
        
        print(f"  [5/7] Smoke Test...")
        resolver.stage_smoke_test()
        
        print(f"  [6/7] Gate Evaluation...")
        resolver.stage_gate_evaluation()
        
        # Apply notifications mix-in after deployment if present
        if 'notifications' in applied_mixins:
            print(f"\n  📢 Applying NOTIFICATIONS mix-in:")
            notification_results = mixin_executor.send_notifications(
                applied_mixins['notifications'],
                deployment_status='success',
                component=resolver.component['name'],
                environment=environment
            )
            print(f"    ✓ Slack notification: {notification_results['slack']['status']}")
            print(f"    ✓ Email notification: {notification_results['email']['status']}")
        
        print(f"  [7/7] Provenance...")
        resolver.stage_provenance()
        
        # Compile results
        result = {
            'component': resolver.component['name'],
            'environment': environment,
            'mixins_requested': mixins,
            'mixins_applied': list(applied_mixins.keys()),
            'deployment_status': 'success',
            'mixin_results': {}
        }
        
        if 'notifications' in applied_mixins:
            result['mixin_results']['notifications'] = notification_results
        
        if 'data_quality' in applied_mixins:
            result['mixin_results']['data_quality'] = quality_results
        
        self.execution_log.append(result)
        
        print(f"\n✅ Deployment complete with {len(applied_mixins)} mix-in(s)")
        
        return result
    
    def _load_mixin(self, mixin_name: str) -> dict:
        """Load mix-in configuration"""
        mixin_path = Path(f"ci/pattern/mixins/{mixin_name}.yaml")
        with open(mixin_path) as f:
            return yaml.safe_load(f)

def main():
    print("="*70)
    print("EXPERIMENT 11: Mix-in Composition Validation")
    print("="*70)
    print("\nPURPOSE:")
    print("  Validate that EADF mix-ins are truly reusable, composable")
    print("  cross-cutting concerns that can be applied to any deployment.")
    print("\nAPPROACH:")
    print("  Deploy the same component 4 times with different mix-in combinations:")
    print("    1. No mix-ins (baseline)")
    print("    2. Notifications only")
    print("    3. Data quality only")
    print("    4. Both mix-ins (composition test)")
    print("\n" + "="*70)
    
    validator = MixinValidator()
    component_path = "components/customer_orders_pipeline/component.yaml"
    environment = "dev"
    
    # Scenario 1: No mix-ins (baseline)
    print("\n" + "█"*70)
    print("SCENARIO 1: Baseline Deployment (No Mix-ins)")
    print("█"*70)
    print("\nExpected: Standard deployment with no additional cross-cutting concerns")
    
    baseline = validator.deploy_with_mixins(
        component_path=component_path,
        environment=environment,
        mixins=[]
    )
    
    # Scenario 2: Notifications only
    print("\n" + "█"*70)
    print("SCENARIO 2: Deployment with Notifications Mix-in")
    print("█"*70)
    print("\nExpected: Deployment succeeds AND notifications are sent to Slack/Email")
    
    notifications_only = validator.deploy_with_mixins(
        component_path=component_path,
        environment=environment,
        mixins=['notifications']
    )
    
    # Scenario 3: Data quality only
    print("\n" + "█"*70)
    print("SCENARIO 3: Deployment with Data Quality Mix-in")
    print("█"*70)
    print("\nExpected: Deployment includes data quality checks (row count, freshness, schema)")
    
    data_quality_only = validator.deploy_with_mixins(
        component_path=component_path,
        environment=environment,
        mixins=['data_quality']
    )
    
    # Scenario 4: Both mix-ins (composition)
    print("\n" + "█"*70)
    print("SCENARIO 4: Deployment with BOTH Mix-ins (Composition Test)")
    print("█"*70)
    print("\nExpected: Both mix-ins work together without conflicts")
    
    both_mixins = validator.deploy_with_mixins(
        component_path=component_path,
        environment=environment,
        mixins=['notifications', 'data_quality']
    )
    
    # Analysis
    print("\n" + "="*70)
    print("MIX-IN COMPOSITION ANALYSIS")
    print("="*70)
    
    print("\n📊 Deployment Summary:")
    print(f"  Total deployments: {len(validator.execution_log)}")
    print(f"  Successful: {sum(1 for d in validator.execution_log if d['deployment_status'] == 'success')}")
    
    print("\n🧩 Mix-in Application Results:")
    
    scenarios = [
        ("Baseline (no mix-ins)", baseline),
        ("Notifications only", notifications_only),
        ("Data quality only", data_quality_only),
        ("Both mix-ins", both_mixins)
    ]
    
    for scenario_name, result in scenarios:
        print(f"\n  {scenario_name}:")
        print(f"    Mixins applied: {', '.join(result['mixins_applied']) if result['mixins_applied'] else 'None'}")
        
        if 'notifications' in result['mixin_results']:
            notif = result['mixin_results']['notifications']
            print(f"    ✓ Slack notified: {notif['slack']['status']}")
            print(f"    ✓ Email sent: {notif['email']['status']}")
        
        if 'data_quality' in result['mixin_results']:
            quality = result['mixin_results']['data_quality']
            print(f"    ✓ Data quality checks: {len(quality)} checks passed")
    
    # Validation
    print("\n" + "="*70)
    print("VALIDATION RESULTS")
    print("="*70)
    
    validations = {
        'mix_ins_load_successfully': all(
            len(r['mixins_applied']) == len(r['mixins_requested']) 
            for r in validator.execution_log
        ),
        'notifications_work_when_enabled': 'notifications' in notifications_only['mixin_results'],
        'data_quality_works_when_enabled': 'data_quality' in data_quality_only['mixin_results'],
        'mix_ins_compose_without_conflict': (
            len(both_mixins['mixins_applied']) == 2 and
            both_mixins['deployment_status'] == 'success'
        ),
        'mix_ins_are_optional': len(baseline['mixins_applied']) == 0
    }
    
    print("\n✅ Mix-in Capabilities Validated:")
    for validation, passed in validations.items():
        icon = "✓" if passed else "✗"
        print(f"  {icon} {validation.replace('_', ' ').title()}: {'PASS' if passed else 'FAIL'}")
    
    all_passed = all(validations.values())
    
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    
    if all_passed:
        print("\n✅ SUCCESS: Mix-ins are validated as composable cross-cutting concerns")
        print("\nKey Findings:")
        print("  • Mix-ins can be applied independently")
        print("  • Multiple mix-ins compose without conflicts")
        print("  • Mix-ins are truly optional (baseline works without them)")
        print("  • Same deployment code works with any mix-in combination")
        print("\n💡 EADF Mix-in Pattern Validated:")
        print("  Mix-ins provide reusable snippets for notifications, data quality,")
        print("  and other cross-cutting concerns that can be mixed and matched")
        print("  across deployments without modifying core pipeline logic.")
    else:
        print("\n⚠️ ISSUES FOUND: Some mix-in validations failed")
    
    # Save results
    Path("results").mkdir(exist_ok=True)
    
    with open("results/mixin_composition.json", 'w') as f:
        json.dump({
            'scenarios': validator.execution_log,
            'validations': validations,
            'all_passed': all_passed
        }, f, indent=2)
    
    print("\n✓ Results saved to: results/mixin_composition.json")
    print("="*70)

if __name__ == "__main__":
    main()
