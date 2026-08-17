.PHONY: install test lint run docker-up docker-down benchmark benchmark-detached benchmark-clean research research-quick research-docker publication publication-verify publication-statistics publication-load publication-suite publication-local publication-clean

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

publication-verify:
	python -m research.legal_audit --output results/publication/legal-audit.json

publication:
	mkdir -p results
	docker compose --profile publication up --build --abort-on-container-exit --exit-code-from publication publication

publication-statistics:
	python -m research.publication_statistics --predictions results/publication/predictions.csv --output results/publication/statistics.json --samples $${PUBLICATION_BOOTSTRAP_SAMPLES:-10000} --seed $${PUBLICATION_BOOTSTRAP_SEED:-20260817}

publication-load:
	mkdir -p results
	docker compose --profile publication up --build --abort-on-container-exit --exit-code-from load-matrix load-matrix

publication-suite: benchmark publication publication-load

publication-local: publication-verify
	python -m research.regulatory_validation --output results/publication
	$(MAKE) publication-statistics
	python -m research.reliability_report --report results/publication/report.json --output results/publication/calibration-reliability.svg

publication-clean:
	docker compose --profile publication down --volumes --remove-orphans
	rm -rf results/publication results/load-matrix.json results/load-matrix.html
