#!/bin/bash
# End-to-end workflow for Chapter 1.1
# Generated: 2025-03-22T18:00:14.458Z

set -e

# Check if GitHub integration script exists
if [ ! -f "automation/github-integration-1.1.js" ]; then
  echo "❌ GitHub integration script not found!"
  exit 1
fi

# Set up environment
echo "🔧 Setting up environment..."
export CHAPTER="1.1"
export TIMESTAMP=$(date +%Y%m%d%H%M%S)
export LOG_FILE="pfl-workflow-1.1-$TIMESTAMP.log"

# Run validation
echo "🔍 Validating generated content..."
if [ -f "chapter_1_1_complete.json" ]; then
  echo "✅ JSON schema found"
else
  echo "❌ JSON schema not found!"
  exit 1
fi

# GitHub integration
echo "🔄 Running GitHub integration..."
node automation/github-integration-1.1.js

echo "🎉 Workflow completed successfully!"
echo "📝 See GitHub repository for committed files"
