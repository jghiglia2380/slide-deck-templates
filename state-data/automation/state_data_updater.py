#!/usr/bin/env python3
"""
PFL Academy State Data Automatic Updater

This script automatically updates state-specific variables by:
1. Web searching for current data
2. Extracting and validating values
3. Updating state JSON files
4. Creating version snapshots
5. Notifying teachers of changes
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import anthropic
import schedule
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Written into a field when the updater CANNOT actually source a value.
# Never replace this with a number that the model merely recalled — an
# unsourced figure that looks real is worse than a visibly missing one.
NEEDS_VERIFICATION = "NEEDS_HUMAN_VERIFICATION"


class StateDataUpdater:
    def __init__(self, config_path='config.json', test_mode=False):
        """Initialize the updater with configuration"""
        self.base_dir = Path(__file__).parent.parent
        self.config = self.load_config(config_path)
        self.client = self.init_anthropic_client()
        self.current_version = self.generate_version_tag()
        self.changes_log = []
        self.test_mode = test_mode
        self._state_files = None          # lazy state_code -> Path index
        self.flagged = []                 # fields written as NEEDS_VERIFICATION

        # Can we actually fetch? Only if a web-search tool is configured AND
        # passed to the API. Absent that, the model has no browsing ability and
        # anything it returns is recall, not a lookup. Default: NO.
        self.web_search_tool = self.config.get('anthropic_api', {}).get('web_search_tool')
        if not self.web_search_tool:
            print("⚠️  No web-search tool configured (anthropic_api.web_search_tool).")
            print(f"    Values cannot be sourced; fields will be written as {NEEDS_VERIFICATION}.")

        if self.test_mode:
            print("🧪 TEST MODE — no files will be written.\n")

    def load_config(self, config_path):
        """Load configuration file"""
        with open(Path(__file__).parent / config_path, 'r') as f:
            return json.load(f)

    def init_anthropic_client(self):
        """Initialize Anthropic API client"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return anthropic.Anthropic(api_key=api_key)

    def generate_version_tag(self):
        """Generate version tag based on current date (YYYY-QN format)"""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"{now.year}-Q{quarter}"

    def get_enabled_states(self):
        """Get list of enabled states"""
        return self.config['enabled_states']

    def build_state_index(self):
        """Map 2-letter state code -> states/<full_state_name>.json.

        The files are named for the state ('alabama.json'), not the code
        ('al.json'), so the code cannot be turned into a filename directly.
        The mapping is read from each file's own state_code field rather than
        hardcoded, so adding a state needs no change here.
        """
        if self._state_files is not None:
            return self._state_files

        index = {}
        states_dir = self.base_dir / 'states'
        for path in sorted(states_dir.glob('*.json')):
            try:
                with open(path, 'r') as f:
                    code = json.load(f).get('state_code')
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: could not read {path.name}: {e}")
                continue
            if code:
                index[code.upper()] = path

        self._state_files = index
        return index

    def state_file_path(self, state_code):
        """Resolve a state code to its JSON file, or None."""
        return self.build_state_index().get(state_code.upper())

    def load_state_data(self, state_code):
        """Load existing state JSON file"""
        file_path = self.state_file_path(state_code)
        if file_path is None or not file_path.exists():
            print(f"Warning: State file not found for {state_code}")
            return None

        with open(file_path, 'r') as f:
            return json.load(f)

    def save_state_data(self, state_code, data):
        """Save updated state JSON file"""
        file_path = self.state_file_path(state_code)
        if file_path is None:
            print(f"Warning: cannot save {state_code} — no state file mapped")
            return

        if self.test_mode:
            print(f"  🧪 test mode — not writing {file_path.name}")
            return

        # Backup existing file
        if file_path.exists():
            backup_dir = self.base_dir / 'backups' / self.current_version
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f'{state_code.lower()}.json'

            with open(file_path, 'r') as f:
                with open(backup_path, 'w') as backup:
                    backup.write(f.read())

        # Save new data
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def web_search_variable(self, state_name, variable_name, context=""):
        """Use Claude to web search and extract variable data"""

        # Map variable names to search queries
        query_map = {
            'gas_price_current': f"{state_name} average gas price {datetime.now().strftime('%B %Y')}",
            'avg_auto_loan_rate_new': f"{state_name} new car loan interest rates {datetime.now().year}",
            'avg_auto_loan_rate_used': f"{state_name} used car loan interest rates {datetime.now().year}",
            'avg_mortgage_rate_30yr': f"{state_name} average 30-year mortgage rate {datetime.now().strftime('%B %Y')}",
            'unemployment_rate': f"{state_name} unemployment rate {datetime.now().strftime('%B %Y')}",
            'median_home_price': f"{state_name} median home price {datetime.now().year}",
            'median_rent': f"{state_name} median rent {datetime.now().year}",
            'insurance_avg_teen': f"{state_name} average teen car insurance monthly cost {datetime.now().year}",
            'min_wage': f"{state_name} minimum wage {datetime.now().year}",
            'tuition_public': f"{state_name} average public university tuition {datetime.now().year}-{datetime.now().year + 1}",
            'sales_tax': f"{state_name} state sales tax rate {datetime.now().year}",
        }

        query = query_map.get(variable_name, f"{state_name} {variable_name.replace('_', ' ')} {datetime.now().year}")

        # No web-search tool wired => the model cannot look anything up. Asking
        # it anyway would return a recalled number with no source, which is
        # exactly the failure this guard exists to prevent. Flag the field for a
        # human instead of writing a figure that looks authoritative.
        if not self.web_search_tool:
            self.flagged.append({'state': state_name, 'variable': variable_name, 'query': query})
            return NEEDS_VERIFICATION

        try:
            # Use Claude with web search
            message = self.client.messages.create(
                model=self.config['anthropic_api']['model'],
                max_tokens=self.config['anthropic_api']['max_tokens'],
                temperature=self.config['anthropic_api']['temperature'],
                messages=[{
                    "role": "user",
                    "content": f"""Search the web and find the current value for: {query}

Instructions:
1. Find the most recent, authoritative source (government website, official data source)
2. Extract ONLY the numeric value (no currency symbols, no percent signs, just the number)
3. If it's a percentage, return as decimal (e.g., 6.25 for 6.25%)
4. If it's a dollar amount, return as number (e.g., 12.50 for $12.50)
5. Return ONLY the number, nothing else
6. If you cannot find reliable data, return "NOT_FOUND"

Context: {context}

Return format: Just the number or "NOT_FOUND"
"""
                }]
            )

            result = message.content[0].text.strip()

            # Parse result
            if result == "NOT_FOUND":
                return None

            try:
                return float(result)
            except ValueError:
                print(f"Warning: Could not parse result '{result}' for {variable_name}")
                return None

        except Exception as e:
            print(f"Error searching for {variable_name}: {str(e)}")
            return None

    def update_monthly_variables(self, state_code, state_data):
        """Update variables that change monthly"""
        monthly_vars = [
            'gas_price_current',
            'avg_auto_loan_rate_new',
            'avg_auto_loan_rate_used',
            'avg_mortgage_rate_30yr',
            'unemployment_rate'
        ]

        changes = []
        state_name = state_data['state_name']

        for var in monthly_vars:
            # Determine which section this variable belongs to
            section = self.get_variable_section(var)
            if section and section in state_data:
                old_value = state_data[section].get(var)
                new_value = self.web_search_variable(state_name, var)

                if new_value is not None and new_value != old_value:
                    state_data[section][var] = new_value
                    flagged = new_value == NEEDS_VERIFICATION
                    changes.append({
                        'variable': var,
                        'old_value': old_value,
                        'new_value': new_value,
                        'change_percent': self.percent_change(old_value, new_value),
                        'needs_verification': flagged
                    })
                    if flagged:
                        print(f"  ⚠️  {var}: could not source a value — flagged {NEEDS_VERIFICATION} (was {old_value})")
                    else:
                        print(f"  Updated {var}: {old_value} → {new_value}")

        return changes

    def update_quarterly_variables(self, state_code, state_data):
        """Update variables that change quarterly"""
        quarterly_vars = [
            'median_home_price',
            'median_rent',
            'insurance_avg_teen',
            'avg_monthly_fee',
            'avg_overdraft_fee'
        ]

        changes = []
        state_name = state_data['state_name']

        for var in quarterly_vars:
            section = self.get_variable_section(var)
            if section and section in state_data:
                old_value = state_data[section].get(var)
                new_value = self.web_search_variable(state_name, var)

                if new_value is not None and new_value != old_value:
                    state_data[section][var] = new_value
                    flagged = new_value == NEEDS_VERIFICATION
                    changes.append({
                        'variable': var,
                        'old_value': old_value,
                        'new_value': new_value,
                        'change_percent': self.percent_change(old_value, new_value),
                        'needs_verification': flagged
                    })
                    if flagged:
                        print(f"  ⚠️  {var}: could not source a value — flagged {NEEDS_VERIFICATION} (was {old_value})")
                    else:
                        print(f"  Updated {var}: {old_value} → {new_value}")

        return changes

    def update_annual_variables(self, state_code, state_data):
        """Update variables that change annually"""
        annual_vars = [
            'tuition_public',
            'min_wage',
            'sales_tax',
            'registration_initial',
            'registration_annual'
        ]

        changes = []
        state_name = state_data['state_name']

        for var in annual_vars:
            section = self.get_variable_section(var)
            if section and section in state_data:
                old_value = state_data[section].get(var)
                new_value = self.web_search_variable(state_name, var)

                if new_value is not None and new_value != old_value:
                    state_data[section][var] = new_value
                    flagged = new_value == NEEDS_VERIFICATION
                    changes.append({
                        'variable': var,
                        'old_value': old_value,
                        'new_value': new_value,
                        'change_percent': self.percent_change(old_value, new_value),
                        'needs_verification': flagged
                    })
                    if flagged:
                        print(f"  ⚠️  {var}: could not source a value — flagged {NEEDS_VERIFICATION} (was {old_value})")
                    else:
                        print(f"  Updated {var}: {old_value} → {new_value}")

        return changes

    @staticmethod
    def percent_change(old_value, new_value):
        """Percent change, or 0 when either side isn't numeric.

        new_value is NEEDS_HUMAN_VERIFICATION (a string) whenever the value
        could not be sourced, so this must never assume arithmetic is possible.
        """
        if isinstance(old_value, bool) or isinstance(new_value, bool):
            return 0
        if not isinstance(old_value, (int, float)) or not isinstance(new_value, (int, float)):
            return 0
        if not old_value:
            return 0
        return (new_value - old_value) / old_value * 100

    def get_variable_section(self, variable_name):
        """Determine which section a variable belongs to"""
        section_map = {
            'gas_price_current': 'automotive',
            'avg_auto_loan_rate_new': 'automotive',
            'avg_auto_loan_rate_used': 'automotive',
            'registration_initial': 'automotive',
            'registration_annual': 'automotive',
            'insurance_avg_teen': 'automotive',
            'avg_mortgage_rate_30yr': 'housing',
            'median_home_price': 'housing',
            'median_rent': 'housing',
            'unemployment_rate': 'employment',
            'min_wage': 'employment',
            'tuition_public': 'education',
            'sales_tax': 'taxes',
            'avg_monthly_fee': 'banking',
            'avg_overdraft_fee': 'banking'
        }
        return section_map.get(variable_name)

    def validate_changes(self, changes):
        """Validate that changes are within acceptable ranges"""
        if not self.config['validation']['alert_on_large_changes']:
            return True

        threshold = self.config['validation']['large_change_threshold_percent']

        for change in changes:
            if abs(change['change_percent']) > threshold:
                print(f"  ⚠️  WARNING: Large change detected for {change['variable']}: {change['change_percent']:.1f}%")
                if self.config['validation']['require_manual_approval']:
                    response = input(f"    Approve this change? (y/n): ")
                    if response.lower() != 'y':
                        return False

        return True

    def run_monthly_update(self):
        """Run monthly updates for all enabled states"""
        print(f"\n{'='*60}")
        print(f"MONTHLY UPDATE - {datetime.now().strftime('%B %Y')}")
        print(f"Version: {self.current_version}")
        print(f"{'='*60}\n")

        states = self.get_enabled_states()
        total_changes = []

        for state_code in states:
            print(f"\nProcessing {state_code}...")
            state_data = self.load_state_data(state_code)

            if not state_data:
                continue

            changes = self.update_monthly_variables(state_code, state_data)

            if changes:
                if self.validate_changes(changes):
                    state_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                    self.save_state_data(state_code, state_data)
                    total_changes.extend([{**c, 'state': state_code} for c in changes])
                    verb = "Would save" if self.test_mode else "Saved"
                    print(f"  ✓ {verb} {len(changes)} changes for {state_code}")
                else:
                    print(f"  ✗ Changes rejected for {state_code}")
            else:
                print(f"  No changes for {state_code}")

        self.log_changes(total_changes, 'monthly')
        self.notify_users(total_changes, 'monthly')

        print(f"\n{'='*60}")
        print(f"MONTHLY UPDATE COMPLETE - {len(total_changes)} total changes")
        print(f"{'='*60}\n")

    def run_quarterly_update(self):
        """Run quarterly updates for all enabled states"""
        print(f"\n{'='*60}")
        print(f"QUARTERLY UPDATE - {datetime.now().strftime('%B %Y')}")
        print(f"Version: {self.current_version}")
        print(f"{'='*60}\n")

        states = self.get_enabled_states()
        total_changes = []

        for state_code in states:
            print(f"\nProcessing {state_code}...")
            state_data = self.load_state_data(state_code)

            if not state_data:
                continue

            # Run monthly updates first
            monthly_changes = self.update_monthly_variables(state_code, state_data)
            quarterly_changes = self.update_quarterly_variables(state_code, state_data)

            all_changes = monthly_changes + quarterly_changes

            if all_changes:
                if self.validate_changes(all_changes):
                    state_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                    self.save_state_data(state_code, state_data)
                    total_changes.extend([{**c, 'state': state_code} for c in all_changes])
                    print(f"  ✓ Saved {len(all_changes)} changes for {state_code}")
                else:
                    print(f"  ✗ Changes rejected for {state_code}")
            else:
                print(f"  No changes for {state_code}")

        self.log_changes(total_changes, 'quarterly')
        self.notify_users(total_changes, 'quarterly')

        print(f"\n{'='*60}")
        print(f"QUARTERLY UPDATE COMPLETE - {len(total_changes)} total changes")
        print(f"{'='*60}\n")

    def run_annual_update(self):
        """Run annual updates for all enabled states"""
        print(f"\n{'='*60}")
        print(f"ANNUAL UPDATE - {datetime.now().strftime('%B %Y')}")
        print(f"Version: {self.current_version}")
        print(f"{'='*60}\n")

        states = self.get_enabled_states()
        total_changes = []

        for state_code in states:
            print(f"\nProcessing {state_code}...")
            state_data = self.load_state_data(state_code)

            if not state_data:
                continue

            # Run all updates
            monthly_changes = self.update_monthly_variables(state_code, state_data)
            quarterly_changes = self.update_quarterly_variables(state_code, state_data)
            annual_changes = self.update_annual_variables(state_code, state_data)

            all_changes = monthly_changes + quarterly_changes + annual_changes

            if all_changes:
                if self.validate_changes(all_changes):
                    state_data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                    self.save_state_data(state_code, state_data)
                    total_changes.extend([{**c, 'state': state_code} for c in all_changes])
                    print(f"  ✓ Saved {len(all_changes)} changes for {state_code}")
                else:
                    print(f"  ✗ Changes rejected for {state_code}")
            else:
                print(f"  No changes for {state_code}")

        self.log_changes(total_changes, 'annual')
        self.notify_users(total_changes, 'annual')

        print(f"\n{'='*60}")
        print(f"ANNUAL UPDATE COMPLETE - {len(total_changes)} total changes")
        print(f"{'='*60}\n")

    def log_changes(self, changes, update_type):
        """Log all changes to changelog file"""
        needs_verification = [c for c in changes if c.get('needs_verification')]

        if self.test_mode:
            print(f"\n🧪 test mode — not writing changelog "
                  f"({len(changes)} change(s), {len(needs_verification)} needing verification)")
            return

        changelog_dir = self.base_dir / 'changelog'
        changelog_dir.mkdir(exist_ok=True)

        changelog_file = changelog_dir / f'{self.current_version}_{update_type}.json'

        changelog_data = {
            'version': self.current_version,
            'update_type': update_type,
            'timestamp': datetime.now().isoformat(),
            'changes': changes,
            'total_changes': len(changes),
            'states_affected': list(set([c['state'] for c in changes])),
            'needs_verification_count': len(needs_verification),
            'needs_verification': needs_verification,
            'web_search_tool': self.web_search_tool or None
        }

        with open(changelog_file, 'w') as f:
            json.dump(changelog_data, f, indent=2)

        print(f"\n📝 Changelog saved: {changelog_file}")

    def notify_users(self, changes, update_type):
        """Generate notifications for teachers/admins"""
        if not self.config['notifications']['enabled']:
            return

        if not changes:
            return

        if self.test_mode:
            print("🧪 test mode — not writing notifications")
            return

        notifications_dir = self.base_dir / 'notifications'
        notifications_dir.mkdir(exist_ok=True)

        notification_file = notifications_dir / f'{self.current_version}_{update_type}.json'

        # Group changes by state
        by_state = {}
        for change in changes:
            state = change['state']
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(change)

        notifications = []
        for state, state_changes in by_state.items():
            notification = {
                'state': state,
                'version': self.current_version,
                'update_type': update_type,
                'timestamp': datetime.now().isoformat(),
                'message': self.generate_notification_message(state, state_changes, update_type),
                'changes': state_changes,
                'learning_moment': self.generate_learning_moment(state_changes)
            }
            notifications.append(notification)

        with open(notification_file, 'w') as f:
            json.dump(notifications, f, indent=2)

        print(f"\n📬 Notifications generated: {notification_file}")

    def generate_notification_message(self, state, changes, update_type):
        """Generate human-readable notification message"""
        change_count = len(changes)
        variable_list = ', '.join([c['variable'].replace('_', ' ') for c in changes[:3]])

        if change_count > 3:
            variable_list += f" and {change_count - 3} more"

        return f"📊 Data Update Alert for {state}\n\n" \
               f"{change_count} variable(s) updated in the {update_type} update ({self.current_version}):\n" \
               f"{variable_list}\n\n" \
               f"Student work submitted before this update remains graded against previous data.\n" \
               f"New assignments will use updated values."

    def generate_learning_moment(self, changes):
        """Generate educational context for variable changes"""
        moments = []

        for change in changes:
            var = change['variable']
            old = change['old_value']
            new = change['new_value']
            pct = change['change_percent']

            if var == 'unemployment_rate':
                moments.append(f"💡 Unemployment rates change based on economic conditions, seasonal employment, and job market trends.")
            elif var == 'gas_price_current':
                moments.append(f"💡 Gas prices fluctuate due to crude oil costs, refining capacity, supply/demand, and geopolitical events.")
            elif var == 'min_wage':
                moments.append(f"💡 Minimum wage changes are set by state legislatures and can vary significantly between states.")
            elif 'rate' in var:
                moments.append(f"💡 Interest rates are influenced by Federal Reserve policy, inflation, and economic growth.")

        return list(set(moments))[:3]  # Return up to 3 unique learning moments

    def setup_schedule(self):
        """Setup scheduled tasks"""
        cfg = self.config['update_schedules']

        if cfg['monthly']['enabled']:
            schedule_time = cfg['monthly']['time']
            schedule.every().month.at(schedule_time).do(self.run_monthly_update)
            print(f"✓ Monthly updates scheduled for day {cfg['monthly']['day_of_month']} at {schedule_time}")

        if cfg['quarterly']['enabled']:
            schedule_time = cfg['quarterly']['time']
            # Note: This is simplified - actual implementation would check current month
            schedule.every().month.at(schedule_time).do(self.check_quarterly_update)
            print(f"✓ Quarterly updates scheduled for months {cfg['quarterly']['months']} at {schedule_time}")

        if cfg['annual']['enabled']:
            schedule_time = cfg['annual']['time']
            schedule.every().month.at(schedule_time).do(self.check_annual_update)
            print(f"✓ Annual updates scheduled for month {cfg['annual']['month']} at {schedule_time}")

    def check_quarterly_update(self):
        """Check if quarterly update should run this month"""
        current_month = datetime.now().month
        if current_month in self.config['update_schedules']['quarterly']['months']:
            self.run_quarterly_update()

    def check_annual_update(self):
        """Check if annual update should run this month"""
        current_month = datetime.now().month
        if current_month == self.config['update_schedules']['annual']['month']:
            self.run_annual_update()

    def run(self):
        """Main run loop"""
        print("\n" + "="*60)
        print("PFL ACADEMY STATE DATA UPDATER")
        print("="*60)
        print(f"\nMonitoring {len(self.get_enabled_states())} states")
        print(f"Current version: {self.current_version}\n")

        self.setup_schedule()

        print("\n🚀 Scheduler running... (Press Ctrl+C to exit)\n")

        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='PFL Academy State Data Updater')
    parser.add_argument('--run-now', choices=['monthly', 'quarterly', 'annual'],
                       help='Run update immediately instead of scheduling')
    parser.add_argument('--state', help='Update specific state only')
    parser.add_argument('--test', action='store_true', help='Test mode - no changes saved')

    args = parser.parse_args()

    updater = StateDataUpdater(test_mode=args.test)

    if args.run_now:
        if args.run_now == 'monthly':
            updater.run_monthly_update()
        elif args.run_now == 'quarterly':
            updater.run_quarterly_update()
        elif args.run_now == 'annual':
            updater.run_annual_update()
    else:
        updater.run()

    if updater.flagged:
        print(f"\n{'='*60}")
        print(f"⚠️  {len(updater.flagged)} field(s) written as {NEEDS_VERIFICATION}")
        print("These could NOT be sourced. A human must supply and verify each")
        print("value before this data is merged or served.")
        print(f"{'='*60}")
        for f in updater.flagged[:20]:
            print(f"  {f['state']:<18} {f['variable']:<28} query: {f['query']}")
        if len(updater.flagged) > 20:
            print(f"  … and {len(updater.flagged) - 20} more")


if __name__ == '__main__':
    main()
