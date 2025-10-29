"""
Environment Simulator - Manages multi-environment deployments
Simulates realistic file operations and state management
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnvironmentSimulator:
    """
    Simulates physical environment with filesystem operations
    """
    
    def __init__(self, base_path: str = "environments"):
        """Initialize environment simulator"""
        self.base_path = Path(base_path)
        self.environments = ['dev', 'sit', 'uat', 'prod']
        
        # Initialize environment directories
        for env in self.environments:
            env_path = self.base_path / env
            (env_path / "pipelines").mkdir(parents=True, exist_ok=True)
            (env_path / "logs").mkdir(parents=True, exist_ok=True)
            (env_path / "backups").mkdir(parents=True, exist_ok=True)
            
            # Initialize state if not exists
            state_file = env_path / "state.json"
            if not state_file.exists():
                self._save_state(env, {
                    'environment': env,
                    'deployed_components': {},
                    'deployment_count': 0,
                    'last_deployment': None
                })
    
    def get_state(self, environment: str) -> Dict[str, Any]:
        """Get current environment state"""
        state_file = self.base_path / environment / "state.json"
        with open(state_file) as f:
            return json.load(f)
    
    def _save_state(self, environment: str, state: Dict[str, Any]):
        """Save environment state"""
        state_file = self.base_path / environment / "state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def deploy_artifact(self, 
                       component_name: str,
                       artifact_path: Path,
                       environment: str,
                       version: str) -> Dict[str, Any]:
        """
        Deploy artifact to environment
        Simulates actual file copy operation
        """
        logger.info(f"  📦 Deploying {component_name} v{version} to {environment}")
        
        # Destination path
        env_path = self.base_path / environment
        dest_path = env_path / "pipelines" / f"{component_name}_v{version}.json"
        
        # Check if artifact exists
        if not artifact_path.exists():
            raise FileNotFoundError(f"Artifact not found: {artifact_path}")
        
        # Backup existing artifact if present
        if dest_path.exists():
            backup_path = env_path / "backups" / f"{component_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy2(dest_path, backup_path)
            logger.info(f"  💾 Backed up existing artifact to: {backup_path.name}")
        
        # Copy artifact to environment
        shutil.copy2(artifact_path, dest_path)
        logger.info(f"  ✓ Artifact copied to: {dest_path}")
        
        # Update environment state
        state = self.get_state(environment)
        state['deployed_components'][component_name] = {
            'version': version,
            'deployed_at': datetime.now().isoformat(),
            'artifact_path': str(dest_path),
            'status': 'deployed'
        }
        state['deployment_count'] += 1
        state['last_deployment'] = datetime.now().isoformat()
        self._save_state(environment, state)
        
        # Log deployment
        self._log_deployment(environment, component_name, version, 'deployed')
        
        return {
            'status': 'success',
            'environment': environment,
            'component': component_name,
            'version': version,
            'artifact_location': str(dest_path)
        }
    
    def rollback_artifact(self, 
                         component_name: str,
                         environment: str) -> Dict[str, Any]:
        """
        Rollback artifact to previous version
        Simulates restoration from backup
        """
        logger.info(f"  ↩️  Rolling back {component_name} in {environment}")
        
        env_path = self.base_path / environment
        backups_path = env_path / "backups"
        
        # Find most recent backup
        backups = sorted(backups_path.glob(f"{component_name}_backup_*.json"), reverse=True)
        
        if not backups:
            raise FileNotFoundError(f"No backup found for {component_name}")
        
        latest_backup = backups[0]
        
        # Get current state
        state = self.get_state(environment)
        current_version = state['deployed_components'].get(component_name, {}).get('version', 'unknown')
        
        # Restore from backup
        dest_path = env_path / "pipelines" / f"{component_name}_v{current_version}.json"
        
        # Delete failed deployment
        if dest_path.exists():
            dest_path.unlink()
        
        # Restore backup
        shutil.copy2(latest_backup, dest_path)
        logger.info(f"  ✓ Restored from backup: {latest_backup.name}")
        
        # Update state
        state['deployed_components'][component_name]['status'] = 'rolled_back'
        state['deployed_components'][component_name]['rolled_back_at'] = datetime.now().isoformat()
        self._save_state(environment, state)
        
        # Log rollback
        self._log_deployment(environment, component_name, current_version, 'rolled_back')
        
        return {
            'status': 'rolled_back',
            'environment': environment,
            'component': component_name,
            'restored_from': str(latest_backup)
        }
    
    def promote_artifact(self,
                        component_name: str,
                        from_environment: str,
                        to_environment: str) -> Dict[str, Any]:
        """
        Promote artifact from one environment to another
        Simulates cross-environment file copy
        """
        logger.info(f"  🚀 Promoting {component_name}: {from_environment} → {to_environment}")
        
        # Get source artifact
        source_state = self.get_state(from_environment)
        
        if component_name not in source_state['deployed_components']:
            raise ValueError(f"{component_name} not found in {from_environment}")
        
        component_info = source_state['deployed_components'][component_name]
        source_artifact = Path(component_info['artifact_path'])
        
        if not source_artifact.exists():
            raise FileNotFoundError(f"Source artifact not found: {source_artifact}")
        
        # Deploy to target environment
        version = component_info['version']
        result = self.deploy_artifact(
            component_name=component_name,
            artifact_path=source_artifact,
            environment=to_environment,
            version=version
        )
        
        logger.info(f"  ✓ Promotion complete: {from_environment} → {to_environment}")
        
        return result
    
    def verify_deployment(self, 
                         component_name: str,
                         environment: str) -> bool:
        """
        Verify artifact is correctly deployed
        Checks file exists and state is consistent
        """
        state = self.get_state(environment)
        
        if component_name not in state['deployed_components']:
            return False
        
        component_info = state['deployed_components'][component_name]
        artifact_path = Path(component_info['artifact_path'])
        
        # Check file exists
        if not artifact_path.exists():
            logger.error(f"  ✗ Artifact file not found: {artifact_path}")
            return False
        
        # Check state is deployed
        if component_info['status'] != 'deployed':
            logger.error(f"  ✗ Component status: {component_info['status']}")
            return False
        
        logger.info(f"  ✓ Deployment verified in {environment}")
        return True
    
    def _log_deployment(self, environment: str, component: str, version: str, action: str):
        """Log deployment action to environment log"""
        log_file = self.base_path / environment / "logs" / "deployments.log"
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'version': version,
            'action': action,
            'environment': environment
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_deployment_history(self, environment: str) -> list:
        """Get deployment history for environment"""
        log_file = self.base_path / environment / "logs" / "deployments.log"
        
        if not log_file.exists():
            return []
        
        history = []
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    history.append(json.loads(line))
        
        return history
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """Get summary of all environments"""
        summary = {}
        
        for env in self.environments:
            state = self.get_state(env)
            history = self.get_deployment_history(env)
            
            summary[env] = {
                'deployed_components': len(state['deployed_components']),
                'total_deployments': state['deployment_count'],
                'last_deployment': state['last_deployment'],
                'recent_history': history[-5:] if history else []
            }
        
        return summary
    
    def cleanup_environment(self, environment: str):
        """Clean up environment (for testing)"""
        env_path = self.base_path / environment
        
        # Remove all pipelines
        pipelines_path = env_path / "pipelines"
        if pipelines_path.exists():
            shutil.rmtree(pipelines_path)
            pipelines_path.mkdir()
        
        # Reset state
        self._save_state(environment, {
            'environment': environment,
            'deployed_components': {},
            'deployment_count': 0,
            'last_deployment': None
        })
        
        logger.info(f"  🧹 Cleaned up {environment} environment")
