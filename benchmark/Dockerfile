FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace
COPY benchmark ./benchmark
RUN mkdir -p /results

ENTRYPOINT ["python", "-m", "benchmark.runner"]
