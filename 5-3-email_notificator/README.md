Email Notificator

This service listens to the AZURE_NOTIFICATION_QUEUE and emails the message payload using Resend.

Environment variables
- AZURE_SERVICEBUS_CONNECTION_STRING
- AZURE_NOTIFICATION_QUEUE
- RESEND_API_KEY
- NOTIFICATION_EMAIL
- NOTIFICATION_FROM_EMAIL (optional, defaults to onboarding@resend.dev)

Run locally
- Install deps: uv sync
- Run: uv run email_notificator/email_notificator.py
