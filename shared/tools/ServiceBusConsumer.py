import json
import logging
import time

from azure.servicebus import ServiceBusClient, ServiceBusReceiveMode
from azure.servicebus.management import QueueProperties

from shared.models.messages import AppMessage
from shared.tools.MessageHandler import MessageHandler

# Configure logger
logger = logging.getLogger(__name__)


class ServiceBusConsumer:
    """
    A class to consume messages from Azure Service Bus queues.
    """

    def __init__(self, connection_string: str, queue_name: str):
        """
        Initialize the Service Bus consumer.

        Args:
            connection_string (str): Azure Service Bus connection string
            queue_name (str): Name of the queue to consume from
        """
        self.connection_string = connection_string
        self.queue_name = queue_name
        self.client = ServiceBusClient.from_connection_string(connection_string)
        self.is_running = False

    def start_continuous_listening(
        self,
        message_handler: MessageHandler,
        max_concurrent_calls: int = 1,
    ) -> None:
        """
        Start continuous listening for messages from the queue.

        Args:
            message_handler: An object implementing MessageProcessor with a .process(msg) method
            max_concurrent_calls (int): Maximum number of concurrent message processing
        """
        self.is_running = True
        logger.info(f"Starting continuous listening on queue '{self.queue_name}'")

        try:
            with self.client:
                receiver = self.client.get_queue_receiver(
                    queue_name=self.queue_name, receive_mode=ServiceBusReceiveMode.RECEIVE_AND_DELETE
                )
                with receiver:
                    while self.is_running:
                        try:
                            # Receive messages
                            received_msgs = receiver.receive_messages(
                                max_message_count=max_concurrent_calls, max_wait_time=10
                            )

                            for message in received_msgs:
                                settle_ok = False
                                try:
                                    app_message = AppMessage.parse(json.loads(str(message)))
                                    if app_message is not None:
                                        # Handler returns success boolean
                                        settle_ok = message_handler.handle_message(app_message)
                                except Exception as handler_error:  # noqa: BLE001
                                    logger.error(
                                        "Error processing message %s: %s",
                                        getattr(message, "message_id", None),
                                        handler_error,
                                    )
                                finally:
                                    # If auto_complete True we let SDK complete automatically only on success.
                                    # When auto_complete is True the SDK completes after context exit if no exception.
                                    # We want explicit settle to avoid reprocessing loops.
                                    try:
                                        if settle_ok:
                                            receiver.complete_message(message)
                                        else:
                                            # Abandon so it can be retried or moved to DLQ based on max delivery count
                                            receiver.abandon_message(message)
                                    except Exception as settle_err:  # noqa: BLE001
                                        logger.debug("Failed to settle message explicitly: %s", settle_err)

                            # Small delay to prevent tight loop when no messages
                            if not received_msgs:
                                time.sleep(1)

                        except KeyboardInterrupt:
                            logger.info("Received keyboard interrupt, stopping...")
                            self.is_running = False
                            break
                        except Exception as e:
                            logger.error(f"Error in message processing loop: {str(e)}")
                            time.sleep(5)  # Wait before retrying

        except Exception as e:
            logger.error(f"Failed to start continuous listening: {str(e)}")
        finally:
            self.is_running = False
            logger.debug("Stopped continuous listening")

    def stop_listening(self) -> None:
        """Stop the continuous listening loop."""
        self.is_running = False
        logger.debug("Stopping continuous listening...")

    def get_queue_info(self) -> QueueProperties | None:
        """
        Get information about the queue.

        Returns:
            Dict: Queue information
        """
        try:
            with self.client:
                # Use ServiceBusAdministrationClient for management operations
                from azure.servicebus.management import ServiceBusAdministrationClient

                admin_client = ServiceBusAdministrationClient.from_connection_string(self.connection_string)

                queue_properties = admin_client.get_queue(self.queue_name)

                logger.debug(f"Queue info retrieved for '{self.queue_name}'")
                return queue_properties

        except Exception as e:
            logger.error(f"Failed to get queue info: {str(e)}")
            return None

    def close(self) -> None:
        """Close the Service Bus client connection."""
        if self.client:
            self.client.close()
