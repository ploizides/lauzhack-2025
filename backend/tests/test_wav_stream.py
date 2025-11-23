"""
WAV File Streaming Test Client for Real-Time Podcast AI Assistant.
Streams a WAV file in chunks to simulate live audio input.
No FFmpeg required - WAV files are already in a compatible format.
"""

import asyncio
import json
import wave
import websockets
from pathlib import Path
from datetime import datetime


# WAV file path - using relative path from this file's location
# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
TEST_DATA_DIR = SCRIPT_DIR / "test_data"

# WAV_FILE_PATH = TEST_DATA_DIR / "audio.wav"
WAV_FILE_PATH = TEST_DATA_DIR / "LexNuclear.wav"

# Streaming configuration
CHUNK_DURATION_MS = 100  # Send chunks every 100ms (simulates real-time)
BYTES_PER_SECOND = 32000  # 16kHz * 2 bytes per sample (for 16-bit audio)


async def stream_wav_file():
    """
    Stream WAV file in chunks to simulate live audio.
    Reads the WAV file and sends it in real-time chunks.
    """
    wav_path = Path(WAV_FILE_PATH)

    # Check if file exists
    if not wav_path.exists():
        print(f"❌ WAV file not found: {WAV_FILE_PATH}")
        print("\nPlease:")
        print("1. Verify the file exists at the path")
        print("2. Update WAV_FILE_PATH in the script")
        return

    print("=" * 60)
    print("Real-Time Podcast AI Assistant - WAV Stream Test")
    print("=" * 60)
    print()

    # Open and validate WAV file
    try:
        with wave.open(str(wav_path), 'rb') as wav_file:
            # Get WAV file properties
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            duration_seconds = n_frames / framerate

            print(f"📁 File: {wav_path.name}")
            print(f"   Size: {wav_path.stat().st_size / 1024 / 1024:.2f} MB")
            print(f"   Duration: {duration_seconds / 60:.1f} minutes ({duration_seconds:.1f} seconds)")
            print(f"   Format: {channels} channel(s), {sample_width * 8}-bit, {framerate}Hz")
            print()

            # Check if format is compatible with Deepgram
            # Deepgram prefers: mono (1 channel), 16-bit, 16kHz
            if channels == 1 and sample_width == 2 and framerate == 16000:
                print("✅ WAV format is optimal for Deepgram (mono, 16-bit, 16kHz)")
            elif channels <= 2 and sample_width == 2:
                print(f"⚠️  WAV format will work but not optimal:")
                print(f"   - Channels: {channels} (prefer 1/mono)")
                print(f"   - Sample rate: {framerate}Hz (prefer 16000Hz)")
                print("   Deepgram will handle conversion automatically")
            else:
                print(f"⚠️  Unusual WAV format detected:")
                print(f"   - Channels: {channels}")
                print(f"   - Sample width: {sample_width * 8}-bit")
                print(f"   - Sample rate: {framerate}Hz")
                print("   May have issues - consider converting to 16-bit PCM")

            print()
            print(f"Streaming in {CHUNK_DURATION_MS}ms chunks (simulating real-time)")
            print("=" * 60)
            print()

    except wave.Error as e:
        print(f"❌ Invalid WAV file: {e}")
        return

    # Connect to WebSocket
    uri = "ws://localhost:8000/listen"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to server")
            print()
            print("🎙️  Starting audio stream...")
            print("=" * 60)
            print("Transcriptions will appear below:")
            print("=" * 60)
            print()

            # Open WAV file for streaming
            with wave.open(str(wav_path), 'rb') as wav_file:
                # Calculate chunk size in frames
                frames_per_chunk = int((CHUNK_DURATION_MS / 1000.0) * wav_file.getframerate())

                # Track progress
                total_frames = wav_file.getnframes()
                frames_sent = 0
                start_time = asyncio.get_event_loop().time()

                # Create task to receive transcriptions
                async def receive_transcriptions():
                    """Receive and display transcriptions from server."""
                    try:
                        while True:
                            response = await websocket.recv()
                            data = json.loads(response)

                            if data.get("type") == "transcript":
                                is_final = data.get("is_final", False)
                                text = data.get("text", "")
                                confidence = data.get("confidence", 0)
                                timestamp = data.get("timestamp", "")

                                # Display transcription
                                marker = "🎤 FINAL" if is_final else "⏸️  PARTIAL"
                                print(f"{marker} [{confidence:.2%}] {text}")

                            elif data.get("type") == "topic_update":
                                topic = data.get("current_topic", "Unknown")
                                total = data.get("total_topics", 0)
                                print(f"\n📊 TOPIC UPDATE: {topic} (Total topics: {total})\n")

                            elif data.get("type") == "fact_queued":
                                sentence = data.get("sentence", "")[:60]
                                queue_size = data.get("queue_size", 0)
                                print(f"🔍 Fact check queued: {sentence}... (Queue: {queue_size})")

                            elif data.get("type") == "error":
                                print(f"❌ Error: {data.get('message')}")

                    except websockets.exceptions.ConnectionClosed:
                        print("\n✓ Connection closed by server")
                    except Exception as e:
                        print(f"\n✗ Error receiving: {e}")

                # Start receiving task
                receive_task = asyncio.create_task(receive_transcriptions())

                try:
                    # Stream audio chunks
                    while frames_sent < total_frames:
                        # Read chunk
                        audio_chunk = wav_file.readframes(frames_per_chunk)

                        if not audio_chunk:
                            break

                        # Send chunk to server
                        await websocket.send(audio_chunk)

                        # Update progress
                        frames_sent += frames_per_chunk
                        progress_pct = (frames_sent / total_frames) * 100
                        elapsed_time = asyncio.get_event_loop().time() - start_time

                        # Show progress every 5 seconds of audio
                        if frames_sent % (wav_file.getframerate() * 5) < frames_per_chunk:
                            audio_time = frames_sent / wav_file.getframerate()
                            print(f"\n[Progress: {progress_pct:.1f}% | Audio time: {audio_time:.1f}s | Elapsed: {elapsed_time:.1f}s]\n")

                        # Sleep to simulate real-time streaming
                        await asyncio.sleep(CHUNK_DURATION_MS / 1000.0)

                    # All chunks sent
                    print()
                    print("=" * 60)
                    print(f"✓ Audio stream complete!")
                    print(f"  Sent {frames_sent:,} frames ({frames_sent / wav_file.getframerate():.1f}s of audio)")
                    print(f"  Elapsed time: {asyncio.get_event_loop().time() - start_time:.1f}s")
                    print("=" * 60)
                    print()

                    # Wait a bit for final transcriptions
                    print("Waiting for final transcriptions...")
                    await asyncio.sleep(5)

                except asyncio.CancelledError:
                    print("\n✓ Streaming cancelled by user")
                finally:
                    # Cancel receive task
                    receive_task.cancel()
                    try:
                        await receive_task
                    except asyncio.CancelledError:
                        pass

    except websockets.exceptions.WebSocketException as e:
        print(f"✗ WebSocket error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def quick_test():
    """
    Quick test to validate WAV file without streaming.
    """
    wav_path = Path(WAV_FILE_PATH)

    print("=" * 60)
    print("WAV File Validation")
    print("=" * 60)
    print()

    if not wav_path.exists():
        print(f"❌ File not found: {WAV_FILE_PATH}")
        return

    try:
        with wave.open(str(wav_path), 'rb') as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            duration = n_frames / framerate

            print(f"✓ File: {wav_path.name}")
            print(f"  Size: {wav_path.stat().st_size / 1024 / 1024:.2f} MB")
            print(f"  Duration: {duration / 60:.1f} minutes")
            print(f"  Channels: {channels}")
            print(f"  Sample width: {sample_width * 8}-bit")
            print(f"  Sample rate: {framerate}Hz")
            print(f"  Total frames: {n_frames:,}")
            print()

            # Check compatibility
            if channels == 1 and sample_width == 2 and framerate == 16000:
                print("✅ Format: Perfect for Deepgram!")
            elif channels <= 2 and sample_width == 2:
                print("✅ Format: Compatible (Deepgram will convert)")
            else:
                print("⚠️  Format: May need conversion")

            print()
            print("Ready to stream!")

    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Quick validation mode
        await quick_test()
    else:
        # Full streaming mode
        await stream_wav_file()


if __name__ == "__main__":
    print()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✓ Stopped by user (Ctrl+C)")
        print()
