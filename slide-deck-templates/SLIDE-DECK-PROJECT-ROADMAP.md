# Slide Deck Template System - Complete Project Specification

**Created:** December 4, 2025  
**Author:** Justin / Claude  
**Purpose:** Create a template system for generating consistent, state-customized slide decks  
**Deliverable:** GitHub repo for dev team to complete buildout

---

## TABLE OF CONTENTS

1. [Problem Statement](#problem-statement)
2. [Solution Overview](#solution-overview)
3. [Deliverables Checklist](#deliverables-checklist)
4. [Component Specifications](#component-specifications)
5. [JSON Content Schema](#json-content-schema)
6. [State Variable Reference](#state-variable-reference)
7. [Generator Script Specification](#generator-script-specification)
8. [Testing Requirements](#testing-requirements)
9. [Dev Team Instructions](#dev-team-instructions)

---

## PROBLEM STATEMENT

### Current Issues

1. **Inconsistent Templates:** ~50% of existing slide decks have broken formatting
   - L-01, L-02, L-03: Correct (purple gradient, proper logo, clean layout)
   - L-04 and many others: Broken (wrong logo, wrong colors, different structure)

2. **State-Specific Chapter Numbering:** Same L-chapter maps to different chapter IDs per state
   - L-14 (Saving Basics) = Oklahoma 5.1, Colorado 3.2, Texas 4.1
   - Title slide must show state-specific chapter number

3. **State-Specific Standard Names:** Footer must show correct standard per state
   - Oklahoma: "Standard 1: Income & Careers"
   - Colorado: "Standard 1: Financial Foundations"

4. **State Variable Injection:** 12 chapters contain state-specific data
   - Minimum wage, tax rates, median home prices, etc.
   - Must pull from state JSON files and inject into slides

### Scale of the Problem

- 69 chapters (L-01 through L-69)
- 36 states with financial literacy mandates
- 45-69 chapters per state (varies by curriculum requirements)
- Potentially 2,000+ unique slide deck files needed

---

## SOLUTION OVERVIEW

### Architecture: 4-Component Template System

```
┌─────────────────────────────────────────────────────────────────┐
│                     GENERATOR SCRIPT                            │
│                  generate-slide-decks.js                        │
└─────────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   TEMPLATE   │ │   CONTENT    │ │    STATE     │ │   CHAPTER    │
│              │ │              │ │  VARIABLES   │ │   MAPPING    │
│ slide-       │ │ L-01.json    │ │              │ │              │
│ template.html│ │ L-02.json    │ │ oklahoma.json│ │ Oklahoma-    │
│              │ │ ...          │ │ texas.json   │ │ simple-      │
│ (CSS+HTML    │ │ L-69.json    │ │ ...          │ │ data.md      │
│  structure)  │ │              │ │ (86 vars)    │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │   OUTPUT FILES      │
                    │                     │
                    │ /oklahoma/          │
                    │   chapter-1-1.html  │
                    │   chapter-1-2.html  │
                    │ /colorado/          │
                    │   chapter-1-1.html  │
                    │   ...               │
                    └─────────────────────┘
```

### Component Responsibilities

| Component | What It Contains | Who Creates It |
|-----------|------------------|----------------|
| `slide-template.html` | All CSS, slide type HTML structures, placeholder markers | Us (this project) |
| `L-XX.json` (69 files) | Slide-by-slide content for each chapter | 2-3 by us as examples, rest by dev team |
| `{state}.json` (36 files) | State variable data (min wage, tax rates, etc.) | Already exists |
| `{State}-simple-data.md` (36 files) | L-chapter to state chapter ID mapping | Already exists |
| `generate-slide-decks.js` | Node script that combines all pieces | Us (this project) |

---

## DELIVERABLES CHECKLIST

### Must Deliver (Us)

- [ ] `slide-template.html` - Master template with all CSS and slide structures
- [ ] `CONTENT-SCHEMA.md` - JSON schema documentation with examples
- [ ] `L-01.json` - Complete content file (proof of concept, no state vars)
- [ ] `L-03.json` - Complete content file (proof of concept, WITH state vars)
- [ ] `generate-slide-decks.js` - Generator script
- [ ] `README.md` - Quick start guide for dev team
- [ ] `SLIDE-TYPES-REFERENCE.md` - Visual guide to all slide types/layouts

### Already Exists (Reference)

- [x] `/state-data/states/*.json` - 36 state variable files
- [x] `/Simple-Data-Files-Updated/*.md` - 36 state chapter mapping files
- [x] `/slide-decks/L-01-jobs-vs-careers-slides.html` - Reference "good" template
- [x] `/state-data/VARIABLE_CATEGORIES.json` - Variable update schedule

### Dev Team Completes

- [ ] Extract remaining 67 L-XX.json content files
- [ ] Run generator for all states
- [ ] Convert HTML to PDF (Puppeteer or similar)
- [ ] QA review

---

## COMPONENT SPECIFICATIONS

### 1. slide-template.html

**Purpose:** Single HTML file containing ALL CSS and HTML structure patterns. Generator script will clone this and inject content.

**Requirements:**

#### CSS Variables (Design System)
```css
:root {
    /* Primary Brand */
    --primary: #4F46E5;
    --primary-dark: #3730A3;
    --primary-light: #818CF8;
    
    /* Secondary - Teal */
    --teal: #0D9488;
    --teal-dark: #0F766E;
    --teal-light: #5EEAD4;
    
    /* Tertiary - Blue */
    --blue: #3B82F6;
    --blue-light: #DBEAFE;
    
    /* Accent - Green */
    --green: #10B981;
    --green-light: #D1FAE5;
    
    /* Accent - Amber */
    --amber: #F59E0B;
    --amber-light: #FEF3C7;
    --amber-pale: #FFFBEB;
    
    /* Accent - Rose */
    --rose: #F43F5E;
    --rose-light: #FFE4E6;
    
    /* Neutrals */
    --text-dark: #1E293B;
    --text-body: #475569;
    --text-light: #64748B;
    --bg-light: #F8FAFC;
    --bg-slate: #F1F5F9;
    --white: #FFFFFF;
}
```

#### Slide Types (5 total)

| Type | Class | Purpose | Header Color |
|------|-------|---------|--------------|
| Title | `slide-title` | Opening slide with chapter info | Purple gradient |
| Hook | `slide-hook` | Essential question | Dark slate |
| Content | `slide-content` | Standard content | Purple/Teal/Blue |
| Discussion | `slide-discussion` | Discussion prompts | Teal or Purple |
| Closing | `slide-closing` | End slide with logo | Purple gradient |

#### Content Layouts (10+ patterns)

| Layout | Class | Use Case |
|--------|-------|----------|
| Objectives | `objectives-expanded` | 2x2 grid of learning objectives |
| Vocabulary | `vocab-container` | Term + definition + example rows |
| Balanced | `balanced-layout` | Two-column with text + stats |
| Comparison | `comparison-grid` | Side-by-side comparison (vs) |
| Scenario | `scenario-layout` | Example story + outcome boxes |
| Takeaways | `takeaway-grid` | 2x2 key takeaways |
| Activity | `activity-layout` | Instructions + numbered steps |
| Check | `check-grid` | 2x2 comprehension questions |
| Concept | `concept-full` | Full-width explanation |
| Three Column | `three-column` | Three equal cards |
| Bullet List | `bullet-list-full` | Full-width styled bullets |

#### Placeholder Markers

The template must support these placeholders (double curly braces):

**Chapter/Structure Placeholders:**
- `{{CHAPTER_ID}}` - State-specific chapter number (e.g., "1.1", "3.2")
- `{{CHAPTER_TITLE}}` - Chapter title text
- `{{CHAPTER_SUBTITLE}}` - Subtitle text
- `{{STANDARD_NAME}}` - Full standard name (e.g., "Standard 1: Income & Careers")
- `{{STANDARD_NUMBER}}` - Just the number (e.g., "1")
- `{{SLIDE_NUMBER}}` - Current slide number
- `{{TOTAL_SLIDES}}` - Total slide count
- `{{STATE_NAME}}` - State name

**State Variable Placeholders (examples):**
- `{{MIN_WAGE}}` - Minimum wage
- `{{INCOME_TAX_RATE}}` - State income tax rate
- `{{SALES_TAX}}` - State sales tax
- `{{MEDIAN_HOME_PRICE}}` - Median home price
- `{{MEDIAN_RENT}}` - Median rent
- `{{GAS_PRICE_CURRENT}}` - Current gas price
- (See full list in State Variable Reference section)

---

### 2. Content JSON Files (L-XX.json)

**Purpose:** Store all text content for each chapter in a structured format that the generator can process.

**Location:** `/slide-deck-templates/slide-content/`

**Naming:** `L-01.json`, `L-02.json`, ... `L-69.json`

---

## JSON CONTENT SCHEMA

### Top-Level Structure

```json
{
  "metadata": {
    "lChapter": "L-01",
    "title": "Jobs vs. Careers",
    "subtitle": "Understanding the Path to Financial Success",
    "totalSlides": 20,
    "hasStateVariables": false,
    "stateVariablesUsed": []
  },
  "slides": [
    { /* slide 1 */ },
    { /* slide 2 */ },
    { /* ... */ }
  ]
}
```

### Slide Type Schemas

#### Type: title

```json
{
  "number": 1,
  "type": "title",
  "content": {
    "title": "Jobs vs. Careers",
    "titleSize": "large",
    "subtitle": "Understanding the Path to Financial Success"
  }
}
```

**titleSize options:** `"large"` (100px), `"medium"` (80px), `"small"` (64px)

#### Type: hook

```json
{
  "number": 2,
  "type": "hook",
  "content": {
    "label": "Essential Question",
    "question": "What's the difference between <em>earning a paycheck</em> and <em>building a financial future</em>?"
  }
}
```

**Note:** `<em>` tags render in teal-light color for emphasis.

#### Type: content

```json
{
  "number": 3,
  "type": "content",
  "headerColor": "teal",
  "content": {
    "headerTitle": "Learning Objectives",
    "layout": "objectives-expanded",
    "layoutData": { /* layout-specific data */ }
  }
}
```

**headerColor options:** `"purple"` (default), `"teal"`, `"blue"`

#### Type: discussion

```json
{
  "number": 15,
  "type": "discussion",
  "variant": "teal",
  "content": {
    "badge": "Discussion",
    "question": "What specific decisions did Maya and Carlos make that transformed their work from 'just a job' into a career?"
  }
}
```

**variant options:** `"teal"` (default), `"purple"`

#### Type: closing

```json
{
  "number": 20,
  "type": "closing",
  "content": {
    "tagline": "Building Financial Futures, One Lesson at a Time",
    "website": "www.pflacademy.org",
    "copyright": "© 2025 PFL Academy. All rights reserved."
  }
}
```

### Layout Data Schemas

#### Layout: objectives-expanded

```json
{
  "layout": "objectives-expanded",
  "layoutData": {
    "objectives": [
      {
        "number": 1,
        "verb": "Differentiate",
        "description": "Distinguish between a job and a career based on growth potential..."
      },
      {
        "number": 2,
        "verb": "Identify",
        "description": "Recognize how career paths affect long-term earning potential..."
      },
      {
        "number": 3,
        "verb": "Evaluate",
        "description": "Assess your personal interests, skills, and values..."
      },
      {
        "number": 4,
        "verb": "Develop",
        "description": "Create preliminary career path strategies..."
      }
    ]
  }
}
```

#### Layout: vocab-container

```json
{
  "layout": "vocab-container",
  "layoutData": {
    "terms": [
      {
        "term": "Job",
        "definition": "A position of employment that provides immediate income...",
        "example": "Retail cashier, food service worker, seasonal positions..."
      },
      {
        "term": "Career",
        "definition": "A sequence of related jobs in a particular field...",
        "example": "Nursing, software development, accounting, teaching..."
      }
    ]
  }
}
```

#### Layout: balanced-layout

```json
{
  "layout": "balanced-layout",
  "layoutData": {
    "leftPanel": {
      "title": "More Than Just Semantics",
      "paragraphs": [
        "The distinction between jobs and careers has <strong>significant financial implications</strong>...",
        "A <strong>job</strong> primarily functions as a way to earn money...",
        "A <strong>career</strong> represents connected positions..."
      ],
      "highlightBox": {
        "icon": "💡",
        "text": "Your career will likely be your primary income source for 40+ years."
      }
    },
    "rightPanel": {
      "stats": [
        { "value": "40+", "label": "Years of Working Life", "color": "teal" },
        { "value": "$1M+", "label": "Lifetime Earnings Difference", "color": "purple" }
      ],
      "infoCard": {
        "title": "Key Questions to Ask:",
        "color": "amber",
        "items": [
          "Where does this position lead?",
          "What skills will I gain here?",
          "Is there room to grow?"
        ]
      }
    }
  }
}
```

#### Layout: comparison-grid

```json
{
  "layout": "comparison-grid",
  "layoutData": {
    "leftColumn": {
      "icon": "📋",
      "title": "Jobs",
      "items": [
        "Less specialized education needed",
        "May be temporary or short-term",
        "Limited advancement opportunities"
      ]
    },
    "rightColumn": {
      "icon": "🚀",
      "title": "Careers",
      "items": [
        "Requires education or training investment",
        "Long-term professional trajectory",
        "Clear advancement pathways"
      ]
    }
  }
}
```

#### Layout: scenario-layout

```json
{
  "layout": "scenario-layout",
  "layoutData": {
    "scenario": {
      "icon": "👩‍⚕️",
      "name": "Maya's Journey: Fast Food → Healthcare Career",
      "paragraphs": [
        "Maya worked at a fast-food restaurant during high school...",
        "After graduation, Maya enrolled in a community college nursing program..."
      ]
    },
    "outcomes": [
      { "type": "before", "label": "Before (Fast Food Job)", "value": "$7.25/hr", "detail": "No benefits • Irregular hours" },
      { "type": "after", "label": "After (RN Career)", "value": "$35+/hr", "detail": "Full benefits • Career growth" },
      { "type": "neutral", "label": "5-Year Investment", "value": "383% ROI", "detail": "Education paid off quickly" }
    ]
  }
}
```

#### Layout: takeaway-grid

```json
{
  "layout": "takeaway-grid",
  "layoutData": {
    "takeaways": [
      { "number": 1, "title": "Jobs vs. Careers", "description": "Jobs provide immediate income; careers offer growth..." },
      { "number": 2, "title": "Career Capital Compounds", "description": "Skills, experience, and network are valuable assets..." },
      { "number": 3, "title": "Benefits Matter", "description": "Career positions typically include benefits worth $10,000+..." },
      { "number": 4, "title": "Start Early", "description": "The decisions you make now establish your financial foundation..." }
    ]
  }
}
```

#### Layout: activity-layout

```json
{
  "layout": "activity-layout",
  "layoutData": {
    "main": {
      "icon": "📋",
      "title": "Complete the Student Activity Packet",
      "description": "In the activity packet, you'll create a preliminary Career Path Plan..."
    },
    "steps": [
      "Research 2-3 career fields that interest you",
      "Map education requirements and salary ranges",
      "Create short, mid, and long-term goals",
      "Identify career capital you can build now",
      "Calculate potential financial outcomes"
    ]
  }
}
```

#### Layout: check-grid

```json
{
  "layout": "check-grid",
  "layoutData": {
    "questions": [
      { "number": 1, "question": "What is the main difference between a job and a career?" },
      { "number": 2, "question": "Name three types of career capital you could start building right now." },
      { "number": 3, "question": "Why do careers typically offer better financial outcomes?" },
      { "number": 4, "question": "How do benefits add to the financial value of a career?" }
    ]
  }
}
```

#### Layout: concept-full

```json
{
  "layout": "concept-full",
  "layoutData": {
    "title": "What Is Career Capital?",
    "paragraphs": [
      "Career capital is your professional wealth—the skills, experiences, connections..."
    ],
    "bulletPoints": [
      "<strong>Technical Skills:</strong> Programming, accounting, medical procedures...",
      "<strong>Soft Skills:</strong> Communication, leadership, problem-solving...",
      "<strong>Certifications:</strong> Industry credentials that validate expertise..."
    ],
    "keyPoint": {
      "text": "The more career capital you accumulate, the more options you'll have."
    }
  }
}
```

### State Variable Usage in Content

When a chapter uses state variables, reference them in the content:

```json
{
  "metadata": {
    "lChapter": "L-03",
    "title": "Income and Taxes",
    "hasStateVariables": true,
    "stateVariablesUsed": [
      "STATE_NAME",
      "MIN_WAGE",
      "INCOME_TAX_RATE",
      "SALES_TAX"
    ]
  },
  "slides": [
    {
      "number": 5,
      "type": "content",
      "content": {
        "headerTitle": "State Tax Overview",
        "layout": "balanced-layout",
        "layoutData": {
          "leftPanel": {
            "paragraphs": [
              "In {{STATE_NAME}}, the minimum wage is ${{MIN_WAGE}} per hour.",
              "The state income tax rate is {{INCOME_TAX_RATE}}%.",
              "Sales tax is {{SALES_TAX}}% before local additions."
            ]
          }
        }
      }
    }
  ]
}
```

---

## STATE VARIABLE REFERENCE

### Available Variables (86 total)

**Source:** `/state-data/states/{state}.json`

#### Taxes (29 variables)
| Variable | Example (OK) | Description |
|----------|--------------|-------------|
| `income_tax_rate` | 4.75 | State income tax rate % |
| `sales_tax` | 4.5 | State sales tax % |
| `local_sales_tax_max` | 7.0 | Maximum local sales tax % |
| `combined_sales_tax_max` | 11.5 | Max combined rate % |
| `property_tax_county_rate` | 0.30 | County property tax % |
| `assessment_percentage` | 11 | Property assessment ratio % |
| `homestead_exemption` | 1000 | Homestead exemption $ |
| `gas_tax` | varies | State gas tax |
| `estate_tax` | varies | State estate tax |

#### Automotive (10 variables)
| Variable | Example (OK) | Description |
|----------|--------------|-------------|
| `registration_initial` | 96 | Initial registration $ |
| `registration_annual` | 96 | Annual registration $ |
| `avg_auto_loan_rate_new` | 6.72 | New car loan rate % |
| `avg_auto_loan_rate_used` | 7.48 | Used car loan rate % |
| `insurance_avg_teen` | 295 | Monthly teen insurance $ |
| `insurance_avg_adult` | varies | Monthly adult insurance $ |
| `gas_price_current` | 2.75 | Current gas price $ |
| `inspection_required` | false | Inspection required? |
| `inspection_cost` | 0 | Inspection cost $ |

#### Housing (6 variables)
| Variable | Example (OK) | Description |
|----------|--------------|-------------|
| `median_home_price` | 195000 | Median home price $ |
| `median_rent` | 1045 | Median monthly rent $ |
| `avg_mortgage_rate_30yr` | 7.12 | 30-year mortgage rate % |
| `homeowners_avg_monthly` | 225 | Monthly homeowners insurance $ |
| `housing_market_trends` | text | Market description |
| `first_time_homebuyer_program` | text | State program name |

#### Employment (4 variables)
| Variable | Example (OK) | Description |
|----------|--------------|-------------|
| `min_wage` | 7.25 | Minimum wage $ |
| `unemployment_rate` | 3.4 | Unemployment rate % |
| `major_industries` | text | Major industries list |
| `employment_rate` | varies | Employment rate % |

#### Banking (4 variables)
| Variable | Example (OK) | Description |
|----------|--------------|-------------|
| `avg_monthly_fee` | 10 | Avg checking account fee $ |
| `avg_overdraft_fee` | 32 | Avg overdraft fee $ |
| `minor_banking_rules` | text | Rules for minor accounts |
| `local_credit_union_name` | text | Example credit union |

#### Local Examples (20+ variables)
| Variable | Example (OK) | Description |
|----------|--------------|-------------|
| `major_city` | Oklahoma City | Primary city |
| `major_city_1` | Oklahoma City | First major city |
| `major_city_2` | Tulsa | Second major city |
| `suburb_city` | Edmond | Example suburb |
| `rural_area` | Western Oklahoma | Rural area name |
| `major_retailers` | text | Local retailers |
| `utility_providers` | text | Local utilities |

#### URLs (14 variables)
| Variable | Example |
|----------|---------|
| `dmv_url` | https://oklahoma.gov/service-oklahoma |
| `tax_authority_url` | https://oklahoma.gov/tax |
| `labor_department_url` | https://oklahoma.gov/oesc |
| `consumer_protection_url` | https://www.oag.ok.gov/... |

### Chapters Using State Variables

| Chapter | Variables Used | Count |
|---------|---------------|-------|
| L-03 | income_tax_rate, min_wage, sales_tax | ~7 |
| L-06 | All tax variables | ~16 |
| L-30 | median_home_price, median_rent, mortgage_rate, property taxes | ~24 |
| L-46 | registration, insurance, gas_price, auto loans | ~20 |
| L-50 | Local examples, prices | ~23 |
| L-51 | state_name | ~3 |
| L-52 | state_name | ~3 |
| L-53 | state_name | ~3 |
| L-57 | Credit union info | ~3 |
| L-58 | estate_tax | ~2 |
| L-59 | ALL property tax variables | ~60+ |
| L-68 | Tax rates | ~3 |

---

## GENERATOR SCRIPT SPECIFICATION

### File: `generate-slide-decks.js`

### CLI Interface

```bash
# Generate all states, all chapters
node generate-slide-decks.js

# Generate one state, all chapters
node generate-slide-decks.js --state Oklahoma

# Generate all states, one chapter
node generate-slide-decks.js --chapter L-01

# Generate specific combination
node generate-slide-decks.js --state Oklahoma --chapter L-01

# List available states
node generate-slide-decks.js --list-states

# List available chapters (based on JSON files present)
node generate-slide-decks.js --list-chapters

# Validate JSON content files
node generate-slide-decks.js --validate
```

### Core Functions

```javascript
// 1. Load the master template
function loadTemplate() {
  return fs.readFileSync('./slide-template.html', 'utf8');
}

// 2. Load chapter content JSON
function loadContent(lChapter) {
  const path = `./slide-content/${lChapter}.json`;
  return JSON.parse(fs.readFileSync(path, 'utf8'));
}

// 3. Load state variables
function loadStateVariables(stateName) {
  const slug = stateName.toLowerCase().replace(/\s+/g, '-');
  const path = `./state-data/states/${slug}.json`;
  return JSON.parse(fs.readFileSync(path, 'utf8'));
}

// 4. Load state chapter mapping
function loadChapterMapping(stateName) {
  // Parse from {State}-simple-data.md
  // Returns: { "L-01": { chapterId: "1.1", standard: 1, standardTitle: "..." }, ... }
}

// 5. Build variable context for a specific state + chapter
function buildVariableContext(stateVars, chapterMapping, lChapter, content) {
  return {
    // Chapter info
    CHAPTER_ID: chapterMapping[lChapter].chapterId,
    CHAPTER_TITLE: content.metadata.title,
    CHAPTER_SUBTITLE: content.metadata.subtitle,
    STANDARD_NAME: `Standard ${chapterMapping[lChapter].standard}: ${chapterMapping[lChapter].standardTitle}`,
    STANDARD_NUMBER: chapterMapping[lChapter].standard,
    STATE_NAME: stateVars.state_name,
    TOTAL_SLIDES: content.metadata.totalSlides,
    
    // State variables (flattened)
    MIN_WAGE: stateVars.employment.min_wage,
    INCOME_TAX_RATE: stateVars.taxes.income_tax_rate,
    SALES_TAX: stateVars.taxes.sales_tax,
    MEDIAN_HOME_PRICE: stateVars.housing.median_home_price,
    MEDIAN_RENT: stateVars.housing.median_rent,
    // ... all other variables
  };
}

// 6. Render a single slide to HTML
function renderSlide(slide, variables, slideTemplates) {
  // Select appropriate template based on slide.type
  // Inject content based on slide.content.layout
  // Replace all {{PLACEHOLDER}} markers
}

// 7. Generate complete deck HTML
function generateDeck(lChapter, stateName) {
  const template = loadTemplate();
  const content = loadContent(lChapter);
  const stateVars = loadStateVariables(stateName);
  const mapping = loadChapterMapping(stateName);
  const vars = buildVariableContext(stateVars, mapping, lChapter, content);
  
  // Generate each slide
  const slidesHtml = content.slides.map(slide => 
    renderSlide(slide, vars)
  ).join('\n\n');
  
  // Inject into template
  return template.replace('{{SLIDES_CONTENT}}', slidesHtml);
}

// 8. Main execution
function main() {
  // Parse CLI args
  // Loop through states and chapters
  // Write output files to /output/{state}/chapter-{X.X}-slides.html
}
```

### Output Structure

```
/output/
  /oklahoma/
    chapter-1-1-jobs-vs-careers-slides.html
    chapter-1-2-paying-for-education-slides.html
    chapter-1-3-income-and-taxes-slides.html
    ...
  /colorado/
    chapter-1-1-...
    ...
  /texas/
    ...
```

### Error Handling

- Missing content JSON → Skip with warning
- Missing state variable → Use placeholder text "[MISSING: VAR_NAME]"
- Invalid JSON → Fail with descriptive error
- Missing chapter in state mapping → Skip with warning

---

## TESTING REQUIREMENTS

### Before Handoff, Verify:

1. **Template renders correctly**
   - Open slide-template.html in browser
   - Verify all CSS loads
   - Check all slide types display properly

2. **L-01 generates correctly**
   - Run: `node generate-slide-decks.js --state Oklahoma --chapter L-01`
   - Open output, verify matches original L-01 design
   - Check chapter ID shows "1.1" (Oklahoma mapping)

3. **L-03 generates with state variables**
   - Run: `node generate-slide-decks.js --state Oklahoma --chapter L-03`
   - Verify Oklahoma min wage ($7.25) appears
   - Verify Oklahoma tax rate (4.75%) appears
   - Run: `node generate-slide-decks.js --state California --chapter L-03`
   - Verify California min wage ($16.00) appears
   - Verify California tax rate (different) appears

4. **Chapter mapping works**
   - Generate L-14 for Oklahoma → Should show "Chapter 5.1"
   - Generate L-14 for Colorado → Should show different chapter ID
   - Verify standard name in footer matches state

5. **Batch generation works**
   - Run: `node generate-slide-decks.js --state Oklahoma`
   - Verify all available chapters generate
   - Spot check 3-4 random files

---

## DEV TEAM INSTRUCTIONS

### Setup

```bash
git clone [repo-url]
cd slide-deck-templates
npm install  # If any dependencies
```

### File Structure

```
slide-deck-templates/
├── README.md                    # Quick start
├── SLIDE-DECK-PROJECT-ROADMAP.md  # This file
├── CONTENT-SCHEMA.md            # JSON schema docs
├── SLIDE-TYPES-REFERENCE.md     # Visual guide
├── slide-template.html          # Master template
├── generate-slide-decks.js      # Generator script
├── slide-content/               # Content JSON files
│   ├── L-01.json               # (provided)
│   ├── L-03.json               # (provided)
│   └── ... (you create L-02, L-04 through L-69)
├── state-data/                  # Copy of state variables
│   └── states/
│       ├── oklahoma.json
│       ├── texas.json
│       └── ...
└── state-mappings/              # Copy of simple-data files
    ├── Oklahoma-simple-data.md
    ├── Texas-simple-data.md
    └── ...
```

### Creating Content JSON Files

1. Open existing slide deck HTML: `/slide-decks/L-XX-...-slides.html`
2. For each slide, create corresponding JSON entry
3. Use schema examples in `CONTENT-SCHEMA.md`
4. Validate: `node generate-slide-decks.js --validate`

### Generating Decks

```bash
# Test single chapter
node generate-slide-decks.js --state Oklahoma --chapter L-01

# Generate all for one state
node generate-slide-decks.js --state Oklahoma

# Generate everything (all states, all chapters)
node generate-slide-decks.js
```

### Converting to PDF

Use Puppeteer or similar:

```javascript
const puppeteer = require('puppeteer');

async function htmlToPdf(htmlPath, pdfPath) {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto(`file://${htmlPath}`);
  await page.pdf({
    path: pdfPath,
    width: '1920px',
    height: '1080px',
    printBackground: true,
    landscape: true
  });
  await browser.close();
}
```

---

## TIMELINE ESTIMATE FOR DEV TEAM

| Task | Est. Time |
|------|-----------|
| Review documentation | 1-2 hours |
| Extract L-02 through L-10 content | 4-6 hours |
| Extract L-11 through L-30 content | 8-10 hours |
| Extract L-31 through L-50 content | 8-10 hours |
| Extract L-51 through L-69 content | 8-10 hours |
| Run full generation | 1 hour |
| PDF conversion setup | 2-3 hours |
| QA review | 4-6 hours |
| **Total** | **~40-50 hours** |

Note: Content extraction is parallelizable across team members.

---

## APPENDIX: REFERENCE FILES

### Good Template (Use as Reference)
`/slide-decks/L-01-jobs-vs-careers-slides.html`

### Broken Template (Example of What NOT to Do)
`/slide-decks/L-04-financial-goal-setting-slides.html`

### State Variable Schema
`/state-data/VARIABLE_CATEGORIES.json`

### State Data Example
`/state-data/states/oklahoma.json`

### Chapter Mapping Example
`/Simple-Data-Files-Updated/Oklahoma-simple-data.md`
