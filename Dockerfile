FROM python:3.12-slim AS runtime

ARG VERSION=0.2.0

LABEL org.opencontainers.image.title="VeriWeave Govern" \
      org.opencontainers.image.description="Policy enforcement and evidence governance control plane for enterprise AI agents" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.source="https://github.com/vtavakkoli/veriweave-govern" \
      org.opencontainers.image.licenses="BUSL-1.1"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN useradd --create-home --uid 10001 govern
WORKDIR /app

COPY pyproject.toml README.md LICENSE COMMERCIAL-LICENSE.md ./
COPY app ./app
COPY benchmark ./benchmark
RUN python -m pip install --upgrade pip && python -m pip install .

COPY config ./config
RUN mkdir -p /app/data && chown -R govern:govern /app
USER govern

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')"

CMD ["python", "-m", "app.main"]
