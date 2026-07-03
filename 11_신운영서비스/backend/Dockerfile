FROM python:3.12-slim

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml ./
RUN uv sync --no-dev
COPY heatgrid_ops ./heatgrid_ops
CMD ["uv", "run", "uvicorn", "heatgrid_ops.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
