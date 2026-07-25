#!/usr/bin/env python3
"""
Variable-to-Asset Mapping Generator

This script scans all assets.md files and HTML files in the content-complete directory
to extract state variable usage ({{VARIABLE_NAME}} pattern) and generates a comprehensive
mapping of which variables are used by which assets.

Output: variable_to_asset_mapping.json
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

def extract_variables_from_file(file_path):
    """Extract all {{VARIABLE}} patterns from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all {{VARIABLE}} patterns
        pattern = r'\{\{([A-Z_]+)\}\}'
        variables = re.findall(pattern, content)

        return list(set(variables))  # Return unique variables
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def scan_chapter_directories(base_path):
    """Scan all L-* chapter directories for assets and variables."""

    variable_to_assets = defaultdict(lambda: {
        'chapters': set(),
        'assets': set(),
        'count': 0
    })

    asset_to_variables = {}
    chapter_summaries = {}

    # Patterns to match chapter directories
    chapter_dirs = []

    # Find all L-* directories
    for item in sorted(Path(base_path).glob('L-*')):
        if item.is_dir():
            chapter_num = item.name.split('-')[1]
            try:
                if int(chapter_num) >= 3:  # L-3 and above
                    chapter_dirs.append(item)
            except ValueError:
                continue

    print(f"Found {len(chapter_dirs)} chapter directories to scan")

    for chapter_dir in chapter_dirs:
        chapter_name = chapter_dir.name
        print(f"\nScanning {chapter_name}...")

        chapter_variables = set()
        chapter_assets = []

        # Scan assets.md file
        assets_md = chapter_dir / 'assets' / 'assets.md'
        if assets_md.exists():
            variables = extract_variables_from_file(assets_md)
            chapter_variables.update(variables)
            print(f"  Found {len(variables)} variables in assets.md")

        # Scan HTML files in downloads directory
        downloads_dir = chapter_dir / 'assets' / 'downloads'
        if downloads_dir.exists():
            html_files = list(downloads_dir.glob('*.html'))
            print(f"  Scanning {len(html_files)} HTML files...")

            for html_file in html_files:
                asset_name = html_file.stem
                variables = extract_variables_from_file(html_file)

                if variables:
                    chapter_assets.append({
                        'file': asset_name,
                        'variables': variables,
                        'count': len(variables)
                    })

                    # Map variables to this asset
                    asset_key = f"{chapter_name}/{asset_name}"
                    asset_to_variables[asset_key] = variables

                    # Map each variable to this asset
                    for var in variables:
                        variable_to_assets[var]['chapters'].add(chapter_name)
                        variable_to_assets[var]['assets'].add(asset_key)
                        variable_to_assets[var]['count'] += 1

                    chapter_variables.update(variables)

        # Store chapter summary
        chapter_summaries[chapter_name] = {
            'total_variables': len(chapter_variables),
            'variables': sorted(list(chapter_variables)),
            'assets': chapter_assets,
            'asset_count': len(chapter_assets)
        }

    return variable_to_assets, asset_to_variables, chapter_summaries

def generate_mapping_report(base_path, output_file='variable_to_asset_mapping.json'):
    """Generate comprehensive variable-to-asset mapping report."""

    print("=" * 60)
    print("Variable-to-Asset Mapping Generator")
    print("=" * 60)

    var_to_assets, asset_to_vars, chapter_summaries = scan_chapter_directories(base_path)

    # Convert sets to lists for JSON serialization
    var_to_assets_serializable = {}
    for var, data in var_to_assets.items():
        var_to_assets_serializable[var] = {
            'chapters': sorted(list(data['chapters'])),
            'assets': sorted(list(data['assets'])),
            'usage_count': data['count']
        }

    # Generate statistics
    total_variables = len(var_to_assets)
    total_assets = len(asset_to_vars)
    total_chapters = len(chapter_summaries)

    # Most used variables
    most_used = sorted(
        var_to_assets_serializable.items(),
        key=lambda x: x[1]['usage_count'],
        reverse=True
    )[:10]

    # Create comprehensive report
    report = {
        'generated_at': str(Path(base_path).absolute()),
        'statistics': {
            'total_variables': total_variables,
            'total_assets': total_assets,
            'total_chapters': total_chapters
        },
        'most_used_variables': {
            var: data for var, data in most_used
        },
        'variable_to_assets': var_to_assets_serializable,
        'asset_to_variables': asset_to_vars,
        'chapter_summaries': chapter_summaries
    }

    # Write to JSON file
    output_path = Path(base_path) / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Variables Found: {total_variables}")
    print(f"Total Assets Analyzed: {total_assets}")
    print(f"Total Chapters Scanned: {total_chapters}")
    print(f"\nTop 10 Most Used Variables:")
    for i, (var, data) in enumerate(most_used, 1):
        print(f"{i:2d}. {var:40s} - Used {data['usage_count']} times across {len(data['chapters'])} chapters")

    print(f"\nFull report saved to: {output_path}")
    print("=" * 60)

    return report

if __name__ == '__main__':
    # Set base path to content-complete directory
    script_dir = Path(__file__).parent
    content_complete_path = script_dir / 'content-complete'

    if not content_complete_path.exists():
        print(f"Error: {content_complete_path} does not exist")
        exit(1)

    generate_mapping_report(content_complete_path)
