ARG BASE_IMAGE_PREFIX=
FROM ${BASE_IMAGE_PREFIX}hackaton-open-overheid-poc-base:latest

COPY 6-1-agent-backend/ ./agent-backend/

CMD ["uv", "run", "--no-sync", "agent-backend/main.py"]
