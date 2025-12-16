#!/usr/bin/env node

/**
 * HTML to JSON Slide Deck Converter
 * 
 * Converts existing HTML slide deck files to the JSON format
 * expected by generate-slide-decks.js
 * 
 * Usage:
 *   node html-to-json-converter.js                    # Convert all
 *   node html-to-json-converter.js --chapter=L-02    # Convert single chapter
 *   node html-to-json-converter.js --test            # Test mode (L-02 only)
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { JSDOM } from 'jsdom';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============================================================================
// CONFIGURATION
// ============================================================================

const CONFIG = {
    sourceDir: path.join(__dirname, '..', 'slide-decks'),
    outputDir: path.join(__dirname, 'slide-content'),
    // Skip L-01 and L-03 since they already exist
    skipExisting: ['L-01', 'L-03']
};

// Known state variables that might appear in content
const STATE_VARIABLES = [
    'STATE_NAME', 'STATE_GRANT_PROGRAM', 'STATE_TUITION_PUBLIC', 'STATE_TUITION_COMMUNITY',
    'MIN_WAGE', 'INCOME_TAX_RATE', 'SALES_TAX', 'LOCAL_SALES_TAX_MAX', 'COMBINED_SALES_TAX_MAX',
    'PROPERTY_TAX_COUNTY_RATE', 'ASSESSMENT_PERCENTAGE', 'HOMESTEAD_EXEMPTION',
    'MEDIAN_HOME_PRICE', 'MEDIAN_RENT', 'AVG_MORTGAGE_RATE_30YR',
    'REGISTRATION_INITIAL', 'REGISTRATION_ANNUAL', 'GAS_PRICE_CURRENT', 'INSURANCE_AVG_TEEN',
    'AVG_AUTO_LOAN_RATE_NEW', 'AVG_AUTO_LOAN_RATE_USED',
    'UNEMPLOYMENT_RATE', 'MAJOR_INDUSTRIES', 'MAJOR_CITY', 'MAJOR_CITY_1', 'MAJOR_CITY_2',
    'AVG_MONTHLY_FEE', 'AVG_OVERDRAFT_FEE', 'LOCAL_CREDIT_UNION_NAME',
    'DMV_URL', 'TAX_AUTHORITY_URL', 'LABOR_DEPARTMENT_URL', 'CONSUMER_PROTECTION_URL'
];

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function cleanText(text) {
    if (!text) return '';
    return text
        .replace(/\s+/g, ' ')
        .trim();
}

function extractInnerHTML(element) {
    if (!element) return '';
    return element.innerHTML
        .replace(/\s+/g, ' ')
        .trim();
}

function detectStateVariables(content) {
    const found = [];
    const contentStr = JSON.stringify(content);
    
    STATE_VARIABLES.forEach(varName => {
        if (contentStr.includes(`{{${varName}}}`) || contentStr.includes(varName)) {
            found.push(varName);
        }
    });
    
    // Also check for any {{VARIABLE}} pattern
    const matches = contentStr.match(/\{\{([A-Z_]+)\}\}/g);
    if (matches) {
        matches.forEach(match => {
            const varName = match.replace(/[{}]/g, '');
            if (!found.includes(varName)) {
                found.push(varName);
            }
        });
    }
    
    return [...new Set(found)];
}

function determineHeaderColor(headerElement) {
    if (!headerElement) return 'purple';
    const classList = headerElement.className || '';
    if (classList.includes('teal')) return 'teal';
    if (classList.includes('blue')) return 'blue';
    return 'purple';
}

// ============================================================================
// SLIDE TYPE PARSERS
// ============================================================================

function parseTitleSlide(slideElement, doc) {
    const h1 = slideElement.querySelector('h1');
    const subtitle = slideElement.querySelector('.subtitle');
    const chapterLabel = slideElement.querySelector('.chapter-label');
    
    // Try to determine title size from font-size style if present
    let titleSize = 'large';
    if (h1) {
        const fontSize = h1.style?.fontSize;
        if (fontSize) {
            const size = parseInt(fontSize);
            if (size <= 64) titleSize = 'small';
            else if (size <= 80) titleSize = 'medium';
        }
    }
    
    return {
        type: 'title',
        content: {
            title: cleanText(h1?.textContent),
            titleSize: titleSize,
            subtitle: cleanText(subtitle?.textContent)
        }
    };
}

function parseHookSlide(slideElement) {
    const label = slideElement.querySelector('.label');
    const question = slideElement.querySelector('.question');
    
    return {
        type: 'hook',
        content: {
            label: cleanText(label?.textContent) || 'Essential Question',
            question: extractInnerHTML(question)
        }
    };
}

function parseDiscussionSlide(slideElement) {
    const badge = slideElement.querySelector('.badge');
    const question = slideElement.querySelector('.question');
    
    // Check background style for variant
    const style = slideElement.getAttribute('style') || '';
    let variant = 'teal';
    if (style.includes('primary') || style.includes('6D29D8')) {
        variant = 'purple';
    }
    
    return {
        type: 'discussion',
        variant: variant,
        content: {
            badge: cleanText(badge?.textContent) || 'Discussion',
            question: extractInnerHTML(question)
        }
    };
}

function parseClosingSlide(slideElement) {
    const tagline = slideElement.querySelector('.tagline');
    const website = slideElement.querySelector('.website');
    const copyright = slideElement.querySelector('.copyright');
    
    return {
        type: 'closing',
        content: {
            tagline: cleanText(tagline?.textContent) || 'Building Financial Futures, One Lesson at a Time',
            website: cleanText(website?.textContent) || 'www.pflacademy.co',
            copyright: cleanText(copyright?.textContent) || '© 2025 PFL Academy. All rights reserved.'
        }
    };
}

function parseContentSlide(slideElement) {
    const header = slideElement.querySelector('.slide-header');
    const body = slideElement.querySelector('.slide-body');
    const headerTitle = header?.querySelector('h2');
    
    const headerColor = determineHeaderColor(header);
    
    // Detect layout type
    const layout = detectLayout(body);
    const layoutData = extractLayoutData(body, layout);
    
    return {
        type: 'content',
        headerColor: headerColor,
        content: {
            headerTitle: cleanText(headerTitle?.textContent),
            layout: layout,
            layoutData: layoutData
        }
    };
}

function detectLayout(bodyElement) {
    if (!bodyElement) return 'generic';
    
    if (bodyElement.querySelector('.objectives-expanded')) return 'objectives-expanded';
    if (bodyElement.querySelector('.vocab-container')) return 'vocab-container';
    if (bodyElement.querySelector('.balanced-layout')) return 'balanced-layout';
    if (bodyElement.querySelector('.comparison-grid')) return 'comparison-grid';
    if (bodyElement.querySelector('.scenario-layout')) return 'scenario-layout';
    if (bodyElement.querySelector('.takeaway-grid')) return 'takeaway-grid';
    if (bodyElement.querySelector('.activity-layout')) return 'activity-layout';
    if (bodyElement.querySelector('.check-grid')) return 'check-grid';
    if (bodyElement.querySelector('.concept-full')) return 'concept-full';
    if (bodyElement.querySelector('.priority-list')) return 'priority-list';
    
    return 'generic';
}

function extractLayoutData(bodyElement, layout) {
    if (!bodyElement) return {};
    
    switch (layout) {
        case 'objectives-expanded':
            return extractObjectivesLayout(bodyElement);
        case 'vocab-container':
            return extractVocabLayout(bodyElement);
        case 'balanced-layout':
            return extractBalancedLayout(bodyElement);
        case 'comparison-grid':
            return extractComparisonLayout(bodyElement);
        case 'scenario-layout':
            return extractScenarioLayout(bodyElement);
        case 'takeaway-grid':
            return extractTakeawayLayout(bodyElement);
        case 'activity-layout':
            return extractActivityLayout(bodyElement);
        case 'check-grid':
            return extractCheckLayout(bodyElement);
        case 'concept-full':
            return extractConceptLayout(bodyElement);
        case 'priority-list':
            return extractPriorityLayout(bodyElement);
        default:
            return extractGenericLayout(bodyElement);
    }
}

function extractObjectivesLayout(body) {
    const objectives = [];
    const cards = body.querySelectorAll('.objective-card');
    
    cards.forEach((card, index) => {
        const number = card.querySelector('.number');
        const verb = card.querySelector('h3');
        const description = card.querySelector('p');
        
        objectives.push({
            number: parseInt(number?.textContent) || (index + 1),
            verb: cleanText(verb?.textContent),
            description: cleanText(description?.textContent)
        });
    });
    
    return { objectives };
}

function extractVocabLayout(body) {
    const terms = [];
    const rows = body.querySelectorAll('.vocab-row');
    
    rows.forEach(row => {
        const termBox = row.querySelector('.vocab-term-box .term');
        const defBox = row.querySelector('.vocab-def-box p');
        const exampleBox = row.querySelector('.vocab-example-box p');
        
        terms.push({
            term: cleanText(termBox?.textContent),
            definition: cleanText(defBox?.textContent),
            example: cleanText(exampleBox?.textContent)
        });
    });
    
    return { terms };
}

function extractBalancedLayout(body) {
    const layout = body.querySelector('.balanced-layout');
    if (!layout) return {};
    
    const contentPanel = layout.querySelector('.content-panel');
    const statsPanel = layout.querySelector('.stats-panel');
    
    // Extract left panel
    const leftPanel = {
        title: '',
        paragraphs: [],
        highlightBox: null
    };
    
    if (contentPanel) {
        const h3 = contentPanel.querySelector('h3');
        leftPanel.title = cleanText(h3?.textContent);
        
        const paragraphs = contentPanel.querySelectorAll('p:not(.highlight-box p)');
        paragraphs.forEach(p => {
            const text = extractInnerHTML(p);
            if (text && !text.includes('💡') && !text.includes('🎯') && !text.includes('📅')) {
                leftPanel.paragraphs.push(text);
            }
        });
        
        const highlightBox = contentPanel.querySelector('.highlight-box');
        if (highlightBox) {
            const highlightP = highlightBox.querySelector('p');
            const text = extractInnerHTML(highlightP);
            // Try to extract icon from start of text
            const iconMatch = text.match(/^([💡🎯📅🔄💰📊])\s*/);
            leftPanel.highlightBox = {
                icon: iconMatch ? iconMatch[1] : '💡',
                text: text.replace(/^[💡🎯📅🔄💰📊]\s*/, '')
            };
        }
    }
    
    // Extract right panel
    const rightPanel = {
        stats: [],
        infoCard: null
    };
    
    if (statsPanel) {
        const statCards = statsPanel.querySelectorAll('.stat-card');
        statCards.forEach(card => {
            const number = card.querySelector('.number');
            const label = card.querySelector('.label');
            let color = 'teal';
            if (card.classList.contains('purple')) color = 'purple';
            else if (card.classList.contains('green')) color = 'green';
            else if (card.classList.contains('rose')) color = 'rose';
            
            rightPanel.stats.push({
                value: cleanText(number?.textContent),
                label: cleanText(label?.textContent),
                color: color
            });
        });
        
        const infoCard = statsPanel.querySelector('.info-card');
        if (infoCard) {
            const h4 = infoCard.querySelector('h4');
            const items = infoCard.querySelectorAll('li');
            let color = 'amber';
            if (infoCard.classList.contains('blue')) color = 'blue';
            else if (infoCard.classList.contains('green')) color = 'green';
            
            rightPanel.infoCard = {
                title: cleanText(h4?.textContent),
                color: color,
                items: Array.from(items).map(li => cleanText(li.textContent))
            };
        }
        
        // Check for priority list
        const priorityList = statsPanel.querySelector('.priority-list');
        if (priorityList) {
            rightPanel.priorityList = extractPriorityItems(priorityList);
        }
    }
    
    return { leftPanel, rightPanel };
}

