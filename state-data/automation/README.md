# PFL Academy State Data Automation System

Fully automated system for updating state-specific curriculum variables using AI-powered web search.

## Overview

This system automatically:
- ✅ Searches the web for current state data (gas prices, tax rates, wages, etc.)
- ✅ Extracts and validates values
- ✅ Updates state JSON files
- ✅ Creates version snapshots
- ✅ Notifies teachers of changes with learning moments
- ✅ Protects student work with data versioning

## Quick Start

### 1. Install Dependencies

```bash
cd state-data/automation
pip install -r requirements.txt
```

### 2. Set Environment Variable

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 3. Run Updates

**Run immediately:**
```bash
# Monthly update (5 variables)
python state_data_updater.py --run-now monthly

# Quarterly update (11 variables)
python state_data_updater.py --run-now quarterly

# Annual update (48 variables)
python state_data_updater.py --run-now annual
```

**Run on schedule:**
```bash
# Start scheduler (runs in background)
python state_data_updater.py
```

## Update Schedule

### Monthly Updates (1st of each month, 2:00 AM)
Updates 5 volatile variables:
- Gas prices
- Auto loan rates (new/used)
- Mortgage rates
- Unemployment rates

**Estimated runtime:** 15-20 minutes per state (36 states = ~6-12 hours total)

### Quarterly Updates (Jan/Apr/Jul/Oct, 1st, 3:00 AM)
Updates 11 variables (monthly + quarterly):
- Median home prices
- Median rent
- Teen insurance rates
- Bank fees

**Estimated runtime:** 20-30 minutes per state (36 states = ~12-18 hours total)

### Annual Updates (September 1st, 4:00 AM)
Updates 48 variables (all automated variables):
- Public university tuition
- Minimum wage
- Sales tax rates
- DMV registration fees
- And 44 more...

**Estimated runtime:** 2-3 hours per state (36 states = ~72-108 hours total)

## Configuration

Edit `config.json` to customize:

### Enable/Disable States
```json
{
  "enabled_states": ["AL", "AK", "AZ", ...],
  "total_states": 36
}
```

### Adjust Update Schedule
```json
{
  "update_schedules": {
    "monthly": {
      "enabled": true,
      "day_of_month": 1,
      "time": "02:00"
    }
  }
}
```

### Change Update Frequency
Want bi-monthly instead of monthly? Edit config:
```json
{
  "monthly": {
    "enabled": false
  },
  "bi_monthly": {
    "enabled": true,
    "months": [1, 3, 5, 7, 9, 11]
  }
}
```

## Data Versioning

Every update creates a new version tag (e.g., `2025-Q4`).

**Student work protection:**
- Student submits assignment on Oct 15, 2025 → Locked to `2025-Q4` data
- Jan 1, 2026: Data updates to `2026-Q1`
- Student's Oct work remains graded against `2025-Q4` data (stays correct)
- New assignments use `2026-Q1` data

**Version files:**
```
backups/
  2025-Q4/
    texas.json
    california.json
    ...
  2026-Q1/
    texas.json
    ...
```

## Teacher Notifications

Every update generates notifications with:

1. **What Changed**
   ```
   📊 Data Update Alert for TX

   5 variable(s) updated in the monthly update (2026-Q1):
   gas price current, avg auto loan rate new, avg mortgage rate 30yr

   Student work submitted before this update remains graded
   against previous data.
   ```

2. **Learning Moments**
   ```
   💡 Gas prices fluctuate due to crude oil costs, refining
   capacity, supply/demand, and geopolitical events.

   💡 Interest rates are influenced by Federal Reserve policy,
   inflation, and economic growth.
   ```

3. **Detailed Changelog**
   - Old value → New value
   - Percent change
   - Timestamp

**Notification files:**
```
notifications/
  2026-Q1_monthly.json
  2026-Q1_quarterly.json
  2026-Q1_annual.json
```

## How It Works

### Variable Categories

**MONTHLY** (5 vars) - Most volatile:
- `gas_price_current`
- `avg_auto_loan_rate_new`
- `avg_auto_loan_rate_used`
- `avg_mortgage_rate_30yr`
- `unemployment_rate`

**QUARTERLY** (6 vars) - Moderately changing:
- `median_home_price`
- `median_rent`
- `insurance_avg_teen`
- `avg_monthly_fee`
- `avg_overdraft_fee`
- `housing_market_trends`

**ANNUALLY** (26 vars) - Changes once per year:
- `tuition_public`
- `min_wage`
- `sales_tax`
- `registration_initial`
- `registration_annual`
- And 21 more...

**AS_NEEDED** (44 vars) - Rarely changes:
- URLs, agency names, local examples
- Updated manually when needed

**SPECIAL_HANDLING** (22 vars) - Complex data:
- Tax examples arrays
- Property tax tables
- Updated annually with special processing

### Web Search Process

For each variable:

1. **Generate search query**
   ```
   "Texas average gas price November 2025"
   ```

2. **Claude searches web**
   - Finds official sources (government sites, BLS, Fed Reserve)
   - Extracts numeric value
   - Validates format

