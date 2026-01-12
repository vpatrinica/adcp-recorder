#!/bin/bash
#
# build.sh - Build and package ADCP Recorder
#
# This script creates distribution packages for the ADCP Recorder,
# runs tests, and generates checksums for verification.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ADCP Recorder - Build Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Step 1: Clean previous builds
echo -e "${YELLOW}[1/7] Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.egg-info
rm -rf adcp_recorder.egg-info
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Step 2: Check Python version
echo -e "${YELLOW}[2/7] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" || {
    echo -e "${RED}✗ Python 3.9+ required${NC}"
    exit 1
}
echo -e "${GREEN}✓ Python version OK${NC}"
echo ""

# Step 3: Install build dependencies
echo -e "${YELLOW}[3/7] Installing build dependencies...${NC}"
python3 -m pip install --quiet --upgrade pip setuptools wheel build
echo -e "${GREEN}✓ Build dependencies installed${NC}"
echo ""

# Step 4: Run tests
echo -e "${YELLOW}[4/7] Running test suite...${NC}"
if [ -d "adcp_recorder/tests" ]; then
    # Install test dependencies
    python3 -m pip install --quiet -e ".[dev]"
    
    # Run tests
    python3 -m pytest adcp_recorder/tests -v --tb=short || {
        echo -e "${RED}✗ Tests failed${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${YELLOW}⚠ No tests directory found, skipping tests${NC}"
fi
echo ""

# Step 5: Generate coverage report (optional)
echo -e "${YELLOW}[5/7] Generating coverage report...${NC}"
if command -v pytest &> /dev/null; then
    python3 -m pytest adcp_recorder/tests --cov=adcp_recorder --cov-report=html --cov-report=term-missing --quiet || {
        echo -e "${YELLOW}⚠ Coverage generation failed, continuing...${NC}"
    }
    if [ -d "htmlcov" ]; then
        echo -e "${GREEN}✓ Coverage report generated in htmlcov/${NC}"
    fi
else
    echo -e "${YELLOW}⚠ pytest not available, skipping coverage${NC}"
fi
echo ""

# Step 6: Build distributions
echo -e "${YELLOW}[6/7] Building distributions...${NC}"
python3 -m build || {
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Distributions built${NC}"
echo ""

# Step 7: Generate checksums
echo -e "${YELLOW}[7/7] Generating checksums...${NC}"
cd dist
sha256sum * > SHA256SUMS
echo -e "${GREEN}✓ Checksums generated${NC}"
echo ""

# Display build artifacts
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Build artifacts:"
ls -lh dist/
echo ""
echo "Checksums:"
cat dist/SHA256SUMS
echo ""

# Verify package integrity
echo -e "${YELLOW}Verifying package integrity...${NC}"
cd "$PROJECT_ROOT"
python3 -m pip install --quiet --force-reinstall dist/*.whl
python3 -c "import adcp_recorder; print(f'Package version: {adcp_recorder.__version__ if hasattr(adcp_recorder, \"__version__\") else \"unknown\"}')" || {
    echo -e "${YELLOW}⚠ Version check failed (this is OK if __version__ is not defined)${NC}"
}
python3 -c "from adcp_recorder.cli.main import cli; print('CLI import: OK')"
echo -e "${GREEN}✓ Package integrity verified${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build artifacts ready for distribution!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "To install the package:"
echo "  pip install dist/adcp_recorder-*.whl"
echo ""
echo "To upload to PyPI (requires credentials):"
echo "  python3 -m pip install twine"
echo "  python3 -m twine upload dist/*"
echo ""