function extractPriorityItems(list) {
    const items = [];
    const priorityItems = list.querySelectorAll('.priority-item');
    
    priorityItems.forEach((item, index) => {
        const rank = item.querySelector('.rank');
        const h4 = item.querySelector('h4');
        const p = item.querySelector('p');
        
        let rankClass = 'first';
        if (rank?.classList.contains('second')) rankClass = 'second';
        else if (rank?.classList.contains('third')) rankClass = 'third';
        else if (rank?.classList.contains('fourth')) rankClass = 'fourth';
        
        items.push({
            rank: index + 1,
            rankClass: rankClass,
            title: cleanText(h4?.textContent),
            description: cleanText(p?.textContent)
        });
    });
    
    return items;
}

function extractComparisonLayout(body) {
    const grid = body.querySelector('.comparison-grid');
    if (!grid) return {};
    
    const leftCol = grid.querySelector('.compare-column.left');
    const rightCol = grid.querySelector('.compare-column.right');
    
    function extractColumn(col) {
        if (!col) return { icon: '', title: '', items: [] };
        const h3 = col.querySelector('h3');
        const items = col.querySelectorAll('li');
        
        // Extract emoji from title
        const titleText = cleanText(h3?.textContent);
        const iconMatch = titleText.match(/^([🎁💳📋🚀✓!])\s*/);
        
        return {
            icon: iconMatch ? iconMatch[1] : '',
            title: titleText.replace(/^[🎁💳📋🚀]\s*/, ''),
            items: Array.from(items).map(li => cleanText(li.textContent))
        };
    }
    
    return {
        leftColumn: extractColumn(leftCol),
        rightColumn: extractColumn(rightCol)
    };
}

