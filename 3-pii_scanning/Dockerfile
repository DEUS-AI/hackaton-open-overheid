ARG BASE_IMAGE_PREFIX=
FROM ${BASE_IMAGE_PREFIX}hackaton-open-overheid-poc-base:latest

COPY 3-pii_scanning/ ./pii_scanning/

CMD ["uv", "run", "--no-sync", "pii_scanning/pii_scanning.py"]
