#!/usr/bin/env python3
"""
Calculate average precision, recall, and F1 scores from validation metrics files.
Analyzes static_line_validation_metrics.json and validation_metrics.json
for activemq_59 and zookeeper_48 projects.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

name_keys = {
    'static_line_validation_metrics.json': 'Static Analysis',
    'validation_metrics.json': 'TraceLLM',
    'zookeeper_48': 'Zookeeper',
    'activemq_59': 'ActiveMQ',
}


def load_metrics(file_path: Path) -> Dict:
    """
    Load metrics from a JSON file.

    Args:
        file_path: Path to the metrics JSON file

    Returns:
        Dictionary containing metrics for each test
    """
    if not file_path.exists():
        print(f"Warning: File {file_path} does not exist")
        return {}

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_averages(metrics_data: Dict) -> Tuple[float, float, float]:
    """
    Calculate average precision, recall, and F1 from metrics data.

    Args:
        metrics_data: Dictionary containing metrics for each test

    Returns:
        Tuple of (avg_precision, avg_recall, avg_f1)
    """
    if not metrics_data:
        return 0.0, 0.0, 0.0

    precisions = []
    recalls = []
    f1s = []

    for test_id, metrics in metrics_data.items():
        if 'precision' in metrics:
            precisions.append(metrics['precision'])
        if 'recall' in metrics:
            recalls.append(metrics['recall'])
        if 'f1' in metrics:
            f1s.append(metrics['f1'])

    avg_precision = sum(precisions) / len(precisions) if precisions else 0.0
    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    avg_f1 = sum(f1s) / len(f1s) if f1s else 0.0

    return avg_precision, avg_recall, avg_f1


def main():
    # Define the directories and files to analyze
    base_dir = Path('output')
    projects = ['zookeeper_48', 'activemq_59']
    metric_files = ['static_line_validation_metrics.json', 'validation_metrics.json']

    print("=" * 80)
    print("Validation Metrics Analysis")
    print("=" * 80)

    all_results = {}

    # Process each project
    for project in projects:
        print(f"\n{'=' * 80}")
        print(f"Project: {project}")
        print(f"{'=' * 80}")

        project_results = {}

        # Process each metric file
        for metric_file in metric_files:
            file_path = base_dir / project / metric_file

            if not file_path.exists():
                print(f"\nFile not found: {file_path}")
                continue

            print(f"\n{metric_file}:")
            print("-" * 80)

            metrics_data = load_metrics(file_path)

            if not metrics_data:
                print("  No data found")
                continue

            avg_precision, avg_recall, avg_f1 = calculate_averages(metrics_data)

            project_results[metric_file] = {
                'num_tests': len(metrics_data),
                'avg_precision': avg_precision,
                'avg_recall': avg_recall,
                'avg_f1': avg_f1
            }

        all_results[project] = project_results

    # Print summary comparison
    print(f"\n\n{'=' * 80}")
    print("Summary Comparison")
    print(f"{'=' * 80}")

    for metric_file in metric_files:
        print(f"\n{name_keys[metric_file]}:")
        print("-" * 80)
        print(f"{'Project':<20} {'Tests':<10} {'Average Precision':<12} {'Average Recall':<12} {'Average F1 Score':<12}")
        print("-" * 80)

        for project in projects:
            if project in all_results and metric_file in all_results[project]:
                results = all_results[project][metric_file]
                print(f"{name_keys[project]:<20} {results['num_tests']:<10} "
                      f"{results['avg_precision']:<12.4f} "
                      f"{results['avg_recall']:<12.4f} "
                      f"{results['avg_f1']:<12.4f}")


if __name__ == "__main__":
    main()
