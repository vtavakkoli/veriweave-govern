.PHONY: install test lint run docker-up docker-down benchmark benchmark-detached benchmark-clean

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check app benchmark tests

run:
	python -m app.main

docker-up:
	docker compose up --build -d govern

docker-down:
	docker compose down

benchmark:
	mkdir -p results
	docker compose up --build --abort-on-container-exit --exit-code-from test test

benchmark-detached:
	sh scripts/run-benchmark.sh

benchmark-clean:
	docker compose rm -sf test
	rm -f results/benchmark-report.html results/benchmark-results.json
