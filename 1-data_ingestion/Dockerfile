ARG BASE_IMAGE_PREFIX=
# If set (e.g. aitacr.azurecr.io/), pulls base image from registry
FROM ${BASE_IMAGE_PREFIX}hackaton-open-overheid-poc-base:latest

# Keep internal path stable
COPY 1-data_ingestion/ ./data_ingestion/

CMD ["uv", "run", "--no-sync", "data_ingestion/data_ingestion.py"]
