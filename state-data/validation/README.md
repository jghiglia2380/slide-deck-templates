# State Data Validation

Automated validation system for PFL Academy state JSON files.

## Quick Start

```bash
# Validate all states
node validate.js

# Validate a specific state
node validate.js texas

# Include URL accessibility checks (slower)
node validate.js --check-urls

# Validate specific state with URL checks
node validate.js california --check-urls
```

## What It Checks

### ✅ Automated Validation

1. **Structure**
   - JSON parses correctly
   - Root is an object
   - No syntax errors

2. **Required Fields**
   - All 12 top-level sections present:
     - `state_name`, `state_code`, `last_updated`
     - `data_sources`, `automotive`, `taxes`
     - `housing`, `employment`, `education`
     - `banking`, `consumer_protection`, `local_examples`

3. **Data Types**
   - `state_code` is 2 uppercase letters (e.g., "TX", "CA")
   - `last_updated` is in YYYY-MM-DD format
   - Numeric fields are numbers (not strings)
   - Required data type validation for all 86+ variables

4. **Value Ranges**
   - Reasonable ranges for all numeric values
   - Example checks:
     - Sales tax: 0-15%
     - Median home price: $50,000-$5,000,000
     - Minimum wage: $5-$25
     - Gas price: $1-$10/gallon

5. **Placeholder Detection**
   - Flags text containing: "FILL_IN", "TODO", "TBD", "PLACEHOLDER"
   - Detects bracketed placeholders: `[City Name]`, `[Insert Here]`
   - Ensures all data is real, not placeholder content

6. **Data Freshness**
   - Checks `last_updated` is within 12 months
   - Warns if data is stale

7. **URL Accessibility** (optional, use `--check-urls`)
   - Verifies all URLs in `data_sources` are accessible
   - Makes HEAD requests to check HTTP status
   - Reports broken links

## Understanding Results

### Pass Rate
- **100%**: All states valid, ready for production
- **< 100%**: Some states have errors and need fixes

### Error Types

**🔴 Errors** (must fix):
- Missing required fields
- Invalid data types
- Values out of reasonable ranges
- Placeholder text detected
- JSON parsing errors

**🟡 Warnings** (informational):
- Data older than 12 months (needs update)
- Values at edges of typical ranges (unusual but valid)
- Inaccessible URLs (may be temporary)

### Example Output

```
PFL Academy State Data Validation

Validating 4 state(s)...

━━━ TEXAS ━━━
✓ VALID

Warnings:
  ⚠ taxes.assessment_percentage unusual value: 100 (typical range: 0-100)

━━━ CALIFORNIA ━━━
✓ VALID

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validation Summary

Total States:   4
Valid:          4
Invalid:        0
Errors:         0
Warnings:       2

Pass Rate:      100.0%

✓ All states passed validation!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Results File

After validation, results are saved to `validation-results.json`:

```json
{
  "totalStates": 4,
  "validStates": 4,
  "invalidStates": 0,
  "warnings": 2,
  "errors": 0,
  "stateResults": {
    "texas": {
      "file": "texas.json",
      "valid": true,
      "errors": [],
      "warnings": ["..."],
      "checks": {
        "structure": true,
        "required_fields": true,
        "data_types": true,
        "value_ranges": true,
        "placeholders": true,
        "data_freshness": true,
        "urls": false
      }
    }
  }
}
```

## Common Validation Failures

### Missing Required Field
```
Error: Missing required fields: employment, education
```
**Fix**: Add the missing sections to the JSON file

### Invalid State Code
```
Error: state_code must be 2 uppercase letters (got: tx)
```
**Fix**: Change `"state_code": "tx"` to `"state_code": "TX"`

### Value Out of Range
```
Error: taxes.sales_tax out of range: 25 (expected 0-15)
```
**Fix**: Verify the value - if correct, this may indicate a schema update is needed

### Placeholder Text Detected
```
Error: Found placeholder text: local_examples.major_city: "[Insert Major City]"
```
**Fix**: Replace placeholder with real city name

### Stale Data Warning
```
Warning: Data is 400 days old (last updated: 2023-10-01)
```
**Fix**: Update the data and change `last_updated` to current date

## Integration with Workflow

### Before Committing New States
```bash
# 1. Create/update state file
# 2. Validate
node validate.js new-york