3. **Extract clean value**
   ```
   "$2.89/gallon" → 2.89
   "6.25%" → 6.25
   ```

4. **Validate change**
   - Check if > 10% different (configurable)
   - Alert if large change
   - Optionally require manual approval

5. **Update state file**
   - Backup old version
   - Save new value
   - Update `last_updated` timestamp

## Validation & Safety

### Pre-Update Validation
- Checks all state files exist
- Validates JSON structure
- Verifies API connectivity

### Post-Update Validation
- Runs validation script on all updated states
- Checks value ranges
- Ensures no placeholder text
- Verifies data types

### Auto-Rollback
If validation fails:
```python
{
  "validation": {
    "auto_rollback_on_failure": true
  }
}
```
System automatically restores from backup.

### Large Change Alerts
```python
{
  "validation": {
    "alert_on_large_changes": true,
    "large_change_threshold_percent": 10
  }
}
```

If gas price changes > 10%, system alerts:
```
⚠️  WARNING: Large change detected for gas_price_current: 15.2%
Texas: $2.89 → $3.33

This seems unusual. Approve? (y/n)
```

## Manual Override

### Update Specific State
```bash
python state_data_updater.py --state TX --run-now monthly
```

### Update Specific Variable
Edit the state JSON file directly, then run validation:
```bash
cd ../validation
node validate.js texas
```

### Skip Auto-Update for Variable
In `config.json`:
```json
{
  "skip_variables": ["gas_price_current"]
}
```

## Logs

All updates logged to:
```
logs/
  updates.log
```

Example log entry:
```
2026-01-01 02:15:32 [INFO] Monthly update started (2026-Q1)
2026-01-01 02:16:45 [INFO] Processing TX...
2026-01-01 02:16:52 [INFO]   Updated gas_price_current: 2.89 → 2.95
2026-01-01 02:17:10 [INFO]   Updated unemployment_rate: 4.1 → 3.9
2026-01-01 02:17:25 [INFO]   ✓ Saved 2 changes for TX
...
2026-01-01 08:32:18 [INFO] Monthly update complete - 89 total changes
```

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
Set environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or add to `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### Web search returns "NOT_FOUND"
- Source website may have changed
- Data may not be publicly available
- Try manual update for that variable

### Updates taking too long
- Reduce `max_tokens` in config (default: 4000)
- Increase `temperature` slightly for faster responses
- Update fewer states at once

### False "large change" alerts
- Adjust `large_change_threshold_percent` in config
- Set `require_manual_approval: false` for auto-approval

## Cost Estimates

**Using Anthropic Claude:**
- ~100 tokens per variable search
- ~500 tokens per state
- ~18,000 tokens per monthly update (all 36 states)
- **~$0.27 per monthly update** (at $0.015/1K tokens)

**Annual costs:**
- Monthly updates: 12 × $0.27 = $3.24/year
- Quarterly updates: 4 × $0.54 = $2.16/year
- Annual update: 1 × $16.20 = $16.20/year
- **Total: ~$22/year**

Extremely cost-effective for automated data updates!

## Production Deployment

### Option 1: Dedicated Server
```bash
# Install on Ubuntu server
sudo apt install python3 python3-pip
pip3 install -r requirements.txt

# Run as systemd service
sudo cp pfl-updater.service /etc/systemd/system/
sudo systemctl enable pfl-updater
sudo systemctl start pfl-updater
```

### Option 2: Cloud Function (AWS Lambda / Google Cloud)
- Upload as serverless function
- Trigger via CloudWatch Events / Cloud Scheduler
- Extremely cost-effective (<$1/month)

### Option 3: GitHub Actions
```yaml
# .github/workflows/update-state-data.yml
name: Update State Data
on:
  schedule:
    - cron: '0 2 1 * *'  # 1st of month, 2 AM
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: python state_data_updater.py --run-now monthly
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Integration with Platform

Sebastian's team should:

1. **Load data version with student submission**
   ```javascript
   {
     student_id: "12345",
     chapter_id: "L-46",
     submitted_at: "2025-10-15",
     data_version: "2025-Q4",  // ← Lock to version
     answers: {...}
   }
   ```

2. **Grade against historical data**
   ```javascript
   const studentVersion = submission.data_version; // "2025-Q4"
   const stateData = loadStateData('TX', studentVersion);
   // Use 2025-Q4 data for grading, not current data
   ```

3. **Show notifications to teachers**
   ```javascript
   const notifications = loadNotifications(currentVersion);
   // Display in teacher dashboard
   ```

## Future Enhancements

### Phase 2 (Recommended for 6 months out):
- Real-time API connections (Fed Reserve, BLS)
- Predictive analytics ("Gas prices likely to rise next month")
- Comparative state analysis ("TX vs CA on this metric")

### Phase 3 (12+ months):
- Machine learning for anomaly detection
- Automated fact-checking
- Student-facing "data changed" notifications

---

**Questions?** See main documentation in `../README.md` or validation guide in `../validation/README.md`

**Last Updated:** 2025-11-14
**Version:** 1.0.0
