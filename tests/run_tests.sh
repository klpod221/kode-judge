#!/bin/bash

# Script to validate and run Postman collection tests
# Requires Newman (Postman CLI) to be installed: npm install -g newman

set -e

echo "==================================="
echo "KodeJudge API Test Runner"
echo "==================================="
echo ""

# Check if Newman is installed
if ! command -v newman &> /dev/null; then
    echo "⚠️  Newman is not installed!"
    echo "   Install it with: npm install -g newman newman-reporter-html"
    echo ""
    read -p "Do you want to install Newman now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        npm install -g newman newman-reporter-html
    else
        exit 1
    fi
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
POSTMAN_DIR="$SCRIPT_DIR/postman"
REPORTS_DIR="$SCRIPT_DIR/reports"

# Check if collection file exists
COLLECTION_FILE="$POSTMAN_DIR/KodeJudge-API-Tests.postman_collection.json"
if [ ! -f "$COLLECTION_FILE" ]; then
    echo "❌ Collection file not found: $COLLECTION_FILE"
    exit 1
fi

# Validate JSON
echo "🔍 Validating Postman collection JSON..."
if node -e "JSON.parse(require('fs').readFileSync('$COLLECTION_FILE', 'utf8')); console.log('✓ JSON is valid')"; then
    echo ""
else
    echo "❌ Invalid JSON in collection file"
    exit 1
fi

# Create reports directory if it doesn't exist
mkdir -p "$REPORTS_DIR"

# Check if API server is running
echo "🔍 Checking API server..."
API_URL="http://localhost:8000"
if curl -s -f -o /dev/null "$API_URL/health/ping"; then
    echo "✓ API server is running at $API_URL"
    echo ""
else
    echo "⚠️  API server is not responding at $API_URL"
    echo "   Please start the server with: docker-compose up"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run tests
echo "==================================="
echo "Running Tests"
echo "==================================="
echo ""

# Create environment file if it doesn't exist
ENV_FILE="$POSTMAN_DIR/postman_environment.json"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating environment file..."
    cat > "$ENV_FILE" << EOF
{
  "name": "KodeJudge Local Environment",
  "values": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8000",
      "enabled": true
    }
  ]
}
EOF
fi

# Generate timestamp for report files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
HTML_REPORT="$REPORTS_DIR/test-results_${TIMESTAMP}.html"
JSON_REPORT="$REPORTS_DIR/test-results_${TIMESTAMP}.json"

# Run Newman with options
newman run "$COLLECTION_FILE" \
    --environment "$ENV_FILE" \
    --reporters cli,json,html \
    --reporter-html-export "$HTML_REPORT" \
    --reporter-json-export "$JSON_REPORT" \
    --timeout-request 30000 \
    --delay-request 100 \
    --bail \
    --color on

echo ""
echo "==================================="
echo "Test Results"
echo "==================================="
echo "✓ HTML Report: $HTML_REPORT"
echo "✓ JSON Report: $JSON_REPORT"
echo ""
