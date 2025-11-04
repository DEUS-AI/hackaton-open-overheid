import atexit
import logging
import os
import sys
from dataclasses import asdict
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

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


# Global Mongo client (service-level singleton)
mongo_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Get a singleton MongoDB client instance for the service.

    Builds the connection string from env vars on first use and reuses the
    same client afterwards. Returns the connected MongoClient.

    Also ensures that the necessary collections and indexes are set up.
    """

    global mongo_client
    if mongo_client is not None:
        return mongo_client

    uri = os.getenv("MONGO_URI")
    if not uri:
        host = os.getenv("MONGO_HOST", "mongodb")
        port = os.getenv("MONGO_PORT", "27017")
        db = os.getenv("MONGO_DB", "overheid")
        user = os.getenv("MONGO_USER", "mongoadmin")
        pwd = os.getenv("MONGO_PASSWORD", "mongopass")
        auth_db = os.getenv("MONGO_AUTH_DB", "admin")
        uri = f"mongodb://{user}:{pwd}@{host}:{port}/{db}?authSource={auth_db}"

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Ensure connection is live
        client.admin.command("ping")
        mongo_client = client

        database_name = os.getenv("MONGO_DB", "overheid")
        documents_collection_name = os.getenv("MONGO_COLLECTION", "messages")
        chunks_collection_name = os.getenv("MONGO_CHUNKS_COLLECTION", "chunks")

        db = client[database_name]
        documents_collection = db[documents_collection_name]
        chunks_collection = db[chunks_collection_name]

        documents_collection.create_index("data.id", unique=True, sparse=True)
        chunks_collection.create_index("document_id")
        chunks_collection.create_index("chunk_id")

        logger.info("Connected to MongoDB %s", database_name)
        logger.info("Collections: %s, %s", documents_collection_name, chunks_collection_name)

        # Ensure clean shutdown
        atexit.register(lambda: mongo_client and mongo_client.close())
        return client
    except PyMongoError as e:  # noqa: BLE001
        logger.error("Failed to create MongoDB client: %s", e)
        raise


class StorageProcessor(MessageProcessor):
    def process(self, message: AppMessage) -> None:
        try:
            # Determine DB/collection from environment
            database_name = os.getenv("MONGO_DB", "overheid")
            documents_collection_name = os.getenv("MONGO_COLLECTION", "messages")
            chunks_collection_name = os.getenv("MONGO_CHUNKS_COLLECTION", "chunks")

            db = get_client()[database_name]
            documents_collection = db[documents_collection_name]
            chunks_collection = db[chunks_collection_name]

            # Extract document id for status
            document_id = None
            if message.data is not None:
                document_id = getattr(message.data, "id", None) or getattr(message.data, "name", None)

            if document_id:
                update_status("data-storage", document_id, "started")

            vector_chunks = []
            if message.data and message.data.payload and "vector_chunks" in message.data.payload:
                vector_chunks = message.data.payload.pop("vector_chunks", [])

            message_dict = asdict(message)
            result = documents_collection.insert_one(message_dict)
            doc_mongo_id = str(result.inserted_id)

            chunks_inserted = 0
            if vector_chunks and document_id:
                chunk_docs = []

                for chunk in vector_chunks:
                    chunk_doc = {
                        "document_id": document_id,
                        "document_mongo_id": doc_mongo_id,
                        "chunk_id": chunk.get("metadata", {}).get("chunk_id"),
                        "total_chunks": chunk.get("metadata", {}).get("total_chunks"),
                        "text": chunk.get("text", ""),
                        "embedding": chunk.get("embedding", []),
                        "metadata": chunk.get("metadata", {}),
                    }
                    chunk_docs.append(chunk_doc)

                if chunk_docs:
                    chunks_result = chunks_collection.insert_many(chunk_docs)
                    chunks_inserted = len(chunks_result.inserted_ids)

            if document_id:
                extra_info = {"mongo_id": doc_mongo_id, "chunks_inserted": chunks_inserted}
                update_status("data-storage", document_id, "ok", **extra_info)

            logger.info(
                "Inserted document with _id=%s in %s/%s with %d chunks",
                doc_mongo_id,
                database_name,
                documents_collection_name,
                chunks_inserted,
            )
        except PyMongoError as e:  # noqa: BLE001
            logger.error("Failed to insert document into MongoDB: %s", e)
            try:
                if document_id:
                    update_status("data-storage", document_id, "error", reason=str(e))
            except Exception:  # noqa: BLE001
                pass


def main() -> None:
    CONNECTION_STRING = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
    INPUT_QUEUE_NAME = os.getenv("AZURE_DATA_STORAGE_QUEUE", "data-storage")

    logger.info(f"Starting data storage service.\nInput: {INPUT_QUEUE_NAME} Output: None")

    # Lazily initialize Mongo connection on first use
    get_client()

    consumer = ServiceBusConsumer(CONNECTION_STRING, INPUT_QUEUE_NAME)

    try:
        logger.info("\n--- Starting continuous listening ---")
        logger.info("Press Ctrl+C to stop")
        processor = StorageProcessor()
        handler = MessageHandler(processor, None)
        consumer.start_continuous_listening(handler)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
