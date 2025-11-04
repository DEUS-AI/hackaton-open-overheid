from __future__ import annotations

import logging
from collections.abc import Callable

from shared.models.messages import AppMessage
from shared.tools.MessageProcessor import MessageProcessor

logger = logging.getLogger(__name__)


class MessageHandler:
    """Wraps a MessageProcessor and an optional callback to execute after processing.

    Parameters:
        message_processor: A MessageProcessor to transform/validate the incoming AppMessage.
        after_process: Callback executed only if processing returns a non-None AppMessage.

    Returns (from handle_message):
        bool: True if the message was processed successfully (processor returned a non-None AppMessage),
              False otherwise.
    """

    def __init__(
        self,
        message_processor: MessageProcessor | None = None,
        after_process: Callable[[AppMessage], None] | None = lambda msg: None,
    ) -> None:
        self.message_processor = message_processor
        self.after_process = after_process

    def handle_message(self, message: AppMessage) -> bool:
        if not self.message_processor:
            logger.error("No message processor defined, cannot process message")
            return False
        msg_processed = None
        try:
            msg_processed = self.message_processor.process(message)
        except Exception as e:  # noqa: BLE001
            logger.exception("Unhandled exception while processing message: %s", e)
            return False
        if msg_processed and self.after_process:
            try:
                self.after_process(msg_processed)
            except Exception as cb_err:  # noqa: BLE001
                logger.error("after_process callback failed: %s", cb_err)
        if msg_processed:
            logger.info("Message processed successfully: %s", msg_processed)
            return True
        logger.error("Message processing failed")
        return False
