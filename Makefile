.PHONY: install test lint run docker-up docker-down benchmark benchmark-detached benchmark-clean research research-quick research-docker publication publication-local publication-clean

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check app benchmark research consulting tests

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

research:
	python -m research.experiments --seeds 30 --cases 2000 --output results/research-v1

research-quick:
	python -m research.experiments --seeds 3 --cases 300 --output results/research-quick

research-docker:
	mkdir -p results
	docker compose --profile research run --rm research

publication:
	mkdir -p results
	docker compose --profile publication up --build --abort-on-container-exit --exit-code-from publication publication

publication-local:
	python -m research.regulatory_validation --output results/publication

publication-clean:
	docker compose --profile publication down --volumes --remove-orphans
	rm -rf results/publication