# 3. If valid, commit
git add states/new-york.json
git commit -m "Add New York state data"
```

### Pre-Push Hook (Recommended)
Add to `.git/hooks/pre-push`:

```bash
#!/bin/bash
cd state-data/validation
node validate.js

if [ $? -ne 0 ]; then
  echo "❌ State validation failed. Fix errors before pushing."
  exit 1
fi
```

### Continuous Integration
Run validation in CI pipeline to ensure all states remain valid:

```yaml
# .github/workflows/validate-states.yml
name: Validate State Data
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: cd state-data/validation && node validate.js
```

## Validation Rules Reference

### Required Top-Level Fields
- `state_name` (string)
- `state_code` (string, 2 uppercase letters)
- `last_updated` (string, YYYY-MM-DD format)
- `data_sources` (object)
- `automotive` (object)
- `taxes` (object)
- `housing` (object)
- `employment` (object)
- `education` (object)
- `banking` (object)
- `consumer_protection` (object)
- `local_examples` (object)

### Numeric Range Limits

| Field | Minimum | Maximum | Unit |
|-------|---------|---------|------|
| `registration_initial` | 0 | 1000 | dollars |
| `registration_annual` | 0 | 500 | dollars |
| `avg_auto_loan_rate_new` | 0 | 30 | percent |
| `insurance_avg_teen` | 50 | 1000 | dollars/month |
| `gas_price_current` | 1 | 10 | dollars/gallon |
| `sales_tax` | 0 | 15 | percent |
| `median_home_price` | 50000 | 5000000 | dollars |
| `median_rent` | 300 | 10000 | dollars/month |
| `min_wage` | 5 | 25 | dollars/hour |
| `unemployment_rate` | 0 | 20 | percent |
| `tuition_public` | 1000 | 50000 | dollars/year |

*Full range list available in `validate.js` source code*

### Data Freshness
- **Maximum Age**: 365 days
- **Recommended Update**: Annually (September 1st)
- **Critical Fields**: Update more frequently
  - `gas_price_current` (quarterly)
  - `avg_mortgage_rate_30yr` (quarterly)
  - `unemployment_rate` (quarterly)

## Extending Validation

### Adding New Checks

Edit `validate.js` and add to the `VALIDATION_RULES` object:

```javascript
VALIDATION_RULES: {
  // Add new required field
  REQUIRED_FIELDS: [
    ...existing,
    'new_section'
  ],

  // Add new range check
  RANGES: {
    ...existing,
    new_field: { min: 0, max: 100 }
  }
}
```

### Custom Validation Functions

Add custom validation methods to the `StateValidator` class:

```javascript
class StateValidator {
  // ... existing methods

  checkCustomRule(data, result) {
    // Your custom validation logic
    if (someCondition) {
      result.errors.push('Custom error message');
    }
  }
}
```

Then call it in the `validateStateFile` method.

## Troubleshooting

### Script Won't Run
```
Error: Cannot find module 'fs'
```
**Fix**: Ensure you're using Node.js 12+

### Permission Denied
```
Error: EACCES: permission denied
```
**Fix**: Run `chmod +x validate.js`

### Validation Takes Too Long
- Don't use `--check-urls` flag for quick validation
- URL checks make HEAD requests to all data source URLs
- Use URL checks only for deep validation before major releases

## Advanced Usage

### Programmatic Use

```javascript
const StateValidator = require('./validate.js');

const validator = new StateValidator({ checkUrls: false });
await validator.validate('texas');

console.log(validator.results);
```

### Batch Validation of New States

```bash
# Validate only recently added states
for state in new-york pennsylvania ohio; do
  node validate.js $state
done
```

### Integration with State Data Builder

```bash
# Build state data and validate in one step
npm run build-state texas && node validation/validate.js texas
```

## Support

For validation issues:
1. Check this README for common errors
2. Review `validation-results.json` for detailed diagnostics
3. Consult `../schema.json` for field requirements
4. See `../README.md` for data source guidelines

---

**Last Updated**: 2025-11-14
**Version**: 1.0.0
**Maintainer**: PFL Academy Development Team
