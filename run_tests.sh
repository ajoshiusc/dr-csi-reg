#!/bin/bash
"""
Test Runner Script for DR-CSI Registration Pipeline
This script runs the complete test suite with different configurations.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if pytest is installed
check_pytest() {
    if ! .venv/bin/python -c "import pytest" 2>/dev/null; then
        print_error "pytest is not installed. Installing test requirements..."
        .venv/bin/pip install -r requirements-test.txt
    fi
}

# Run specific test categories
run_unit_tests() {
    print_status "Running unit tests..."
    .venv/bin/python -m pytest tests/ -m "not integration and not slow" -v
}

run_integration_tests() {
    print_status "Running integration tests..."
    .venv/bin/python -m pytest tests/test_integration.py -v
}

run_all_tests() {
    print_status "Running all tests..."
    .venv/bin/python -m pytest tests/ -v
}

run_coverage() {
    print_status "Running tests with coverage..."
    .venv/bin/python -m pytest tests/ --cov=src --cov-report=html --cov-report=term -v
}

run_fast_tests() {
    print_status "Running fast tests only..."
    .venv/bin/python -m pytest tests/ -m "not slow" -v
}

run_specific_module() {
    local module=$1
    print_status "Running tests for module: $module"
    .venv/bin/python -m pytest tests/test_$module.py -v
}

run_working_tests() {
    print_status "Running working tests only..."
    .venv/bin/python -m pytest tests/test_imports.py tests/test_working_conversion.py -v
}

# Main script logic
main() {
    local test_type=${1:-"all"}
    
    print_status "DR-CSI Registration Pipeline Test Runner"
    print_status "========================================="
    
    # Check dependencies
    check_pytest
    
    case $test_type in
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "coverage")
            run_coverage
            ;;
        "fast")
            run_fast_tests
            ;;
        "conversion")
            run_specific_module "conversion"
            ;;
        "registration")
            run_specific_module "registration"
            ;;
        "pipeline")
            run_specific_module "registration_pipeline"
            ;;
        "utils")
            run_specific_module "utils"
            ;;
        "warping")
            run_specific_module "warping"
            ;;
        "imports")
            run_specific_module "imports"
            ;;
        "working")
            run_working_tests
            ;;
        "all")
            run_all_tests
            ;;
        *)
            print_error "Unknown test type: $test_type"
            print_status "Available test types:"
            print_status "  unit         - Run unit tests only"
            print_status "  integration  - Run integration tests only" 
            print_status "  coverage     - Run tests with coverage report"
            print_status "  fast         - Run fast tests only"
            print_status "  conversion   - Test conversion modules"
            print_status "  registration - Test registration modules"
            print_status "  pipeline     - Test pipeline modules"
            print_status "  utils        - Test utility modules"
            print_status "  warping      - Test warping modules"
            print_status "  imports      - Test import functionality"
            print_status "  working      - Test only verified working tests"
            print_status "  all          - Run all tests (default)"
            exit 1
            ;;
    esac
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_status "All tests passed!"
    else
        print_error "Some tests failed!"
    fi
    
    return $exit_code
}

# Run main function with all arguments
main "$@"
