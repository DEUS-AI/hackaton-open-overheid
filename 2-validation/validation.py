#!/usr/bin/env python3
"""
Validation Service

This module is responsible for validating documents from the data ingestion service,
performing validation checks, and forwarding valid documents to the PII scanning service.
"""

import datetime
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure '/app' (the project root in containers) is on sys.path before importing 'shared'
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import shared modules after path is set
from shared.models.messages import AppMessage, ValidationInfo
from shared.tools.MessageProcessor import MessageProcessor
from shared.tools.pipeline_status import update_status
from shared.tools.ServiceBusHandler import ServiceBusHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class ValidationProcessor(MessageProcessor):
    """Processor for handling document validation."""

    @staticmethod
    def validate_document(message_data: AppMessage) -> tuple[bool, str | None, AppMessage]:
        """
        Validate the document data from the incoming message.

        Args:
            message_data: The document data to validate

        Returns:
            A tuple containing:
            - Boolean indicating if validation passed
            - Optional error message if validation failed
            - The validated (and potentially enhanced) message data
        """
        try:
            logger.info("Validating document...")

            # Extract data section
            data = message_data.data
            if not data:
                return False, "Missing 'data' section in message", message_data

            # Validate source
            if not data.source:
                return False, "Missing document source", message_data

            # Check if extracted text is present
            payload = data.payload
            if not payload:
                return False, "Missing payload in document data", message_data

            extracted_text = payload.get("extracted_text")
            if not extracted_text:
                return False, "Missing extracted text in payload", message_data

            # Validate text content (minimum length)
            if len(extracted_text) < 10:  # Arbitrary minimum length
                return (
                    False,
                    "Document text too short, possibly empty document",
                    message_data,
                )

            # Add validation timestamp
            message_data.validation = ValidationInfo(
                timestamp=datetime.datetime.now(),
                status="valid",
                message="Document passed validation checks",
            )

            # Return validated message
            return True, None, message_data

        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-except
            logger.error("Error during validation: %s", e)
            return False, f"Validation error: {str(e)}", message_data

    def process(self, message: AppMessage) -> AppMessage | None:  # type: ignore[override]
        """
        Process incoming message, validate document, and prepare for PII
        scanning.

            Args:
                message: The incoming message to process

            Returns:
                Processed and validated message, or None if validation fails
        """
        try:
            if message.data is None:
                logger.error("Missing data block in message")
                logger.info("Processing message from unknown source")
                return None

            logger.info(
                "Processing message from %s",
                message.data.source or "unknown source",
            )

            document_id = message.data.id or message.data.name
            if document_id:
                update_status("validation", document_id, "started")

            # Validate the document
            # Use the static method of this same class
            is_valid, error_message, app_msg_validated = ValidationProcessor.validate_document(message)

            if not is_valid:
                if document_id:
                    update_status("validation", document_id, "error", reason=error_message or "unknown")
                logger.warning(
                    "Document validation failed %s: %s",
                    message.data.name or "unknown name",
                    error_message,
                )
                return None

            logger.info("Document successfully validated")

            if document_id:
                update_status("validation", document_id, "ok")
            return app_msg_validated

        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-except
            logger.error("Error processing message: %s", e)
            import traceback

            logger.error(traceback.format_exc())
            return None


def main() -> None:
    """Main entry point for the Validation Service."""
    try:
        # Get connection parameters from environment variables
        connection_string = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
        input_queue = os.getenv("AZURE_VALIDATION_QUEUE", "validation")
        output_queue = os.getenv("AZURE_PII_SCANNING_QUEUE", "pii-scanning")

        if not connection_string:
            raise ValueError("AZURE_SERVICEBUS_CONNECTION_STRING not set")

        # Create a service bus handler with the validation processor
        handler = ServiceBusHandler(
            connection_string=connection_string,
            input_queue=input_queue,
            output_queue=output_queue,
            message_processor=ValidationProcessor(),
            message_subject="document_validated",
        )

        # Start the service
        handler.start()
    except Exception as e:  # noqa: BLE001  # pylint: disable=broad-except
        logger.error("Failed to start Validation Service: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
