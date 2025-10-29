"""
Base Experiment Class - Eliminates redundancy across experiments
Provides common functionality for all EADF validation experiments
"""

import sys
sys.path.insert(0, '.')

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

class BaseExperiment:
    """
    Base class for all EADF validation experiments
    Provides common functionality to eliminate code duplication
    """
    
    def __init__(self, experiment_id: int, experiment_name: str):
        """
        Initialize experiment
        
        Args:
            experiment_id: Unique experiment number (1-13)
            experiment_name: Human-readable name
        """
        self.experiment_id = experiment_id
        self.experiment_name = experiment_name
        self.start_time = None
        self.end_time = None
        self.results = {}
        self.validations = {}
        
        # Ensure results directory exists
        Path("results").mkdir(exist_ok=True)
    
    def print_header(self, purpose: str = None, design_claim: str = None, approach: str = None):
        """
        Print standardized experiment header
        
        Args:
            purpose: What this experiment validates
            design_claim: Design pattern claim being tested
            approach: How the experiment works
        """
        logger.info("=" * 80)
        logger.info(f"EXPERIMENT {self.experiment_id}: {self.experiment_name}")
        logger.info("=" * 80)
        
        if purpose:
            logger.info(f"\nPURPOSE:")
            logger.info(f"  {purpose}")
        
        if design_claim:
            logger.info(f"\nDESIGN PATTERN CLAIM:")
            logger.info(f"  {design_claim}")
        
        if approach:
            logger.info(f"\nVALIDATION APPROACH:")
            logger.info(f"  {approach}")
        
        logger.info("\n" + "=" * 80)
    
    def print_section(self, title: str, symbol: str = "█"):
        """Print section separator"""
        logger.info(f"\n{symbol * 80}")
        logger.info(title)
        logger.info(f"{symbol * 80}")
    
    def print_subsection(self, title: str):
        """Print subsection separator"""
        logger.info(f"\n{'─' * 80}")
        logger.info(title)
        logger.info(f"{'─' * 80}")
    
    def print_validation_results(self, validations: Dict[str, bool]):
        """
        Print validation results in standardized format
        
        Args:
            validations: Dict mapping validation name to pass/fail
        """
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION RESULTS")
        logger.info("=" * 80)
        
        logger.info(f"\n✅ Validations:")
        for validation, passed in validations.items():
            icon = "✓" if passed else "✗"
            status = "PASS" if passed else "FAIL"
            logger.info(f"  {icon} {validation.replace('_', ' ').title()}: {status}")
        
        self.validations = validations
    
    def print_conclusion(self, success: bool, findings: List[str] = None, 
                        pattern_validated: str = None):
        """
        Print standardized conclusion
        
        Args:
            success: Overall success status
            findings: List of key findings
            pattern_validated: Design pattern aspect validated
        """
        logger.info("\n" + "=" * 80)
        logger.info("CONCLUSION")
        logger.info("=" * 80)
        
        if success:
            logger.info(f"\n✅ SUCCESS: {self.experiment_name} validated")
            
            if findings:
                logger.info("\nKey Findings:")
                for finding in findings:
                    logger.info(f"  • {finding}")
            
            if pattern_validated:
                logger.info(f"\n💡 EADF Pattern Validated:")
                logger.info(f"  {pattern_validated}")
        else:
            logger.info(f"\n⚠️ ISSUES FOUND: Some validations failed")
    
    def save_results(self, filename: str = None):
        """
        Save experiment results to JSON
        
        Args:
            filename: Output filename (default: experiment_{id}_results.json)
        """
        if filename is None:
            filename = f"experiment_{self.experiment_id}_results.json"
        
        output = {
            'experiment_id': self.experiment_id,
            'experiment_name': self.experiment_name,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.end_time else None,
            'validations': self.validations,
            'all_passed': all(self.validations.values()) if self.validations else False,
            'results': self.results
        }
        
        output_path = Path("results") / filename
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"\n✓ Results saved to: {output_path}")
    
    def run(self):
        """
        Main experiment execution (override in subclasses)
        This method should be implemented by each specific experiment
        """
        raise NotImplementedError("Subclasses must implement run() method")
    
    def execute(self):
        """
        Execute experiment with timing and error handling
        This is the main entry point called from main()
        """
        self.start_time = datetime.now()
        
        try:
            # Run the actual experiment logic
            self.run()
            
            self.end_time = datetime.now()
            logger.info("=" * 80)
            
        except Exception as e:
            self.end_time = datetime.now()
            logger.error(f"\n✗ Experiment failed with error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


class QuickValidation:
    """Helper class for quick validation checks"""
    
    @staticmethod
    def check(condition: bool, success_msg: str, fail_msg: str = None) -> bool:
        """
        Quick validation check with logging
        
        Args:
            condition: Condition to check
            success_msg: Message to print if True
            fail_msg: Message to print if False
        
        Returns:
            The condition value
        """
        if condition:
            logger.info(f"  ✓ {success_msg}")
        else:
            msg = fail_msg if fail_msg else f"Failed: {success_msg}"
            logger.info(f"  ✗ {msg}")
        
        return condition
    
    @staticmethod
    def log_metric(name: str, value: Any, unit: str = ""):
        """Log a metric in a standardized format"""
        logger.info(f"  {name}: {value}{unit}")


class ResultsCollector:
    """Helper class for collecting and summarizing results"""
    
    def __init__(self):
        self.items = []
    
    def add(self, name: str, value: Any, status: str = None):
        """Add a result item"""
        self.items.append({
            'name': name,
            'value': value,
            'status': status
        })
    
    def print_summary(self, title: str = "Summary"):
        """Print collected results"""
        logger.info(f"\n📊 {title}:")
        for item in self.items:
            status_icon = ""
            if item['status'] == 'success':
                status_icon = "✓ "
            elif item['status'] == 'failed':
                status_icon = "✗ "
            
            logger.info(f"  {status_icon}{item['name']}: {item['value']}")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {item['name']: item['value'] for item in self.items}


def create_experiment_template(experiment_id: int, name: str, 
                               purpose: str, claim: str, approach: str):
    """
    Factory function to create a new experiment with standard structure
    
    Args:
        experiment_id: Experiment number
        name: Experiment name
        purpose: What it validates
        claim: Design pattern claim
        approach: Validation approach
    
    Returns:
        BaseExperiment subclass
    """
    
    class TemplatedExperiment(BaseExperiment):
        def __init__(self):
            super().__init__(experiment_id, name)
        
        def run(self):
            self.print_header(purpose=purpose, design_claim=claim, approach=approach)
            
            # Experiment-specific logic goes here
            # ...
            
            self.print_validation_results({})
            self.print_conclusion(success=True)
            self.save_results()
    
    return TemplatedExperiment


# Example usage in experiment files:
"""
from eadf_core.base_experiment import BaseExperiment, QuickValidation

class MyExperiment(BaseExperiment):
    def __init__(self):
        super().__init__(
            experiment_id=1,
            experiment_name="My Validation"
        )
    
    def run(self):
        # Print header
        self.print_header(
            purpose="Validate something important",
            design_claim="EADF does X",
            approach="Test X by doing Y"
        )
        
        # Run tests
        self.print_section("RUNNING TESTS")
        
        result = do_something()
        QuickValidation.check(result, "Something works correctly")
        
        # Print validation
        self.print_validation_results({
            'test_passes': True,
            'no_errors': True
        })
        
        # Print conclusion
        self.print_conclusion(
            success=True,
            findings=["Finding 1", "Finding 2"],
            pattern_validated="EADF validates X correctly"
        )
        
        # Save results
        self.save_results()

def main():
    experiment = MyExperiment()
    experiment.execute()

if __name__ == "__main__":
    main()
"""
