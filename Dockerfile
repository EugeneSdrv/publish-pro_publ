FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the application dependencies.
WORKDIR /app

# Copy the application into the container.
COPY uv.lock pyproject.toml /app/

ENV PATH="/app/.venv/bin:$PATH"

RUN uv venv
RUN uv sync --frozen --no-cache

# Copy the application into the container.
COPY . /app

# Run the application.
CMD ["uv run fastapi dev app/main.py --host ${SERVICE_HOST} --port ${SERVICE_PORT}"]
