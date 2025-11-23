"""
Main entry point for Real-Time Podcast AI Assistant.
Implements FastAPI WebSocket server with Deepgram integration.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator
from deepgram import AsyncDeepgramClient
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from deepgram import DeepgramClient
from deepgram.core.events import EventType

from backend.app.core.config import settings
from backend.app.core.state_manager import state, TranscriptSegment
from backend.app.engines.topic_engine import topic_engine
from backend.app.engines.fact_engine import fact_engine

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG to see detailed messages
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
    logger.info("Transcription + Topic Tracking + Fact Checking enabled")
    
    # Start fact-checking queue processor in background
    fact_queue_task = asyncio.create_task(fact_engine.process_fact_queue())
    logger.info("Fact queue processor started")

    yield

    # Shutdown
    logger.info("Shutting down...")
    # if fact_queue_task:
    #     fact_queue_task.cancel()
    #     try:
    #         await fact_queue_task
    #     except asyncio.CancelledError:
    #         pass
    logger.info("Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="Real-Time Podcast AI Assistant",
    description="AI-powered assistant for live podcast transcription and fact-checking",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# DISABLED: Topics endpoint
# @app.get("/topics")
# async def get_topics():
#     """Get topic timeline and summary."""
#     return JSONResponse(content=topic_engine.get_topic_summary())


# DISABLED: Facts endpoint
# @app.get("/facts")
# async def get_facts():
#     """Get recent fact-checking results."""
#     facts = [
#         {
#             "claim": result.claim,
#             "verdict": result.verdict,
#             "confidence": result.confidence,
#             "explanation": result.explanation,
#             "key_facts": result.key_facts,
#             "evidence_sources": result.evidence_sources,
#             "timestamp": result.timestamp.isoformat(),
#         }
#         for result in state.fact_results[-20:]  # Last 20 results
#     ]
#     return JSONResponse(content={"total": len(state.fact_results), "recent": facts})


@app.get("/transcript")
async def get_transcript():
    """Get full transcript."""
    segments = list(state.transcript_buffer)
    transcript_text = "\n".join([f"[{seg.timestamp.strftime('%H:%M:%S')}] {seg.text}" for seg in segments if seg.is_final])
    return JSONResponse(content={
        "total_segments": len(segments),
        "final_segments": len([s for s in segments if s.is_final]),
        "transcript": transcript_text
    })


@app.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    """
    Process an audio file and return transcription, topics, and fact-checks.

    This endpoint is designed for demos - it processes a complete audio file
    and returns all analysis results in one response.

    Args:
        file: Audio file (WAV, MP3, etc.)

    Returns:
        JSON with transcript, topics, and fact-check results
    """
    logger.info(f"Processing audio file: {file.filename}")

    try:
        # Read the audio file
        audio_data = await file.read()

        # Initialize Deepgram client
        deepgram = DeepgramClient(api_key=settings.deepgram_api_key)

        logger.info("Sending audio to Deepgram for transcription...")

        # Send to Deepgram prerecorded API using the correct method
        response = deepgram.listen.v1.media.transcribe_file(
            request=audio_data,
            model="nova-3",
            smart_format=True,
            punctuate=True,
            paragraphs=True,
            utterances=True,
        )

        # Extract transcript
        transcript_data = response.results
        if not transcript_data or not transcript_data.channels:
            raise HTTPException(status_code=500, detail="No transcription results from Deepgram")

        # Get the full transcript
        alternatives = transcript_data.channels[0].alternatives
        if not alternatives:
            raise HTTPException(status_code=500, detail="No alternatives in transcription")

        full_transcript = alternatives[0].transcript
        paragraphs = alternatives[0].paragraphs.paragraphs if hasattr(alternatives[0], 'paragraphs') else []

        logger.info(f"Transcription complete: {len(full_transcript)} characters")

        # Process topics from paragraphs
        topics_list = []
        if paragraphs:
            for i, para in enumerate(paragraphs[:5]):  # Process first 5 paragraphs for demo
                para_text = " ".join([sentence.text for sentence in para.sentences])
                if len(para_text) > 50:  # Only process substantial paragraphs
                    topic_result = await topic_engine.extract_topic(para_text)
                    if topic_result:
                        topic, keywords = topic_result
                        topics_list.append({
                            "topic": topic,
                            "keywords": keywords,
                            "text_sample": para_text[:100] + "..."
                        })

        logger.info(f"Extracted {len(topics_list)} topics")

        # Process fact-checking on key sentences
        fact_checks = []
        if paragraphs:
            sentences_to_check = []
            for para in paragraphs[:3]:  # Check first 3 paragraphs
                for sentence in para.sentences[:2]:  # First 2 sentences per paragraph
                    if len(sentence.text) > 30:  # Only substantial sentences
                        sentences_to_check.append(sentence.text)

            # Fact-check each sentence
            for sentence in sentences_to_check[:5]:  # Limit to 5 for demo
                logger.info(f"Fact-checking: {sentence[:50]}...")

                # Run the full fact-checking pipeline
                result = await fact_engine.check_fact(sentence)
                if result:
                    fact_checks.append({
                        "claim": result.claim,
                        "verdict": result.verdict,
                        "confidence": result.confidence,
                        "explanation": result.explanation,
                        "key_facts": result.key_facts,
                        "sources": result.evidence_sources
                    })

        logger.info(f"Completed {len(fact_checks)} fact-checks")

        # Return comprehensive results
        return JSONResponse(content={
            "status": "success",
            "filename": file.filename,
            "transcript": {
                "full_text": full_transcript,
                "word_count": len(full_transcript.split()),
                "paragraph_count": len(paragraphs) if paragraphs else 0
            },
            "topics": topics_list,
            "fact_checks": fact_checks,
            "summary": {
                "total_topics": len(topics_list),
                "total_fact_checks": len(fact_checks),
                "verified_claims": len([f for f in fact_checks if f["verdict"] == "SUPPORTED"]),
                "false_claims": len([f for f in fact_checks if f["verdict"] == "REFUTED"])
            }
        })

    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")


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

        # Connect to Deepgram using v1 live API
        # Model: nova-3 for best accuracy
        # Note: We convert stereo to mono before sending, so channels=1
        options = {
            "model": "nova-3",
            "encoding": "linear16",
            "sample_rate": "48000",
            "channels": "1",
        }
        async with deepgram.listen.v1.connect(**options) as dg_connection:

            # Event handlers for Deepgram
            def on_message(message):
                """Handle incoming transcription from Deepgram."""
                try:
                    # Log raw message structure for debugging
                    logger.debug(f"Raw message type: {type(message).__name__}")
                    
                    # Deepgram v1 message structure: message.channel.alternatives[0].transcript
                    if hasattr(message, 'channel') and hasattr(message.channel, 'alternatives'):
                        alternatives = message.channel.alternatives
                        if len(alternatives) > 0 and hasattr(alternatives[0], 'transcript'):
                            sentence = alternatives[0].transcript
                            
                            # Skip empty transcripts
                            if not sentence or len(sentence.strip()) == 0:
                                return
                            
                            # Check if this is a final result
                            is_final = getattr(message, 'is_final', True)
                            
                            # Also check speech_final (natural speech endpoint)
                            speech_final = getattr(message, 'speech_final', False)

                            # Get confidence from alternatives
                            confidence = getattr(alternatives[0], 'confidence', 1.0)
                            
                            logger.debug(f"Transcript: is_final={is_final}, speech_final={speech_final}, len={len(sentence)}, text={sentence[:50]}")

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

                            # Topic tracking (Fast Loop)
                            if is_final and state.should_update_topics():
                                finalized_text = state.consume_finalized_sentences()
                                asyncio.create_task(update_topics_async(websocket, finalized_text))

                            # Fact checking (Slow Loop - queued)
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
            
            chunk_count = 0
            bytes_sent = 0

            # Main loop: receive audio from client and forward to Deepgram
            try:
                while True:
                    # Receive audio data from client
                    data = await websocket.receive()

                    if "bytes" in data:
                        chunk_count += 1
                        chunk_size = len(data["bytes"])
                        bytes_sent += chunk_size
                        
                        # Log every 50 chunks
                        if chunk_count % 50 == 0:
                            logger.info(f"Sent {chunk_count} chunks, {bytes_sent:,} bytes total")
                        
                        # Convert stereo to mono (average L and R channels)
                        # Audio is 16-bit PCM stereo (2 bytes per sample, 2 channels)
                        import struct
                        audio_bytes = data["bytes"]
                        
                        # Unpack all 16-bit samples
                        samples = struct.unpack(f'<{len(audio_bytes)//2}h', audio_bytes)
                        
                        # Average every pair of samples (L and R channels)
                        mono_samples = []
                        for i in range(0, len(samples), 2):
                            if i + 1 < len(samples):
                                avg = (samples[i] + samples[i+1]) // 2
                                mono_samples.append(avg)
                            else:
                                mono_samples.append(samples[i])
                        
                        mono_bytes = struct.pack(f'<{len(mono_samples)}h', *mono_samples)
                        
                        # Forward mono audio to Deepgram using send_media() for async v1
                        await dg_connection.send_media(mono_bytes)

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
        # Truncate error message to fit WebSocket control frame limit (max 123 bytes)
        error_msg = str(e)[:100]
        await websocket.close(code=1011, reason=error_msg)


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
