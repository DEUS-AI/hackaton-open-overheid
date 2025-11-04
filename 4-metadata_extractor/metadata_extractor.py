import datetime as dt
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai import GenerativeModel

# Ensure '/app' (the project root in containers) is on sys.path before importing 'shared'
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from shared.models.messages import AppMessage, MetadataInfo
from shared.tools.MessageProcessor import MessageProcessor
from shared.tools.pipeline_status import update_status
from shared.tools.ServiceBusConsumer import ServiceBusConsumer
from shared.tools.ServiceBusHandler import MessageHandler
from shared.tools.ServiceBusPublisher import ServiceBusPublisher

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dataStoragePublisher = None
searchIndexPublisher = None
notificationPublisher = None

METADATA_TEXT_SYSTEM_PROMPT = (
    "You are an expert in Dutch law and government documents. Extract metadata from a provided document text. "
    "Return ONLY valid JSON with these exact fields and types (no markdown, no commentary):\n"
    "{\n"
    '  "official_title": string,\n'
    '  "document_type": string,\n'
    '  "identifiers": object,\n'
    '  "summary": string | null,\n'
    '  "keywords": string[],\n'
    '  "issuing_authority": string,\n'
    '  "official_publication": string,\n'
    '  "publication_number": string | null,\n'
    '  "publication_date": string | null,  // ISO-8601 date like 2024-05-20\n'
    '  "effective_date": string | null,     // ISO-8601 date\n'
    '  "repeal_date": string | null,        // ISO-8601 date\n'
    '  "geographic_scope": string[],\n'
    '  "sector_scope": string[],\n'
    '  "target_audience": string[],\n'
    '  "has_sanction_regime": boolean,\n'
    '  "amends": string[],\n'
    '  "repeals": string[],\n'
    '  "implements": string[],\n'
    '  "related_case_law": string[],\n'
    '  "legal_basis": string[]\n'
    "}\n"
    "If information is missing, use null for strings or empty arrays for lists."
)

CONNECTION_STRING = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
INPUT_QUEUE_NAME = os.getenv("AZURE_EXTRACTOR_QUEUE", "extractor")
OUTPUT_DATA_STORAGE_QUEUE_NAME = os.getenv("AZURE_EMBEDDING_QUEUE", "embedding")
OUTPUT_SEARCH_INDEX_QUEUE_NAME = os.getenv("AZURE_SEARCH_INDEX_QUEUE", "search-index")
OUTPUT_NOTIFICATION_QUEUE_NAME = os.getenv("AZURE_NOTIFICATION_QUEUE", "notifications")


