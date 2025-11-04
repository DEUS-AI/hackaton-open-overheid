#!/usr/bin/env python3
"""
Data Ingestion Service

This module ingests documents from various sources, extracts text for PDFs,
and forwards results to the validation service via Azure Service Bus.
"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path

import PyPDF2
import requests  # type: ignore
import urllib3
from dotenv import load_dotenv

# Ensure '/app' (the project root in containers) is on sys.path before importing 'shared'
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import shared modules after path is set
from shared.models.messages import AppMessage
from shared.tools.MessageProcessor import MessageProcessor
from shared.tools.pipeline_status import update_status
from shared.tools.ServiceBusHandler import ServiceBusHandler

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
# Set third-party loggers to a higher level to reduce noise
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class DataIngestionMessageProcessor(MessageProcessor):
    """Processor that downloads PDFs, extracts text, and builds AppMessage."""

    @staticmethod
    def download_and_extract_pdf_text(url: str) -> str | None:
        """
        Download PDF from URL and extract its text content.

        Args:
            url: URL of the PDF document to download and process

        Returns:
            Extracted text content from the PDF, or None if an error occurs
        """
        temp_file_path = None

        try:
            # If the 'url' is actually a local path (shared volume), read directly
            if os.path.exists(url):  # local absolute or relative path
                logger.info("Reading local PDF file: %s", url)
                temp_file_path = url
            else:
                # Download the PDF without SSL verification
                logger.info(f"Downloading PDF from {url}...")
                response = requests.get(url, verify=False, timeout=30)

                if response.status_code != 200:
                    logger.error(f"Error downloading PDF: {response.status_code}")
                    return None

                # Use a temporary file to save the PDF
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                    temp_file_path = temp_file.name
                    temp_file.write(response.content)

            # Extract text from the PDF
            with open(temp_file_path, "rb") as file:
                try:
                    pdf_reader = PyPDF2.PdfReader(file)

                    # Extract text from all pages
                    text = ""
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:  # Some pages may not have text
                            text += page_text + "\n"

                    logger.info(
                        "Successfully extracted text from PDF (%d chars)",
                        len(text),
                    )
                    return text

                except Exception as e:  # noqa: BLE001
                    logger.error(f"Error processing PDF: {e}")
                    return None

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error in download_and_extract_pdf_text: {e}")
            return None

        finally:
            # Clean up only if it was a downloaded temp file (not an existing path)
            if temp_file_path and os.path.exists(temp_file_path):
                is_local_source = os.path.exists(url)
                safe_to_remove = True
                if is_local_source:
                    # If original path is the same local file, don't delete
                    try:
                        if os.path.samefile(temp_file_path, url):
                            safe_to_remove = False
                    except OSError:
                        pass
                if safe_to_remove and os.path.basename(temp_file_path).startswith("tmp"):
                    try:
                        os.remove(temp_file_path)
                    except OSError:
                        pass

    def process(self, message: AppMessage) -> AppMessage | None:
        try:
            if message.data is None:
                logger.error("Missing data block in message")
                return None
            logger.info(
                "Processing message from %s",
                (getattr(message.data, "source", None) or "data_ingestion_service"),
            )

            # Determine file extension
            file_extension = (message.data.extension or "").lower()

            # Only process PDF files
            if file_extension != "pdf":
                logger.warning(
                    "Ignoring non-PDF file: %s.%s",
                    message.data.name or "unknown",
                    file_extension,
                )
                return None

            # Get PDF URL
            pdf_url = message.data.url
            if not pdf_url:
                logger.error("No URL provided in the message")
                return None

            # Download and extract text from PDF
            extracted_text = DataIngestionMessageProcessor.download_and_extract_pdf_text(pdf_url)
            document_id = message.data.id or message.data.name
            if not extracted_text:
                if document_id:
                    update_status("ingestion", document_id, "error", reason="extraction_failed")
                return None

            # Merge payload with extracted_text
            payload = dict(message.data.payload or {})
            payload["extracted_text"] = extracted_text
            message.data.payload = payload
            if document_id:
                update_status("ingestion", document_id, "ok")
            return message

        except json.JSONDecodeError as e:  # noqa: BLE001
            logger.error(f"Invalid JSON in message: {e}")
            return None
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error processing message: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return None


def main() -> None:
    """Main entry point for the Data Ingestion Service."""
    try:
        # Get connection parameters from environment variables
        connection_string = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
        # Support both historic and new env var names for the input queue
        input_queue = (
            os.getenv("AZURE_DATA_INGESTION_QUEUE") or os.getenv("AZURE_DOCUMENT_INGESTION_QUEUE") or "ingestion"
        )
        output_queue = os.getenv("AZURE_VALIDATION_QUEUE", "validation")

        if not connection_string:
            raise ValueError("AZURE_SERVICEBUS_CONNECTION_STRING not set")

        # Create a service bus handler with the data ingestion processor
        handler = ServiceBusHandler(
            connection_string=connection_string,
            input_queue=input_queue,
            output_queue=output_queue,
            message_processor=DataIngestionMessageProcessor(),
            message_subject="document_processed",
        )

        # Start the service
        handler.start()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to start Data Ingestion Service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
