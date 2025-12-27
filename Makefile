.PHONY: test venv deps clean lint format release version typecheck test-simple help

help:
	@echo "Home Assistant Ollama Conversation Integration - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  help          - Show this help message"
	@echo "  version       - Display current version from manifest.json"
	@echo "  venv          - Create Python virtual environment"
	@echo "  deps          - Install dependencies"
	@echo "  test          - Run full test suite with coverage"
	@echo "  test-simple   - Run basic tests without coverage"
	@echo "  lint          - Check code style with ruff"
	@echo "  format        - Format code with black and isort"
	@echo "  typecheck     - Type check with mypy"
	@echo "  clean         - Remove generated files and venv"
	@echo "  release       - Create and push git tag, create GitHub release (runs tests)"
	@echo "  release-quick - Create release without running tests"
	@echo ""
	@echo "Example workflow:"
	@echo "  make test          # Run tests"
	@echo "  make release       # Create release (after updating version in manifest.json)"

venv:
	python3 -m venv .venv
	@echo "Virtual environment created. Activate with: source .venv/bin/activate"

deps: venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements-test.txt
	@echo "Dependencies installed"

test: deps
	.venv/bin/pytest custom_components/ollama_conversation/ --cov=custom_components.ollama_conversation --cov-report=term-missing --cov-report=html
	@echo "Tests complete. Coverage report: htmlcov/index.html"

test-simple: deps
	.venv/bin/pytest custom_components/ollama_conversation/test_integration.py -v
	@echo "Basic tests passed"

clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf custom_components/ollama_conversation/__pycache__
	rm -rf htmlcov
	rm -rf .pytest_cache
	rm -f .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned up generated files"

lint: deps
	@echo "Linting code..."
	.venv/bin/ruff check custom_components/ || true

format: deps
	@echo "Formatting code..."
	.venv/bin/black custom_components/
	.venv/bin/isort custom_components/

typecheck: deps
	@echo "Type checking..."
	.venv/bin/mypy custom_components/ || true

version:
	@python3 -c "import json; print(f'Current version: {json.load(open("custom_components/ollama_conversation/manifest.json"))["version"]}')"
	@echo "Git tag would be: v$(shell python3 -c "import json; print(json.load(open('custom_components/ollama_conversation/manifest.json'))['version'])")"

release: test-simple
	@echo "Starting release process..."
	@VERSION=$$(python3 -c "import json; print(json.load(open('custom_components/ollama_conversation/manifest.json'))['version'])") && \
	if git diff-index --quiet HEAD --; then \
		if git tag | grep -q "v$$VERSION"; then \
			echo "❌ Error: Tag v$$VERSION already exists"; \
			exit 1; \
		else \
			echo "✅ Creating tag v$$VERSION" && \
			git tag -a "v$$VERSION" -m "Release v$$VERSION" && \
			echo "✅ Pushing tag to origin..." && \
			git push origin "v$$VERSION" && \
			echo "✅ Creating GitHub release for v$$VERSION..." && \
			gh release create "v$$VERSION" \
				--title "Release v$$VERSION" \
				--notes-file CHANGELOG.md \
				--draft=false; \
			echo "🎉 Release v$$VERSION created successfully!"; \
		fi \
	else \
		echo "❌ Error: Working tree has uncommitted changes"; \
		echo "Please commit or stash your changes first."; \
		exit 1; \
	fi

release-quick:
	@echo "Starting quick release process (without tests)..."
	@VERSION=$$(python3 -c "import json; print(json.load(open('custom_components/ollama_conversation/manifest.json'))['version'])") && \
	if git diff-index --quiet HEAD --; then \
		if git tag | grep -q "v$$VERSION"; then \
			echo "❌ Error: Tag v$$VERSION already exists"; \
			exit 1; \
		else \
			echo "✅ Creating tag v$$VERSION" && \
			git tag -a "v$$VERSION" -m "Release v$$VERSION" && \
			echo "✅ Pushing tag to origin..." && \
			git push origin "v$$VERSION" && \
			echo "✅ Creating GitHub release for v$$VERSION..." && \
			gh release create "v$$VERSION" \
				--title "Release v$$VERSION" \
				--notes-file CHANGELOG.md \
				--draft=false; \
			echo "🎉 Release v$$VERSION created successfully!"; \
		fi \
	else \
		echo "❌ Error: Working tree has uncommitted changes"; \
		echo "Please commit or stash your changes first."; \
		exit 1; \
	fi

# Deploy to local Home Assistant for testing
deploy-local:
	@echo "Deploying to local Home Assistant..."
	@if [ -d "/config/custom_components" ]; then \
		cp -r custom_components/ollama_conversation /config/custom_components/ && \
		echo "✅ Deployed to /config/custom_components/ollama_conversation"; \
	else \
		echo "❌ Error: /config/custom_components not found"; \
		echo "Update the path in Makefile or use: make deploy-remote"; \
		exit 1; \
	fi

# Deploy to remote Home Assistant (sanctuarymoon)
deploy-remote:
	@echo "Deploying to sanctuarymoon.local..."
	@read -p "Enter SSH user for sanctuarymoon.local: " USER && \
	scp -r custom_components/ollama_conversation $$USER@sanctuarymoon.local:/config/custom_components/ && \
	echo "✅ Deployed to sanctuarymoon.local:/config/custom_components/ollama_conversation" && \
	echo "⚠️  Remember to restart Home Assistant!"
