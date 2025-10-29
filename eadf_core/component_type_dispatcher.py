"""
Component Type Dispatcher - Routes to type-specific build/deploy logic
Implements the branching rules defined in pipeline.yaml
"""

from typing import Dict

class ComponentTypeDispatcher:
    """
    Dispatches deployment stages to type-specific implementations
    Based on branching rules in pipeline.yaml
    """
    
    def __init__(self):
        # Branching rules from pipeline.yaml
        self.branching_rules = {
            'adf_pipeline': {
                'build': 'build_adf_json',
                'validation': 'validate_adf_schema',
                'deployment': 'deploy_to_adf',
                'smoke_test': 'test_pipeline_run'
            },
            'dbt_project': {
                'build': 'build_dbt_artifacts',
                'validation': 'validate_dbt_models',
                'deployment': 'deploy_dbt_to_warehouse',
                'smoke_test': 'test_dbt_models'
            },
            'databricks_notebook': {
                'build': 'export_notebook',
                'validation': 'validate_notebook_syntax',
                'deployment': 'import_to_databricks',
                'smoke_test': 'execute_notebook_test'
            }
        }
    
    def get_expected_branches(self, component_type: str) -> Dict[str, str]:
        """Get expected branching for a component type"""
        if component_type not in self.branching_rules:
            raise ValueError(f"Unknown component type: {component_type}")
        
        return self.branching_rules[component_type]
    
    def dispatch_build(self, component_type: str) -> str:
        """Dispatch to appropriate build method"""
        rules = self.get_expected_branches(component_type)
        method = rules['build']
        
        # In real implementation, would call the actual method
        # For validation, we just return the method name
        return method
    
    def dispatch_validation(self, component_type: str) -> str:
        """Dispatch to appropriate validation method"""
        rules = self.get_expected_branches(component_type)
        method = rules['validation']
        return method
    
    def dispatch_deployment(self, component_type: str, cloud: str) -> str:
        """Dispatch to appropriate deployment method"""
        rules = self.get_expected_branches(component_type)
        method = rules['deployment']
        
        # Could further dispatch based on cloud if needed
        # e.g., deploy_to_adf_azure vs deploy_to_adf_aws
        
        return method
    
    def dispatch_smoke_test(self, component_type: str) -> str:
        """Dispatch to appropriate smoke test method"""
        rules = self.get_expected_branches(component_type)
        method = rules['smoke_test']
        return method
