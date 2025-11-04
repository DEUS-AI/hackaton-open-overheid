import json
import logging
from typing import Any
from uuid import UUID

from azure.servicebus import ServiceBusClient, ServiceBusMessage

from shared.models.messages import AppMessage

# Configure logger
logger = logging.getLogger(__name__)


class ServiceBusPublisher:
    """
    A class to publish messages to Azure Service Bus topics.
    """

    def __init__(self, connection_string: str, topic_name: str):
        """
        Initialize the Service Bus publisher.

        Args:
            connection_string (str): Azure Service Bus connection string
            topic_name (str): Name of the topic to publish to
        """
        self.connection_string = connection_string
        self.topic_name = topic_name
        self.client = ServiceBusClient.from_connection_string(connection_string)

    def publish_message(
        self,
        message_content: AppMessage,
        subject: str | None = None,
        content_type: str = "application/json",
        custom_properties: dict[str | bytes, int | float | bytes | bool | str | UUID] | None = None,
    ) -> bool:
        """
        Publish a single message to the Service Bus topic.

        Args:
            message_content (AppMessage): The message content to publish
            subject (str, optional): Message subject/label
            content_type (str): Content type of the message
            custom_properties (Dict, optional): Custom properties to add to the message

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            with self.client:
                sender = self.client.get_topic_sender(topic_name=self.topic_name)
                with sender:
                    # Convert message AppMessage content to JSON string using its serializer
                    message_body = json.dumps(message_content.to_dict(), ensure_ascii=False)
                    # Create Service Bus message
                    logger.info("Publishing message to topic '%s': %s", self.topic_name, message_body)
                    message = ServiceBusMessage(
                        body=message_body,
                        content_type=content_type,
                        application_properties=custom_properties if custom_properties else None,
                    )

                    # Add subject if provided
                    if subject:
                        message.subject = subject

                    # Send the message
                    sender.send_messages(message)
                    return True

        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False

    def publish_batch_messages(self, messages: list[dict[Any, Any]], batch_size: int = 100) -> bool:
        """
        Publish multiple messages in batches to the Service Bus topic.

        Args:
            messages (list): List of message contents to publish
            batch_size (int): Number of messages per batch

        Returns:
            bool: True if all batches were sent successfully, False otherwise
        """
        try:
            with self.client:
                sender = self.client.get_topic_sender(topic_name=self.topic_name)
                with sender:
                    # Process messages in batches
                    for i in range(0, len(messages), batch_size):
                        batch = messages[i : i + batch_size]

                        # Create batch of Service Bus messages
                        message_batch = sender.create_message_batch()

                        for msg_content in batch:
                            message_body = json.dumps(msg_content, default=str)
                            message = ServiceBusMessage(body=message_body, content_type="application/json")

                            try:
                                message_batch.add_message(message)
                            except ValueError:
                                # Batch is full, send current batch and create new one
                                sender.send_messages(message_batch)
                                message_batch = sender.create_message_batch()
                                message_batch.add_message(message)

                        # Send the batch
                        if len(message_batch) > 0:
                            sender.send_messages(message_batch)
                            logger.debug(f"Batch of {len(batch)} messages sent successfully")

                    logger.debug(f"All {len(messages)} messages sent successfully to topic '{self.topic_name}'")
                    return True

        except Exception as e:
            logger.error(f"Failed to send batch messages: {str(e)}")
            return False

    def close(self) -> None:
        """Close the Service Bus client connection."""
        if self.client:
            self.client.close()
