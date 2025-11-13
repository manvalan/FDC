#!/bin/bash

# FDC C++ Build Script for macOS/Linux

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== FDC C++ Build Script ===${NC}\n"

# Check if we're in the cpp directory
if [ ! -f "CMakeLists.txt" ]; then
    echo -e "${RED}Error: CMakeLists.txt not found. Please run from cpp/ directory.${NC}"
    exit 1
fi

# Parse arguments
BUILD_TYPE="Release"
BUILD_GUI=OFF
BUILD_TESTS=ON
BUILD_EXAMPLES=ON
CLEAN=false
RUN_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--debug)
            BUILD_TYPE="Debug"
            shift
            ;;
        -g|--gui)
            BUILD_GUI=ON
            shift
            ;;
        --no-tests)
            BUILD_TESTS=OFF
            shift
            ;;
        --no-examples)
            BUILD_EXAMPLES=OFF
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -t|--test)
            RUN_TESTS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -d, --debug       Build in Debug mode (default: Release)"
            echo "  -g, --gui         Build with Qt GUI support"
            echo "  --no-tests        Don't build tests"
            echo "  --no-examples     Don't build examples"
            echo "  -c, --clean       Clean build directory before building"
            echo "  -t, --test        Run tests after building"
            echo "  -h, --help        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Clean if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}Cleaning build directory...${NC}"
    rm -rf build
fi

# Create build directory
mkdir -p build
cd build

# Configure
echo -e "${GREEN}Configuring CMake...${NC}"
echo "  Build type: $BUILD_TYPE"
echo "  GUI: $BUILD_GUI"
echo "  Tests: $BUILD_TESTS"
echo "  Examples: $BUILD_EXAMPLES"
echo ""

cmake .. \
    -DCMAKE_BUILD_TYPE=$BUILD_TYPE \
    -DBUILD_GUI=$BUILD_GUI \
    -DBUILD_TESTS=$BUILD_TESTS \
    -DBUILD_EXAMPLES=$BUILD_EXAMPLES

# Build
echo -e "\n${GREEN}Building...${NC}"
cmake --build . -j$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)

# Run tests if requested
if [ "$RUN_TESTS" = true ] && [ "$BUILD_TESTS" = "ON" ]; then
    echo -e "\n${GREEN}Running tests...${NC}"
    ctest --output-on-failure
fi

# Success message
echo -e "\n${GREEN}✓ Build completed successfully!${NC}"
echo -e "\nBinaries are in: ${YELLOW}build/bin/${NC}"
echo -e "Libraries are in: ${YELLOW}build/lib/${NC}"

if [ "$BUILD_EXAMPLES" = "ON" ]; then
    echo -e "\nTo run basic example:"
    echo -e "  ${YELLOW}./build/bin/basic_example${NC}"
fi

if [ "$BUILD_TESTS" = "ON" ]; then
    echo -e "\nTo run tests:"
    echo -e "  ${YELLOW}cd build && ctest${NC}"
fi
