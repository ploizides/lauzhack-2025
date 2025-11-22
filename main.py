"""
Main entry point for Real-Time Podcast AI Assistant.
Implements FastAPI WebSocket server with Deepgram integration.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType

from config import settings
from state_manager import state, TranscriptSegment
from topic_engine import topic_engine
from fact_engine import fact_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Background task for fact-checking queue
fact_queue_task = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for FastAPI.
    Starts background tasks on startup and cleans up on shutdown.
    """
    global fact_queue_task

    # Startup
    logger.info("Starting Real-Time Podcast AI Assistant")
    logger.info(f"Fact check rate limit: {settings.fact_check_rate_limit}s")
    logger.info(f"Topic update threshold: {settings.topic_update_threshold} sentences")

    # Start fact-checking queue processor
    fact_queue_task = asyncio.create_task(fact_engine.process_fact_queue())
    logger.info("Fact queue processor started")

    yield

    # Shutdown
    logger.info("Shutting down...")
    if fact_queue_task:
        fact_queue_task.cancel()
        try:
            await fact_queue_task
        except asyncio.CancelledError:
            pass
    logger.info("Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="Real-Time Podcast AI Assistant",
    description="AI-powered assistant for live podcast transcription and fact-checking",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Real-Time Podcast AI Assistant",
        "version": "1.0.0",
    }


@app.get("/stats")
async def get_stats():
    """Get current system statistics."""
    return JSONResponse(content=state.get_stats())


@app.get("/topics")
async def get_topics():
    """Get topic timeline and summary."""
    return JSONResponse(content=topic_engine.get_topic_summary())


@app.get("/facts")
async def get_facts():
    """Get recent fact-checking results."""
    facts = [
        {
            "claim": result.claim,
            "verdict": result.verdict,
            "confidence": result.confidence,
            "explanation": result.explanation,
            "key_facts": result.key_facts,
            "evidence_sources": result.evidence_sources,
            "timestamp": result.timestamp.isoformat(),
        }
        for result in state.fact_results[-20:]  # Last 20 results
    ]
    return JSONResponse(content={"total": len(state.fact_results), "recent": facts})


