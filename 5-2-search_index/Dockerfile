ARG BASE_IMAGE_PREFIX=
FROM ${BASE_IMAGE_PREFIX}hackaton-open-overheid-poc-base:latest

COPY 5-2-search_index/ ./search_index/

CMD ["uv", "run", "--no-sync", "search_index/search_index.py"]