function extractScenarioLayout(body) {
    const layout = body.querySelector('.scenario-layout');
    if (!layout) return {};
    
    const scenarioCard = layout.querySelector('.scenario-card');
    const outcomes = layout.querySelector('.scenario-outcomes');
    
    // Extract scenario
    const scenario = {
        icon: '',
        name: '',
        paragraphs: []
    };
    
    if (scenarioCard) {
        const nameDiv = scenarioCard.querySelector('.name');
        const iconDiv = nameDiv?.querySelector('.icon');
        scenario.icon = cleanText(iconDiv?.textContent) || '👤';
        scenario.name = cleanText(nameDiv?.textContent).replace(scenario.icon, '').trim();
        
        const paragraphs = scenarioCard.querySelectorAll('p');
        paragraphs.forEach(p => {
            scenario.paragraphs.push(extractInnerHTML(p));
        });
    }
    
    // Extract outcomes
    const outcomesList = [];
    if (outcomes) {
        const boxes = outcomes.querySelectorAll('.outcome-box');
        boxes.forEach(box => {
            let type = 'neutral';
            if (box.classList.contains('before')) type = 'before';
            else if (box.classList.contains('after')) type = 'after';
            
            const label = box.querySelector('.label');
            const value = box.querySelector('.value');
            const detail = box.querySelector('.detail');
            
            outcomesList.push({
                type: type,
                label: cleanText(label?.textContent),
                value: cleanText(value?.textContent),
                detail: cleanText(detail?.textContent)
            });
        });
    }
    
    return { scenario, outcomes: outcomesList };
}

