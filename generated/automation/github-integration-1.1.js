#!/usr/bin/env node

/**
 * GitHub Integration Script for Chapter 1.1
 * Generated: ${new Date().toISOString()}
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Configuration
const repoUrl = 'https://github.com/jghiglia2380/pfl-academy-90';
const branch = 'chapter-1-1';

// Main execution
function main() {
  try {
    // Check if we're already on the branch
    const currentBranch = execSync('git branch --show-current').toString().trim();
    
    if (currentBranch !== branch) {
      // Create a new branch
      console.log(`Creating branch: ${branch}`);
      execSync(`git checkout -b ${branch}`);
    } else {
      console.log(`Already on branch: ${branch}`);
    }
    
    // Go to root directory
    console.log('Moving to repository root directory...');
    process.chdir('..');
    
    // Stage files (use correct paths)
    console.log('Staging files...');
    
    // Stage HTML files
    try {
      execSync('git add generated/chapter-1-1-day1.html');
      console.log('  Added: generated/chapter-1-1-day1.html');
    } catch (error) {
      console.error(`  Error adding generated/chapter-1-1-day1.html: ${error.message}`);
    }
    
    try {
      execSync('git add generated/chapter-1-1-day2.html');
      console.log('  Added: generated/chapter-1-1-day2.html');
    } catch (error) {
      console.error(`  Error adding generated/chapter-1-1-day2.html: ${error.message}`);
    }
    
    // Stage teacher markdown files
    try {
      execSync('git add generated/chapter_1_1_teacher_day1.md');
      console.log('  Added: generated/chapter_1_1_teacher_day1.md');
    } catch (error) {
      console.error(`  Error adding generated/chapter_1_1_teacher_day1.md: ${error.message}`);
    }
    
    try {
      execSync('git add generated/chapter_1_1_teacher_day2.md');
      console.log('  Added: generated/chapter_1_1_teacher_day2.md');
    } catch (error) {
      console.error(`  Error adding generated/chapter_1_1_teacher_day2.md: ${error.message}`);
    }
    
    // Stage JSON file
    try {
      execSync('git add generated/chapter_1_1_complete.json');
      console.log('  Added: generated/chapter_1_1_complete.json');
    } catch (error) {
      console.error(`  Error adding generated/chapter_1_1_complete.json: ${error.message}`);
    }
    
    // Stage automation scripts
    try {
      execSync('git add generated/automation/github-integration-1.1.js');
      console.log('  Added: generated/automation/github-integration-1.1.js');
    } catch (error) {
      console.error(`  Error adding generated/automation/github-integration-1.1.js: ${error.message}`);
    }
    
    try {
      execSync('git add generated/automation/e2e-workflow-1.1.sh');
      console.log('  Added: generated/automation/e2e-workflow-1.1.sh');
    } catch (error) {
      console.error(`  Error adding generated/automation/e2e-workflow-1.1.sh: ${error.message}`);
    }
    
    // Commit files
    console.log('Creating commit...');
    execSync(`git commit -m "Add Chapter 1.1: Jobs vs. Careers content"`);
    
    // Push to remote
    console.log(`Pushing to ${repoUrl}`);
    execSync(`git push -u origin ${branch}`);
    
    console.log('\n✅ GitHub integration completed successfully!');
    console.log('View your GitHub repository at:');
    console.log(`https://github.com/jghiglia2380/pfl-academy-90/tree/${branch}`);
    console.log('\nCreate a pull request at:');
    console.log(`https://github.com/jghiglia2380/pfl-academy-90/pull/new/${branch}`);
  } catch (error) {
    console.error('\n❌ Error during GitHub integration:', error.message);
    process.exit(1);
  }
}

// Run main function
main();