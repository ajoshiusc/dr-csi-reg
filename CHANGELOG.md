# Changelog

All notable changes to this project will be documented in this file.

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