function extractTakeawayLayout(body) {
    const takeaways = [];
    const items = body.querySelectorAll('.takeaway-item');
    
    items.forEach((item, index) => {
        const number = item.querySelector('.number');
        const h4 = item.querySelector('h4');
        const p = item.querySelector('p');
        
        takeaways.push({
            number: parseInt(number?.textContent) || (index + 1),
            title: cleanText(h4?.textContent),
            description: cleanText(p?.textContent)
        });
    });
    
    return { takeaways };
}

function extractActivityLayout(body) {
    const layout = body.querySelector('.activity-layout');
    if (!layout) return {};
    
    const mainDiv = layout.querySelector('.activity-main');
    const stepsDiv = layout.querySelector('.activity-steps');
    
    const main = {
        icon: '📋',
        title: '',
        description: ''
    };
    
    if (mainDiv) {
        const h3 = mainDiv.querySelector('h3');
        const titleText = cleanText(h3?.textContent);
        const iconMatch = titleText.match(/^([📋📝✍️📊])\s*/);
        main.icon = iconMatch ? iconMatch[1] : '📋';
        main.title = titleText.replace(/^[📋📝✍️📊]\s*/, '');
        
        const paragraphs = mainDiv.querySelectorAll('p');
        main.description = Array.from(paragraphs).map(p => extractInnerHTML(p)).join(' ');
    }
    
    const steps = [];
    if (stepsDiv) {
        const stepItems = stepsDiv.querySelectorAll('.activity-step');
        stepItems.forEach(step => {
            const p = step.querySelector('p');
            steps.push(cleanText(p?.textContent));
        });
    }
    
    return { main, steps };
}

