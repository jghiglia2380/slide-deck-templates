#!/usr/bin/env python3
"""
Comprehensive Audit of Original 45 Chapters for State Variable Opportunities

This script analyzes all 45 original chapters (Standards 1-15, 3 chapters each)
to identify opportunities for state-specific personalization using the 86 existing
variables or new variables that may be needed.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

class ChapterAuditor:
    def __init__(self, content_dir, schema_file):
        self.content_dir = Path(content_dir)
        self.schema = self.load_schema(schema_file)
        self.opportunities = []
        self.new_variables_needed = set()

        # Load existing 86 variables
        self.existing_variables = self.extract_existing_variables()

        # Patterns that suggest state-specific content opportunities
        self.patterns = {
            'state_tax': [
                r'state\s+(?:income\s+)?tax',
                r'(?:state|local)\s+sales\s+tax',
                r'property\s+tax',
                r'tax\s+rate',
                r'varies\s+by\s+state'
            ],
            'wages': [
                r'minimum\s+wage',
                r'\$\d+\.?\d*\s+(?:per\s+)?hour',
                r'hourly\s+(?:wage|rate|pay)'
            ],
            'housing': [
                r'(?:median|average)\s+(?:home|house)\s+price',
                r'rent',
                r'housing\s+(?:cost|market|price)',
                r'real\s+estate'
            ],
            'automotive': [
                r'(?:car|vehicle|auto)\s+registration',
                r'(?:car|auto)\s+insurance',
                r'DMV',
                r'(?:car|vehicle)\s+loan',
                r'gas\s+price'
            ],
            'employment': [
                r'unemployment\s+rate',
                r'job\s+market',
                r'major\s+industries'
            ],
            'education': [
                r'(?:college|university)\s+tuition',
                r'(?:in-state|out-of-state)\s+tuition',
                r'student\s+loan'
            ],
            'local_examples': [
                r'(?:major|local)\s+(?:city|cities)',
                r'(?:local|nearby)\s+(?:business|retailer|bank)',
                r'in\s+your\s+(?:area|state|city)',
                r'credit\s+union'
            ]
        }

    def load_schema(self, schema_file):
        """Load the existing state data schema"""
        with open(schema_file, 'r') as f:
            return json.load(f)

    def extract_existing_variables(self):
        """Extract all variable names from schema"""
        variables = set()

        def extract_from_obj(obj, prefix=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'properties' and isinstance(value, dict):
                        for prop_name in value.keys():
                            var_name = f"{prefix}_{prop_name}" if prefix else prop_name
                            variables.add(var_name.upper())
                    extract_from_obj(value, key if key != 'properties' else prefix)

        extract_from_obj(self.schema)
        return variables

    def find_chapters(self):
        """Find all chapter files in the content directory"""
        chapters = []
        for standard_dir in sorted(self.content_dir.glob('Standard-*')):
            standard_num = standard_dir.name.split('-')[1]
            for chapter_dir in sorted(standard_dir.glob('[0-9]*')):
                chapter_num = chapter_dir.name

                # Find student content files
                student_day1 = chapter_dir / 'student' / 'day1.md'
                student_day2 = chapter_dir / 'student' / 'day2.md'

                if student_day1.exists():
                    chapters.append({
                        'standard': int(standard_num),
                        'chapter': chapter_num,
                        'day': 1,
                        'file': student_day1,
                        'type': 'student'
                    })

                if student_day2.exists():
                    chapters.append({
                        'standard': int(standard_num),
                        'chapter': chapter_num,
                        'day': 2,
                        'file': student_day2,
                        'type': 'student'
                    })

        return chapters

    def analyze_chapter(self, chapter_info):
        """Analyze a single chapter for state variable opportunities"""
        file_path = chapter_info['file']

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        chapter_opportunities = {
            'chapter_id': f"{chapter_info['standard']}.{chapter_info['chapter']}",
            'day': chapter_info['day'],
            'file': str(file_path),
            'opportunities': []
        }

        # Search for each pattern category
        for category, pattern_list in self.patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Get context around the match
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 100)
                    context = content[start:end].replace('\n', ' ')

                    # Find line number
                    line_num = content[:match.start()].count('\n') + 1

                    opportunity = {
                        'category': category,
                        'matched_text': match.group(),
                        'line': line_num,
                        'context': context,
                        'suggested_variable': self.suggest_variable(match.group(), category),
                        'priority': self.calculate_priority(category, match.group())
                    }

                    chapter_opportunities['opportunities'].append(opportunity)

        return chapter_opportunities

    def suggest_variable(self, matched_text, category):
        """Suggest which variable to use for this opportunity"""
        text_lower = matched_text.lower()

        variable_map = {
            'state_tax': {
                'state income tax': 'STATE_INCOME_TAX_RATE',
                'state tax': 'STATE_SALES_TAX',
                'sales tax': 'STATE_SALES_TAX',
                'property tax': 'STATE_PROPERTY_TAX_COUNTY_RATE'
            },
            'wages': {
                'minimum wage': 'STATE_MIN_WAGE',
                'hour': 'STATE_MIN_WAGE (for context)'
            },
            'housing': {
                'home price': 'STATE_MEDIAN_HOME_PRICE',
                'rent': 'STATE_MEDIAN_RENT',
                'housing': 'STATE_HOUSING_MARKET_TRENDS'
            },
            'automotive': {
                'registration': 'STATE_REGISTRATION_ANNUAL',
                'insurance': 'STATE_INSURANCE_AVG_TEEN',
                'dmv': 'STATE_DMV_URL',
                'gas price': 'STATE_GAS_PRICE_CURRENT'
            },
            'employment': {
                'unemployment': 'STATE_UNEMPLOYMENT_RATE',
                'industries': 'STATE_MAJOR_INDUSTRIES'
            },
            'education': {
                'tuition': 'STATE_TUITION_PUBLIC'
            },
            'local_examples': {
                'city': 'STATE_MAJOR_CITY_1',
                'business': 'STATE_MAJOR_RETAILERS',
                'credit union': 'STATE_LOCAL_CREDIT_UNION_NAME'
            }
        }

        if category in variable_map:
            for keyword, variable in variable_map[category].items():
                if keyword in text_lower:
                    return variable

        return f'NEW_VARIABLE_NEEDED ({category})'

    def calculate_priority(self, category, matched_text):
        """Calculate priority: HIGH, MEDIUM, LOW"""
        high_priority_categories = ['state_tax', 'wages', 'housing']
        medium_priority_categories = ['automotive', 'employment', 'education']

        if category in high_priority_categories:
            return 'HIGH'
        elif category in medium_priority_categories:
            return 'MEDIUM'
        else:
            return 'LOW'

    def run_audit(self):
        """Run the complete audit"""
        print("="*80)
        print("COMPREHENSIVE AUDIT OF 45 ORIGINAL CHAPTERS")
        print("Searching for State Variable Personalization Opportunities")
        print("="*80)
        print()

        chapters = self.find_chapters()
        print(f"Found {len(chapters)} chapter files to analyze\n")

        all_results = []

        for chapter_info in chapters:
            print(f"Analyzing: Standard {chapter_info['standard']}.{chapter_info['chapter']} Day {chapter_info['day']}...", end=' ')
            result = self.analyze_chapter(chapter_info)
            all_results.append(result)
            print(f"{len(result['opportunities'])} opportunities found")

        return all_results

    def generate_report(self, results):
        """Generate comprehensive audit report"""
        report = {
            'summary': self.generate_summary(results),
            'by_chapter': results,
            'by_category': self.group_by_category(results),
            'by_priority': self.group_by_priority(results),
            'new_variables_needed': list(self.identify_new_variables(results)),
            'implementation_recommendations': self.generate_recommendations(results)
        }

        return report

    def generate_summary(self, results):
        """Generate summary statistics"""
        total_opportunities = sum(len(r['opportunities']) for r in results)
        chapters_with_opportunities = sum(1 for r in results if len(r['opportunities']) > 0)

        priority_counts = defaultdict(int)
        for result in results:
            for opp in result['opportunities']:
                priority_counts[opp['priority']] += 1

        return {
            'total_chapters_analyzed': len(results),
            'chapters_with_opportunities': chapters_with_opportunities,
            'total_opportunities': total_opportunities,
            'high_priority': priority_counts['HIGH'],
            'medium_priority': priority_counts['MEDIUM'],
            'low_priority': priority_counts['LOW']
        }

    def group_by_category(self, results):
        """Group opportunities by category"""
        by_category = defaultdict(list)
        for result in results:
            for opp in result['opportunities']:
                by_category[opp['category']].append({
                    'chapter': result['chapter_id'],
                    'day': result['day'],
                    'matched_text': opp['matched_text'],
                    'variable': opp['suggested_variable'],
                    'priority': opp['priority']
                })
        return dict(by_category)

    def group_by_priority(self, results):
        """Group opportunities by priority"""
        by_priority = defaultdict(list)
        for result in results:
            for opp in result['opportunities']:
                by_priority[opp['priority']].append({
                    'chapter': result['chapter_id'],
                    'day': result['day'],
                    'category': opp['category'],
                    'matched_text': opp['matched_text'],
                    'variable': opp['suggested_variable']
                })
        return dict(by_priority)

    def identify_new_variables(self, results):
        """Identify which new variables might be needed"""
        new_vars = set()
        for result in results:
            for opp in result['opportunities']:
                if 'NEW_VARIABLE_NEEDED' in opp['suggested_variable']:
                    new_vars.add(opp['suggested_variable'])
        return new_vars

    def generate_recommendations(self, results):
        """Generate implementation recommendations"""
        summary = self.generate_summary(results)

        recommendations = {
            'approach': 'PHASED_IMPLEMENTATION',
            'phases': []
        }

        if summary['high_priority'] > 0:
            recommendations['phases'].append({
                'phase': 1,
                'name': 'High-Impact State Personalization',
                'opportunities': summary['high_priority'],
                'focus': 'State taxes, wages, housing - most variable across states',
                'estimated_effort': f"{summary['high_priority'] * 2} hours",
                'priority': 'MUST_HAVE_FOR_LAUNCH'
            })

        if summary['medium_priority'] > 0:
            recommendations['phases'].append({
                'phase': 2,
                'name': 'Moderate-Impact State Personalization',
                'opportunities': summary['medium_priority'],
                'focus': 'Automotive, employment, education',
                'estimated_effort': f"{summary['medium_priority'] * 1.5} hours",
                'priority': 'SHOULD_HAVE'
            })

        if summary['low_priority'] > 0:
            recommendations['phases'].append({
                'phase': 3,
                'name': 'Enhanced Local Personalization',
                'opportunities': summary['low_priority'],
                'focus': 'Local examples, businesses, nonprofits',
                'estimated_effort': f"{summary['low_priority'] * 1} hours",
                'priority': 'NICE_TO_HAVE'
            })

        return recommendations

    def save_report(self, report, output_file):
        """Save report to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Full audit report saved to: {output_file}")

    def print_summary_report(self, report):
        """Print human-readable summary"""
        print("\n" + "="*80)
        print("AUDIT SUMMARY")
        print("="*80)

        summary = report['summary']
        print(f"\nChapters Analyzed: {summary['total_chapters_analyzed']}")
        print(f"Chapters with Opportunities: {summary['chapters_with_opportunities']}")
        print(f"Total Opportunities Found: {summary['total_opportunities']}\n")

        print("By Priority:")
        print(f"  HIGH:   {summary['high_priority']} opportunities")
        print(f"  MEDIUM: {summary['medium_priority']} opportunities")
        print(f"  LOW:    {summary['low_priority']} opportunities\n")

        print("By Category:")
        for category, opps in report['by_category'].items():
            print(f"  {category}: {len(opps)} opportunities")

        print("\n" + "="*80)
        print("IMPLEMENTATION RECOMMENDATIONS")
        print("="*80)

        for phase in report['implementation_recommendations']['phases']:
            print(f"\nPhase {phase['phase']}: {phase['name']}")
            print(f"  Opportunities: {phase['opportunities']}")
            print(f"  Focus: {phase['focus']}")
            print(f"  Estimated Effort: {phase['estimated_effort']}")
            print(f"  Priority: {phase['priority']}")

        if report['new_variables_needed']:
            print("\n" + "="*80)
            print("NEW VARIABLES NEEDED")
            print("="*80)
            for var in sorted(report['new_variables_needed']):
                print(f"  - {var}")

        print("\n" + "="*80)


def main():
    import sys

    base_dir = Path(__file__).parent.parent
    content_dir = base_dir / 'f-sync-90' / 'content'
    schema_file = Path(__file__).parent / 'schema.json'
    output_file = Path(__file__).parent / 'ORIGINAL_CHAPTERS_AUDIT_REPORT.json'

    if not content_dir.exists():
        print(f"Error: Content directory not found: {content_dir}")
        sys.exit(1)

    if not schema_file.exists():
        print(f"Error: Schema file not found: {schema_file}")
        sys.exit(1)

    auditor = ChapterAuditor(content_dir, schema_file)
    results = auditor.run_audit()
    report = auditor.generate_report(results)
    auditor.save_report(report, output_file)
    auditor.print_summary_report(report)

    print(f"\n✓ Audit complete! Review full details in: {output_file}\n")


if __name__ == '__main__':
    main()
