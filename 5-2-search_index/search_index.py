import json
import logging
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Ensure '/app' (the project root in containers) is on sys.path before importing 'shared'
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from shared.models.messages import AppMessage
from shared.tools.MessageProcessor import MessageProcessor
from shared.tools.pipeline_status import update_status
from shared.tools.ServiceBusHandler import ServiceBusHandler

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logging.getLogger("azure").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class SearchIndexService:
    """Service for handling document indexing in Apache Solr search engine."""

    def __init__(self):
        """Initialize the SearchIndexService with Solr connection settings."""
        self.solr_url = os.getenv("SOLR_URL", "http://127.0.0.1:8983/solr/")
        self.solr_collection = os.getenv("SOLR_COLLECTION", "documents")

        logger.info(f"Using Solr at {self.solr_url} with collection {self.solr_collection}")

    @staticmethod
    def _get_instance():
        """Get or create a singleton instance of SearchIndexService."""
        if not hasattr(SearchIndexService, "_instance"):
            SearchIndexService._instance = SearchIndexService()
        return SearchIndexService._instance

    @staticmethod
    def index_document(message: AppMessage) -> bool:
        """
        Index a document in the search engine.

        Args:
            message: The AppMessage containing document data to index

        Returns:
            Boolean indicating if indexing was successful
        """
        instance = SearchIndexService._get_instance()
        try:
            if not message.data:
                logger.error("No document data found in message")
                return False

            doc_id = message.data.id or message.data.name or f"doc-{int(time.time())}"

            content_text = ""
            if message.data.payload and "extracted_text" in message.data.payload:
                content_text = message.data.payload["extracted_text"]

            search_document = {
                "id": doc_id,
                "source_s": message.data.source,
                "name_s": message.data.name,
                "extension_s": message.data.extension,
                "url_s": message.data.url,
                "content_t": content_text,
            }

            if message.validation:
                search_document.update(
                    {
                        "validation_status_s": message.validation.status,
                        "validation_timestamp_dt": message.validation.timestamp.isoformat()
                        if message.validation.timestamp
                        else None,
                    }
                )

            if message.pii:
                search_document.update(
                    {
                        "has_pii_b": message.pii.has_pii,
                        "pii_engine_s": message.pii.engine,
                        "pii_timestamp_dt": message.pii.timestamp.isoformat() if message.pii.timestamp else None,
                    }
                )

            if message.metadata:
                metadata_dict = {
                    "official_title_s": message.metadata.official_title,
                    "document_type_s": message.metadata.document_type,
                    "issuing_authority_s": message.metadata.issuing_authority,
                    "official_publication_s": message.metadata.official_publication,
                    "publication_number_s": message.metadata.publication_number,
                    "publication_date_dt": message.metadata.publication_date.isoformat()
                    if message.metadata.publication_date
                    else None,
                    "effective_date_dt": message.metadata.effective_date.isoformat()
                    if message.metadata.effective_date
                    else None,
                    "repeal_date_dt": message.metadata.repeal_date.isoformat()
                    if message.metadata.repeal_date
                    else None,
                    "summary_t": message.metadata.summary,
                    "keywords_ss": message.metadata.keywords,
                    "geographic_scope_ss": message.metadata.geographic_scope,
                    "sector_scope_ss": message.metadata.sector_scope,
                    "target_audience_ss": message.metadata.target_audience,
                    "has_sanction_regime_b": message.metadata.has_sanction_regime,
                }
                search_document.update(metadata_dict)

                search_document["metadata_json"] = json.dumps(message.to_dict().get("metadata", {}))

            try:
                solr_endpoint = f"{instance.solr_url}/{instance.solr_collection}/update/json/docs"

                response = requests.post(
                    solr_endpoint,
                    json=search_document,
                    params={"commit": "true", "wt": "json"},
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    # No need for additional commit as we're using commit=true in the initial request
                    pass

                if response.status_code == 200:
                    logger.info(f"Document '{doc_id}' indexed successfully in Solr")
                    return True
                else:
                    logger.error(f"Error indexing document in Solr: {response.text}")
                    return False

            except Exception as e:
                logger.error(f"Error connecting to Solr: {e}")
                import traceback

                logger.error(traceback.format_exc())
                return False

        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False


class SearchIndexProcessor(MessageProcessor):
    """Processor for handling document indexing in search engine."""

    def process(self, message: AppMessage) -> AppMessage | None:
        """
        Process incoming message and index document in search engine.

        Args:
            message: The incoming message to process

        Returns:
            None, as no further processing is needed after indexing
        """
        try:
            document_id = message.data.id or message.data.name if message.data else None

            if document_id:
                update_status("search-index", document_id, "processing")

            source = message.data.source if message.data else "unknown"
            logger.info(f"Processing message from {source}")

            success = SearchIndexService.index_document(message)

            if message.data:
                if success:
                    logger.info("Document successfully indexed in search engine")
                    update_status("search-index", message.data.id, "completed")
                else:
                    logger.warning("Failed to index document in search engine")
                    update_status("search-index", message.data.id, "failed")
            return None

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return None


def main() -> None:
    """Main entry point for the Search Index Service."""
    try:
        connection_string = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
        input_queue = os.getenv("AZURE_SEARCH_INDEX_QUEUE", "search-index")

        if not connection_string:
            raise ValueError("AZURE_SERVICEBUS_CONNECTION_STRING environment variable not set")

        search_service = SearchIndexService._get_instance()

        try:
            solr_ping_url = f"{search_service.solr_url}/{search_service.solr_collection}/admin/ping"
            response = requests.get(solr_ping_url, params={"wt": "json"}, timeout=5)

            if response.status_code == 200:
                status = response.json().get("status", "ERROR")
                if status == "OK":
                    logger.info(f"Successfully connected to Solr at {search_service.solr_url}")

                    schema_url = f"{search_service.solr_url}/{search_service.solr_collection}/schema"
                    schema_response = requests.get(schema_url, params={"wt": "json"})

                    if schema_response.status_code == 200:
                        fields = schema_response.json().get("schema", {}).get("fields", [])
                        dynamic_fields = schema_response.json().get("schema", {}).get("dynamicFields", [])
                        logger.info(
                            f"Schema has {len(fields)} explicit fields and {len(dynamic_fields)} dynamic field patterns"
                        )
                else:
                    logger.error(f"Solr is available but status is not OK: {status}")
                    return
            else:
                logger.error(f"Could not ping Solr collection: {response.status_code} - {response.text}")
                return
        except Exception as e:
            logger.error(f"Error connecting to Solr: {e}")
            return

        handler = ServiceBusHandler(
            connection_string=connection_string,
            input_queue=input_queue,
            output_queue=None,  # No output queue needed as this is the end of the pipeline
            message_processor=SearchIndexProcessor(),
        )

        logger.info(f"Starting Search Index Service, listening on queue: {input_queue}")
        handler.start()
    except Exception as e:
        logger.error(f"Failed to start Search Index Service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
