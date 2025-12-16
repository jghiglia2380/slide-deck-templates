# PFL Academy Slide Deck Generator

## Overview

This system generates state-customized HTML slide decks for PFL Academy curriculum. It combines a master template, chapter content JSON files, and state-specific variables to produce ready-to-use presentation materials for all 36 states.

### Key Features
- **Template-based generation**: Single HTML template with consistent styling
- **State customization**: Automatic variable interpolation for state-specific data
- **Chapter mapping**: Maps L-chapters to state curriculum IDs
- **11 layout patterns**: Objectives, vocab, comparison, scenario, paycheck, and more
- **CLI interface**: Simple command-line tool for generation and validation

---

## Quick Start

### Prerequisites
- Node.js v16+ installed
- Access to the following directories:
  - `/state-data/states/` - State variable JSON files
  - `/Simple-Data-Files-Updated/` - Chapter mapping files

### Installation

```bash
cd slide-deck-templates
npm install  # If you have package.json dependencies
```

### Basic Usage

**Generate slides for a specific state and chapter:**
```bash
node generate-slide-decks.js --state=oklahoma --chapter=L-03
```

**List all available states:**
```bash
node generate-slide-decks.js --list-states
```

**List all available chapters:**
```bash
node generate-slide-decks.js --list-chapters
```

**Validate a content JSON file:**
```bash
node generate-slide-decks.js --validate slide-content/L-03.json
```

### Output Location
Generated files are saved to:
```
output/{state}/chapter-{X.X}-slides.html
```

Example: `output/oklahoma/chapter-03-slides.html`

---

## System Architecture

### File Structure

```
slide-deck-templates/
├── slide-template.html          # Master HTML template
├── generate-slide-decks.js      # Generator script
├── slide-content/               # Chapter content JSON files
│   ├── L-01.json               # Jobs vs. Careers (no state vars)
│   ├── L-03.json               # Income and Taxes (with state vars)
│   └── L-XX.json               # Future chapters...
├── output/                      # Generated slide decks
│   ├── oklahoma/
│   │   ├── chapter-01-slides.html
│   │   └── chapter-03-slides.html
│   ├── california/
│   └── ...
└── README.md                    # This file
```

### External Dependencies

**State Data:**
- Location: `../state-data/states/{state}.json`
- Contains 86 variables per state (tax rates, min wage, costs, etc.)
- Example: `oklahoma.json`, `california.json`

**Chapter Mappings:**
- Location: `../Simple-Data-Files-Updated/{State}-simple-data.md`
- Maps L-chapters to state curriculum IDs
- Format: Markdown tables with L-chapter → state chapter mapping

---

## Content JSON Schema

### Structure Overview

```json
{
  "metadata": {
    "lChapter": "L-03",
    "title": "Income and Taxes",
    "subtitle": "Understanding What Happens to Your Paycheck",
    "totalSlides": 20,
    "hasStateVariables": true,
    "stateVariablesUsed": [
      "STATE_NAME",
      "INCOME_TAX_RATE",
      "LOCAL_INCOME_TAX",
      "SDI_RATE"
    ]
  },
  "slides": [
    {
      "number": 1,
      "type": "title",
      "headerColor": "purple",
      "content": {
        "headerTitle": "Income and Taxes",
        "layout": "title-layout",
        "layoutData": {
          "mainTitle": "Income and Taxes",
          "subtitle": "Understanding What Happens to Your Paycheck"
        }
      }
    }
  ]
}
```

### Metadata Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lChapter` | string | Yes | L-chapter identifier (e.g., "L-01", "L-03") |
| `title` | string | Yes | Chapter title |
| `subtitle` | string | Yes | Chapter subtitle |
| `totalSlides` | number | Yes | Total number of slides |
| `hasStateVariables` | boolean | Yes | Whether chapter uses state-specific data |
| `stateVariablesUsed` | array | Conditional | List of state variables used (required if hasStateVariables is true) |

### Slide Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | number | Yes | Slide number (1-based) |
| `type` | string | Yes | Slide type: `title`, `hook`, `content`, `discussion`, `closing` |
| `headerColor` | string | Yes | Header color: `purple`, `teal`, `blue`, `amber`, `rose` |
| `content` | object | Yes | Content container |
| `content.headerTitle` | string | Yes | Text for slide header |
| `content.layout` | string | Yes | Layout type (see Layout Types section) |
| `content.layoutData` | object | Yes | Layout-specific data |

---

## Layout Types

The system supports 11 distinct layout patterns:

### 1. objectives-expanded
**Purpose:** Display learning objectives
**layoutData structure:**
```json
{
  "objectives": [
    {
      "number": 1,
      "verb": "Differentiate",
      "description": "Distinguish between a job and a career..."
    }
  ]
}
```

