# Unit Tests Documentation

## Overview

The DR-CSI Registration Pipeline includes a comprehensive unit test suite that validates all major components and functionality. The tests are organized into several modules, each focusing on specific aspects of the pipeline.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── test_conversion.py          # Tests for .mat ↔ NIfTI conversion
├── test_registration_pipeline.py  # Tests for registration pipeline
├── test_registration.py        # Tests for core registration functions
├── test_utils.py              # Tests for utility functions
├── test_warping.py            # Tests for image warping operations
├── test_integration.py        # Integration and workflow tests
└── test_imports.py            # Import and dependency tests
```

## Test Categories

### 1. Import Tests (`test_imports.py`)
- ✅ **Python version compatibility** - Ensures Python 3.8+
- ✅ **Required package availability** - numpy, scipy, nibabel, SimpleITK, matplotlib
- ✅ **Module imports** - All pipeline modules import correctly
- ✅ **Optional dependencies** - torch, monai, opencv-python (warnings if missing)

### 2. Conversion Tests (`test_conversion.py`)
- **SpectralMatToNifti Tests**:
  - Basic .mat to NIfTI conversion
  - Custom resolution handling
  - Error handling for missing files
  - Invalid data shape handling
  
- **SpectralNiftiToMat Tests**:
  - Basic NIfTI to .mat conversion
  - Handling missing original reference
  - Empty directory handling
  
- **Round-trip Tests**:
  - Data integrity preservation (.mat → NIfTI → .mat)
  - Resolution preservation
  - Shape consistency

### 3. Registration Tests (`test_registration.py`)
- **Core Registration**:
  - Transform initialization (Euler3D)
  - Registration method setup
  - Nonlinear registration execution
  - Error handling (missing files, SimpleITK errors)
  
- **Transform Operations**:
  - Identity transform creation
  - Different image sizes handling
  - Registration parameter configuration

### 4. Pipeline Tests (`test_registration_pipeline.py`)
- **Directory Registration**:
  - Template selection algorithms
  - Parallel processing
  - Error handling and recovery
  - Output directory creation
  
- **Command Line Interface**:
  - Argument parsing
  - Main function execution

### 5. Utility Tests (`test_utils.py`)
- **File Operations**:
  - File existence validation
  - Directory creation
  - NIfTI file detection
  
- **System Utilities**:
  - GPU availability checking
  - Logging functionality
  
- **Data Validation**:
  - Image dimension validation
  - Spectral data shape validation
  - Resolution array validation

### 6. Warping Tests (`test_warping.py`)
- **Image Warping**:
  - Transform application
  - Identity transform handling
  - Error conditions
  
- **Transform Utilities**:
  - Transform composition
  - Transform inversion
  - Image interpolation
  - Resampling operations

### 7. Integration Tests (`test_integration.py`)
- **Full Workflow**:
  - Complete pipeline execution
  - Error handling across workflow
  - Data consistency verification
  
- **Command Line Interfaces**:
  - Wrapper script testing
  - Workflow script execution
  
- **Performance & Scaling**:
  - Large dataset handling
  - Multiprocessing behavior

## Running Tests

### Basic Test Execution
```bash
# Run all tests
./run_tests.sh all

# Run specific test categories
./run_tests.sh unit
./run_tests.sh integration
./run_tests.sh fast

# Run tests for specific modules
./run_tests.sh conversion
./run_tests.sh registration
./run_tests.sh pipeline
```

### Using Makefile
```bash
# Install test dependencies
make test-install

# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-coverage
```

### Direct pytest Usage
```bash
# Run with virtual environment
.venv/bin/python -m pytest tests/ -v

# Run specific test file
.venv/bin/python -m pytest tests/test_imports.py -v

# Run with coverage
.venv/bin/python -m pytest tests/ --cov=src --cov-report=html -v
```

## Test Results Summary

### ✅ Passing Tests
- **Import Tests**: All 9 tests passing
  - Python version compatibility ✅
  - Required packages available ✅
  - All modules import successfully ✅
  - Optional packages detected ✅

### 🔧 Tests Requiring Actual Data
Some tests are designed to work with mocked data or may require real data files for full validation:
- Conversion tests with actual .mat files
- Registration tests with real NIfTI images
- Full workflow integration tests

### 📊 Coverage Goals
The test suite aims for:
- **Unit Test Coverage**: >90% of core functions
- **Integration Coverage**: Complete workflow validation
- **Error Handling**: All error conditions tested

## Mocking Strategy

The tests use extensive mocking to:
- **Isolate Components**: Test individual functions without dependencies
- **Simulate Conditions**: Test error conditions safely
- **Speed Up Tests**: Avoid slow I/O and computation
- **Ensure Reliability**: Tests don't depend on external files

## Continuous Integration

The test suite is designed for:
- **Fast Feedback**: Quick tests run in <30 seconds
- **Comprehensive Validation**: Full suite provides thorough coverage
- **Error Detection**: Catches regressions early
- **Documentation**: Tests serve as usage examples

## Future Enhancements

Planned test improvements:
- **Performance Benchmarks**: Timing and memory usage tests
- **Visual Validation**: Image comparison tests
- **Hardware Tests**: GPU-specific functionality
- **Stress Tests**: Large dataset handling validation
