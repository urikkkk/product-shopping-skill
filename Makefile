.PHONY: install dev test lint fmt run dry-run web clean

# Install production dependencies
install:
	pip install -e .

# Install with dev + google extras
dev:
	pip install -e ".[all]"

# Run the full test suite
test:
	python -m pytest tests/ -v --tb=short

# Run tests with coverage
test-cov:
	python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Lint the codebase
lint:
	python -m ruff check src/ scripts/ tests/

# Auto-format
fmt:
	python -m ruff format src/ scripts/ tests/
	python -m ruff check --fix src/ scripts/ tests/

# Run the full pipeline (default: XLSX output, ZIP 11201)
run:
	python -m scripts.run_pipeline --zip 11201 --out xlsx

# Dry run (no writes, just show what would happen)
dry-run:
	python -m scripts.run_pipeline --zip 11201 --dry-run

# Serve the web app locally
web:
	@echo "Opening web/keyboard_finder.html ..."
	@open web/keyboard_finder.html 2>/dev/null || xdg-open web/keyboard_finder.html 2>/dev/null || echo "Open web/keyboard_finder.html in your browser"

# Clean generated files
clean:
	rm -rf output/ build/ dist/ *.egg-info __pycache__ .pytest_cache .ruff_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
