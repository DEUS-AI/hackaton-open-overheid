ARG BASE_IMAGE_PREFIX=
FROM ${BASE_IMAGE_PREFIX}hackaton-open-overheid-poc-base:latest

COPY 5-3-email_notificator/ ./email_notificator/

CMD ["uv", "run", "--no-sync", "email_notificator/email_notificator.py"]