### 2. vocab-container
**Purpose:** Vocabulary terms and definitions
**layoutData structure:**
```json
{
  "terms": [
    {
      "term": "Gross Income",
      "definition": "Total earnings before deductions"
    }
  ]
}
```

### 3. comparison-grid
**Purpose:** Side-by-side comparisons
**layoutData structure:**
```json
{
  "columns": [
    {
      "header": "Jobs",
      "items": ["Short-term", "Limited growth", "Hourly pay"]
    },
    {
      "header": "Careers",
      "items": ["Long-term", "Advancement opportunities", "Salary"]
    }
  ]
}
```

### 4. scenario-layout
**Purpose:** Case studies and examples
**layoutData structure:**
```json
{
  "title": "Meet Jordan Rivers",
  "description": "Jordan just started a new job...",
  "highlightBox": {
    "icon": "💡",
    "text": "In {{STATE_NAME}}, state income tax is <strong>{{INCOME_TAX_RATE}}%</strong>"
  }
}
```

### 5. takeaway-grid
**Purpose:** Key points with icons
**layoutData structure:**
```json
{
  "takeaways": [
    {
      "icon": "💰",
      "text": "Gross income is before deductions"
    }
  ]
}
```

### 6. paycheck-breakdown
**Purpose:** Line-by-line paycheck deductions
**layoutData structure:**
```json
{
  "lines": [
    {
      "label": "Gross Pay",
      "amount": "$4,000.00",
      "type": "gross"
    },
    {
      "label": "{{STATE_NAME}} State Tax ({{INCOME_TAX_RATE}}%)",
      "amount": "{{CALCULATED_STATE_TAX_MONTHLY}}",
      "type": "deduction",
      "isStateVariable": true
    },
    {
      "label": "Net Pay",
      "amount": "$3,200.00",
      "type": "net"
    }
  ]
}
```

### 7. balanced-layout
**Purpose:** Equal-width columns
**layoutData structure:**
```json
{
  "leftContent": "Content for left side",
  "rightContent": "Content for right side"
}
```

### 8. activity-layout
**Purpose:** Student activities and exercises
**layoutData structure:**
```json
{
  "activityTitle": "Career Comparison Exercise",
  "instructions": "Compare two career paths...",
  "timeEstimate": "15 minutes"
}
```

### 9. check-grid
**Purpose:** Checklists and validation items
**layoutData structure:**
```json
{
  "items": [
    "✓ Review your W-4 form",
    "✓ Calculate withholdings",
    "✓ Adjust as needed"
  ]
}
```

### 10. three-column
**Purpose:** Three-part information
**layoutData structure:**
```json
{
  "columns": [
    {"title": "Short-term", "content": "..."},
    {"title": "Mid-term", "content": "..."},
    {"title": "Long-term", "content": "..."}
  ]
}
```

### 11. bullet-list-full
**Purpose:** Simple bulleted lists
**layoutData structure:**
```json
{
  "items": [
    "First point",
    "Second point",
    "Third point"
  ]
}
```

---

## State Variables

### Variable Interpolation

State variables use the `{{VARIABLE_NAME}}` syntax and are automatically replaced during generation.

**Example:**
```json
"text": "In {{STATE_NAME}}, the minimum wage is {{MIN_WAGE}}"
```

Becomes:
```
In Oklahoma, the minimum wage is $7.25
```

### Common State Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `STATE_NAME` | string | Full state name | "Oklahoma" |
| `INCOME_TAX_RATE` | number | State income tax rate (%) | 5.0 |
| `SALES_TAX` | number | Sales tax rate (%) | 4.5 |
| `MIN_WAGE` | number | Hourly minimum wage | 7.25 |
| `LOCAL_INCOME_TAX` | number | Local income tax (%) | 0 |
| `SDI_RATE` | number | State disability insurance (%) | 0 |
| `PROPERTY_TAX_RATE` | number | Property tax rate (%) | 0.87 |
| `AVG_RENT_1BR` | number | Average 1BR rent | 750 |

**See `/state-data/VARIABLE_CATEGORIES.json` for complete list of 86 variables.**

### Calculated Fields

The generator automatically computes derived values:

| Calculated Field | Formula | Example |
|-----------------|---------|---------|
| `CALCULATED_STATE_TAX_MONTHLY` | Base salary × (INCOME_TAX_RATE / 100) | $4,000 × 5% = $200.00 |
| `CALCULATED_LOCAL_TAX_MONTHLY` | Base salary × (LOCAL_INCOME_TAX / 100) | $4,000 × 1% = $40.00 |
| `CALCULATED_SDI_MONTHLY` | Base salary × (SDI_RATE / 100) | $4,000 × 1.2% = $48.00 |
| `CALCULATED_TOTAL_STATE_DEDUCTIONS` | Sum of all state-level deductions | $200 + $40 + $48 = $288.00 |

