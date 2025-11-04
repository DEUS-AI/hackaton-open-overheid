from __future__ import annotations

import asyncio
import json
import logging
import os

import aiohttp
from livekit import rtc

# Initialize a logger. If agent.py configures "my-worker", this logger will use that config.
logger = logging.getLogger("my-worker")

# Store active tasks to prevent garbage collection
_active_tasks = set()


# Synchronous handler to schedule the async handler for user text input
def handle_user_text_input(
    reader: rtc.TextStreamReader,
    participant_identity: str,
    room: rtc.Room,
):
    logger.info(f"Creating task for async_handle_user_text_input from participant: {participant_identity}")
    task = asyncio.create_task(async_handle_user_text_input(reader, participant_identity, room))
    _active_tasks.add(task)
    task.add_done_callback(_active_tasks.remove)


# The async handler that processes the text input stream
async def async_handle_user_text_input(
    reader: rtc.TextStreamReader,
    participant_identity: str,
    room: rtc.Room,
):
    try:
        async for text_chunk in reader:
            full_text_query = text_chunk
            logger.info(f"Received text query from {participant_identity} (topic 'custom_topic'): '{full_text_query}'")

            backend_url = os.getenv("BACKEND_URL")
            if not backend_url:
                logger.error("BACKEND_URL environment variable is not set.")
                return "Sorry, the backend service is not configured correctly for search."

            url = f"{backend_url}/search"
            payload = {"query": full_text_query}
            headers = {"accept": "application/json", "Content-Type": "application/json"}

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        response_text = json.dumps(data, ensure_ascii=False)

                logger.info(f"Sending mindmap data from text query (first 200 chars): {response_text[:200]}...")
                await room.local_participant.send_text(response_text, topic="mindmap-data")
            except aiohttp.ClientResponseError as e:
                logger.error(f"HTTP error during text query search: {e.status} {e.message}")
            except Exception as e:
                logger.error(f"Unexpected error in text query search: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Error in async_handle_user_text_input reading loop: {e}", exc_info=True)
