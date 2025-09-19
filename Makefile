# DR-CSI Registration Module Makefile

.PHONY: help install clean example lint

help:	## Show this help message
	@echo "DR-CSI Registration Module (Diffusion-Relaxation Suite)"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:	## Install dependencies in virtual environment
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	@echo "✅ Installation complete. Run 'source .venv/bin/activate'"
	rm -rf data/test_output

example:	## Run complete module workflow example
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
