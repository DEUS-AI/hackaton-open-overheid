#!/usr/bin/env python3
"""
ServiceBusHandler

This module provides a generic handler for Azure Service Bus messaging
operations that can be reused across different services.
"""

from __future__ import annotations

import logging

from shared.models.messages import AppMessage
from shared.tools.MessageHandler import MessageHandler
from shared.tools.MessageProcessor import MessageProcessor
from shared.tools.ServiceBusConsumer import ServiceBusConsumer
from shared.tools.ServiceBusPublisher import ServiceBusPublisher

# Configure logger
logger = logging.getLogger(__name__)


## MessageHandler moved to shared.tools.MessageHandler to decouple concerns.


class ServiceBusHandler:
    """
    Generic handler for Azure Service Bus messaging operations.
    This class can be extended or used directly by different services to handle
    message publishing and consumption.
    """

    def __init__(
        self,
        connection_string: str,
        input_queue: str | None = None,
        output_queue: str | None = None,
        message_processor: MessageProcessor | None = None,
        message_subject: str = "processed_message",
    ) -> None:
        """
        Initialize the Service Bus handler.

        Args:
            connection_string: Azure Service Bus connection string
            input_queue: Input queue name to consume messages from
            output_queue: Output queue name to publish processed messages to
            message_processor: An object implementing MessageProcessor
                (with a .process(msg) method) that returns a BaseMessage or None.
            message_subject: Subject to use when publishing messages
        """
        self.connection_string = connection_string
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.message_processor = message_processor
        self.message_subject = message_subject
        self.publisher: ServiceBusPublisher | None = None
        self.consumer: ServiceBusConsumer | None = None

        if not self.connection_string:
            raise ValueError("Connection string is required")

        # Create publisher once (instead of per message) if an output queue is configured
        if self.output_queue:
            try:
                self.publisher = ServiceBusPublisher(self.connection_string, self.output_queue)
            except Exception as e:  # noqa: BLE001
                logger.error("Failed to create publisher for %s: %s", self.output_queue, e)
                self.publisher = None

    def start(self) -> None:
        """Start listening for messages on the Service Bus input queue."""
        if not self.input_queue:
            logger.error("No input queue specified. Cannot start listening.")
            return

        try:
            logger.info("Starting Service Bus handler on queue: %s", self.input_queue)
            if self.output_queue:
                logger.debug("Publishing to queue: %s", self.output_queue)

            self.consumer = ServiceBusConsumer(self.connection_string, self.input_queue)

            def publish_msg(msg: AppMessage) -> None:
                self.publisher.publish_message(
                    message_content=msg, subject=self.message_subject
                ) if self.publisher else None

            message_handler = MessageHandler(self.message_processor, publish_msg)
            self.consumer.start_continuous_listening(message_handler)

        except KeyboardInterrupt:
            logger.info("Service interrupted, shutting down...")
        except Exception as e:  # noqa: BLE001  # pylint: disable=broad-except
            logger.error("Error starting service: %s", str(e))
            import traceback

            logger.debug(traceback.format_exc())
        finally:
            # Do not close here; allow graceful shutdown via close()
            pass

    def close(self) -> None:
        """Close resources (publisher & consumer)."""
        if self.consumer:
            try:
                self.consumer.stop_listening()
                self.consumer.close()
            except Exception as e:  # noqa: BLE001
                logger.debug("Error closing consumer: %s", e)
        if self.publisher:
            try:
                self.publisher.close()
            except Exception as e:  # noqa: BLE001
                logger.debug("Error closing publisher: %s", e)
