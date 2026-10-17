FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
# Demo data (database + rendered PDFs) ships in the image; the free host's disk is ephemeral.
ENV PAPER_DATA=/app/demo_data PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["sh", "-c", "uv run --no-dev uvicorn paper.web:app --host 0.0.0.0 --port ${PORT:-8000}"]
