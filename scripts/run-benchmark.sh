#!/usr/bin/env sh
set -eu

mkdir -p results

docker compose up --build -d test
container_id="$(docker compose ps -a -q test)"

if [ -z "$container_id" ]; then
  echo "Benchmark container was not created." >&2
  exit 2
fi

while [ "$(docker inspect -f '{{.State.Running}}' "$container_id")" = "true" ]; do
  sleep 1
done

exit_code="$(docker inspect -f '{{.State.ExitCode}}' "$container_id")"
docker compose logs --no-color test

if [ "$exit_code" -ne 0 ]; then
  echo "Benchmark failed with exit code $exit_code." >&2
  exit "$exit_code"
fi

echo "Benchmark passed. Open results/benchmark-report.html"
