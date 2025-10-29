"""
Experiment 1: 7-Stage Pipeline Coverage
Validates that all EADF stages are implemented and working
"""

import sys
sys.path.insert(0, '.')

from eadf_core.resolver import EADFResolver
import json
from pathlib import Path

def test_full_pipeline_execution():
    """Execute full 7-stage pipeline and verify coverage"""
    print("=" * 70)
    print("EXPERIMENT 1: 7-Stage Pipeline Coverage")
    print("=" * 70)
    
    # Execute deployment through all 7 stages
    resolver = EADFResolver(
        component_path="components/customer_orders_pipeline/component.yaml",
        environment_name="dev"
    )
    
    outcome = resolver.execute()
    
    # Verify all stages executed
    print("\n" + "=" * 70)
    print("STAGE COVERAGE ANALYSIS")
    print("=" * 70)
    
    expected_stages = [
        'binding', 'build', 'validation', 'deployment',
        'smoke_test', 'gate_evaluation', 'provenance'
    ]
    
    stages_executed = list(outcome['provenance']['stages'].keys())
    
    coverage_results = []
    for stage in expected_stages:
        status = 'executed' if stage in stages_executed else 'missing'
        stage_status = outcome['provenance']['stages'].get(stage, {}).get('status', 'unknown')
        
        coverage_results.append({
            'name': stage,
            'status': stage_status,
            'executed': stage in stages_executed
        })
        
        icon = "✓" if stage in stages_executed else "✗"
        print(f"  {icon} Stage: {stage:20s} Status: {stage_status}")
    
    # Calculate coverage
    coverage_percent = (len(stages_executed) / len(expected_stages)) * 100
    
    print(f"\n  Stage Coverage: {coverage_percent:.0f}% ({len(stages_executed)}/{len(expected_stages)})")
    
    # Save results
    Path("results").mkdir(exist_ok=True)
    with open("results/stage_coverage.json", 'w') as f:
        json.dump({
            'stages': coverage_results,
            'coverage_percent': coverage_percent,
            'total_stages': len(expected_stages),
            'executed_stages': len(stages_executed)
        }, f, indent=2)
    
    print("\n✓ Results saved to: results/stage_coverage.json")
    print("=" * 70)

if __name__ == "__main__":
    test_full_pipeline_execution()