function extractCheckLayout(body) {
    const questions = [];
    const items = body.querySelectorAll('.check-item');
    
    items.forEach((item, index) => {
        const qNum = item.querySelector('.q-num');
        const p = item.querySelector('p');
        
        questions.push({
            number: index + 1,
            question: cleanText(p?.textContent)
        });
    });
    
    return { questions };
}

function extractConceptLayout(body) {
    const concept = body.querySelector('.concept-full');
    if (!concept) return {};
    
    const h3 = concept.querySelector('h3');
    const paragraphs = concept.querySelectorAll('p:not(.key-point p)');
    const bulletItems = concept.querySelectorAll('li');
    const keyPoint = concept.querySelector('.key-point');
    
    const result = {
        title: cleanText(h3?.textContent),
        paragraphs: Array.from(paragraphs).map(p => extractInnerHTML(p)),
        bulletPoints: Array.from(bulletItems).map(li => extractInnerHTML(li))
    };
    
    if (keyPoint) {
        const keyP = keyPoint.querySelector('p');
        result.keyPoint = {
            text: extractInnerHTML(keyP)
        };
    }
    
    return result;
}

function extractPriorityLayout(body) {
    const list = body.querySelector('.priority-list');
    if (!list) return {};
    
    return {
        items: extractPriorityItems(list)
    };
}

function extractGenericLayout(body) {
    // Fallback: just extract all text content
    const paragraphs = body.querySelectorAll('p');
    const lists = body.querySelectorAll('ul, ol');
    
    return {
        paragraphs: Array.from(paragraphs).map(p => extractInnerHTML(p)),
        lists: Array.from(lists).map(list => {
            return Array.from(list.querySelectorAll('li')).map(li => extractInnerHTML(li));
        })
    };
}

// ============================================================================
// MAIN CONVERSION FUNCTION
// ============================================================================

function convertHtmlToJson(htmlFilePath) {
    console.log(`\n📄 Processing: ${path.basename(htmlFilePath)}`);
    
    // Read HTML file
    const htmlContent = fs.readFileSync(htmlFilePath, 'utf8');
    
    // Parse with JSDOM
    const dom = new JSDOM(htmlContent);
    const doc = dom.window.document;
    
    // Extract chapter info from title
    const title = doc.querySelector('title')?.textContent || '';
    const lChapterMatch = title.match(/L-(\d+)/);
    const lChapter = lChapterMatch ? `L-${lChapterMatch[1].padStart(2, '0')}` : 'L-XX';
    
    // Extract chapter title from first slide
    const titleSlide = doc.querySelector('.slide-title');
    const mainTitle = cleanText(titleSlide?.querySelector('h1')?.textContent) || '';
    const subtitle = cleanText(titleSlide?.querySelector('.subtitle')?.textContent) || '';
    
    // Get all slides
    const slideElements = doc.querySelectorAll('.slide');
    const slides = [];
    
    slideElements.forEach((slideEl, index) => {
        const slideNumber = index + 1;
        let slideData = { number: slideNumber };
        
        // Determine slide type
        if (slideEl.classList.contains('slide-title')) {
            const parsed = parseTitleSlide(slideEl, doc);
            slideData = { ...slideData, ...parsed };
        } else if (slideEl.classList.contains('slide-hook')) {
            const parsed = parseHookSlide(slideEl);
            slideData = { ...slideData, ...parsed };
        } else if (slideEl.classList.contains('slide-discussion')) {
            const parsed = parseDiscussionSlide(slideEl);
            slideData = { ...slideData, ...parsed };
        } else if (slideEl.classList.contains('slide-closing')) {
            const parsed = parseClosingSlide(slideEl);
            slideData = { ...slideData, ...parsed };
        } else if (slideEl.classList.contains('slide-content')) {
            const parsed = parseContentSlide(slideEl);
            slideData = { ...slideData, ...parsed };
        } else {
            // Unknown slide type - try content parsing
            const parsed = parseContentSlide(slideEl);
            slideData = { ...slideData, ...parsed };
        }
        
        slides.push(slideData);
    });
    
    // Build final JSON structure
    const jsonOutput = {
        metadata: {
            lChapter: lChapter,
            title: mainTitle,
            subtitle: subtitle,
            totalSlides: slides.length,
            hasStateVariables: false,
            stateVariablesUsed: []
        },
        slides: slides
    };
    
    // Detect state variables
    const stateVars = detectStateVariables(jsonOutput);
    jsonOutput.metadata.hasStateVariables = stateVars.length > 0;
    jsonOutput.metadata.stateVariablesUsed = stateVars;
    
    console.log(`   ✓ Extracted ${slides.length} slides`);
    if (stateVars.length > 0) {
        console.log(`   ✓ Found state variables: ${stateVars.join(', ')}`);
    }
    
    return jsonOutput;
}

