#!/usr/bin/env python3
"""
EADF Validation Framework - Interactive Experiment Runner
Runs selected experiments and generates visual dashboard

FEATURES:
- Interactive menu to select experiments
- Progress tracking with visual feedback
- Automatic dashboard generation and opening
- Consolidated results summary
"""

import sys
import subprocess
from pathlib import Path
import time
import json
from datetime import datetime
import webbrowser
import platform

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class ExperimentRunner:
    """Interactive experiment runner with menu and progress tracking"""
    
    def __init__(self):
        self.experiments = [
            {
                'id': 1,
                'name': 'Stage Coverage',
                'file': 'experiments/1_stage_coverage.py',
                'description': 'Checks which of the 7 resolver stages execute',
                'duration': '~5s',
                'category': 'Core Pipeline'
            },
            {
                'id': 2,
                'name': 'Configuration Drift',
                'file': 'experiments/2_config_drift.py',
                'description': 'Counts structural parameter drift: per-env baseline vs. environment catalog',
                'duration': '~3s',
                'category': 'Core Pipeline'
            },
            {
                'id': 3,
                'name': 'Deployment Velocity',
                'file': 'experiments/3_velocity.py',
                'description': 'Times the local resolver (10 runs) against a fixed 0.5 s simulated baseline',
                'duration': '~10s',
                'category': 'Core Pipeline'
            },
            {
                'id': 4,
                'name': 'Late Binding',
                'file': 'experiments/4_late_binding.py',
                'description': 'Validates environment parameters bound at runtime',
                'duration': '~3s',
                'category': 'Core Pipeline'
            },
            {
                'id': 5,
                'name': 'Provenance Capture',
                'file': 'experiments/5_provenance.py',
                'description': 'Checks the provenance ledger for 5 top-level sections',
                'duration': '~3s',
                'category': 'Core Pipeline'
            },
            {
                'id': 6,
                'name': 'Multi-Environment Deployment',
                'file': 'experiments/6_deployment_success.py',
                'description': 'Tests deployment across dev→sit→uat→prod',
                'duration': '~8s',
                'category': 'Multi-Environment'
            },
            {
                'id': 7,
                'name': 'Failure & Rollback',
                'file': 'experiments/7_deployment_failures.py',
                'description': 'Injects simulated smoke-test, gate and deployment failures',
                'duration': '~8s',
                'category': 'Multi-Environment'
            },
            {
                'id': 8,
                'name': 'Environment Inspection',
                'file': 'experiments/8_environment_state.py',
                'description': 'Inspects files written to the simulated environment folders',
                'duration': '~5s',
                'category': 'Multi-Environment'
            },
            {
                'id': 9,
                'name': 'Mix-in Composition',
                'file': 'experiments/9_mixin_composition.py',
                'description': 'Applies simulated mix-ins (notifications, data quality) in combination',
                'duration': '~10s',
                'category': 'Advanced Features'
            },
            {
                'id': 10,
                'name': 'Component Type Branching',
                'file': 'experiments/10_component_types.py',
                'description': 'Checks the dispatch labels selected per component type',
                'duration': '~10s',
                'category': 'Advanced Features'
            },
            {
                'id': 11,
                'name': 'Complexity Metrics',
                'file': 'experiments/11_complexity_metrics.py',
                'description': 'Measures EADF LOC/complexity; other approaches are hard-coded estimates',
                'duration': '~5s',
                'category': 'Advanced Features'
            }
        ]
        
        self.results = []
        self.start_time = None
    
    def print_header(self):
        """Print colorful header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}🚀 EADF Validation Framework - Interactive Runner{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")
    
    def print_menu(self):
        """Display interactive menu"""
        
        # Group by category
        categories = {}
        for exp in self.experiments:
            cat = exp['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(exp)
        
        print(f"{Colors.BOLD}Available Experiments:{Colors.END}\n")
        
        for category, exps in categories.items():
            print(f"{Colors.YELLOW}▶ {category}{Colors.END}")
            for exp in exps:
                status = "✓" if Path(exp['file']).exists() else "✗"
                color = Colors.GREEN if status == "✓" else Colors.RED
                
                print(f"  {color}[{exp['id']:2d}]{Colors.END} {exp['name']:<30} {Colors.CYAN}{exp['duration']}{Colors.END}")
                print(f"      {exp['description']}")
            print()
        
        print(f"{Colors.BOLD}Special Options:{Colors.END}")
        print(f"  {Colors.GREEN}[ 0]{Colors.END} Run ALL experiments (recommended)")
        print(f"  {Colors.GREEN}[99]{Colors.END} Generate dashboard only")
        print()
    
    def get_user_selection(self):
        """Get user's experiment selection"""
        
        while True:
            try:
                print(f"{Colors.BOLD}Select experiments to run:{Colors.END}")
                print(f"  • Enter experiment numbers separated by commas (e.g., 1,2,3)")
                print(f"  • Enter 0 for ALL experiments (default)")
                print(f"  • Press Enter for default (ALL)")
                print()
                
                user_input = input(f"{Colors.CYAN}Your selection [0]: {Colors.END}").strip()
                
                # Default to all
                if not user_input or user_input == '0':
                    return [exp['id'] for exp in self.experiments]
                
                # Dashboard only
                if user_input == '99':
                    return [99]
                
                # Parse selection
                selected = [int(x.strip()) for x in user_input.split(',')]
                
                # Validate
                valid_ids = [exp['id'] for exp in self.experiments]
                invalid = [x for x in selected if x not in valid_ids]
                
                if invalid:
                    print(f"{Colors.RED}✗ Invalid experiment IDs: {invalid}{Colors.END}")
                    print(f"{Colors.YELLOW}  Valid IDs: {valid_ids}{Colors.END}\n")
                    continue
                
                return selected
                
            except ValueError:
                print(f"{Colors.RED}✗ Invalid input. Please enter numbers separated by commas.{Colors.END}\n")
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Operation cancelled by user{Colors.END}")
                sys.exit(0)
    
    def confirm_selection(self, selected_ids):
        """Confirm user's selection"""
        
        if selected_ids == [99]:
            print(f"\n{Colors.BOLD}Selected:{Colors.END} Dashboard generation only")
            return True
        
        selected_exps = [exp for exp in self.experiments if exp['id'] in selected_ids]
        total_time = sum(int(exp['duration'].replace('~', '').replace('s', '')) for exp in selected_exps)
        
        print(f"\n{Colors.BOLD}Selected Experiments:{Colors.END}")
        for exp in selected_exps:
            print(f"  {Colors.GREEN}✓{Colors.END} [{exp['id']:2d}] {exp['name']}")
        
        print(f"\n{Colors.BOLD}Summary:{Colors.END}")
        print(f"  Experiments: {len(selected_exps)}")
        print(f"  Estimated time: ~{total_time}s")
        print()
        
        confirm = input(f"{Colors.CYAN}Proceed? [Y/n]: {Colors.END}").strip().lower()
        
        if confirm and confirm not in ['y', 'yes']:
            print(f"{Colors.YELLOW}Operation cancelled{Colors.END}")
            return False
        
        return True
    
    def run_experiment(self, experiment):
        """Run a single experiment"""
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'─'*80}{Colors.END}")
        print(f"{Colors.BOLD}Running: [{experiment['id']}] {experiment['name']}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'─'*80}{Colors.END}\n")
        
        start = time.time()
        
        try:
            # Run experiment
            result = subprocess.run(
                [sys.executable, experiment['file']],
                capture_output=False,  # Show output in real-time
                text=True
            )
            
            duration = time.time() - start
            
            success = result.returncode == 0
            
            self.results.append({
                'id': experiment['id'],
                'name': experiment['name'],
                'success': success,
                'duration': duration,
                'category': experiment['category']
            })
            
            # Print result
            if success:
                print(f"\n{Colors.GREEN}✓ {experiment['name']} completed successfully ({duration:.1f}s){Colors.END}")
            else:
                print(f"\n{Colors.RED}✗ {experiment['name']} failed (exit code: {result.returncode}){Colors.END}")
            
            return success
            
        except Exception as e:
            duration = time.time() - start
            print(f"\n{Colors.RED}✗ {experiment['name']} failed with exception: {e}{Colors.END}")
            
            self.results.append({
                'id': experiment['id'],
                'name': experiment['name'],
                'success': False,
                'duration': duration,
                'error': str(e),
                'category': experiment['category']
            })
            
            return False
    
    def generate_dashboard(self):
        """Generate HTML dashboard"""
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'─'*80}{Colors.END}")
        print(f"{Colors.BOLD}Generating Interactive Dashboard{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'─'*80}{Colors.END}\n")
        
        try:
            # Import and run dashboard generator
            sys.path.insert(0, '.')
            from eadf_core.dashboard_generator import DashboardGenerator
            
            generator = DashboardGenerator()
            dashboard_path = generator.save_dashboard()
            
            print(f"{Colors.GREEN}✓ Dashboard generated: {dashboard_path}{Colors.END}")
            
            return dashboard_path
            
        except Exception as e:
            print(f"{Colors.RED}✗ Dashboard generation failed: {e}{Colors.END}")
            return None
    
    def open_dashboard(self, dashboard_path):
        """Open dashboard in browser"""
        
        if not dashboard_path or not Path(dashboard_path).exists():
            print(f"{Colors.YELLOW}⚠ Dashboard file not found{Colors.END}")
            return
        
        print(f"\n{Colors.CYAN}Opening dashboard in browser...{Colors.END}")
        
        try:
            # Get absolute path
            abs_path = Path(dashboard_path).resolve()
            
            # Open in default browser
            webbrowser.open(f'file://{abs_path}')
            
            print(f"{Colors.GREEN}✓ Dashboard opened in browser{Colors.END}")
            
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ Could not auto-open browser: {e}{Colors.END}")
            print(f"{Colors.CYAN}Please open manually: {Path(dashboard_path).resolve()}{Colors.END}")
    
    def print_summary(self):
        """Print execution summary"""
        
        total_duration = time.time() - self.start_time
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}Execution Summary{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")
        
        # Group by category
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        # Print by category
        for category, results in categories.items():
            print(f"{Colors.BOLD}{category}:{Colors.END}")
            for result in results:
                icon = f"{Colors.GREEN}✓{Colors.END}" if result['success'] else f"{Colors.RED}✗{Colors.END}"
                duration = f"{result['duration']:.1f}s"
                print(f"  {icon} [{result['id']:2d}] {result['name']:<35} {duration}")
            print()
        
        # Overall statistics
        total_exps = len(self.results)
        successful = sum(1 for r in self.results if r['success'])
        failed = total_exps - successful
        
        print(f"{Colors.BOLD}Statistics:{Colors.END}")
        print(f"  Total experiments: {total_exps}")
        print(f"  {Colors.GREEN}Successful: {successful}{Colors.END}")
        if failed > 0:
            print(f"  {Colors.RED}Failed: {failed}{Colors.END}")
        print(f"  Total duration: {total_duration:.1f}s")
        print()
        
        # Final status
        if failed == 0:
            print(f"{Colors.BOLD}{Colors.GREEN}{'✓'*3} ALL EXPERIMENTS PASSED {'✓'*3}{Colors.END}")
            print(f"{Colors.GREEN}EADF validation framework is working perfectly!{Colors.END}")
        else:
            print(f"{Colors.BOLD}{Colors.RED}⚠ {failed} EXPERIMENT(S) FAILED{Colors.END}")
            print(f"{Colors.YELLOW}Please review the errors above{Colors.END}")
        
        print(f"\n{Colors.CYAN}{'='*80}{Colors.END}\n")
    
    def save_execution_report(self):
        """Save execution report to JSON"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_duration': time.time() - self.start_time,
            'experiments_run': len(self.results),
            'successful': sum(1 for r in self.results if r['success']),
            'failed': sum(1 for r in self.results if not r['success']),
            'results': self.results
        }
        
        # Ensure results directory exists
        Path("results").mkdir(exist_ok=True)
        
        report_path = "results/execution_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"{Colors.CYAN}Execution report saved: {report_path}{Colors.END}")
    
    def run(self):
        """Main execution flow"""
        
        self.print_header()
        
        # Show menu
        self.print_menu()
        
        # Get user selection
        selected_ids = self.get_user_selection()
        
        # Confirm
        if not self.confirm_selection(selected_ids):
            return
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}Starting validation framework...{Colors.END}\n")
        time.sleep(1)
        
        self.start_time = time.time()
        
        # Dashboard only mode
        if selected_ids == [99]:
            dashboard_path = self.generate_dashboard()
            if dashboard_path:
                self.open_dashboard(dashboard_path)
            return
        
        # Run selected experiments
        selected_exps = [exp for exp in self.experiments if exp['id'] in selected_ids]
        
        for i, exp in enumerate(selected_exps, 1):
            print(f"\n{Colors.BOLD}Progress: {i}/{len(selected_exps)}{Colors.END}")
            self.run_experiment(exp)
            
            # Small pause between experiments
            if i < len(selected_exps):
                time.sleep(0.5)
        
        # Generate dashboard
        print(f"\n{Colors.BOLD}Finalizing results...{Colors.END}")
        dashboard_path = self.generate_dashboard()
        
        # Print summary
        self.print_summary()
        
        # Save report
        self.save_execution_report()
        
        # Open dashboard
        if dashboard_path:
            print(f"\n{Colors.BOLD}Opening interactive dashboard...{Colors.END}")
            time.sleep(1)
            self.open_dashboard(dashboard_path)
            
            print(f"\n{Colors.BOLD}{Colors.GREEN}View your results in the browser!{Colors.END}")
            print(f"{Colors.CYAN}Dashboard location: {Path(dashboard_path).resolve()}{Colors.END}")

def main():
    """Entry point"""
    try:
        runner = ExperimentRunner()
        runner.run()
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Fatal error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
