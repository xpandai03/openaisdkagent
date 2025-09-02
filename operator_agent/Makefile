.PHONY: setup run smoke test clean help vectorstore-reset test-filesearch

# Default target
help:
	@echo "Available targets:"
	@echo "  setup           - Create venv and install dependencies"
	@echo "  run             - Start the API server"
	@echo "  smoke           - Run smoke tests with curl"
	@echo "  test            - Run Python tests"
	@echo "  test-filesearch - Test FileSearch functionality"
	@echo "  vectorstore-reset - Clear vector store state"
	@echo "  clean           - Remove virtual environment and cache"

setup:
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	@echo "Installing dependencies..."
	./.venv/bin/pip install --upgrade pip
	./.venv/bin/pip install -r requirements.txt
	@echo "Setup complete! Don't forget to:"
	@echo "1. Copy .env.example to .env"
	@echo "2. Add your OPENAI_API_KEY to .env"
	@echo "3. Run: source .venv/bin/activate"

run:
	@echo "Starting Operator Agent API..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

smoke:
	@echo "Testing health endpoint..."
	@curl -s http://127.0.0.1:8000/healthz | python3 -m json.tool
	@echo "\nTesting basic task..."
	@curl -s -X POST http://127.0.0.1:8000/run \
		-H "Content-Type: application/json" \
		-d '{"task":"What is Python?"}' | python3 -m json.tool
	@echo "\nTesting search task..."
	@curl -s -X POST http://127.0.0.1:8000/run \
		-H "Content-Type: application/json" \
		-d '{"task":"Search for the latest Python features"}' | python3 -m json.tool
	@echo "\nTesting FileSearch - jacket preferences..."
	@curl -s -X POST http://127.0.0.1:8000/run \
		-H "Content-Type: application/json" \
		-d '{"task":"What are the jacket preferences in our documentation?"}' | python3 -m json.tool
	@echo "\nTesting FileSearch - Tokyo shops..."
	@curl -s -X POST http://127.0.0.1:8000/run \
		-H "Content-Type: application/json" \
		-d '{"task":"Where can I shop for Patagonia in Tokyo?"}' | python3 -m json.tool

test:
	@echo "Running tests..."
	python -m pytest tests/ -v

test-filesearch:
	@echo "Testing FileSearch functionality..."
	@python tests/test_filesearch.py

test-computer:
	@echo "Testing Computer Use in MOCK mode..."
	@curl -s -X POST http://127.0.0.1:8000/run \
		-H "Content-Type: application/json" \
		-d '{"task":"Open patagonia.com and click on jackets"}' | python3 -m json.tool

bridge:
	@echo "Starting Computer Use LIVE bridge (scaffold)..."
	@python -m app.runtimes.computer_live_bridge

vectorstore-reset:
	@echo "Clearing vector store state..."
	@rm -rf .state
	@echo "State cleared. Vector store will be recreated on next run."

clean:
	@echo "Cleaning up..."
	rm -rf .venv
	rm -rf __pycache__
	rm -rf app/__pycache__
	rm -rf tests/__pycache__
	rm -rf .pytest_cache
	rm -rf .state
	@echo "Clean complete!"