import json
import logging
import os
import sys
from dataclasses import asdict
from pathlib import Path

import resend
from dotenv import load_dotenv

# Ensure '/app' (the project root in containers) is on sys.path before importing 'shared'
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from shared.models.messages import AppMessage
from shared.tools.MessageHandler import MessageHandler
from shared.tools.MessageProcessor import MessageProcessor
from shared.tools.pipeline_status import update_status
from shared.tools.ServiceBusConsumer import ServiceBusConsumer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationProcessor(MessageProcessor):
    def process(self, message: AppMessage) -> None:
        """Handle incoming Service Bus messages and send them via email using Resend.

        Expects environment variables:
        - RESEND_API_KEY: API key for Resend
        - NOTIFICATION_EMAIL: destination email address
        - NOTIFICATION_FROM_EMAIL (optional): custom "from" address. Defaults to onboarding@resend.dev
        """

        # Required env
        api_key = os.getenv("RESEND_API_KEY", "").strip()
        to_email = os.getenv("NOTIFICATION_EMAIL", "").strip()
        from_email = os.getenv("NOTIFICATION_FROM_EMAIL", "onboarding@resend.dev").strip()
        document_id = message.data.id or message.data.name if message.data else None
        if not api_key:
            logger.error("RESEND_API_KEY is not set; cannot send email.")
            return
        if not to_email:
            logger.error("NOTIFICATION_EMAIL is not set; cannot send email.")
            return

        # Configure Resend client once per call (cheap and thread-safe for this use)
        resend.api_key = api_key
        source = message.data.source if message.data and hasattr(message.data, "source") else "unknown"
        subject = f"New message from pipeline (source: {source})"
        try:
            body_pretty = (
                json.dumps(asdict(message), ensure_ascii=False, indent=2)
                if isinstance(message, dict | list)
                else str(message)
            )
        except Exception:  # noqa: BLE001
            body_pretty = str(message)

        # Basic HTML and text bodies
        html = f"""
        <h2>Nuevo mensaje del pipeline</h2>
        <p><strong>Subject:</strong> {subject}</p>
        <pre style="background:#f6f8fa;padding:12px;border-radius:6px;white-space:pre-wrap;">{body_pretty}</pre>
        """
        text = f"Subject: {subject}\n\n{body_pretty}"

        try:
            result = resend.Emails.send(
                {
                    "from": from_email,
                    "to": [to_email],
                    "subject": f"Open Overheid PoC – {subject}",
                    "html": html,
                    "text": text,
                }
            )
            logger.info("Notification email sent via Resend: %s", result.get("id"))
            if document_id:
                update_status("notification", document_id, "ok", email_id=result.get("id"))
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to send email via Resend: %s", e)
            try:
                if "document_id" in locals() and document_id:
                    update_status("notification", document_id, "error", reason=str(e))
            except Exception:  # noqa: BLE001
                pass


def main() -> None:
    CONNECTION_STRING = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
    INPUT_QUEUE_NAME = os.getenv("AZURE_NOTIFICATION_QUEUE", "notification")

    logger.info(f"Starting notification service.\nInput: {INPUT_QUEUE_NAME} Output: None")

    consumer = ServiceBusConsumer(CONNECTION_STRING, INPUT_QUEUE_NAME)

    try:
        logger.info("\n--- Starting continuous listening ---")
        logger.info("Press Ctrl+C to stop")
        processor = NotificationProcessor()
        message_handler = MessageHandler(processor, None)
        consumer.start_continuous_listening(message_handler)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
