"""
Audio-based test client for Real-Time Podcast AI Assistant.
Uses FFmpeg to convert audio files or streams to linear16 PCM format.
"""

import asyncio
import json
import subprocess
import websockets
from pathlib import Path


# FFmpeg path - adjust if needed
FFMPEG_PATH = r"C:\Users\loizi\PycharmProjects\ffmpeg\bin\ffmpeg.exe"

# Test audio source - using BBC World Service live stream
AUDIO_SOURCE = "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"

# Or use a local file:
# AUDIO_SOURCE = "path/to/your/audio.mp3"


async def stream_audio_to_deepgram():
    """
    Stream audio from a source (URL or file) to the server.
    FFmpeg converts to linear16 PCM format that Deepgram expects.
    """
    uri = "ws://localhost:8000/listen"

    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to server")
            print(f"Starting audio stream from: {AUDIO_SOURCE}")

            # FFmpeg command to convert audio to linear16 PCM
            ffmpeg_cmd = [
                FFMPEG_PATH,
                '-i', AUDIO_SOURCE,          # Input source
                '-f', 's16le',               # Output format: 16-bit little-endian PCM
                '-ar', '16000',              # Sample rate: 16kHz
                '-ac', '1',                  # Channels: mono
                '-loglevel', 'error',        # Only show errors
                '-'                          # Output to stdout
            ]

            print("✓ Starting FFmpeg audio conversion...")

            # Start FFmpeg process
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            print("✓ Streaming audio data to server...")
            print("=" * 50)
            print("Listening for transcriptions (Press Ctrl+C to stop)...")
            print("=" * 50)

            # Create tasks for sending and receiving
            async def send_audio():
                """Send audio chunks to the server."""
                try:
                    # Read and send audio in chunks (~80ms recommended)
                    # 2560 bytes = ~80ms at 16kHz linear16
                    chunk_size = 2560

                    while True:
                        chunk = await process.stdout.read(chunk_size)
                        if not chunk:
                            print("\n✓ Audio stream ended")
                            break

                        # Send binary audio data
                        await websocket.send(chunk)

                except Exception as e:
                    print(f"\n✗ Error sending audio: {e}")

            async def receive_transcriptions():
                """Receive and display transcriptions from the server."""
                try:
                    while True:
                        response = await websocket.recv()
                        data = json.loads(response)

                        if data.get("type") == "transcript":
                            is_final = data.get("is_final", False)
                            text = data.get("text", "")
                            confidence = data.get("confidence", 0)

                            # Display transcription
                            marker = "🎤 FINAL" if is_final else "⏸️  PARTIAL"
                            print(f"{marker} [{confidence:.2%}] {text}")

                        elif data.get("type") == "topic_update":
                            topic = data.get("current_topic", "Unknown")
                            total = data.get("total_topics", 0)
                            print(f"\n📊 Topic Update: {topic} (Total: {total})\n")

                        elif data.get("type") == "fact_queued":
                            sentence = data.get("sentence", "")[:50]
                            print(f"🔍 Fact check queued: {sentence}...")

                        elif data.get("type") == "error":
                            print(f"❌ Error: {data.get('message')}")

                except websockets.exceptions.ConnectionClosed:
                    print("\n✓ Connection closed")
                except Exception as e:
                    print(f"\n✗ Error receiving: {e}")

            # Run both tasks concurrently
            try:
                await asyncio.gather(
                    send_audio(),
                    receive_transcriptions()
                )
            except asyncio.CancelledError:
                print("\n✓ Stopping...")

            # Clean up FFmpeg process
            if process.returncode is None:
                process.terminate()
                await process.wait()

    except websockets.exceptions.WebSocketException as e:
        print(f"✗ WebSocket error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def test_with_sample_audio():
    """
    Alternative: Generate test audio using FFmpeg's built-in test source.
    Useful if you don't have an audio file or stream.
    """
    uri = "ws://localhost:8000/listen"

    print("Generating test audio signal...")

    # Generate 10 seconds of test audio (sine wave)
    ffmpeg_cmd = [
        FFMPEG_PATH,
        '-f', 'lavfi',
        '-i', 'sine=frequency=1000:duration=10',  # 1kHz sine wave for 10 seconds
        '-f', 's16le',
        '-ar', '16000',
        '-ac', '1',
        '-loglevel', 'error',
        '-'
    ]

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✓ Connected to {uri}")

            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            print("Sending test audio...")

            while True:
                chunk = await process.stdout.read(2560)
                if not chunk:
                    break
                await websocket.send(chunk)

            print("✓ Test audio sent")

            # Wait for any responses
            await asyncio.sleep(2)

    except Exception as e:
        print(f"✗ Error: {e}")


async def main():
    """Main test runner."""
    print("Real-Time Podcast AI Assistant - Audio Test Client")
    print("=" * 50)
    print()

    # Check if FFmpeg exists
    if not Path(FFMPEG_PATH).exists():
        print(f"❌ FFmpeg not found at: {FFMPEG_PATH}")
        print("\nPlease update FFMPEG_PATH in the script to point to ffmpeg.exe")
        print("Current path:", FFMPEG_PATH)
        return

    print(f"✓ FFmpeg found at: {FFMPEG_PATH}")
    print()

    # Choose test mode
    print("Select test mode:")
    print("1. Stream from BBC World Service (live audio)")
    print("2. Generate test tone (no transcription expected)")
    print()

    choice = input("Enter choice (1 or 2, default=1): ").strip() or "1"

    if choice == "2":
        await test_with_sample_audio()
    else:
        await stream_audio_to_deepgram()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✓ Stopped by user")