**Note:** Base salary defaults to $4,000/month but can be customized.

---

## Creating New Content Files

### Step-by-Step Process

#### 1. Start with the Template
Copy an existing file to use as a starting point:
```bash
cp slide-content/L-01.json slide-content/L-14.json
```

#### 2. Update Metadata
```json
{
  "metadata": {
    "lChapter": "L-14",
    "title": "Your Chapter Title",
    "subtitle": "Your Chapter Subtitle",
    "totalSlides": 18,
    "hasStateVariables": false,  // Set to true if using state data
    "stateVariablesUsed": []     // Add variables if hasStateVariables is true
  }
}
```

#### 3. Build Your Slides
Each slide requires:
- Unique slide number (sequential)
- Slide type (title, hook, content, discussion, closing)
- Header color (purple, teal, blue, amber, rose)
- Content with appropriate layout

**Example:**
```json
{
  "number": 3,
  "type": "content",
  "headerColor": "teal",
  "content": {
    "headerTitle": "Learning Objectives",
    "layout": "objectives-expanded",
    "layoutData": {
      "objectives": [
        {
          "number": 1,
          "verb": "Explain",
          "description": "Describe the concept clearly"
        }
      ]
    }
  }
}
```

#### 4. Add State Variables (if needed)
Replace hard-coded state-specific data with variables:

**Before:**
```json
"text": "In Oklahoma, state income tax is 5%"
```

**After:**
```json
"text": "In {{STATE_NAME}}, state income tax is {{INCOME_TAX_RATE}}%"
```

Don't forget to update metadata:
```json
{
  "hasStateVariables": true,
  "stateVariablesUsed": ["STATE_NAME", "INCOME_TAX_RATE"]
}
```

#### 5. Validate Your Content
```bash
node generate-slide-decks.js --validate slide-content/L-14.json
```

Fix any errors or warnings reported.

#### 6. Test Generation
```bash
node generate-slide-decks.js --state=oklahoma --chapter=L-14
```

Open the generated HTML file to verify output:
```
output/oklahoma/chapter-14-slides.html
```

---

## Development Workflow

### For 67 Remaining Chapters

The current system has 2 complete chapters (L-01, L-03). To complete the remaining 67 chapters:

#### Phase 1: Content Creation (No State Variables)
**Estimate:** 35-40 chapters

For chapters that don't require state customization:
1. Create content JSON file
2. Set `hasStateVariables: false`
3. Build slides using appropriate layouts
4. Validate and test

**Recommended batch approach:**
- Standard 1 chapters: L-02, L-04, L-05 (Career Readiness)
- Standard 2 chapters: L-06, L-07, L-08 (Banking)
- Standard 3 chapters: L-09, L-10, L-11 (Saving & Investing)

#### Phase 2: Content with State Variables
**Estimate:** 29-34 chapters

For chapters requiring state customization:
1. Identify which state variables are needed
2. Replace hard-coded values with {{PLACEHOLDERS}}
3. Update metadata with stateVariablesUsed array
4. Test with 2-3 different states to verify interpolation

**Priority chapters with state variables:**
- L-06: Understanding Tax Filing Requirements
- L-14: Housing Decisions (rent, property tax)
- L-21: Auto Finance (sales tax, registration costs)
- L-28: Higher Education Costs (state tuition)

#### Phase 3: Quality Assurance
1. Validate all 69 JSON files
2. Generate sample output for 3-5 states
3. Visual review of layouts and styling
4. Cross-reference with original curriculum

---

## Troubleshooting

### Common Issues

#### Error: "Cannot read properties of undefined (reading 'split')"
**Cause:** Null or undefined value passed to interpolateVariables
**Fix:** Check that all layoutData fields are defined, or allow empty strings

#### Warning: "No mapping found for L-XX, using fallback"
**Cause:** Chapter mapping missing from state's simple-data.md file
**Impact:** Uses fallback chapter ID (L-XX → XX)
**Fix:** Add mapping to appropriate state file or update all state files

#### Error: "Error loading state data for {state}"
**Cause:** State JSON file not found
**Fix:** Verify state name matches filename (lowercase, hyphenated)
- Correct: `new-york.json`
- Incorrect: `newyork.json`, `New-York.json`

#### Error: "Missing metadata.lChapter"
**Cause:** Invalid or incomplete metadata in content JSON
**Fix:** Validate JSON file and ensure all required metadata fields are present

### Validation Warnings

The validator may report non-critical warnings:

**"Variable {{X}} used but not declared in stateVariablesUsed"**
- Usually indicates a calculated field (expected)
- Or a missing variable in the metadata array (fix required)

