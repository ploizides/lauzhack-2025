"""
Server-Side Stream Processor
Reuses the working WebSocket logic to process audio files server-side
and write results to JSON for frontend consumption.
"""

import asyncio
import json
import logging
import wave
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType

from backend.app.core.config import settings
from backend.app.core.state_manager import state, TranscriptSegment
from backend.app.engines.topic_engine import topic_engine
from backend.app.engines.fact_engine import fact_engine
from backend.app.utils.logger_util import DebugLogger

logger = logging.getLogger(__name__)

# Streaming configuration - same as test_wav_stream.py
CHUNK_DURATION_MS = 100  # Send chunks every 100ms (simulates real-time)
DEFAULT_AUDIO_FILE = Path(__file__).parent.parent.parent / "tests" / "test_data" / "LexNuclear.wav"
RESULTS_FILE = Path(__file__).parent.parent.parent / "stream_output.json"


class StreamProcessor:
    """
    Processes audio files server-side using the same logic as the WebSocket endpoint.
    Writes results incrementally to a JSON file instead of sending via WebSocket.
    """

    def __init__(self, audio_file: Optional[Path] = None):
        self.audio_file = audio_file or DEFAULT_AUDIO_FILE
        self.is_streaming = False
        self.stream_task: Optional[asyncio.Task] = None
        self.fact_monitor_task: Optional[asyncio.Task] = None
        self.last_fact_check_count = 0
        self.session_logger: Optional[DebugLogger] = None
        self.session_start_time: Optional[datetime] = None
        self.results: Dict[str, Any] = {
            "status": "idle",
            "started_at": None,
            "progress": 0.0,
            "transcripts": [],
            "topics": [],
            "topic_path": [],
            "topic_images": [],
            "edges": [],
            "fact_checks": [],
            "fact_verdicts": {
                "SUPPORTED": 0,
                "CONTRADICTED": 0,
                "UNCERTAIN": 0
            },
            "metadata": {}
        }
        self._reset_state()

    def _reset_state(self):
        """Reset application state for new stream."""
        # Clear the state manager buffers
        state.transcript_buffer.clear()
        state.fact_results.clear()
        state.finalized_sentence_count = 0
        state.current_topic_id = None
        self.last_fact_check_count = 0

    async def start_stream(self) -> Dict[str, Any]:
        """Start processing the audio file."""
        if self.is_streaming:
            return {"error": "Stream already running"}

        if not self.audio_file.exists():
            return {"error": f"Audio file not found: {self.audio_file}"}

        # Reset state
        self._reset_state()
        
        # Initialize new session logger
        self.session_logger = DebugLogger()
        self.session_start_time = datetime.now()
        
        self.results = {
            "status": "starting",
            "started_at": self.session_start_time.isoformat(),
            "progress": 0.0,
            "transcripts": [],
            "topics": [],
            "topic_path": [],
            "topic_images": [],
            "edges": [],
            "fact_checks": [],
            "fact_verdicts": {
                "SUPPORTED": 0,
                "CONTRADICTED": 0,
                "UNCERTAIN": 0
            },
            "metadata": {}
        }

        # Get audio file metadata
        with wave.open(str(self.audio_file), 'rb') as wav_file:
            self.results["metadata"] = {
                "filename": self.audio_file.name,
                "channels": wav_file.getnchannels(),
                "sample_width": wav_file.getsampwidth() * 8,  # bits
                "framerate": wav_file.getframerate(),
                "total_frames": wav_file.getnframes(),
                "duration_seconds": wav_file.getnframes() / wav_file.getframerate()
            }

        # Write initial state
        self._write_results()

        # Start streaming task
        self.stream_task = asyncio.create_task(self._process_stream())

        # Start fact-check monitor task
        self.fact_monitor_task = asyncio.create_task(self._monitor_fact_checks())

        self.is_streaming = True

        logger.info(f"Started streaming: {self.audio_file}")
        return {"status": "started", "file": str(self.audio_file)}

    async def stop_stream(self) -> Dict[str, Any]:
        """Stop the current stream."""
        if not self.is_streaming:
            return {"error": "No stream running"}

        self.is_streaming = False

        if self.stream_task:
            self.stream_task.cancel()
            try:
                await self.stream_task
            except asyncio.CancelledError:
                pass

        if self.fact_monitor_task:
            self.fact_monitor_task.cancel()
            try:
                await self.fact_monitor_task
            except asyncio.CancelledError:
                pass

        self.results["status"] = "stopped"
        self._write_results()
        
        # Save session data to logs
        self.save_session()

        logger.info("Stream stopped")
        return {"status": "stopped"}

    def get_status(self) -> Dict[str, Any]:
        """Get current stream status."""
        return {
            "is_streaming": self.is_streaming,
            "status": self.results.get("status"),
            "progress": self.results.get("progress", 0),
            "file": str(self.audio_file),
            "transcripts_count": len(self.results.get("transcripts", [])),
            "topics_count": len(self.results.get("topics", [])),
            "fact_checks_count": len(self.results.get("fact_checks", []))
        }

    def get_results(self) -> Dict[str, Any]:
        """Get current results."""
        return self.results.copy()
    
    def sync_images(self) -> None:
        """Sync topic_images from state to results (for smart image updates)."""
        if self.is_streaming:
            self.results["topic_images"] = state.topic_images.copy()
            self._write_results()

    def save_session(self):
        """
        Save complete session data to a session-specific directory.
        Creates a comprehensive session record including all transcripts, topics, 
        fact checks, and metadata in the session's own folder.
        """
        if not self.session_logger:
            logger.warning("No session logger available - session not saved")
            return
        
        try:
            # Save the DebugLogger's built-in session summary
            self.session_logger.save_summary()
            
            # Also save a comprehensive combined session file in the session directory
            session_end_time = datetime.now()
            session_duration = (session_end_time - self.session_start_time).total_seconds() if self.session_start_time else 0
            
            comprehensive_session = {
                "session_id": self.session_logger.session_id,
                "session_directory": str(self.session_logger.session_dir),
                "started_at": self.session_start_time.isoformat() if self.session_start_time else None,
                "completed_at": session_end_time.isoformat(),
                "duration_seconds": session_duration,
                "status": self.results.get("status", "unknown"),
                "audio_file": {
                    "filename": self.results.get("metadata", {}).get("filename", str(self.audio_file.name)),
                    "path": str(self.audio_file),
                    "metadata": self.results.get("metadata", {})
                },
                "statistics": {
                    "total_transcripts": len(self.results.get("transcripts", [])),
                    "final_transcripts": sum(1 for t in self.results.get("transcripts", []) if t.get("is_final", False)),
                    "total_topics": len(self.results.get("topics", [])),
                    "total_fact_checks": len(self.results.get("fact_checks", [])),
                    "fact_verdicts": {
                        "SUPPORTED": sum(1 for f in self.results.get("fact_checks", []) if f.get("verdict") == "SUPPORTED"),
                        "CONTRADICTED": sum(1 for f in self.results.get("fact_checks", []) if f.get("verdict") == "CONTRADICTED"),
                        "UNCERTAIN": sum(1 for f in self.results.get("fact_checks", []) if f.get("verdict") == "UNCERTAIN"),
                    }
                },
                "transcripts": self.results.get("transcripts", []),
                "topics": self.results.get("topics", []),
                "topic_path": self.results.get("topic_path", []),
                "topic_images": self.results.get("topic_images", []),
                "edges": self.results.get("edges", []),
                "fact_checks": self.results.get("fact_checks", []),
                "fact_verdicts": self.results.get("fact_verdicts", {"SUPPORTED": 0, "CONTRADICTED": 0, "UNCERTAIN": 0})
            }
            
            # Save comprehensive file to the session directory
            comprehensive_file = self.session_logger.session_dir / "complete_session.json"
            
            with open(comprehensive_file, 'w') as f:
                json.dump(comprehensive_session, f, indent=2)
            
            logger.info(f"Session saved successfully to: {self.session_logger.session_dir}")
            logger.info(f"Session stats: {comprehensive_session['statistics']['total_transcripts']} transcripts, "
                       f"{comprehensive_session['statistics']['total_topics']} topics, "
                       f"{comprehensive_session['statistics']['total_fact_checks']} fact checks")
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}", exc_info=True)

    def _write_results(self):
        """Write current results to JSON file."""
        try:
            with open(RESULTS_FILE, 'w') as f:
                json.dump(self.results, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write results: {e}")

    async def _process_stream(self):
        """
        Main streaming logic - reuses the WebSocket endpoint logic
        but writes to JSON instead of sending via WebSocket.
        """
        try:
            self.results["status"] = "streaming"
            self._write_results()

            # Initialize Deepgram client - same as WebSocket endpoint
            deepgram = AsyncDeepgramClient(api_key=settings.deepgram_api_key)

            # Configure Deepgram - same as WebSocket endpoint
            options = {
                "model": "nova-3",
                "encoding": "linear16",
                "sample_rate": "48000",
                "channels": "1",
            }

            async with deepgram.listen.v1.connect(**options) as dg_connection:
                logger.info("Deepgram connection established")

                # Event handlers - adapted from WebSocket endpoint
                def on_message(message):
                    """Handle incoming transcription from Deepgram."""
                    try:
                        if hasattr(message, 'channel') and hasattr(message.channel, 'alternatives'):
                            alternatives = message.channel.alternatives
                            if len(alternatives) > 0 and hasattr(alternatives[0], 'transcript'):
                                sentence = alternatives[0].transcript

                                if not sentence or len(sentence.strip()) == 0:
                                    return

                                is_final = getattr(message, 'is_final', True)
                                confidence = getattr(alternatives[0], 'confidence', 1.0)

                                # Create transcript segment
                                segment = TranscriptSegment(
                                    text=sentence,
                                    is_final=is_final,
                                    timestamp=datetime.now(),
                                    confidence=confidence,
                                )

                                # Add to state buffer
                                state.add_transcript_segment(segment)
                                
                                # Track sentences for image context (decoupled from topics)
                                if is_final:
                                    state.image_sentences.append(sentence)
                                    state.image_update_count += 1

                                # Add to results
                                self.results["transcripts"].append({
                                    "text": sentence,
                                    "is_final": is_final,
                                    "confidence": confidence,
                                    "timestamp": segment.timestamp.isoformat()
                                })
                                
                                # Log to session logger
                                if self.session_logger:
                                    self.session_logger.log_transcript(
                                        text=sentence,
                                        is_final=is_final,
                                        confidence=confidence,
                                        timestamp=segment.timestamp
                                    )

                                # Write to JSON
                                self._write_results()

                                logger.info(f"[{'FINAL' if is_final else 'PARTIAL'}] {sentence}")

                                # Topic tracking (Fast Loop) - same as WebSocket
                                if is_final and state.should_update_topics():
                                    finalized_text = state.consume_finalized_sentences()
                                    asyncio.create_task(self._update_topics(finalized_text))
                                
                                # Smart Image updates (Fast Loop - decoupled from topics!)
                                if is_final and state.should_update_image():
                                    asyncio.create_task(self._update_images())

                                # Fact checking (Slow Loop) - same as WebSocket
                                if is_final:
                                    asyncio.create_task(self._queue_fact_check(sentence))

                    except Exception as e:
                        logger.error(f"Error processing Deepgram message: {e}")

                def on_error(error):
                    """Handle Deepgram errors."""
                    logger.error(f"Deepgram error: {error}")
                    self.results["status"] = "error"
                    self.results["error"] = str(error)
                    self._write_results()

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

                # Start listening
                listen_task = asyncio.create_task(dg_connection.start_listening())

                # Stream audio file - adapted from test_wav_stream.py
                with wave.open(str(self.audio_file), 'rb') as wav_file:
                    frames_per_chunk = int((CHUNK_DURATION_MS / 1000.0) * wav_file.getframerate())
                    total_frames = wav_file.getnframes()
                    frames_sent = 0

                    while frames_sent < total_frames and self.is_streaming:
                        # Read chunk
                        audio_chunk = wav_file.readframes(frames_per_chunk)

                        if not audio_chunk:
                            break

                        # Convert stereo to mono (same as WebSocket endpoint)
                        import struct
                        samples = struct.unpack(f'<{len(audio_chunk)//2}h', audio_chunk)
                        mono_samples = []
                        for i in range(0, len(samples), 2):
                            if i + 1 < len(samples):
                                avg = (samples[i] + samples[i+1]) // 2
                                mono_samples.append(avg)
                            else:
                                mono_samples.append(samples[i])

                        mono_bytes = struct.pack(f'<{len(mono_samples)}h', *mono_samples)

                        # Send to Deepgram
                        await dg_connection.send_media(mono_bytes)

                        # Update progress
                        frames_sent += frames_per_chunk
                        self.results["progress"] = (frames_sent / total_frames) * 100

                        # Update every 5% progress
                        if frames_sent % (total_frames // 20) < frames_per_chunk:
                            self._write_results()
                            logger.info(f"Progress: {self.results['progress']:.1f}%")

                        # Sleep to simulate real-time streaming
                        await asyncio.sleep(CHUNK_DURATION_MS / 1000.0)

                # Stream complete
                logger.info("Audio streaming complete, waiting for final transcriptions...")
                await asyncio.sleep(5)  # Wait for final processing

                # Clean up
                listen_task.cancel()
                try:
                    await listen_task
                except asyncio.CancelledError:
                    pass

            # Mark as complete
            self.results["status"] = "complete"
            self.results["completed_at"] = datetime.now().isoformat()
            self.results["progress"] = 100.0
            self._write_results()
            
            # Save session data to logs
            self.save_session()

            logger.info("Stream processing complete")

        except asyncio.CancelledError:
            logger.info("Stream cancelled")
            self.results["status"] = "cancelled"
            self._write_results()
            # Save session even when cancelled
            self.save_session()
        except Exception as e:
            logger.error(f"Stream processing error: {e}", exc_info=True)
            self.results["status"] = "error"
            self.results["error"] = str(e)
            self._write_results()
            # Save session even when error occurs
            self.save_session()
        finally:
            self.is_streaming = False

    async def _update_topics(self, text: str):
        """Update topic tree (Fast Loop) - same as WebSocket endpoint."""
        try:
            topic_id = await topic_engine.update_topic_tree(text)

            if topic_id:
                summary = topic_engine.get_topic_summary()
                current_timestamp = datetime.now()

                # Get topic node data
                topic_node = state.topic_tree.nodes.get(topic_id)
                node_data = topic_node['data'] if topic_node and 'data' in topic_node else None

                # Get image URL if available
                image_url = None
                for img_entry in reversed(state.topic_images):
                    if img_entry["topic_id"] == topic_id:
                        image_url = img_entry["image_url"]
                        break

                # Add to results
                self.results["topics"].append({
                    "topic_id": topic_id,
                    "topic": summary["current_topic"],
                    "keywords": node_data.keywords if node_data and hasattr(node_data, 'keywords') else [],
                    "sentence_count": node_data.sentence_count if node_data and hasattr(node_data, 'sentence_count') else 0,
                    "weight": node_data.weight if node_data and hasattr(node_data, 'weight') else 1.0,
                    "image_url": image_url,
                    "total_topics": summary["total_topics"],
                    "timestamp": current_timestamp.isoformat()
                })

                # Update topic_path (full chronological path)
                self.results["topic_path"] = state.topic_path.copy()

                # Update topic_images (all images found so far)
                self.results["topic_images"] = state.topic_images.copy()

                # Update edges (parent-child relationships)
                self.results["edges"] = [
                    {"source": source, "target": target}
                    for source, target in state.topic_tree.edges
                ]

                # Log to session logger
                if self.session_logger and node_data:
                    self.session_logger.log_topic(
                        topic=summary["current_topic"],
                        keywords=node_data.keywords if hasattr(node_data, 'keywords') else [],
                        sentence_count=node_data.sentence_count if hasattr(node_data, 'sentence_count') else 0,
                        timestamp=current_timestamp
                    )

                # Write to JSON
                self._write_results()

                logger.info(f"Topic update: {summary['current_topic']}")

        except Exception as e:
            logger.error(f"Error updating topics: {e}")

    async def _update_images(self):
        """Update images based on conversation context (Fast Loop - decoupled from topics!)."""
        try:
            from backend.app.engines.image_engine import image_engine
            
            print(f"🖼️  Triggering smart image update...")
            await image_engine.search_and_update_smart_image()
            
            # Sync images to results immediately
            self.sync_images()
            
            # Log the update
            if state.topic_images:
                latest_image = state.topic_images[-1]
                logger.info(f"Smart image updated: {latest_image['topic']} -> {latest_image['image_url']}")
        
        except Exception as e:
            logger.error(f"Error updating images: {e}")

    async def _queue_fact_check(self, sentence: str):
        """Queue a fact check (Slow Loop) - same as WebSocket endpoint."""
        try:
            # Add to fact-checking queue
            await state.fact_queue.put(sentence)

            logger.info(f"Queued for fact check: {sentence[:50]}...")

        except Exception as e:
            logger.error(f"Error queuing fact check: {e}")

    async def _monitor_fact_checks(self):
        """
        Monitor the fact_results list and capture new results.
        This runs in the background and checks for new fact-check results
        from the fact_engine.process_fact_queue() background task.
        """
        try:
            while self.is_streaming:
                # Check if there are new fact-check results
                current_count = len(state.fact_results)

                if current_count > self.last_fact_check_count:
                    # Get new results
                    new_results = state.fact_results[self.last_fact_check_count:current_count]

                    for result in new_results:
                        # Add to our results
                        self.results["fact_checks"].append({
                            "claim": result.claim,
                            "verdict": result.verdict,
                            "confidence": result.confidence,
                            "explanation": result.explanation,
                            "key_facts": result.key_facts,
                            "evidence_sources": result.evidence_sources,
                            "search_query": result.search_query,
                            "timestamp": result.timestamp.isoformat()
                        })

                        # Update verdict aggregation counts
                        if result.verdict in self.results["fact_verdicts"]:
                            self.results["fact_verdicts"][result.verdict] += 1

                        # Log to session logger
                        if self.session_logger:
                            self.session_logger.log_fact_check(
                                claim=result.claim,
                                verdict=result.verdict,
                                confidence=result.confidence,
                                explanation=result.explanation,
                                key_facts=result.key_facts,
                                evidence_sources=result.evidence_sources,
                                timestamp=result.timestamp
                            )

                        logger.info(f"Fact check result: {result.verdict} - {result.claim[:50]}...")

                    # Update counter
                    self.last_fact_check_count = current_count

                    # Write to JSON
                    self._write_results()

                # Check every second
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Fact check monitor stopped")
        except Exception as e:
            logger.error(f"Error in fact check monitor: {e}")


# Global stream processor instance
stream_processor = StreamProcessor()
