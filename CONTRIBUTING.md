# Contributing to DR-CSI Registration Pipeline

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/ajoshiusc/dr-csi-reg.git
cd dr-csi-reg
```

2. **Set up development environment**
```bash
make install
source .venv/bin/activate
```

3. **Test the installation**
```bash
make test
```

## Project Structure

- `src/` - Core source code and modules
- `docs/` - Documentation files
- `data/` - Sample data and outputs  
- `scripts/` - Utility scripts and job files
- `examples/` - Example workflows
- Root wrapper scripts for easy access

## Making Changes

### Code Style
- Follow PEP 8 Python style guidelines
- Use descriptive function and variable names
- Include docstrings for all functions
- Keep lines under 120 characters

### Adding Features
1. Create new modules in `src/` directory
2. Add wrapper scripts in root if needed for CLI access
3. Update documentation in `docs/`
4. Add examples to `examples/` directory
5. Update tests and Makefile if necessary

### Testing
- Run `make test` before submitting changes
- Test with sample data in `data/` directory
- Verify all wrapper scripts work correctly
- Check that documentation is accurate

## Submission Guidelines

1. **Issues**: Use GitHub issues for bug reports and feature requests
2. **Pull Requests**: 
   - Create feature branches from `main`
   - Include clear descriptions of changes
   - Update relevant documentation
   - Ensure all tests pass

## Code Review Process

1. All changes require review before merging
2. Maintainers will review for:
   - Code quality and style
   - Documentation completeness
   - Test coverage
   - Compatibility with existing functionality

## Questions?

Feel free to open an issue for questions about contributing or development setup.
