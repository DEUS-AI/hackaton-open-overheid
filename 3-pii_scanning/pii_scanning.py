#!/usr/bin/env python3
"""
PII Scanning Service

Listens to the PII scanning queue and determines if the payload.extracted_text
contains personal information using the octopii library.
Prints a message to the console indicating whether PII was found.
"""

import datetime as dt
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Ensure '/app' (the project root in containers) is on sys.path before importing 'shared'
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from shared.models.messages import AppMessage, PiiScanInfo
from shared.tools.MessageProcessor import MessageProcessor
from shared.tools.pipeline_status import update_status
from shared.tools.ServiceBusHandler import ServiceBusHandler  # noqa: E402

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class PiiProcessor(MessageProcessor):
    """
    Service that determines whether a message contains PII in
    payload.extracted_text.
    """

    @staticmethod
    def naive_regex_pii_scan(text: str) -> tuple[bool, dict[str, Any]]:
        """
        Fallback PII detection using simple regexes (email, phone, IBAN-like).
        """
        patterns = {
            "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
            "iban_like": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"),
        }
        matches: dict[str, list[str]] = {}
        for name, pat in patterns.items():
            found = pat.findall(text)
            if found:
                # De-duplicate and keep a few examples only
                uniq = list(dict.fromkeys(found))[:5]
                if uniq:
                    matches[name] = uniq
        return (len(matches) > 0), {"engine": "naive-regex", "matches": matches}

    def process(self, message: AppMessage) -> AppMessage | None:  # type: ignore[override]
        """
        Process an incoming message, detect PII on extracted_text and print a
        result. Returns None since we don't forward the message further.
        """
        try:
            # Normalize to AppMessage first
            data = message.data
            payload = (data.payload if data else {}) or {}
            text = payload.get("extracted_text") if isinstance(payload, dict) else None
            doc_name = (data.name if data else None) or "<unknown>"
            document_id = (data.id if data else None) or (data.name if data else None)
            if document_id:
                update_status("pii-scanning", document_id, "started")
            if not isinstance(text, str) or not text.strip():
                logger.info("[PII] Document '%s': no text to scan", doc_name)
                if document_id:
                    update_status("pii-scanning", document_id, "skipped", reason="no_text")
                return None
            # Run scan
            has_pii, details = PiiProcessor.naive_regex_pii_scan(text)
            if has_pii:
                logger.info(
                    "[PII] Document '%s': PERSONAL DATA DETECTED | engine=%s | details=%s",
                    doc_name,
                    details.get("engine"),
                    details.get("matches"),
                )
            else:
                logger.info(
                    "[PII] Document '%s': no personal data detected | engine=%s",
                    doc_name,
                    details.get("engine"),
                )
            if document_id:
                update_status("pii-scanning", document_id, "ok", details=details)

            message.pii = PiiScanInfo(
                has_pii=has_pii,
                engine=details.get("engine"),
                matches=details.get("matches"),
                timestamp=dt.datetime.now(),
            )
            return message
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:  # noqa: BLE001
            logger.error("Error in PII scanning: %s", e)
            if document_id:  # type: ignore[name-defined]
                try:
                    update_status("pii-scanning", document_id, "error", reason=str(e))  # type: ignore[name-defined]
                except Exception:  # noqa: BLE001
                    pass
            return None


def main() -> None:
    connection_string = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
    input_queue = os.getenv("AZURE_PII_SCANNING_QUEUE", "pii-scanning")
    output_queue = os.getenv("AZURE_EXTRACTOR_QUEUE", "extractor")
    if not connection_string:
        raise ValueError("AZURE_SERVICEBUS_CONNECTION_STRING is not set")
    logger.info("Starting PII scanning service. Input queue: %s", input_queue)
    handler = ServiceBusHandler(
        connection_string=connection_string,
        input_queue=input_queue,
        output_queue=output_queue,
        message_processor=PiiProcessor(),
        message_subject="pii_scanned",
    )
    handler.start()


if __name__ == "__main__":
    main()