**"hasStateVariables is true but no {{PLACEHOLDERS}} found"**
- Content file claims to use state variables but has none
- Either add variables or set hasStateVariables to false

---

## CLI Reference

### Complete Command Syntax

```bash
node generate-slide-decks.js [options]
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--state=<name>` | State name (lowercase) | `--state=oklahoma` |
| `--chapter=<id>` | L-chapter ID | `--chapter=L-03` |
| `--list-states` | List all available states | - |
| `--list-chapters` | List all available chapters | - |
| `--validate <file>` | Validate content JSON file | `--validate slide-content/L-03.json` |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (validation failed, file not found, etc.) |

---

## CSS Design System

The `slide-template.html` file contains a comprehensive CSS design system with:

### Color Palette
```css
--primary: #4F46E5    /* Indigo (purple) */
--teal: #0D9488
--blue: #3B82F6
--amber: #F59E0B
--rose: #F43F5E
--green: #10B981
```

### Slide Type Classes
- `.slide-title` - Title slides
- `.slide-hook` - Hook/engagement slides
- `.slide-content` - Main content slides
- `.slide-discussion` - Discussion prompts
- `.slide-closing` - Closing/summary slides

### Header Colors
- `.slide-header.purple` - Default purple header
- `.slide-header.teal` - Teal header
- `.slide-header.blue` - Blue header
- `.slide-header.amber` - Amber/orange header
- `.slide-header.rose` - Rose/pink header

### Layout Classes
See "Layout Types" section for complete list of 11 layout patterns.

---

## Production Deployment

### Batch Generation Script

To generate all chapters for all states:

```bash
#!/bin/bash
# generate-all.sh

STATES=("alabama" "california" "oklahoma" "texas" "virginia")
CHAPTERS=("L-01" "L-03" "L-06" "L-14" "L-21")

for state in "${STATES[@]}"; do
  for chapter in "${CHAPTERS[@]}"; do
    echo "Generating $state - $chapter..."
    node generate-slide-decks.js --state=$state --chapter=$chapter
  done
done

echo "Complete! Generated $(ls -1 output/*/*.html | wc -l) files."
```

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Generate Slide Decks

on:
  push:
    paths:
      - 'slide-content/*.json'
      - 'state-data/states/*.json'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'

      - name: Generate all slides
        run: |
          cd slide-deck-templates
          node generate-slide-decks.js --state=oklahoma --chapter=L-01
          # Add more generation commands

      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: slide-decks
          path: slide-deck-templates/output/
```

---

## Performance Considerations

### Generation Speed
- **Single chapter:** ~100-200ms
- **State (69 chapters):** ~10-15 seconds
- **All states (36 × 69):** ~8-10 minutes

### File Sizes
- **Template:** ~65 KB (with all CSS)
- **Generated HTML:** ~25-35 KB per chapter
- **Total (all outputs):** ~60-90 MB

### Optimization Tips
1. **Parallel generation:** Use worker threads for multi-state generation
2. **Caching:** Cache loaded template and state data
3. **Minification:** Minify HTML output for production

---

## Roadmap

### Completed ✓
- [x] Master HTML template with CSS design system
- [x] Generator script with CLI interface
- [x] State variable interpolation
- [x] Chapter mapping integration
- [x] 11 layout types
- [x] Validation system
- [x] L-01 and L-03 proof-of-concept

### In Progress
- [ ] Complete remaining 67 chapters (L-02, L-04-L-69)
- [ ] Add chapter mappings to all state files
- [ ] Visual QA for all layouts

### Future Enhancements
- [ ] Interactive mode for content creation
- [ ] Automated screenshot generation
- [ ] PDF export functionality
- [ ] Speaker notes integration
- [ ] Accessibility improvements (WCAG 2.1 AA)
- [ ] Theme customization (bank branding)
- [ ] Multi-language support (Spanish translation)

---

## Support & Contact

### Documentation
- **Project Roadmap:** `SLIDE-DECK-PROJECT-ROADMAP.md`
- **State Variables:** `/state-data/VARIABLE_CATEGORIES.json`
- **Chapter Mappings:** `/Simple-Data-Files-Updated/{State}-simple-data.md`

### Getting Help
- Review this README and the roadmap document
- Check troubleshooting section above
- Validate your JSON files before reporting issues
- Test with a working chapter (L-01 or L-03) to isolate problems

### Contributing
When creating new chapters:
1. Follow the JSON schema structure
2. Use appropriate layout types
3. Validate before committing
4. Test generation with at least 2 states
5. Document any new layout patterns or variables

---

## License

Copyright 2025 PFL Academy. All rights reserved.

---

**Version:** 1.0
**Last Updated:** December 2025
**Status:** Production Ready
