#!/usr/bin/env python3
"""
PDF Generator for PFL Academy Assets

This script converts all HTML assets to print-ready PDFs, maintaining the styling
and interactive elements where possible. It uses Playwright for high-fidelity
HTML-to-PDF conversion.

Features:
- Scans all L-* chapter directories for HTML assets
- Generates PDFs with proper print styling
- Supports state variable replacement (optional)
- Creates both generic and state-specific versions
- Maintains file organization

Requirements:
    pip install playwright
    playwright install chromium
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: Playwright not installed")
    print("Install with: pip install playwright && playwright install chromium")
    sys.exit(1)

class PDFGenerator:
    def __init__(self, base_path, output_dir=None, state_data=None):
        self.base_path = Path(base_path)
        self.output_dir = Path(output_dir) if output_dir else self.base_path / 'pdf-output'
        self.state_data = state_data or {}
        self.conversion_log = []

    def replace_variables(self, html_content):
        """Replace {{VARIABLE}} patterns with actual state data."""
        import re

        def replacer(match):
            var_name = match.group(1)
            return str(self.state_data.get(var_name, f"{{{{f{var_name}}}}}"))

        pattern = r'\{\{([A-Z_]+)\}\}'
        return re.sub(pattern, replacer, html_content)

    def convert_html_to_pdf(self, html_path, pdf_path, replace_vars=False):
        """Convert a single HTML file to PDF using Playwright."""
        try:
            # Read HTML content
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Optionally replace variables
            if replace_vars and self.state_data:
                html_content = self.replace_variables(html_content)

            # Create temporary HTML file if variables were replaced
            if replace_vars:
                temp_html = html_path.parent / f"temp_{html_path.name}"
                with open(temp_html, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                source_file = temp_html
            else:
                source_file = html_path

            # Convert to PDF using Playwright
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()

                # Load HTML file
                page.goto(f'file://{source_file.absolute()}')

                # Wait for any dynamic content to load
                page.wait_for_timeout(1000)

                # Generate PDF with print-friendly settings
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                page.pdf(
                    path=str(pdf_path),
                    format='Letter',
                    print_background=True,
                    margin={
                        'top': '0.5in',
                        'right': '0.5in',
                        'bottom': '0.5in',
                        'left': '0.5in'
                    }
                )

                browser.close()

            # Clean up temporary file
            if replace_vars and temp_html.exists():
                temp_html.unlink()

            self.conversion_log.append({
                'status': 'success',
                'html': str(html_path),
                'pdf': str(pdf_path),
                'timestamp': datetime.now().isoformat()
            })

            return True

        except Exception as e:
            self.conversion_log.append({
                'status': 'error',
                'html': str(html_path),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            print(f"Error converting {html_path}: {e}")
            return False

    def scan_and_convert(self, chapters=None, replace_vars=False):
        """Scan all chapter directories and convert HTML files to PDFs."""

        print("=" * 70)
        print("PFL Academy PDF Generator")
        print("=" * 70)
        print(f"Source: {self.base_path}")
        print(f"Output: {self.output_dir}")
        if replace_vars:
            print(f"State data: {len(self.state_data)} variables")
        print("=" * 70)

        # Find all L-* directories
        chapter_dirs = []
        for item in sorted(self.base_path.glob('L-*')):
            if item.is_dir():
                chapter_num = item.name.split('-')[1]
                try:
                    if int(chapter_num) >= 3:  # L-3 and above
                        if chapters is None or item.name in chapters:
                            chapter_dirs.append(item)
                except ValueError:
                    continue

        print(f"\nFound {len(chapter_dirs)} chapter directories to process\n")

        total_converted = 0
        total_failed = 0

        for chapter_dir in chapter_dirs:
            chapter_name = chapter_dir.name
            print(f"Processing {chapter_name}...")

            # Find HTML files in downloads directory
            downloads_dir = chapter_dir / 'assets' / 'downloads'
            if not downloads_dir.exists():
                print(f"  No downloads directory found, skipping")
                continue

            html_files = list(downloads_dir.glob('*.html'))
            if not html_files:
                print(f"  No HTML files found, skipping")
                continue

            print(f"  Found {len(html_files)} HTML files")

            # Create output directory for this chapter
            chapter_output = self.output_dir / chapter_name
            chapter_output.mkdir(parents=True, exist_ok=True)

            # Convert each HTML file
            for html_file in html_files:
                pdf_name = html_file.stem + '.pdf'
                pdf_path = chapter_output / pdf_name

                print(f"    Converting {html_file.name}...", end=' ')

                if self.convert_html_to_pdf(html_file, pdf_path, replace_vars):
                    print("✓")
                    total_converted += 1
                else:
                    print("✗")
                    total_failed += 1

        print("\n" + "=" * 70)
        print("CONVERSION SUMMARY")
        print("=" * 70)
        print(f"Successfully converted: {total_converted} files")
        print(f"Failed conversions: {total_failed} files")
        print(f"Output directory: {self.output_dir}")

        # Save conversion log
        log_file = self.output_dir / 'conversion_log.json'
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_converted': total_converted,
                    'total_failed': total_failed,
                    'timestamp': datetime.now().isoformat()
                },
                'details': self.conversion_log
            }, f, indent=2)

        print(f"Conversion log saved: {log_file}")
        print("=" * 70)

        return total_converted, total_failed

def load_state_data(state_data_file):
    """Load state-specific data from JSON file."""
    try:
        with open(state_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading state data: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(
        description='Convert PFL Academy HTML assets to PDFs'
    )
    parser.add_argument(
        '--base-path',
        default='content-complete',
        help='Base path to content-complete directory'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory for PDFs (default: content-complete/pdf-output)'
    )
    parser.add_argument(
        '--chapters',
        nargs='+',
        help='Specific chapters to convert (e.g., L-46 L-47)'
    )
    parser.add_argument(
        '--state-data',
        help='Path to JSON file with state variable data'
    )
    parser.add_argument(
        '--replace-vars',
        action='store_true',
        help='Replace {{VARIABLE}} patterns with state data'
    )

    args = parser.parse_args()

    # Resolve base path
    script_dir = Path(__file__).parent
    base_path = script_dir / args.base_path

    if not base_path.exists():
        print(f"Error: Base path {base_path} does not exist")
        sys.exit(1)

    # Load state data if provided
    state_data = {}
    if args.state_data:
        state_data = load_state_data(args.state_data)

    # Create generator
    generator = PDFGenerator(
        base_path=base_path,
        output_dir=args.output_dir,
        state_data=state_data
    )

    # Run conversion
    converted, failed = generator.scan_and_convert(
        chapters=args.chapters,
        replace_vars=args.replace_vars
    )

    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == '__main__':
    main()
