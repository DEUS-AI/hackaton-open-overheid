ARG BASE_IMAGE_PREFIX=
FROM ${BASE_IMAGE_PREFIX}hackaton-open-overheid-poc-base:latest

COPY 4-metadata_extractor/ ./metadata_extractor/

CMD ["uv", "run", "--no-sync", "metadata_extractor/metadata_extractor.py"]
