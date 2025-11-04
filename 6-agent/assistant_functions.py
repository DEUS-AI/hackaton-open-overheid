from __future__ import annotations

import json
import logging
import os
from typing import Annotated

import aiohttp
from livekit import rtc
from livekit.agents import llm

# Initialize a logger. If agent.py configures "my-worker", this logger will use that config.
logger = logging.getLogger("my-worker")


class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()
        # Explicitly initialize _room here to ensure the attribute exists
        self._room: rtc.Room | None = None
        self._participant: rtc.RemoteParticipant | None = (
            None  # Also good practice to init this if base class might not
        )

        has_room_attr_after_super_init = hasattr(self, "_room")
        initial_room_value_str = str(self._room)  # Use str() for logging if it's None
        logger.info(
            f"AssistantFnc instance CREATED with id: {id(self)}. "
            f"Post super().__init__() and explicit self._room = None, hasattr(self, '_room'): {has_room_attr_after_super_init}. "  # noqa: E501
            f"Initial self._room value: {initial_room_value_str}"
        )

    def init(self, room: rtc.Room, participant: rtc.RemoteParticipant) -> None:
        # Log state before assignments
        logger.info(
            f"AssistantFnc instance ({id(self)}) PRE-MANUAL-INIT. "
            f"Current self._room: {str(self._room)}, Current self._participant: {str(self._participant)}"
        )

        # Directly assign room and participant, as super().init() does not exist
        self._room = room
        self._participant = participant

        # Log state after assignments
        room_name_post_manual_init = self._room.name if self._room else "None"
        participant_identity_post_manual_init = self._participant.identity if self._participant else "None"

        logger.info(
            f"AssistantFnc instance ({id(self)}) POST-MANUAL-INIT. "
            f"Room set to: {room_name_post_manual_init}. "
            f"Participant set to: {participant_identity_post_manual_init}. "
            f"Actual self._room object: {str(self._room)}"
        )

    @llm.ai_callable()
    async def search_documents(
        self,
        query: Annotated[str, llm.TypeInfo(description="The user's query to search for documents or information.")],
    ):
        """Performs a document search based on the user's query and sends the results to a designated data channel for
        mindmap display."""
        # Log state at the beginning of the function call
        has_room_attr_at_call = hasattr(self, "_room")
        # self._room should exist now, so we can access it. Check if it's None.
        room_value_at_call_str = str(self._room.name if self._room else self._room)
        logger.info(
            f"AI Function Call: search_documents on instance ({id(self)}), Query: {query}. "
            f"Current hasattr(self, '_room'): {has_room_attr_at_call}. "
            f"Current self._room value: {room_value_at_call_str}"
        )

        # The hasattr check is less critical now if __init__ guarantees it, but checking for None is key.
        if not self._room:  # This is the crucial check now
            logger.error(
                f"CRITICAL: AssistantFnc instance ({id(self)}): self._room is None. "
                f"Framework init() likely did not run or failed."
            )
            return (
                "Sorry, I cannot perform the search right now due to an internal error (room context not initialized)."
            )

        backend_url = os.getenv("BACKEND_URL")
        if not backend_url:
            logger.error("BACKEND_URL environment variable is not set.")
            return "Sorry, the backend service is not configured correctly for search."

        url = f"{backend_url}/search"
        payload = {"query": query}
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    response_text = json.dumps(data, ensure_ascii=False)

            logger.info(f"Sending mindmap data to room (first 200 chars): {response_text[:200]}...")
            await self._room.local_participant.send_text(response_text, topic="mindmap-data")
            return "I have performed the search. The results should now be available in the mindmap display."
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error during search_documents: {e.status} {e.message}")
            return f"Sorry, I encountered an error while searching: The server responded with status {e.status}."
        except Exception as e:
            logger.error(f"Unexpected error in search_documents: {e}", exc_info=True)
            return "Sorry, an unexpected error occurred while I was trying to search for documents."
