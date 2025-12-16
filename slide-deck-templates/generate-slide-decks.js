#!/usr/bin/env node

/**
 * PFL Academy Slide Deck Generator
 *
 * Generates state-customized HTML slide decks by combining:
 * - slide-template.html (master template)
 * - slide-content/L-XX.json (chapter content)
 * - state-data/states/{state}.json (state variables)
 * - Simple-Data-Files-Updated/{State}-simple-data.md (chapter mappings)
 *
 * Usage:
 *   node generate-slide-decks.js --state=oklahoma --chapter=L-03
 *   node generate-slide-decks.js --list-states
 *   node generate-slide-decks.js --list-chapters
 *   node generate-slide-decks.js --validate L-03.json
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// ES module equivalents for __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
    templatePath: path.join(__dirname, 'slide-template.html'),
    contentDir: path.join(__dirname, 'slide-content'),
    stateDataDir: path.join(__dirname, '..', 'state-data', 'states'),
    chapterMappingDir: path.join(__dirname, '..', 'Simple-Data-Files-Updated'),
    outputDir: path.join(__dirname, 'output'),
};

// State variables that can be calculated from base data
const CALCULATED_FIELDS = {
    CALCULATED_STATE_TAX_MONTHLY: (vars, baseAmount = 4000) => {
        const rate = parseFloat(vars.INCOME_TAX_RATE || 0);
        return `$${((baseAmount * rate) / 100).toFixed(2)}`;
    },
    CALCULATED_LOCAL_TAX_MONTHLY: (vars, baseAmount = 4000) => {
        const rate = parseFloat(vars.LOCAL_INCOME_TAX || 0);
        return `$${((baseAmount * rate) / 100).toFixed(2)}`;
    },
    CALCULATED_SDI_MONTHLY: (vars, baseAmount = 4000) => {
        const rate = parseFloat(vars.SDI_RATE || 0);
        return `$${((baseAmount * rate) / 100).toFixed(2)}`;
    },
    CALCULATED_TOTAL_STATE_DEDUCTIONS: (vars, baseAmount = 4000) => {
        const stateRate = parseFloat(vars.INCOME_TAX_RATE || 0);
        const localRate = parseFloat(vars.LOCAL_INCOME_TAX || 0);
        const sdiRate = parseFloat(vars.SDI_RATE || 0);
        const total = ((baseAmount * (stateRate + localRate + sdiRate)) / 100);
        return `$${total.toFixed(2)}`;
    }
};

// ============================================================================
// CLI ARGUMENT PARSING
// ============================================================================

function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        state: null,
        chapter: null,
        listStates: false,
        listChapters: false,
        validate: null,
    };

    args.forEach(arg => {
        if (arg.startsWith('--state=')) {
            options.state = arg.split('=')[1].toLowerCase();
        } else if (arg.startsWith('--chapter=')) {
            options.chapter = arg.split('=')[1].toUpperCase();
        } else if (arg === '--list-states') {
            options.listStates = true;
        } else if (arg === '--list-chapters') {
            options.listChapters = true;
        } else if (arg === '--validate') {
            options.validate = args[args.indexOf(arg) + 1];
        }
    });

    return options;
}

// ============================================================================
// FILE LOADING FUNCTIONS
// ============================================================================

function loadTemplate() {
    try {
        return fs.readFileSync(CONFIG.templatePath, 'utf8');
    } catch (error) {
        console.error(`❌ Error loading template: ${error.message}`);
        process.exit(1);
    }
}

function loadContentJSON(lChapter) {
    const contentPath = path.join(CONFIG.contentDir, `${lChapter}.json`);

    try {
        const content = fs.readFileSync(contentPath, 'utf8');
        return JSON.parse(content);
    } catch (error) {
        console.error(`❌ Error loading content JSON for ${lChapter}: ${error.message}`);
        process.exit(1);
    }
}

function loadStateVariables(stateName) {
    const statePath = path.join(CONFIG.stateDataDir, `${stateName}.json`);

    try {
        const content = fs.readFileSync(statePath, 'utf8');
        return JSON.parse(content);
    } catch (error) {
        console.error(`❌ Error loading state data for ${stateName}: ${error.message}`);
        console.error(`   Expected file: ${statePath}`);
        process.exit(1);
    }
}

function loadChapterMapping(stateName) {
    // Try multiple filename formats
    const possibleNames = [
        `${stateName}-simple-data.md`,
        `${stateName.charAt(0).toUpperCase() + stateName.slice(1)}-simple-data.md`,
        `${stateName.toUpperCase()}-simple-data.md`
    ];

    for (const fileName of possibleNames) {
        const mappingPath = path.join(CONFIG.chapterMappingDir, fileName);
        if (fs.existsSync(mappingPath)) {
            try {
                return fs.readFileSync(mappingPath, 'utf8');
            } catch (error) {
                console.error(`❌ Error reading chapter mapping: ${error.message}`);
                process.exit(1);
            }
        }
    }

    console.error(`❌ Chapter mapping file not found for ${stateName}`);
    console.error(`   Tried: ${possibleNames.join(', ')}`);
    process.exit(1);
}

// ============================================================================
// CHAPTER MAPPING PARSER
// ============================================================================

function parseChapterMapping(markdownContent, lChapter) {
    // Parse markdown to find mapping for L-chapter to state chapter ID
    // Format: | L-03 | 1.3 | Income and Taxes |

    const lines = markdownContent.split('\n');
    const tableRows = lines.filter(line => line.trim().startsWith('|'));

    for (const row of tableRows) {
        const columns = row.split('|').map(col => col.trim()).filter(col => col);

        if (columns[0] === lChapter) {
            return {
                stateChapter: columns[1],
                title: columns[2] || 'Unknown Chapter'
            };
        }
    }

    console.warn(`⚠️  Warning: No mapping found for ${lChapter}, using fallback`);
    return {
        stateChapter: lChapter.replace('L-', ''),
        title: 'Unknown Chapter'
    };
}

// ============================================================================
// VARIABLE INTERPOLATION
// ============================================================================

function interpolateVariables(template, stateVars, contentData) {
    // Handle null/undefined template
    if (!template || typeof template !== 'string') {
        return template || '';
    }

    let result = template;

    // Replace basic state variables
    Object.keys(stateVars).forEach(key => {
        const placeholder = `{{${key}}}`;
        const value = stateVars[key];

        // Handle different value types
        let displayValue = value;
        if (typeof value === 'number') {
            displayValue = value.toString();
        } else if (typeof value === 'boolean') {
            displayValue = value ? 'Yes' : 'No';
        } else if (value === null || value === undefined) {
            displayValue = 'N/A';
        }

        result = result.split(placeholder).join(displayValue);
    });

    // Replace calculated fields
    Object.keys(CALCULATED_FIELDS).forEach(fieldName => {
        const placeholder = `{{${fieldName}}}`;
        const calculateFn = CALCULATED_FIELDS[fieldName];
        const calculatedValue = calculateFn(stateVars);

        result = result.split(placeholder).join(calculatedValue);
    });

    // Replace metadata placeholders
    if (contentData && contentData.metadata) {
        result = result.replace('{{CHAPTER_TITLE}}', contentData.metadata.title || '');
        result = result.replace('{{CHAPTER_SUBTITLE}}', contentData.metadata.subtitle || '');
    }

    return result;
}

// ============================================================================
// SLIDE GENERATION
// ============================================================================

function generateSlideHTML(slide, stateVars) {
    let slideHTML = '';

    // Determine slide type class
    const slideClass = `slide-${slide.type}`;
    const headerClass = slide.headerColor || 'purple';

    slideHTML += `<div class="slide ${slideClass}">\n`;

    // Add slide header
    if (slide.content && slide.content.headerTitle) {
        slideHTML += `  <div class="slide-header ${headerClass}">\n`;
        slideHTML += `    <h1>${interpolateVariables(slide.content.headerTitle, stateVars, null)}</h1>\n`;
        slideHTML += `  </div>\n`;
    }

    // Add slide content based on layout
    slideHTML += `  <div class="slide-body">\n`;
    slideHTML += generateLayoutContent(slide.content, stateVars);
    slideHTML += `  </div>\n`;

    // Add slide footer
    slideHTML += `  <div class="slide-footer">\n`;
    slideHTML += `    <span class="slide-number">${slide.number}</span>\n`;
    slideHTML += `  </div>\n`;

    slideHTML += `</div>\n\n`;

    return slideHTML;
}

function generateLayoutContent(content, stateVars) {
    if (!content || !content.layout) {
        return '';
    }

    const layoutData = content.layoutData || {};
    let html = '';

    switch (content.layout) {
        case 'objectives-expanded':
            html = generateObjectivesLayout(layoutData, stateVars);
            break;
        case 'vocab-container':
            html = generateVocabLayout(layoutData, stateVars);
            break;
        case 'comparison-grid':
            html = generateComparisonLayout(layoutData, stateVars);
            break;
        case 'scenario-layout':
            html = generateScenarioLayout(layoutData, stateVars);
            break;
        case 'takeaway-grid':
            html = generateTakeawayLayout(layoutData, stateVars);
            break;
        case 'paycheck-breakdown':
            html = generatePaycheckLayout(layoutData, stateVars);
            break;
        case 'bullet-list-full':
            html = generateBulletListLayout(layoutData, stateVars);
            break;
        default:
            html = generateGenericLayout(layoutData, stateVars);
    }

    return html;
}

// Layout generators for each type
function generateObjectivesLayout(data, stateVars) {
    let html = '<div class="objectives-expanded">\n';

    if (data.objectives) {
        data.objectives.forEach(obj => {
            html += `  <div class="objective-item">\n`;
            html += `    <div class="objective-number">${obj.number}</div>\n`;
            html += `    <div class="objective-content">\n`;
            html += `      <div class="objective-verb">${interpolateVariables(obj.verb, stateVars, null)}</div>\n`;
            html += `      <div class="objective-description">${interpolateVariables(obj.description, stateVars, null)}</div>\n`;
            html += `    </div>\n`;
            html += `  </div>\n`;
        });
    }

    html += '</div>\n';
    return html;
}

function generateVocabLayout(data, stateVars) {
    let html = '<div class="vocab-container">\n';

    if (data.terms) {
        data.terms.forEach(term => {
            html += `  <div class="vocab-card">\n`;
            html += `    <div class="vocab-term">${interpolateVariables(term.term, stateVars, null)}</div>\n`;
            html += `    <div class="vocab-definition">${interpolateVariables(term.definition, stateVars, null)}</div>\n`;
            html += `  </div>\n`;
        });
    }

    html += '</div>\n';
    return html;
}

function generateComparisonLayout(data, stateVars) {
    let html = '<div class="comparison-grid">\n';

    if (data.columns) {
        data.columns.forEach(col => {
            html += `  <div class="comparison-column">\n`;
            html += `    <div class="comparison-header">${interpolateVariables(col.header, stateVars, null)}</div>\n`;
            html += `    <ul class="comparison-list">\n`;

            if (col.items) {
                col.items.forEach(item => {
                    html += `      <li>${interpolateVariables(item, stateVars, null)}</li>\n`;
                });
            }

            html += `    </ul>\n`;
            html += `  </div>\n`;
        });
    }

    html += '</div>\n';
    return html;
}

function generateScenarioLayout(data, stateVars) {
    let html = '<div class="scenario-layout">\n';

    if (data.title) {
        html += `  <h2>${interpolateVariables(data.title, stateVars, null)}</h2>\n`;
    }

    if (data.description) {
        html += `  <p class="scenario-description">${interpolateVariables(data.description, stateVars, null)}</p>\n`;
    }

    if (data.highlightBox) {
        html += `  <div class="highlight-box">\n`;
        html += `    <span class="highlight-icon">${data.highlightBox.icon}</span>\n`;
        html += `    <span class="highlight-text">${interpolateVariables(data.highlightBox.text, stateVars, null)}</span>\n`;
        html += `  </div>\n`;
    }

    html += '</div>\n';
    return html;
}

function generateTakeawayLayout(data, stateVars) {
    let html = '<div class="takeaway-grid">\n';

    if (data.takeaways) {
        data.takeaways.forEach(item => {
            html += `  <div class="takeaway-card">\n`;
            html += `    <div class="takeaway-icon">${item.icon}</div>\n`;
            html += `    <div class="takeaway-text">${interpolateVariables(item.text, stateVars, null)}</div>\n`;
            html += `  </div>\n`;
        });
    }

    html += '</div>\n';
    return html;
}

function generatePaycheckLayout(data, stateVars) {
    let html = '<div class="paycheck-breakdown">\n';
    html += '  <h3>Monthly Paycheck Breakdown</h3>\n';

    if (data.lines) {
        data.lines.forEach(line => {
            const lineClass = line.type || '';
            const isStateVar = line.isStateVariable ? ' data-state-variable="true"' : '';

            html += `  <div class="paycheck-line ${lineClass}"${isStateVar}>\n`;
            html += `    <span class="label">${interpolateVariables(line.label, stateVars, null)}</span>\n`;
            html += `    <span class="amount">${interpolateVariables(line.amount, stateVars, null)}</span>\n`;
            html += `  </div>\n`;
        });
    }

    html += '</div>\n';
    return html;
}

function generateBulletListLayout(data, stateVars) {
    let html = '<div class="bullet-list-full">\n';

    if (data.items) {
        html += '  <ul>\n';
        data.items.forEach(item => {
            html += `    <li>${interpolateVariables(item, stateVars, null)}</li>\n`;
        });
        html += '  </ul>\n';
    }

    html += '</div>\n';
    return html;
}

function generateGenericLayout(data, stateVars) {
    // Fallback for unknown layouts
    let html = '<div class="generic-content">\n';
    html += `  <pre>${JSON.stringify(data, null, 2)}</pre>\n`;
    html += '</div>\n';
    return html;
}

// ============================================================================
// MAIN GENERATION FUNCTION
// ============================================================================

function generateSlideDeck(state, lChapter) {
    console.log(`\n🎯 Generating slide deck for ${lChapter} - ${state}`);
    console.log('─'.repeat(60));

    // Load all required files
    console.log('📂 Loading template...');
    const template = loadTemplate();

    console.log(`📂 Loading content JSON (${lChapter}.json)...`);
    const contentData = loadContentJSON(lChapter);

    console.log(`📂 Loading state data (${state}.json)...`);
    const stateVars = loadStateVariables(state);

    console.log(`📂 Loading chapter mapping for ${state}...`);
    const mappingContent = loadChapterMapping(state);
    const mapping = parseChapterMapping(mappingContent, lChapter);

    console.log(`✓ Mapped to state chapter: ${mapping.stateChapter}`);

    // Generate slides HTML
    console.log(`\n🔨 Generating ${contentData.slides.length} slides...`);
    let slidesHTML = '';

    contentData.slides.forEach((slide, index) => {
        slidesHTML += generateSlideHTML(slide, stateVars);
        process.stdout.write(`   Slide ${index + 1}/${contentData.slides.length}\r`);
    });

    console.log(`\n✓ All slides generated`);

    // Replace template placeholders
    console.log('\n🔄 Interpolating variables...');
    let finalHTML = template.replace('<!-- SLIDES_CONTENT -->', slidesHTML);
    finalHTML = interpolateVariables(finalHTML, stateVars, contentData);

    // Add state-specific metadata
    finalHTML = finalHTML.replace('{{STATE_CHAPTER}}', mapping.stateChapter);

    // Ensure output directory exists
    const stateOutputDir = path.join(CONFIG.outputDir, state);
    if (!fs.existsSync(stateOutputDir)) {
        fs.mkdirSync(stateOutputDir, { recursive: true });
    }

    // Write output file
    const outputFileName = `chapter-${mapping.stateChapter}-slides.html`;
    const outputPath = path.join(stateOutputDir, outputFileName);

    console.log(`\n💾 Writing output file...`);
    fs.writeFileSync(outputPath, finalHTML, 'utf8');

    console.log(`\n✅ Success!`);
    console.log(`   Output: ${outputPath}`);
    console.log(`   Size: ${(finalHTML.length / 1024).toFixed(2)} KB`);
    console.log('─'.repeat(60));

    return outputPath;
}

// ============================================================================
// VALIDATION FUNCTION
// ============================================================================

function validateContentJSON(filePath) {
    console.log(`\n🔍 Validating: ${filePath}`);
    console.log('─'.repeat(60));

    try {
        const content = fs.readFileSync(filePath, 'utf8');
        const data = JSON.parse(content);

        let errors = [];
        let warnings = [];

        // Check metadata
        if (!data.metadata) {
            errors.push('Missing metadata object');
        } else {
            if (!data.metadata.lChapter) errors.push('Missing metadata.lChapter');
            if (!data.metadata.title) errors.push('Missing metadata.title');
            if (data.metadata.hasStateVariables === undefined) {
                errors.push('Missing metadata.hasStateVariables');
            }
        }

        // Check slides array
        if (!data.slides || !Array.isArray(data.slides)) {
            errors.push('Missing or invalid slides array');
        } else {
            data.slides.forEach((slide, index) => {
                if (!slide.number) warnings.push(`Slide ${index}: missing number`);
                if (!slide.type) warnings.push(`Slide ${index}: missing type`);
                if (!slide.content) warnings.push(`Slide ${index}: missing content`);
            });
        }

        // Check for state variables if hasStateVariables is true
        if (data.metadata && data.metadata.hasStateVariables) {
            const contentString = JSON.stringify(data);
            const placeholderRegex = /\{\{([A-Z_]+)\}\}/g;
            const foundVars = new Set();
            let match;

            while ((match = placeholderRegex.exec(contentString)) !== null) {
                foundVars.add(match[1]);
            }

            if (foundVars.size === 0) {
                warnings.push('hasStateVariables is true but no {{PLACEHOLDERS}} found');
            }

            const declaredVars = new Set(data.metadata.stateVariablesUsed || []);
            foundVars.forEach(v => {
                if (!declaredVars.has(v) && !CALCULATED_FIELDS[v]) {
                    warnings.push(`Variable {{${v}}} used but not declared in stateVariablesUsed`);
                }
            });
        }

        // Print results
        if (errors.length === 0 && warnings.length === 0) {
            console.log('✅ Validation passed!');
            console.log(`   Slides: ${data.slides.length}`);
            console.log(`   State variables: ${data.metadata.hasStateVariables ? 'Yes' : 'No'}`);
        } else {
            if (errors.length > 0) {
                console.log('\n❌ Errors:');
                errors.forEach(err => console.log(`   - ${err}`));
            }
            if (warnings.length > 0) {
                console.log('\n⚠️  Warnings:');
                warnings.forEach(warn => console.log(`   - ${warn}`));
            }
        }

        console.log('─'.repeat(60));
        return errors.length === 0;

    } catch (error) {
        console.log(`❌ Validation failed: ${error.message}`);
        console.log('─'.repeat(60));
        return false;
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function listStates() {
    console.log('\n📍 Available States:\n');

    try {
        const files = fs.readdirSync(CONFIG.stateDataDir);
        const states = files
            .filter(f => f.endsWith('.json'))
            .map(f => f.replace('.json', ''))
            .sort();

        states.forEach(state => {
            console.log(`   • ${state}`);
        });

        console.log(`\n   Total: ${states.length} states\n`);
    } catch (error) {
        console.error(`❌ Error reading state directory: ${error.message}`);
    }
}

function listChapters() {
    console.log('\n📚 Available Chapters:\n');

    try {
        const files = fs.readdirSync(CONFIG.contentDir);
        const chapters = files
            .filter(f => f.endsWith('.json'))
            .map(f => f.replace('.json', ''))
            .sort();

        chapters.forEach(chapter => {
            try {
                const data = loadContentJSON(chapter);
                const stateVars = data.metadata.hasStateVariables ? '✓' : ' ';
                console.log(`   [${stateVars}] ${chapter.padEnd(8)} - ${data.metadata.title}`);
            } catch (error) {
                console.log(`   [ ] ${chapter.padEnd(8)} - (error loading)`);
            }
        });

        console.log(`\n   Total: ${chapters.length} chapters`);
        console.log(`   [✓] = Has state variables\n`);
    } catch (error) {
        console.error(`❌ Error reading content directory: ${error.message}`);
    }
}

function showHelp() {
    console.log(`
╔════════════════════════════════════════════════════════════╗
║        PFL Academy Slide Deck Generator v1.0               ║
╚════════════════════════════════════════════════════════════╝

Usage:
  node generate-slide-decks.js [options]

Options:
  --state=<name>           State name (lowercase, e.g., oklahoma)
  --chapter=<id>           L-chapter ID (e.g., L-01, L-03)
  --list-states            List all available states
  --list-chapters          List all available chapters
  --validate <file>        Validate a content JSON file

Examples:
  Generate Oklahoma slides for Chapter L-03:
    node generate-slide-decks.js --state=oklahoma --chapter=L-03

  List all states:
    node generate-slide-decks.js --list-states

  Validate content file:
    node generate-slide-decks.js --validate slide-content/L-03.json

Output:
  Generated files are saved to: output/{state}/chapter-{X.X}-slides.html
`);
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

function main() {
    const options = parseArgs();

    // Handle utility commands
    if (options.listStates) {
        listStates();
        return;
    }

    if (options.listChapters) {
        listChapters();
        return;
    }

    if (options.validate) {
        const isValid = validateContentJSON(options.validate);
        process.exit(isValid ? 0 : 1);
    }

    // Handle generation
    if (options.state && options.chapter) {
        try {
            generateSlideDeck(options.state, options.chapter);
            process.exit(0);
        } catch (error) {
            console.error(`\n❌ Generation failed: ${error.message}`);
            console.error(error.stack);
            process.exit(1);
        }
    } else {
        // Show help if no valid options provided
        showHelp();
    }
}

// Run main function
main();

// Export for testing
export {
    generateSlideDeck,
    validateContentJSON,
    interpolateVariables,
    parseChapterMapping
};
