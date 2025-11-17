# PFL Academy Automation Scripts

This directory contains automation scripts for managing PFL Academy assets and generating distribution-ready materials.

## Table of Contents

1. [Variable-to-Asset Mapping Generator](#variable-to-asset-mapping-generator)
2. [PDF Generator](#pdf-generator)
3. [State Data Management](#state-data-management)

---

## Variable-to-Asset Mapping Generator

**Script:** `generate_variable_mapping.py`

### Purpose

Scans all chapter assets (HTML files and assets.md specifications) to extract state variable usage patterns and generate a comprehensive mapping of which variables are used by which assets.

### Usage

```bash
# Basic usage (scans content-complete directory)
python3 generate_variable_mapping.py

# Output
# - Console summary showing top 10 most used variables
# - JSON file: content-complete/variable_to_asset_mapping.json
```

### Output Structure

The generated `variable_to_asset_mapping.json` contains:

```json
{
  "generated_at": "/path/to/content-complete",
  "statistics": {
    "total_variables": 49,
    "total_assets": 16,
    "total_chapters": 27
  },
  "most_used_variables": {
    "STATE_NAME": {
      "chapters": ["L-3-income-and-taxes", "L-6-federal-state-taxes", ...],
      "assets": ["L-46/Auto_Finance_Decision_Calculator", ...],
      "usage_count": 14
    }
  },
  "variable_to_assets": { ... },
  "asset_to_variables": { ... },
  "chapter_summaries": { ... }
}
```

### Use Cases

- **State Data Preparation**: Identify which variables need values for state-specific versions
- **Asset Dependencies**: Understand which assets require state data
- **Variable Auditing**: Find unused or inconsistent variable names
- **Documentation**: Generate reference material for template developers

---

## PDF Generator

**Script:** `pdf_generator.py`

### Purpose

Converts HTML assets to print-ready PDF files with optional state variable replacement. Creates distribution-ready materials for teachers.

### Requirements

```bash
# Install Playwright
pip install playwright

# Install Chromium browser
playwright install chromium
```

### Usage

#### Basic Conversion (No Variable Replacement)

```bash
# Convert all HTML assets to PDFs
python3 pdf_generator.py

# Convert specific chapters
python3 pdf_generator.py --chapters L-46 L-47 L-48

# Specify custom output directory
python3 pdf_generator.py --output-dir /path/to/pdfs
```

#### State-Specific Conversion (With Variable Replacement)

```bash
# Convert with Oklahoma state data
python3 pdf_generator.py --state-data sample_state_data.json --replace-vars

# Convert specific chapters with state data
python3 pdf_generator.py \
  --chapters L-46 L-47 \
  --state-data oklahoma_data.json \
  --replace-vars
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--base-path` | Path to content-complete directory | `content-complete` |
| `--output-dir` | Output directory for PDFs | `content-complete/pdf-output` |
| `--chapters` | Specific chapters to convert (space-separated) | All chapters |
| `--state-data` | Path to JSON file with state variable data | None |
| `--replace-vars` | Replace {{VARIABLE}} patterns with state data | False |

### Output

The script generates:

1. **PDF Files**: One PDF per HTML asset, organized by chapter
   ```
   pdf-output/
   ├── L-46-automobile-finance/
   │   ├── Auto_Finance_Decision_Calculator.pdf
   │   ├── Total_Cost_Ownership_Worksheet.pdf
   │   ├── Vehicle_Financing_Decision_Matrix.pdf
   │   └── State_Cost_Reference_Sheet.pdf
   ├── L-47-introduction-to-investment-types/
   │   ├── Investment_Type_Comparison_Tool.pdf
   │   └── ...
   └── conversion_log.json
   ```

2. **Conversion Log**: `conversion_log.json` with detailed success/error information

### PDF Features

- **Letter size** (8.5" x 11") format
- **0.5-inch margins** on all sides
- **Print backgrounds** enabled (preserves colors and styling)
- **Self-contained** (no external dependencies)
- **High fidelity** (matches HTML appearance)

### Example Workflow: Creating State-Specific Asset Bundles

```bash
# 1. Generate variable mapping to see what data is needed
python3 generate_variable_mapping.py

# 2. Create state data JSON files for each target state
# (Edit sample_state_data.json with actual state values)
cp sample_state_data.json texas_data.json
# Edit texas_data.json...

# 3. Generate Oklahoma-specific PDFs
python3 pdf_generator.py \
  --state-data sample_state_data.json \
  --replace-vars \
  --output-dir pdf-output/oklahoma

# 4. Generate Texas-specific PDFs
python3 pdf_generator.py \
  --state-data texas_data.json \
  --replace-vars \
  --output-dir pdf-output/texas

# 5. Create ZIP archives for distribution
cd pdf-output/oklahoma
zip -r oklahoma-pfl-assets.zip L-*
cd ../texas
zip -r texas-pfl-assets.zip L-*
```

---

## State Data Management

### Creating State Data Files

State data files are JSON files containing values for all state-specific variables used in assets.

**Template:** `sample_state_data.json`

### Required Variables by Asset Type

#### Auto Finance Assets (L-46, L-30)
- `STATE_SALES_TAX`
- `STATE_REGISTRATION_INITIAL`
- `STATE_REGISTRATION_ANNUAL`
- `STATE_AVG_AUTO_LOAN_RATE_NEW`
- `STATE_AVG_AUTO_LOAN_RATE_USED`
- `STATE_INSURANCE_AVG_TEEN`
- `STATE_GAS_PRICE_CURRENT`
- `STATE_INSPECTION_REQUIRED` (boolean)
- `STATE_INSPECTION_COST`
- `STATE_DMV_URL`

#### Tax-Related Assets (L-3, L-6)
- `STATE_INCOME_TAX_RATE`
- `STATE_SALES_TAX`
- `STATE_PROPERTY_TAX_RATE`

#### Housing Assets (L-30)
- `STATE_AVERAGE_HOME_PRICE`
- `STATE_AVERAGE_RENT_1BR`
- `STATE_AVERAGE_RENT_2BR`
- `STATE_RENTER_PERCENTAGE`
- `STATE_HOMEOWNER_PERCENTAGE`

#### Common Variables
- `STATE_NAME`
- `STATE_CODE`
- `STATE_CAPITAL`
- `STATE_POPULATION`
- `STATE_MEDIAN_HOUSEHOLD_INCOME`
- `STATE_UNEMPLOYMENT_RATE`
- `STATE_MINIMUM_WAGE`

### State Data Sources

Recommended sources for accurate state data:

1. **Tax Rates**: State Department of Revenue websites
2. **Auto Insurance**: Insurance.com, NerdWallet state averages
3. **Gas Prices**: AAA Gas Prices, EIA.gov
4. **Housing Prices**: Zillow, Realtor.com market reports
5. **Auto Loan Rates**: Bankrate.com, local credit unions
6. **Registration Fees**: State DMV/BMV websites
7. **Economic Data**: Bureau of Labor Statistics, Census Bureau

### Variable Naming Conventions

- **All uppercase** with underscores: `STATE_VARIABLE_NAME`
- **Prefix**: All state-specific variables start with `STATE_`
- **Boolean values**: Use `true`/`false` (lowercase)
- **Currency**: Numeric string without $ or commas: `"245.00"`
- **Percentages**: Numeric string without % symbol: `"4.5"`
- **URLs**: Full URL with protocol: `"https://example.com/"`

---

## Troubleshooting

### Variable Mapping Issues

**Problem**: Variables not being detected
- **Solution**: Ensure variables use exact pattern `{{VARIABLE_NAME}}` (double curly braces, all caps)

**Problem**: Incorrect counts in mapping
- **Solution**: Clear any cached files and re-run the script

### PDF Generation Issues

**Problem**: `playwright` not found
```bash
pip install playwright
playwright install chromium
```

**Problem**: PDFs missing styling
- **Solution**: Ensure `print_background=True` in PDF generation settings (already set in script)

**Problem**: Variables not replaced in PDFs
- **Solution**: Verify you're using `--replace-vars` flag and `--state-data` points to valid JSON

**Problem**: PDF conversion timeout
- **Solution**: Increase `page.wait_for_timeout()` value in script (default: 1000ms)

---

## Advanced Usage

### Batch Processing Multiple States

Create a shell script to generate PDFs for all 50 states:

```bash
#!/bin/bash
# generate_all_states.sh

STATES=(
  "alabama"
  "alaska"
  # ... add all states
)

for state in "${STATES[@]}"; do
  echo "Processing $state..."
  python3 pdf_generator.py \
    --state-data "state-data/${state}_data.json" \
    --replace-vars \
    --output-dir "pdf-output/${state}"
done

echo "All states processed!"
```

### Integration with Supabase Storage

Upload generated PDFs to Supabase storage buckets:

```python
from supabase import create_client
import os

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_pdfs(local_dir, bucket_name, state_code):
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            if file.endswith('.pdf'):
                file_path = os.path.join(root, file)
                storage_path = f"{state_code}/{os.path.basename(root)}/{file}"

                with open(file_path, 'rb') as f:
                    supabase.storage.from_(bucket_name).upload(
                        storage_path,
                        f.read()
                    )

upload_pdfs('pdf-output/oklahoma', 'asset-pdfs', 'OK')
```

---

## Maintenance

### Updating Scripts

When adding new state variables:

1. Update assets.md files with new `{{VARIABLE}}` patterns
2. Update HTML templates with new variables
3. Run `generate_variable_mapping.py` to regenerate mapping
4. Update `sample_state_data.json` with new variable defaults
5. Update this README with variable documentation

### Testing New Assets

Before bulk PDF generation:

```bash
# Test single chapter first
python3 pdf_generator.py --chapters L-46

# Verify PDF quality and styling
# Then run full conversion
```

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the conversion_log.json for error details
3. Verify HTML files open correctly in browser before PDF conversion
4. Ensure state data JSON is valid (use `python -m json.tool state_data.json`)

---

## Script Versions

- `generate_variable_mapping.py` - v1.0 (2025-03-26)
- `pdf_generator.py` - v1.0 (2025-03-26)

Last updated: 2025-03-26
