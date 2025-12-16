#!/usr/bin/env node

/**
 * Remove emojis from all JSON slide content files
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const contentDir = path.join(__dirname, 'slide-content');

// Regex to match emojis and common emoji unicode ranges
const emojiRegex = /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F600}-\u{1F64F}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2300}-\u{23FF}]|[\u{2B50}]|[\u{203C}-\u{3299}]|[🎯💡💰📋📊🎓📚👩👨🔄⚠️✓✅❌!→●•]/gu;

// Also clean up leftover emoji artifacts like broken surrogate pairs
const surrogateRegex = /[\uD800-\uDFFF]/g;

function cleanEmojis(text) {
    if (typeof text !== 'string') return text;
    return text
        .replace(emojiRegex, '')
        .replace(surrogateRegex, '')
        .replace(/\s{2,}/g, ' ')  // Clean up double spaces left behind
        .trim();
}

function cleanObject(obj) {
    if (typeof obj === 'string') {
        return cleanEmojis(obj);
    }
    if (Array.isArray(obj)) {
        return obj.map(item => cleanObject(item));
    }
    if (typeof obj === 'object' && obj !== null) {
        const cleaned = {};
        for (const [key, value] of Object.entries(obj)) {
            // Skip the 'icon' field entirely - remove it
            if (key === 'icon') {
                continue;
            }
            cleaned[key] = cleanObject(value);
        }
        return cleaned;
    }
    return obj;
}

function processFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const data = JSON.parse(content);
    const cleaned = cleanObject(data);
    fs.writeFileSync(filePath, JSON.stringify(cleaned, null, 2), 'utf8');
}

// Process all JSON files
const files = fs.readdirSync(contentDir).filter(f => f.endsWith('.json'));

console.log(`\nCleaning emojis from ${files.length} files...\n`);

files.forEach(file => {
    const filePath = path.join(contentDir, file);
    processFile(filePath);
    console.log(`  ✓ ${file}`);
});

console.log(`\n✅ Done! Removed emojis from ${files.length} files.\n`);
