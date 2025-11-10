#!/bin/bash
# Build script for Lambda deployment package
# This script prepares the backend code and dependencies for AWS Lambda deployment
# Note: SAM CLI handles most of the build, but this ensures data/ is available

set -e  # Exit on error

echo "=========================================="
echo "SpendSense Lambda Build Script"
echo "=========================================="
echo ""

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
BACKEND_DIR="$PROJECT_ROOT/backend"
DATA_DIR="$PROJECT_ROOT/data"
BACKEND_DATA_DIR="$BACKEND_DIR/data"

echo "Project root: $PROJECT_ROOT"
echo "Backend directory: $BACKEND_DIR"
echo ""

# Copy data directory into backend/ for Lambda packaging
# This ensures seed data is available in the Lambda package
if [ -d "$DATA_DIR" ]; then
    echo "Copying data directory to backend/..."
    if [ -d "$BACKEND_DATA_DIR" ]; then
        rm -rf "$BACKEND_DATA_DIR"
    fi
    cp -r "$DATA_DIR" "$BACKEND_DATA_DIR"
    echo "✅ Data directory copied to backend/data/"
else
    echo "⚠️  Warning: data/ directory not found at $DATA_DIR"
    echo "   Seed data will not be available in Lambda"
fi

echo ""
echo "Build preparation complete!"
echo ""
echo "Next steps:"
echo "  1. Run: sam build"
echo "  2. Test locally: sam local start-api"
echo "  3. Deploy: sam deploy --guided"
echo ""
echo "Note: The data/ directory has been copied to backend/data/ for Lambda packaging"
echo ""

