ARG BASE_IMAGE_PREFIX=
FROM ${BASE_IMAGE_PREFIX}hackaton-open-overheid-poc-base:latest

COPY 2-validation/ ./validation/

CMD ["uv", "run", "--no-sync", "validation/validation.py"]
