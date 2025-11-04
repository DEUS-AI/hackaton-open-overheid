ARG BASE_IMAGE_PREFIX=
FROM ${BASE_IMAGE_PREFIX}hackaton-open-overheid-poc-base:latest

COPY 4-5-embedding_generator/ ./embedding_generator/

CMD ["uv", "run", "embedding_generator/embedding_generator.py"]