function processAllFiles(options = {}) {
    console.log('\n' + '═'.repeat(60));
    console.log('  HTML to JSON Slide Deck Converter');
    console.log('═'.repeat(60));
    
    // Ensure output directory exists
    if (!fs.existsSync(CONFIG.outputDir)) {
        fs.mkdirSync(CONFIG.outputDir, { recursive: true });
    }
    
    // Get list of HTML files
    const htmlFiles = fs.readdirSync(CONFIG.sourceDir)
        .filter(f => f.endsWith('.html') && f.startsWith('L-'))
        .sort();
    
    console.log(`\n📂 Found ${htmlFiles.length} HTML files in ${CONFIG.sourceDir}`);
    
    let processed = 0;
    let skipped = 0;
    let errors = 0;
    
    for (const htmlFile of htmlFiles) {
        // Extract L-chapter from filename
        const match = htmlFile.match(/^(L-\d+)/);
        if (!match) continue;
        
        const lChapter = match[1];
        
        // Check if should process
        if (options.chapter && options.chapter !== lChapter) {
            continue;
        }
        
        // Check if should skip existing
        if (CONFIG.skipExisting.includes(lChapter)) {
            console.log(`\n⏭️  Skipping ${lChapter} (already exists)`);
            skipped++;
            continue;
        }
        
        try {
            const htmlPath = path.join(CONFIG.sourceDir, htmlFile);
            const jsonData = convertHtmlToJson(htmlPath);
            
            // Write output
            const outputPath = path.join(CONFIG.outputDir, `${lChapter}.json`);
            fs.writeFileSync(outputPath, JSON.stringify(jsonData, null, 2), 'utf8');
            console.log(`   💾 Saved: ${lChapter}.json`);
            
            processed++;
        } catch (error) {
            console.error(`   ❌ Error processing ${htmlFile}: ${error.message}`);
            errors++;
        }
    }
    
    console.log('\n' + '═'.repeat(60));
    console.log(`  COMPLETE`);
    console.log(`  ✓ Processed: ${processed}`);
    console.log(`  ⏭️  Skipped: ${skipped}`);
    if (errors > 0) console.log(`  ❌ Errors: ${errors}`);
    console.log('═'.repeat(60) + '\n');
}

// ============================================================================
// CLI
// ============================================================================

function main() {
    const args = process.argv.slice(2);
    const options = {};
    
    args.forEach(arg => {
        if (arg.startsWith('--chapter=')) {
            options.chapter = arg.split('=')[1].toUpperCase();
        } else if (arg === '--test') {
            options.chapter = 'L-02';
        }
    });
    
    processAllFiles(options);
}

main();
