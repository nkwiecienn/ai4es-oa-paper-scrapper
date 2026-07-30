#!/usr/bin/env python3
"""
Convenience script to analyze ROB data by experiments.

Usage:
    python analyze_rob_experiments.py processed_export_XXXXX.json
"""

import sys
import os
import json

# Add services to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'papers', 'services')))

from rob_comparison_by_experiments import generate_experiment_report, print_experiment_report


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_rob_experiments.py <export_json_file>")
        print("\nExample:")
        print("  python analyze_rob_experiments.py ../paper_pipeline_data/exports/processed_export_1234567.json")
        sys.exit(1)
    
    export_file = sys.argv[1]
    
    if not os.path.exists(export_file):
        print(f"Error: File not found: {export_file}")
        sys.exit(1)
    
    print(f"Loading export from {export_file}...")
    
    # Load export
    with open(export_file, "r") as f:
        papers_data = json.load(f)
    
    print(f"Loaded {len(papers_data)} papers")
    
    # Generate report
    print("Analyzing ROB assessments by experiments...")
    report = generate_experiment_report(papers_data)
    
    # Print report
    print_experiment_report(report, max_experiments=30)
    
    # Save report JSON
    output_file = export_file.replace(".json", "_experiment_report.json")
    with open(output_file, "w") as f:
        # Convert sets to lists for JSON serialization
        report_serializable = json.loads(json.dumps(report, default=str))
        json.dump(report_serializable, f, indent=2)
    
    print(f"\n✓ Full report saved to {output_file}")
    print(f"  Total unique experiments: {report['summary']['total_experiments_assessed']}")
    print(f"  Experiments with conflicts: {report['summary']['experiments_with_conflicts']}")
    print(f"  Experiments with high agreement: {report['summary']['experiments_with_high_agreement']}")


if __name__ == "__main__":
    main()