def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` fences if present."""
    text = text.strip()
    fence = re.compile(r"^```(?:json)?\n(.*)\n```$", re.DOTALL | re.IGNORECASE)
    m = fence.match(text)
    return m.group(1).strip() if m else text


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    if isinstance(value, (int, float)):  # noqa: UP038
        return bool(value)
    return default


def _coerce_list_str(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if x is not None]
    # accept comma-separated string
    if isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    return []


def _parse_date(value: Any) -> dt.date | None:
    if not value:
        return None
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        s = value.strip()
        # Keep only date part if datetime
        s = s.split("T")[0]
        try:
            return dt.date.fromisoformat(s)
        except ValueError:
            return None
    return None


class MetadataProcessor(MessageProcessor):
    """MessageProcessor implementation for metadata extraction.

    Accepts the normalized AzureSBMessage-like dict produced by ServiceBusConsumer
    (or a raw JSON string as fallback), extracts metadata using Gemini, publishes
    fan-out messages, and returns a MetadataExtractedMessage.
    """

    def __init__(self) -> None:
        # Lazily initialize client to avoid env issues in import time
        self._client: GenerativeModel | None = None

    def _get_gemini_client(self) -> GenerativeModel:
        if self._client is None:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY is not set in environment")
            self._client = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=METADATA_TEXT_SYSTEM_PROMPT,
            )
        return self._client

    # --- Model call ---
    def _extract_metadata_obj(self, text: str) -> dict[str, Any]:
        client = self._get_gemini_client()
        user_prompt = f"Extract metadata from the following document text. Output only JSON.\n\nTEXT:\n{text.strip()}"
        resp = client.generate_content(user_prompt)
        raw = resp.text or ""
        cleaned = _strip_code_fences(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            maybe = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not maybe:
                raise
            return json.loads(maybe.group(0))

    def _to_metadata_info(self, obj: dict[str, Any]) -> MetadataInfo:
        return MetadataInfo(
            official_title=str(obj.get("official_title") or "Unknown"),
            document_type=str(obj.get("document_type") or "Unknown"),
            identifiers=dict(obj.get("identifiers") or {}),
            summary=(obj.get("summary") if obj.get("summary") is not None else None),
            keywords=_coerce_list_str(obj.get("keywords")),
            issuing_authority=str(obj.get("issuing_authority") or "Unknown"),
            official_publication=str(obj.get("official_publication") or "Unknown"),
            publication_number=(obj.get("publication_number") if obj.get("publication_number") else None),
            publication_date=_parse_date(obj.get("publication_date")),
            effective_date=_parse_date(obj.get("effective_date")),
            repeal_date=_parse_date(obj.get("repeal_date")),
            geographic_scope=_coerce_list_str(obj.get("geographic_scope")),
            sector_scope=_coerce_list_str(obj.get("sector_scope")),
            target_audience=_coerce_list_str(obj.get("target_audience")),
            has_sanction_regime=_coerce_bool(obj.get("has_sanction_regime"), False),
            amends=_coerce_list_str(obj.get("amends")),
            repeals=_coerce_list_str(obj.get("repeals")),
            implements=_coerce_list_str(obj.get("implements")),
            related_case_law=_coerce_list_str(obj.get("related_case_law")),
            legal_basis=_coerce_list_str(obj.get("legal_basis")),
            timestamp=dt.datetime.now(),
        )

    def process(self, message: AppMessage) -> AppMessage | None:
        document_id = message.data.id or message.data.name if message.data else "<unknown>"

        scanned_text = (
            message.data.payload.get("extracted_text")
            if (message.data is not None and hasattr(message.data, "payload"))
            else {}
        )

        if document_id:
            update_status("extractor", document_id, "started")

        if not isinstance(scanned_text, str) or not scanned_text.strip():
            logger.warning("No extracted_text in payload; skipping Gemini call")
            if document_id:
                update_status("extractor", document_id, "skipped", reason="no_text")
            return None

        try:
            if document_id:
                update_status("extractor", document_id, "generating")
            obj = self._extract_metadata_obj(scanned_text)
            md = self._to_metadata_info(obj)

            if document_id:
                update_status("extractor", document_id, "ok")
            message.metadata = md
            logger.info(f"Extracted metadata for document ID {document_id}")
            return message
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to process message: %s", e)
            if document_id:
                try:
                    update_status("extractor", document_id, "error", reason=str(e))
                except Exception:  # noqa: BLE001
                    pass
            return None


def main() -> None:
    logger.info(
        f"Starting metadata extraction service.\nInput: {INPUT_QUEUE_NAME} Output: {OUTPUT_DATA_STORAGE_QUEUE_NAME}, {OUTPUT_SEARCH_INDEX_QUEUE_NAME}, {OUTPUT_NOTIFICATION_QUEUE_NAME}"
    )

    consumer = ServiceBusConsumer(CONNECTION_STRING, INPUT_QUEUE_NAME)

    try:
        logger.info("\n--- Starting continuous listening ---")
        logger.info("Press Ctrl+C to stop")
        processor = MetadataProcessor()

        def publish_to_queues(msg: AppMessage) -> None:
            dataStoragePublisher = ServiceBusPublisher(CONNECTION_STRING, OUTPUT_DATA_STORAGE_QUEUE_NAME)
            searchIndexPublisher = ServiceBusPublisher(CONNECTION_STRING, OUTPUT_SEARCH_INDEX_QUEUE_NAME)
            notificationPublisher = ServiceBusPublisher(CONNECTION_STRING, OUTPUT_NOTIFICATION_QUEUE_NAME)
            dataStoragePublisher.publish_message(msg)
            searchIndexPublisher.publish_message(msg)
            notificationPublisher.publish_message(msg)

        handler = MessageHandler(processor, publish_to_queues)
        consumer.start_continuous_listening(handler)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
