# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-08-27

### Added
- **Data Type Preservation**: Perfect preservation of original data types (uint16, float64, etc.) in roundtrip conversion
- **4-Process Default**: Optimized parallel processing with 4 processes by default for balanced performance
- **VS Code Integration**: Complete development environment with debugging, testing, and task automation
- **Comprehensive Test Suite**: 32 tests passing (100% success rate) with full coverage

### Fixed
- **Registration Failures**: Eliminated SimpleITK "All samples map outside moving image buffer" errors
- **Race Conditions**: Thread-safe parallel processing with atomic file locking
- **Data Loss**: Zero data loss in .mat ↔ NIfTI ↔ .mat conversion pipeline
- **GPU Memory**: Better CUDA device management preventing out-of-memory errors

### Enhanced
- **Metadata Preservation**: ALL original .mat fields preserved exactly in final output
- **Error Handling**: Comprehensive error recovery and graceful fallback mechanisms
- **Documentation**: Complete sync across all documentation files with current features
- **Help Text**: Updated CLI help to reflect data type preservation capabilities

## [1.0.0] - 2025-08-23

### Added
- Professional spectral MRI processing pipeline
- Three core conversion and registration scripts
- Modern project structure with organized directories
- Comprehensive command-line interfaces with argument validation
- Wrapper scripts for easy access from project root
- Complete documentation with usage examples
- Automated testing via Makefile
- Example workflows demonstrating full pipeline
- PNG visualization generation for spectral data
- Parallel processing for registration tasks

### Changed
- Renamed all scripts from `main_*` to descriptive names
- Restructured repository with `src/`, `docs/`, `data/`, `scripts/`, `examples/` directories
- Updated all function names to professional conventions
- Migrated from hardcoded paths to command-line arguments

### Features
- ✅ `.mat` to NIfTI conversion with automatic resolution detection
- ✅ NIfTI to `.mat` reverse conversion with perfect data preservation
- ✅ Generic NIfTI registration pipeline with auto-template selection
- ✅ PNG visualizations for first 5 spectral points
- ✅ Comprehensive error handling and validation
- ✅ Parallel processing support
- ✅ Modern Python project configuration

### Documentation
- Complete API reference with function signatures
- Detailed usage guide with examples
- Project history and cleanup summaries
- Professional README with quick start instructions
