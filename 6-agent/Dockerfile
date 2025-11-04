ARG BASE_IMAGE_PREFIX=
FROM ${BASE_IMAGE_PREFIX}hackaton-open-overheid-poc-base:latest

WORKDIR /app

# Install only the agent dependency group into the existing project venv
# Note: pyproject.toml and uv.lock are already present from the base image at /app
RUN uv sync --frozen --group agent --no-dev

# Copy agent source from build context (which is 6-agent/)
COPY 6-agent ./agent/

# Run agent using the shared venv
CMD ["uv", "run", "--no-sync", "agent/agent.py", "dev"]
