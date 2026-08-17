FROM python:3.13-slim AS runtime

ARG VERSION=0.4.0

LABEL org.opencontainers.image.title="VeriWeave Govern" \
      org.opencontainers.image.description="Deterministic policy enforcement, evidence governance, and scientific benchmarking for enterprise AI agents" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.source="https://github.com/vtavakkoli/veriweave-govern" \
      org.opencontainers.image.licenses="Apache-2.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN useradd --create-home --uid 10001 govern
WORKDIR /app

COPY pyproject.toml README.md LICENSE NOTICE ./
COPY app ./app
COPY benchmark ./benchmark
COPY research ./research
COPY consulting ./consulting
RUN python -m pip install --upgrade pip && python -m pip install .

COPY config ./config
COPY standards ./standards
RUN mkdir -p /app/data /app/results && chown -R govern:govern /app
USER govern

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')"

CMD ["python", "-m", "app.main"]
