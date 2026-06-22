# Container image for a single MCP agent server (Cop or Thief).
# Build:  docker build -t cop-thief .
# Run Cop:    docker run -e MCP_TOKEN=secret -p 8001:8001 cop-thief cop-server   --host 0.0.0.0 --port 8001
# Run Thief:  docker run -e MCP_TOKEN=secret -p 8002:8002 cop-thief thief-server --host 0.0.0.0 --port 8002
FROM python:3.12-slim

# uv is the only package manager used in this project.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY config ./config

# Install into a project venv from the locked dependencies.
RUN uv sync --frozen --no-dev

EXPOSE 8001 8002

# Pass "cop-server" or "thief-server" (plus --host/--port) as the run command.
ENTRYPOINT ["uv", "run"]
CMD ["cop-server", "--host", "0.0.0.0", "--port", "8001"]
