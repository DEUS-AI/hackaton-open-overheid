from __future__ import annotations

import logging
import os

from assistant_functions import AssistantFnc
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai
from text_input_handler import handle_user_text_input

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()

    # Get agent and chat_ctx from run_multimodal_agent
    # Run multimodal agent for voice interactions
    run_multimodal_agent(ctx, participant)

    # Register text stream handler for user text input
    TEXT_INPUT_TOPIC = "custom_topic"
    ctx.room.register_text_stream_handler(
        TEXT_INPUT_TOPIC,
        lambda reader, p_identity: handle_user_text_input(reader, p_identity, ctx.room),
    )
    logger.info(f"Registered text handler for topic '{TEXT_INPUT_TOPIC}'")

    logger.info("agent started")


def run_multimodal_agent(
    ctx: JobContext, participant: rtc.RemoteParticipant
) -> tuple[MultimodalAgent, llm.ChatContext]:
    logger.info("starting multimodal agent")

    # Construct the path to the instructions file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    instructions_file_path = os.path.join(current_dir, "instructions.txt")

    try:
        with open(instructions_file_path, encoding="utf-8") as f:
            agent_instructions = f.read().strip()
    except FileNotFoundError:
        logger.error(f"Instructions file not found at {instructions_file_path}. Using default instructions.")
        # Fallback instructions if the file is missing
        agent_instructions = (
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation. "
            "You were created as a demo to showcase the capabilities of LiveKit's agents framework. "
            "When a user asks you to search for information or documents, use the 'search_documents' tool."
        )
    except Exception as e:
        logger.error(f"Error reading instructions file {instructions_file_path}: {e}. Using default instructions.")
        # Fallback instructions on other errors
        agent_instructions = (
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation. "
            "You were created as a demo to showcase the capabilities of LiveKit's agents framework. "
            "When a user asks you to search for information or documents, use the 'search_documents' tool."
        )

    model = openai.realtime.RealtimeModel(
        instructions=agent_instructions,
        modalities=["audio", "text"],
    )

    chat_ctx = llm.ChatContext()
    chat_ctx.append(
        text="Context about the user: you are talking to a software engineer who's building voice AI applications. "
        "Greet the user with a friendly greeting and ask how you can help them today."
        "Inform them that you can search for documents if they need.",
        role="assistant",
    )

    # Instantiate the function context
    fnc_ctx = AssistantFnc()
    logger.info(f"RUN_MULTIMODAL_AGENT: Created AssistantFnc instance, id: {id(fnc_ctx)}")

    # Manually call init on the function context
    logger.info(f"RUN_MULTIMODAL_AGENT: Manually calling fnc_ctx.init() for instance id: {id(fnc_ctx)}")
    fnc_ctx.init(room=ctx.room, participant=participant)
    logger.info(f"RUN_MULTIMODAL_AGENT: Manual fnc_ctx.init() call completed for instance id: {id(fnc_ctx)}")

    agent = MultimodalAgent(
        model=model,
        chat_ctx=chat_ctx,
        fnc_ctx=fnc_ctx,
    )
    agent.start(ctx.room, participant)

    # to enable the agent to speak first
    agent.generate_reply()

    return agent, chat_ctx


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
