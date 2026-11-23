"""
Experiment 2: Configuration Drift Detection
Validates late binding eliminates drift
"""

import yaml
import json
from pathlib import Path

def extract_param_paths(config, prefix=''):
    """Extract all parameter paths"""
    paths = set()
    for key, value in config.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            paths.update(extract_param_paths(value, path))
        else:
            paths.add(path)
    return paths

def test_baseline_drift():
    """Test baseline environment-specific configs (drift-prone)"""
    print("\n" + "=" * 70)
    print("BASELINE: Environment-Specific Configuration (Drift-Prone)")
    print("=" * 70)
    
    # Simulate baseline with separate files per environment
    baseline_configs = {
        'dev': {
            'pipeline_name': 'customer_orders',
            'factory_name': 'dev-adf-001',
            'resource_group': 'dev-rg',
            'schedule': '0 * * * *',
            'max_retries': 3
        },
        'prod': {
            'pipeline_name': 'customer_orders',
            'adf_name': 'prod-adf-001',  # DRIFT: Different key name
            'resource_group': 'prod-rg',
            'cron_schedule': '0 */1 * * *',  # DRIFT: Different key name
            'retries': 3  # DRIFT: Different key name
        }
    }
    
    # Detect drift
    dev_params = extract_param_paths(baseline_configs['dev'])
    prod_params = extract_param_paths(baseline_configs['prod'])
    
    missing = dev_params - prod_params
    extra = prod_params - dev_params
    
    drift_count = len(missing) + len(extra)
    
    print(f"  Dev parameters: {len(dev_params)}")
    print(f"  Prod parameters: {len(prod_params)}")
    print(f"  Missing in prod: {missing}")
    print(f"  Extra in prod: {extra}")
    print(f"  Total drift incidents: {drift_count}")
    
    return drift_count

def test_eadf_consistency():
    """Test EADF centralized configuration (drift-free)"""
    print("\n" + "=" * 70)
    print("EADF: Centralized Configuration with Late Binding")
    print("=" * 70)
    
    # Load EADF environments
    with open("ci/env/environments.yaml") as f:
        environments = yaml.safe_load(f)
    
    env_configs = environments['environments']
    
    # Check structural consistency
    reference_params = extract_param_paths(env_configs['dev'])
    
    drift_count = 0
    for env_name, env_config in env_configs.items():
        if env_name == 'dev':
            continue
        
        env_params = extract_param_paths(env_config)
        missing = reference_params - env_params
        
        if missing:
            print(f"  ⚠ {env_name}: Missing parameters: {missing}")
            drift_count += len(missing)
    
    if drift_count == 0:
        print(f"  ✓ All environments have consistent structure")
        print(f"  ✓ Zero configuration drift detected")
    
    print(f"  Drift incidents: {drift_count}")
    
    return drift_count

def main():
    print("=" * 70)
    print("EXPERIMENT 2: Configuration Drift Detection")
    print("=" * 70)
    
    baseline_drift = test_baseline_drift()
    eadf_drift = test_eadf_consistency()
    
    print("\n" + "=" * 70)
    print("DRIFT ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Baseline Drift Incidents: {baseline_drift}")
    print(f"EADF Catalog Issues: {eadf_drift}")
    print("Note: the baseline is two hand-written configs and the catalog check counts")
    print("missing keys in the illustrative prod_aws entry. The counts are not a")
    print("like-for-like reduction, so no percentage is reported.")
    
    # Save results
    Path("results").mkdir(exist_ok=True)
    with open("results/config_drift_results.json", 'w') as f:
        json.dump({
            'baseline_drift': baseline_drift,
            'eadf_issues': eadf_drift,
            'note': 'Counts of missing parameter keys; not a like-for-like reduction. No percentage reported.'
        }, f, indent=2)
    
    print("\n✓ Results saved to: results/config_drift_results.json")
    print("=" * 70)

if __name__ == "__main__":
    main()
