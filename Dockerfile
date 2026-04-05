FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json frontend/pnpm-lock.yaml* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash fastlit

COPY pyproject.toml README.md ./
COPY fastlit ./fastlit
COPY examples ./examples
COPY docs ./docs
COPY scripts ./scripts
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .
COPY --from=frontend-builder /app/fastlit/server/static ./fastlit/server/static

# Switch to non-root user
USER fastlit

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_fastlit/health')" || exit 1

CMD ["fastlit", "run", "examples/app.py", "--host", "0.0.0.0", "--port", "8501"]
