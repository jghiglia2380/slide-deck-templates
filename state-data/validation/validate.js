#!/usr/bin/env node

/**
 * PFL Academy State Data Validation Script
 *
 * Validates state JSON files against schema requirements
 *
 * Usage:
 *   node validate.js                    # Validate all states
 *   node validate.js texas              # Validate specific state
 *   node validate.js --check-urls       # Include URL accessibility checks
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// Configuration
const STATE_DATA_DIR = path.join(__dirname, '..', 'states');
const SCHEMA_FILE = path.join(__dirname, '..', 'schema.json');
const RESULTS_FILE = path.join(__dirname, 'validation-results.json');

// Validation rules
const VALIDATION_RULES = {
  // Required fields
  REQUIRED_FIELDS: [
    'state_name',
    'state_code',
    'last_updated',
    'data_sources',
    'automotive',
    'taxes',
    'housing',
    'employment',
    'education',
    'banking',
    'consumer_protection',
    'local_examples'
  ],

  // Reasonable value ranges
  RANGES: {
    registration_initial: { min: 0, max: 1000 },
    registration_annual: { min: 0, max: 500 },
    avg_auto_loan_rate_new: { min: 0, max: 30 },
    avg_auto_loan_rate_used: { min: 0, max: 30 },
    insurance_avg_teen: { min: 50, max: 1000 },
    gas_price_current: { min: 1, max: 10 },
    sales_tax: { min: 0, max: 15 },
    local_sales_tax_min: { min: 0, max: 10 },
    local_sales_tax_max: { min: 0, max: 10 },
    combined_sales_tax_min: { min: 0, max: 20 },
    combined_sales_tax_max: { min: 0, max: 20 },
    property_tax_county_rate: { min: 0, max: 5 },
    property_tax_school_rate: { min: 0, max: 5 },
    assessment_percentage: { min: 0, max: 100 },
    homestead_exemption: { min: 0, max: 500000 },
    median_home_price: { min: 50000, max: 5000000 },
    median_rent: { min: 300, max: 10000 },
    avg_mortgage_rate_30yr: { min: 0, max: 20 },
    min_wage: { min: 5, max: 25 },
    unemployment_rate: { min: 0, max: 20 },
    tuition_public: { min: 1000, max: 50000 },
    avg_monthly_fee: { min: 0, max: 50 },
    avg_overdraft_fee: { min: 0, max: 100 }
  },

  // Placeholder text patterns to flag
  PLACEHOLDER_PATTERNS: [
    /FILL_IN/i,
    /TODO/i,
    /TBD/i,
    /PLACEHOLDER/i,
    /EXAMPLE/i,
    /REPLACE_ME/i,
    /INSERT_HERE/i,
    /\[.*\]/,  // Bracketed placeholders like [City Name]
  ],

  // Maximum age for last_updated (in days)
  MAX_DATA_AGE_DAYS: 365
};

// Colors for terminal output
const COLORS = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

class StateValidator {
  constructor(options = {}) {
    this.checkUrls = options.checkUrls || false;
    this.results = {
      totalStates: 0,
      validStates: 0,
      invalidStates: 0,
      warnings: 0,
      errors: 0,
      stateResults: {}
    };
  }

  /**
   * Validate all states or a specific state
   */
  async validate(stateName = null) {
    console.log(`${COLORS.cyan}PFL Academy State Data Validation${COLORS.reset}\n`);

    const stateFiles = this.getStateFiles(stateName);

    if (stateFiles.length === 0) {
      console.error(`${COLORS.red}Error: No state files found${COLORS.reset}`);
      return;
    }

    console.log(`Validating ${stateFiles.length} state(s)...\n`);

    for (const file of stateFiles) {
      await this.validateStateFile(file);
    }

    this.printSummary();
    this.saveResults();
  }

  /**
   * Get list of state files to validate
   */
  getStateFiles(stateName) {
    if (stateName) {
      const filename = `${stateName.toLowerCase()}.json`;
      const filepath = path.join(STATE_DATA_DIR, filename);
      return fs.existsSync(filepath) ? [filepath] : [];
    }

    if (!fs.existsSync(STATE_DATA_DIR)) {
      return [];
    }

    return fs.readdirSync(STATE_DATA_DIR)
      .filter(f => f.endsWith('.json'))
      .map(f => path.join(STATE_DATA_DIR, f));
  }

  /**
   * Validate a single state file
   */
  async validateStateFile(filepath) {
    const filename = path.basename(filepath);
    const stateName = filename.replace('.json', '');

    console.log(`${COLORS.blue}━━━ ${stateName.toUpperCase()} ━━━${COLORS.reset}`);

    const stateResult = {
      file: filename,
      valid: true,
      errors: [],
      warnings: [],
      checks: {
        structure: false,
        required_fields: false,
        data_types: false,
        value_ranges: false,
        placeholders: false,
        data_freshness: false,
        urls: false
      }
    };

    try {
      // Load and parse JSON
      const data = JSON.parse(fs.readFileSync(filepath, 'utf8'));

      // Run validation checks
      this.checkStructure(data, stateResult);
      this.checkRequiredFields(data, stateResult);
      this.checkDataTypes(data, stateResult);
      this.checkValueRanges(data, stateResult);
      this.checkPlaceholders(data, stateResult);
      this.checkDataFreshness(data, stateResult);

      if (this.checkUrls) {
        await this.checkUrlAccessibility(data, stateResult);
      }

      // Determine overall validity
      stateResult.valid = stateResult.errors.length === 0;

      // Update counters
      this.results.totalStates++;
      if (stateResult.valid) {
        this.results.validStates++;
        console.log(`${COLORS.green}✓ VALID${COLORS.reset}\n`);
      } else {
        this.results.invalidStates++;
        console.log(`${COLORS.red}✗ INVALID${COLORS.reset}\n`);
      }

      this.results.errors += stateResult.errors.length;
      this.results.warnings += stateResult.warnings.length;

    } catch (error) {
      stateResult.valid = false;
      stateResult.errors.push(`Failed to parse JSON: ${error.message}`);
      this.results.invalidStates++;
      this.results.errors++;
      console.log(`${COLORS.red}✗ PARSE ERROR: ${error.message}${COLORS.reset}\n`);
    }

    this.results.stateResults[stateName] = stateResult;

    // Print errors and warnings
    this.printIssues(stateResult);
  }

  /**
   * Check basic structure
   */
  checkStructure(data, result) {
    if (typeof data !== 'object' || data === null) {
      result.errors.push('Root must be an object');
      return;
    }
    result.checks.structure = true;
  }

  /**
   * Check required top-level fields
   */
  checkRequiredFields(data, result) {
    const missing = [];

    for (const field of VALIDATION_RULES.REQUIRED_FIELDS) {
      if (!(field in data)) {
        missing.push(field);
      }
    }

    if (missing.length > 0) {
      result.errors.push(`Missing required fields: ${missing.join(', ')}`);
    } else {
      result.checks.required_fields = true;
    }
  }

  /**
   * Check data types
   */
  checkDataTypes(data, result) {
    const errors = [];

    // State code must be 2 uppercase letters
    if (data.state_code && !/^[A-Z]{2}$/.test(data.state_code)) {
      errors.push(`state_code must be 2 uppercase letters (got: ${data.state_code})`);
    }

    // Check date format
    if (data.last_updated && !/^\d{4}-\d{2}-\d{2}$/.test(data.last_updated)) {
      errors.push(`last_updated must be in YYYY-MM-DD format (got: ${data.last_updated})`);
    }

    // Check automotive fields
    if (data.automotive) {
      this.checkNumericFields(data.automotive, 'automotive', errors);
    }

    // Check tax fields
    if (data.taxes) {
      this.checkNumericFields(data.taxes, 'taxes', errors);
    }

    // Check housing fields
    if (data.housing) {
      this.checkNumericFields(data.housing, 'housing', errors);
    }

    // Check employment fields
    if (data.employment) {
      this.checkNumericFields(data.employment, 'employment', errors);
    }

    if (errors.length > 0) {
      result.errors.push(...errors);
    } else {
      result.checks.data_types = true;
    }
  }

  /**
   * Helper to check numeric fields
   */
  checkNumericFields(obj, section, errors) {
    for (const [key, value] of Object.entries(obj)) {
      if (key in VALIDATION_RULES.RANGES) {
        if (typeof value !== 'number') {
          errors.push(`${section}.${key} must be a number (got: ${typeof value})`);
        }
      }
    }
  }

  /**
   * Check value ranges
   */
  checkValueRanges(data, result) {
    const errors = [];
    const warnings = [];

    this.checkRangesInObject(data.automotive, 'automotive', errors, warnings);
    this.checkRangesInObject(data.taxes, 'taxes', errors, warnings);
    this.checkRangesInObject(data.housing, 'housing', errors, warnings);
    this.checkRangesInObject(data.employment, 'employment', errors, warnings);
    this.checkRangesInObject(data.education, 'education', errors, warnings);
    this.checkRangesInObject(data.banking, 'banking', errors, warnings);

    if (errors.length > 0) {
      result.errors.push(...errors);
    } else {
      result.checks.value_ranges = true;
    }

    if (warnings.length > 0) {
      result.warnings.push(...warnings);
    }
  }

  /**
   * Helper to check ranges in an object
   */
  checkRangesInObject(obj, section, errors, warnings) {
    if (!obj) return;

    for (const [key, value] of Object.entries(obj)) {
      if (key in VALIDATION_RULES.RANGES && typeof value === 'number') {
        const { min, max } = VALIDATION_RULES.RANGES[key];

        if (value < min || value > max) {
          errors.push(`${section}.${key} out of range: ${value} (expected ${min}-${max})`);
        }

        // Soft warnings for unusual values
        const midpoint = (min + max) / 2;
        const threshold = (max - min) * 0.4;
        if (Math.abs(value - midpoint) > threshold) {
          warnings.push(`${section}.${key} unusual value: ${value} (typical range: ${min}-${max})`);
        }
      }
    }
  }

  /**
   * Check for placeholder text
   */
  checkPlaceholders(data, result) {
    const placeholders = [];

    this.findPlaceholders(data, '', placeholders);

    if (placeholders.length > 0) {
      result.errors.push(`Found placeholder text: ${placeholders.join(', ')}`);
    } else {
      result.checks.placeholders = true;
    }
  }

  /**
   * Recursively search for placeholder patterns
   */
  findPlaceholders(obj, path, placeholders) {
    if (typeof obj === 'string') {
      for (const pattern of VALIDATION_RULES.PLACEHOLDER_PATTERNS) {
        if (pattern.test(obj)) {
          placeholders.push(`${path}: "${obj.substring(0, 50)}..."`);
          break;
        }
      }
    } else if (Array.isArray(obj)) {
      obj.forEach((item, idx) => {
        this.findPlaceholders(item, `${path}[${idx}]`, placeholders);
      });
    } else if (typeof obj === 'object' && obj !== null) {
      for (const [key, value] of Object.entries(obj)) {
        const newPath = path ? `${path}.${key}` : key;
        this.findPlaceholders(value, newPath, placeholders);
      }
    }
  }

  /**
   * Check data freshness
   */
  checkDataFreshness(data, result) {
    if (!data.last_updated) {
      result.warnings.push('Missing last_updated field');
      return;
    }

    const lastUpdated = new Date(data.last_updated);
    const now = new Date();
    const daysDiff = (now - lastUpdated) / (1000 * 60 * 60 * 24);

    if (daysDiff > VALIDATION_RULES.MAX_DATA_AGE_DAYS) {
      result.warnings.push(`Data is ${Math.floor(daysDiff)} days old (last updated: ${data.last_updated})`);
    } else {
      result.checks.data_freshness = true;
    }
  }

  /**
   * Check URL accessibility (optional, slower)
   */
  async checkUrlAccessibility(data, result) {
    if (!data.data_sources) {
      result.warnings.push('Missing data_sources object');
      return;
    }

    const urls = Object.values(data.data_sources).filter(v => typeof v === 'string' && v.startsWith('http'));
    const brokenUrls = [];

    for (const url of urls) {
      const accessible = await this.checkUrl(url);
      if (!accessible) {
        brokenUrls.push(url);
      }
    }

    if (brokenUrls.length > 0) {
      result.warnings.push(`Inaccessible URLs: ${brokenUrls.join(', ')}`);
    } else if (urls.length > 0) {
      result.checks.urls = true;
    }
  }

  /**
   * Check if URL is accessible (HEAD request)
   */
  checkUrl(url) {
    return new Promise((resolve) => {
      const client = url.startsWith('https') ? https : http;

      const req = client.request(url, { method: 'HEAD', timeout: 5000 }, (res) => {
        resolve(res.statusCode >= 200 && res.statusCode < 400);
      });

      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });

      req.end();
    });
  }

  /**
   * Print issues for a state
   */
  printIssues(stateResult) {
    if (stateResult.errors.length > 0) {
      console.log(`${COLORS.red}Errors:${COLORS.reset}`);
      stateResult.errors.forEach(err => {
        console.log(`  ${COLORS.red}✗${COLORS.reset} ${err}`);
      });
      console.log();
    }

    if (stateResult.warnings.length > 0) {
      console.log(`${COLORS.yellow}Warnings:${COLORS.reset}`);
      stateResult.warnings.forEach(warn => {
        console.log(`  ${COLORS.yellow}⚠${COLORS.reset} ${warn}`);
      });
      console.log();
    }
  }

  /**
   * Print summary
   */
  printSummary() {
    console.log(`${COLORS.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLORS.reset}`);
    console.log(`${COLORS.cyan}Validation Summary${COLORS.reset}\n`);

    console.log(`Total States:   ${this.results.totalStates}`);
    console.log(`${COLORS.green}Valid:${COLORS.reset}          ${this.results.validStates}`);
    console.log(`${COLORS.red}Invalid:${COLORS.reset}        ${this.results.invalidStates}`);
    console.log(`${COLORS.red}Errors:${COLORS.reset}         ${this.results.errors}`);
    console.log(`${COLORS.yellow}Warnings:${COLORS.reset}       ${this.results.warnings}`);

    const passRate = this.results.totalStates > 0
      ? ((this.results.validStates / this.results.totalStates) * 100).toFixed(1)
      : 0;

    console.log(`\nPass Rate:      ${passRate}%`);

    if (this.results.validStates === this.results.totalStates) {
      console.log(`\n${COLORS.green}✓ All states passed validation!${COLORS.reset}`);
    } else {
      console.log(`\n${COLORS.red}✗ Some states failed validation${COLORS.reset}`);
    }

    console.log(`${COLORS.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLORS.reset}\n`);
  }

  /**
   * Save results to JSON file
   */
  saveResults() {
    try {
      const resultsDir = path.dirname(RESULTS_FILE);
      if (!fs.existsSync(resultsDir)) {
        fs.mkdirSync(resultsDir, { recursive: true });
      }

      fs.writeFileSync(
        RESULTS_FILE,
        JSON.stringify(this.results, null, 2),
        'utf8'
      );

      console.log(`Results saved to: ${RESULTS_FILE}\n`);
    } catch (error) {
      console.error(`${COLORS.red}Failed to save results: ${error.message}${COLORS.reset}\n`);
    }
  }
}

// CLI execution
if (require.main === module) {
  const args = process.argv.slice(2);
  const options = {
    checkUrls: args.includes('--check-urls')
  };

  const stateName = args.find(arg => !arg.startsWith('--'));

  const validator = new StateValidator(options);
  validator.validate(stateName).catch(error => {
    console.error(`${COLORS.red}Validation failed: ${error.message}${COLORS.reset}`);
    process.exit(1);
  });
}

module.exports = StateValidator;
