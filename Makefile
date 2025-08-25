# DR-CSI Registration Pipeline Makefile

.PHONY: help install test test-unit test-integration test-coverage test-install clean example lint

help:	## Show this help message
	@echo "DR-CSI Registration Pipeline"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:	## Install dependencies in virtual environment
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	@echo "✅ Installation complete. Run 'source .venv/bin/activate'"

test-install:	## Install test dependencies
	pip install -r requirements-test.txt
	@echo "✅ Test dependencies installed"

test:	## Run all unit tests
	./run_tests.sh all

test-unit:	## Run unit tests only
	./run_tests.sh unit

test-integration:	## Run integration tests only  
	./run_tests.sh integration

test-coverage:	## Run tests with coverage report
	./run_tests.sh coverage

test-fast:	## Run fast tests only (skip slow ones)
	./run_tests.sh fast

test-conversion:	## Test conversion modules
	./run_tests.sh conversion

test-registration:	## Test registration modules
	./run_tests.sh registration

test-pipeline:	## Test pipeline modules
	./run_tests.sh pipeline

test-working:	## Run only verified working tests
	./run_tests.sh working

test-sample:	## Test the pipeline with sample data
	@echo "Testing mat to nifti conversion..."
	python convert_mat_to_nifti.py data/data_wip_patient2.mat data/test_output
	@echo "✅ Test conversion successful"
	@echo "Cleaning up test files..."
	rm -rf data/test_output

example:	## Run complete pipeline example
	python examples/run_complete_pipeline.py

lint:	## Check code quality (if you have pylint installed)
	@if command -v pylint >/dev/null 2>&1; then \
		pylint src/*.py; \
	else \
		echo "pylint not found. Install with: pip install pylint"; \
	fi

clean:	## Clean up generated files and cache
	rm -rf __pycache__ src/__pycache__
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "✅ Cleaned up cache files"

show-docs:	## Show documentation locations
	@echo "📖 Documentation files:"
	@echo "  README.md - Quick start and overview"
	@echo "  docs/DOCUMENTATION.md - Detailed usage guide" 
	@echo "  docs/API_REFERENCE.md - Function references"
	@echo "  examples/ - Example workflows"
