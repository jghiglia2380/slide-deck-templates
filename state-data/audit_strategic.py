#!/usr/bin/env python3
"""
Strategic Audit of Original 45 Chapters for State Variable Opportunities

This refined audit focuses on genuine opportunities for state personalization
by using word boundaries and context-aware analysis.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

class StrategicChapterAuditor:
    def __init__(self, content_dir, schema_file):
        self.content_dir = Path(content_dir)
        self.schema = self.load_schema(schema_file)
        self.opportunities = []

        # Refined patterns using word boundaries
        self.patterns = {
            'state_tax': [
                r'\bstate\s+(?:income\s+)?tax(?:es)?\b',
                r'\bsales\s+tax\b',
                r'\bproperty\s+tax\b',
                r'\btax\s+rate\b',
                r'\bstate\s+tax\s+rate\b'
            ],
            'wages': [
                r'\bminimum\s+wage\b',
                r'\bhourly\s+(?:wage|rate|pay)\b'
            ],
            'housing': [
                r'\bmedian\s+(?:home|house)\s+price\b',
                r'\bhousing\s+(?:cost|market|price)s?\b',
                r'\baverage\s+rent\b',
                r'\bmedian\s+rent\b',
                r'\brental\s+(?:cost|market)\b'
            ],
            'automotive': [
                r'\bvehicle\s+registration\b',
                r'\bcar\s+registration\b',
                r'\bDMV\s+fees?\b',
                r'\bregistration\s+fees?\b'
            ],
            'employment': [
                r'\bunemployment\s+rate\b',
                r'\bjob\s+market\b',
                r'\bmajor\s+industries\b',
                r'\bemployment\s+opportunities\b'
            ],
            'education': [
                r'\bcollege\s+tuition\b',
                r'\buniversity\s+tuition\b',
                r'\bin-state\s+tuition\b',
                r'\bout-of-state\s+tuition\b',
                r'\bpublic\s+(?:college|university)\s+cost\b'
            ],
            'banking': [
                r'\bbank(?:ing)?\s+fees?\b',
                r'\boverdraft\s+fees?\b',
                r'\bATM\s+fees?\b',
                r'\bmonthly\s+(?:account|service)\s+fees?\b'
            ],
            'local_examples': [
                r'\bin\s+your\s+(?:state|area|city|community)\b',
                r'\blocal\s+(?:business|retailer|bank|credit\s+union)\b',
                r'\bnearby\s+(?:business|retailer|bank)\b'
            ]
        }

    def load_schema(self, schema_file):
        """Load the existing state data schema"""
        with open(schema_file, 'r') as f:
            return json.load(f)

    def find_chapters(self):
        """Find all chapter files in the content directory"""
        chapters = []
        for standard_dir in sorted(self.content_dir.glob('Standard-*')):
            standard_num = standard_dir.name.split('-')[1]

            # Skip Standard 15 (already has L-chapters)
            if int(standard_num) > 14:
                continue

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
            category_matches = []

            for pattern in pattern_list:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                category_matches.extend(matches)

            # Only consider if there are multiple mentions (2+)
            if len(category_matches) >= 2:
                # Get first match for context
                match = category_matches[0]
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end].replace('\n', ' ')

                # Find line number
                line_num = content[:match.start()].count('\n') + 1

                opportunity = {
                    'category': category,
                    'match_count': len(category_matches),
                    'first_match_text': match.group(),
                    'line': line_num,
                    'context': context,
                    'suggested_variables': self.suggest_variables(category),
                    'priority': self.calculate_priority(category, len(category_matches))
                }

                chapter_opportunities['opportunities'].append(opportunity)

        return chapter_opportunities

    def suggest_variables(self, category):
        """Suggest which variables to use for this category"""
        variable_map = {
            'state_tax': ['STATE_SALES_TAX', 'STATE_INCOME_TAX_RATE', 'STATE_PROPERTY_TAX_COUNTY_RATE'],
            'wages': ['STATE_MIN_WAGE'],
            'housing': ['STATE_MEDIAN_HOME_PRICE', 'STATE_MEDIAN_RENT', 'STATE_HOUSING_MARKET_TRENDS'],
            'automotive': ['STATE_REGISTRATION_ANNUAL', 'STATE_INSURANCE_AVG_TEEN', 'STATE_DMV_URL'],
            'employment': ['STATE_UNEMPLOYMENT_RATE', 'STATE_MAJOR_INDUSTRIES'],
            'education': ['STATE_TUITION_PUBLIC'],
            'banking': ['STATE_AVG_MONTHLY_FEE', 'STATE_AVG_OVERDRAFT_FEE'],
            'local_examples': ['STATE_MAJOR_CITY_1', 'STATE_MAJOR_RETAILERS', 'STATE_LOCAL_CREDIT_UNION_NAME']
        }

        return variable_map.get(category, [])

    def calculate_priority(self, category, match_count):
        """Calculate priority based on category and frequency"""
        high_priority_categories = ['state_tax', 'wages', 'housing', 'education']

        # High priority if in key category AND mentioned frequently
        if category in high_priority_categories and match_count >= 3:
            return 'HIGH'
        elif category in high_priority_categories and match_count == 2:
            return 'MEDIUM'
        else:
            return 'LOW'

    def run_audit(self):
        """Run the strategic audit"""
        print("="*80)
        print("STRATEGIC AUDIT OF ORIGINAL 45 CHAPTERS")
        print("Identifying Genuine State Personalization Opportunities")
        print("="*80)
        print()

        chapters = self.find_chapters()
        print(f"Found {len(chapters)} chapter files to analyze\n")

        all_results = []

        for chapter_info in chapters:
            print(f"Analyzing: Standard {chapter_info['standard']}.{chapter_info['chapter']} Day {chapter_info['day']}...", end=' ')
            result = self.analyze_chapter(chapter_info)

            # Only include chapters with opportunities
            if result['opportunities']:
                all_results.append(result)
                print(f"{len(result['opportunities'])} categories found")
            else:
                print("no opportunities")

        return all_results

    def generate_strategic_report(self, results):
        """Generate strategic recommendations"""
        report = {
            'summary': self.generate_summary(results),
            'high_priority_chapters': self.identify_high_priority_chapters(results),
            'by_category': self.group_by_category(results),
            'recommendations': self.generate_strategic_recommendations(results)
        }

        return report

    def generate_summary(self, results):
        """Generate summary statistics"""
        total_chapters_with_opps = len(results)
        total_opportunities = sum(len(r['opportunities']) for r in results)

        priority_counts = defaultdict(int)
        for result in results:
            for opp in result['opportunities']:
                priority_counts[opp['priority']] += 1

        return {
            'total_chapters_with_opportunities': total_chapters_with_opps,
            'total_opportunity_categories': total_opportunities,
            'high_priority': priority_counts['HIGH'],
            'medium_priority': priority_counts['MEDIUM'],
            'low_priority': priority_counts['LOW']
        }

    def identify_high_priority_chapters(self, results):
        """Identify chapters that would benefit most from state variables"""
        high_priority = []

        for result in results:
            high_priority_opps = [o for o in result['opportunities'] if o['priority'] == 'HIGH']

            if high_priority_opps:
                high_priority.append({
                    'chapter_id': result['chapter_id'],
                    'day': result['day'],
                    'high_priority_categories': len(high_priority_opps),
                    'categories': [o['category'] for o in high_priority_opps],
                    'total_matches': sum(o['match_count'] for o in high_priority_opps)
                })

        # Sort by number of high priority opportunities
        high_priority.sort(key=lambda x: x['total_matches'], reverse=True)

        return high_priority

    def group_by_category(self, results):
        """Group opportunities by category"""
        by_category = defaultdict(lambda: {'chapters': [], 'total_mentions': 0})

        for result in results:
            for opp in result['opportunities']:
                by_category[opp['category']]['chapters'].append({
                    'chapter': result['chapter_id'],
                    'day': result['day'],
                    'mentions': opp['match_count'],
                    'priority': opp['priority']
                })
                by_category[opp['category']]['total_mentions'] += opp['match_count']

        return dict(by_category)

    def generate_strategic_recommendations(self, results):
        """Generate strategic recommendations"""
        high_priority = [r for r in results if any(o['priority'] == 'HIGH' for o in r['opportunities'])]

        recommendations = {
            'approach': 'STRATEGIC_ENHANCEMENT',
            'total_chapters_recommended': len(high_priority),
            'estimated_variables_to_add': sum(
                len(set(v for o in r['opportunities'] for v in o['suggested_variables']))
                for r in high_priority
            ),
            'phases': []
        }

        if high_priority:
            recommendations['phases'].append({
                'phase': 1,
                'name': 'High-Impact State Personalization',
                'chapters': len(high_priority),
                'focus': 'Chapters with 3+ mentions of state-specific content',
                'estimated_effort': f"{len(high_priority) * 2} hours",
                'priority': 'RECOMMENDED'
            })

        return recommendations

    def save_report(self, report, output_file):
        """Save report to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Strategic audit report saved to: {output_file}")

    def print_strategic_summary(self, report):
        """Print human-readable strategic summary"""
        print("\n" + "="*80)
        print("STRATEGIC AUDIT SUMMARY")
        print("="*80)

        summary = report['summary']
        print(f"\nChapters with Opportunities: {summary['total_chapters_with_opportunities']}")
        print(f"Total Opportunity Categories: {summary['total_opportunity_categories']}")
        print(f"  HIGH Priority: {summary['high_priority']}")
        print(f"  MEDIUM Priority: {summary['medium_priority']}")
        print(f"  LOW Priority: {summary['low_priority']}")

        print("\n" + "-"*80)
        print("TOP OPPORTUNITIES BY CATEGORY")
        print("-"*80)

        for category, data in sorted(report['by_category'].items(),
                                     key=lambda x: x[1]['total_mentions'],
                                     reverse=True)[:5]:
            print(f"\n{category.upper().replace('_', ' ')}:")
            print(f"  Total mentions: {data['total_mentions']}")
            print(f"  Chapters affected: {len(data['chapters'])}")

            # Show top 3 chapters
            top_chapters = sorted(data['chapters'], key=lambda x: x['mentions'], reverse=True)[:3]
            for ch in top_chapters:
                print(f"    - Chapter {ch['chapter']} Day {ch['day']}: {ch['mentions']} mentions ({ch['priority']} priority)")

        print("\n" + "-"*80)
        print("HIGH PRIORITY CHAPTERS (Top 10)")
        print("-"*80)

        for i, ch in enumerate(report['high_priority_chapters'][:10], 1):
            print(f"\n{i}. Chapter {ch['chapter_id']} Day {ch['day']}")
            print(f"   Categories: {', '.join(ch['categories'])}")
            print(f"   Total state-specific mentions: {ch['total_matches']}")

        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)

        recs = report['recommendations']
        print(f"\nApproach: {recs['approach']}")
        print(f"Chapters recommended for enhancement: {recs['total_chapters_recommended']}")
        print(f"Estimated new variable instances to add: {recs['estimated_variables_to_add']}")

        for phase in recs['phases']:
            print(f"\nPhase {phase['phase']}: {phase['name']}")
            print(f"  Chapters: {phase['chapters']}")
            print(f"  Focus: {phase['focus']}")
            print(f"  Estimated Effort: {phase['estimated_effort']}")
            print(f"  Priority: {phase['priority']}")

        print("\n" + "="*80)


def main():
    import sys

    base_dir = Path(__file__).parent.parent
    content_dir = base_dir / 'f-sync-90' / 'content'
    schema_file = Path(__file__).parent / 'schema.json'
    output_file = Path(__file__).parent / 'STRATEGIC_AUDIT_REPORT.json'

    if not content_dir.exists():
        print(f"Error: Content directory not found: {content_dir}")
        sys.exit(1)

    if not schema_file.exists():
        print(f"Error: Schema file not found: {schema_file}")
        sys.exit(1)

    auditor = StrategicChapterAuditor(content_dir, schema_file)
    results = auditor.run_audit()
    report = auditor.generate_strategic_report(results)
    auditor.save_report(report, output_file)
    auditor.print_strategic_summary(report)

    print(f"\n✓ Strategic audit complete! Review details in: {output_file}\n")


if __name__ == '__main__':
    main()
