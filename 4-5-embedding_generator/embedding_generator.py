import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

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
logger = logging.getLogger(__name__)


class EmbeddingGeneratorService:
    """Service for generating document embeddings."""

    def __init__(self) -> Any:
        """Initialize the EmbeddingGeneratorService with embedding model settings."""
        self.model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)

        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", ", ", " "],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )

        logger.info(f"Embedding service initialized with model: {self.model_name}")
        logger.info(f"Chunk size: {self.chunk_size}, Overlap: {self.chunk_overlap}")

    @staticmethod
    def _get_instance():
        if not hasattr(EmbeddingGeneratorService, "_instance"):
            EmbeddingGeneratorService._instance = EmbeddingGeneratorService()
        return EmbeddingGeneratorService._instance

    def _split_document(self, text: str, metadata: dict = None) -> list[dict]:
        if not text:
            return []

        chunks = self.text_splitter.split_text(text)
        logger.info(f"Document split into {len(chunks)} chunks")

        result_chunks = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = {
                "chunk_id": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk_text),
                "first_50_chars": chunk_text[:50].replace("\n", " "),
            }

            if metadata:
                chunk_metadata.update(metadata)

            result_chunks.append({"text": chunk_text, "metadata": chunk_metadata})

        return result_chunks

    def generate_embeddings(self, chunks: list[dict]) -> list[dict]:
        if not chunks:
            return []

        texts = [chunk["text"] for chunk in chunks]

        try:
            embeddings = self.model.encode(texts)
            logger.info(f"Generated {len(embeddings)} embeddings")

            for i, embedding in enumerate(embeddings):
                chunks[i]["embedding"] = embedding.tolist()

            return chunks
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            logger.error(traceback.format_exc())
            return []

    @staticmethod
    def process_document(message: AppMessage) -> AppMessage:
        instance = EmbeddingGeneratorService._get_instance()
        try:
            start_time = time.time()

            if not message.data:
                logger.error("No document data found in message")
                return message

            if message.data:
                update_status("embedding", message.data.id, "started")

            content_text = ""
            if message.data.payload and "extracted_text" in message.data.payload:
                content_text = message.data.payload["extracted_text"]

            if not content_text:
                logger.warning("No text content found in document payload")
                if message.data:
                    update_status(message.data.id, "embedding", "completed", "No text content to embed")
                return message

            doc_metadata = {
                "document_id": message.data.id,
                "source": message.data.source,
                "name": message.data.name,
                "extension": message.data.extension,
                "url": message.data.url,
            }

            if message.metadata:
                doc_metadata.update(
                    {
                        "official_title": message.metadata.official_title,
                        "document_type": message.metadata.document_type,
                        "issuing_authority": message.metadata.issuing_authority,
                        "keywords": message.metadata.keywords if hasattr(message.metadata, "keywords") else [],
                    }
                )

            chunks = instance._split_document(content_text, doc_metadata)

            if not chunks:
                logger.warning(f"No chunks created for document {message.data.id}")
                if message.data:
                    update_status("embedding", message.data.id, "completed", "Document too small for chunking")
                return message

            embedded_chunks = instance.generate_embeddings(chunks)

            if not embedded_chunks:
                logger.error(f"Failed to generate embeddings for document {message.data.id}")
                if message.data:
                    update_status("embedding", message.data.id, "failed", "Failed to generate embeddings")
                return message

            if not message.data.payload:
                message.data.payload = {}

            message.data.payload["vector_chunks"] = embedded_chunks

            elapsed_time = time.time() - start_time
            logger.info(f"Generated embeddings for document {message.data.id} in {elapsed_time:.2f} seconds")

            if message.data:
                update_status("embedding", message.data.id, "completed")

            return message

        except Exception as e:
            logger.error(f"Error processing document for embeddings: {e}")
            logger.error(traceback.format_exc())

            if message and message.data:
                update_status("embedding", message.data.id, "failed", f"Error: {str(e)}")

            return message


class EmbeddingProcessor(MessageProcessor):
    """Processor for handling document embedding generation."""

    def process(self, message: Any) -> AppMessage | None:
        try:
            if isinstance(message, str):
                try:
                    message_data = json.loads(message)
                except json.JSONDecodeError:
                    logger.error("Failed to decode message as JSON")
                    return None
            else:
                message_data = message

            if isinstance(message_data, AppMessage):
                app_message = message_data
            else:
                app_message = AppMessage.parse(message_data)

            if app_message and app_message.data:
                try:
                    update_status("embedding", app_message.data.id, "received")
                except Exception as e:
                    logger.warning(f"No se pudo actualizar estado inicial: {e}")

            source = app_message.data.source if app_message.data else "unknown"
            logger.info(f"Processing message from {source}")

            processed_message = EmbeddingGeneratorService.process_document(app_message)

            return processed_message

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())
            return None


def main() -> None:
    try:
        connection_string = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING", "")
        input_queue = os.getenv("AZURE_EMBEDDING_QUEUE", "embedding")
        output_queue = os.getenv("AZURE_DATA_STORAGE_QUEUE", "data-storage")

        if not connection_string:
            raise ValueError("AZURE_SERVICEBUS_CONNECTION_STRING environment variable not set")

        handler = ServiceBusHandler(
            connection_string=connection_string,
            input_queue=input_queue,
            output_queue=output_queue,
            message_processor=EmbeddingProcessor(),
        )

        logger.info("Starting Embedding Generator Service")
        logger.info(f"Listening on queue: {input_queue}")
        logger.info(f"Publishing to queue: {output_queue}")

        handler.start()
    except Exception as e:
        logger.error(f"Failed to start Embedding Generator Service: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
