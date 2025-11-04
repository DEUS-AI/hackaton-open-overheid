ARG BASE_IMAGE_PREFIX=
FROM ${BASE_IMAGE_PREFIX}hackaton-open-overheid-poc-base:latest

COPY 5-1-data_storage/ ./data_storage/

CMD ["uv", "run", "--no-sync", "data_storage/data_storage.py"]