@app.websocket("/listen")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for audio streaming.

    The client should:
    1. Connect to this WebSocket
    2. Send raw audio data (PCM, 16kHz, mono recommended)
    3. Receive real-time transcription events

    This endpoint:
    1. Forwards audio to Deepgram
    2. Processes transcription events
    3. Updates topic tree (Fast Loop)
    4. Queues fact checks (Slow Loop)
    """
    await websocket.accept()
    logger.info(f"WebSocket connection accepted from {websocket.client}")

    # Initialize Deepgram client
    try:
        deepgram = AsyncDeepgramClient(api_key=settings.deepgram_api_key)

        # Connect to Deepgram v2 using async context manager
        async with deepgram.listen.v2.connect(
            model="nova-2",
            encoding="linear16",
            sample_rate="16000"
        ) as dg_connection:

            # Event handlers for Deepgram
            def on_message(message):
                """Handle incoming transcription from Deepgram."""
                try:
                    # Check if message has transcript attribute
                    if hasattr(message, 'transcript') and message.transcript:
                        sentence = message.transcript
                        is_final = getattr(message, 'is_final', True)

                        # Get confidence from words if available
                        confidence = 1.0
                        if hasattr(message, 'words') and message.words and len(message.words) > 0:
                            confidence = sum(w.confidence for w in message.words) / len(message.words)

                        # Create transcript segment
                        segment = TranscriptSegment(
                            text=sentence,
                            is_final=is_final,
                            timestamp=datetime.now(),
                            confidence=confidence,
                        )

                        # Add to state buffer
                        state.add_transcript_segment(segment)

                        # Send transcript to client (schedule as task to avoid blocking)
                        asyncio.create_task(websocket.send_json(
                            {
                                "type": "transcript",
                                "text": sentence,
                                "is_final": is_final,
                                "confidence": segment.confidence,
                                "timestamp": segment.timestamp.isoformat(),
                            }
                        ))

                        logger.info(f"[{'FINAL' if is_final else 'PARTIAL'}] {sentence}")

                        # FAST LOOP: Update topics when threshold is reached
                        if is_final and state.should_update_topics():
                            finalized_text = state.consume_finalized_sentences()
                            asyncio.create_task(update_topics_async(websocket, finalized_text))

                        # SLOW LOOP: Queue fact check for finalized sentences
                        # Use create_task to avoid blocking the WebSocket heartbeat
                        if is_final:
                            asyncio.create_task(queue_fact_check_async(websocket, sentence))

                except Exception as e:
                    logger.error(f"Error processing Deepgram message: {e}")

            def on_error(error):
                """Handle Deepgram errors."""
                logger.error(f"Deepgram error: {error}")
                asyncio.create_task(websocket.send_json({"type": "error", "message": str(error)}))

            def on_close(_):
                """Handle Deepgram connection close."""
                logger.info("Deepgram connection closed")

            def on_open(_):
                """Handle Deepgram connection open."""
                logger.info("Deepgram connection opened")

            # Register event handlers
            dg_connection.on(EventType.OPEN, on_open)
            dg_connection.on(EventType.MESSAGE, on_message)
            dg_connection.on(EventType.ERROR, on_error)
            dg_connection.on(EventType.CLOSE, on_close)

            # Start listening task
            listen_task = asyncio.create_task(dg_connection.start_listening())
            logger.info("Deepgram connection started successfully")

            # Main loop: receive audio from client and forward to Deepgram
            try:
                while True:
                    # Receive audio data from client
                    data = await websocket.receive()

                    if "bytes" in data:
                        # Forward audio to Deepgram using _send (internal method for v2)
                        await dg_connection._send(data["bytes"])

                    elif "text" in data:
                        # Handle control messages from client
                        import json
                        message = json.loads(data["text"])

                        if message.get("type") == "close":
                            logger.info("Client requested close")
                            break

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
            finally:
                # Clean up Deepgram connection
                listen_task.cancel()
                try:
                    await listen_task
                except asyncio.CancelledError:
                    pass
                logger.info("Deepgram connection finished")

    except Exception as e:
        logger.error(f"Failed to initialize Deepgram: {e}")
        await websocket.close(code=1011, reason=str(e))


async def update_topics_async(websocket: WebSocket, text: str):
    """
    Asynchronously update topic tree (Fast Loop).

    Args:
        websocket: WebSocket to send updates to
        text: Finalized text to analyze
    """
    try:
        topic_id = await topic_engine.update_topic_tree(text)

        if topic_id:
            summary = topic_engine.get_topic_summary()
            await websocket.send_json(
                {
                    "type": "topic_update",
                    "topic_id": topic_id,
                    "current_topic": summary["current_topic"],
                    "total_topics": summary["total_topics"],
                }
            )
            logger.info(f"Topic update sent: {summary['current_topic']}")

    except Exception as e:
        logger.error(f"Error updating topics: {e}")


async def queue_fact_check_async(websocket: WebSocket, sentence: str):
    """
    Asynchronously queue a fact check (Slow Loop).

    This function does NOT block - it just queues the sentence
    for processing by the background fact-checking worker.

    Args:
        websocket: WebSocket to send updates to
        sentence: Finalized sentence to fact-check
    """
    try:
        # Add to fact-checking queue
        await state.fact_queue.put(sentence)
        logger.info(f"Queued for fact check: {sentence[:50]}...")

        # Optionally notify client
        await websocket.send_json(
            {
                "type": "fact_queued",
                "sentence": sentence,
                "queue_size": state.fact_queue.qsize(),
            }
        )

    except Exception as e:
        logger.error(f"Error queuing fact check: {e}")


# WebSocket endpoint for fact check results (optional)
@app.websocket("/facts/stream")
async def fact_stream_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint that streams fact-checking results in real-time.
    """
    await websocket.accept()
    logger.info("Fact stream client connected")

    last_sent_count = 0

    try:
        while True:
            # Check for new fact results
            current_count = len(state.fact_results)

            if current_count > last_sent_count:
                # Send new results
                new_results = state.fact_results[last_sent_count:current_count]

                for result in new_results:
                    await websocket.send_json(
                        {
                            "type": "fact_result",
                            "claim": result.claim,
                            "verdict": result.verdict,
                            "confidence": result.confidence,
                            "explanation": result.explanation,
                            "key_facts": result.key_facts,
                            "evidence_sources": result.evidence_sources,
                            "timestamp": result.timestamp.isoformat(),
                        }
                    )

                last_sent_count = current_count

            # Wait a bit before checking again
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info("Fact stream client disconnected")


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload during development
        log_level="info",
    )
