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

# Test audio source options:

# Option 1: Local audio file (recommended for demo)
# Place your podcast file (MP3, WAV, etc.) in the 'test_audio' folder
AUDIO_SOURCE = r"C:\Users\loizi\PycharmProjects\lauzhack-2025\test_audio\podcast_sample.wav"

# Option 2: Use MP3 instead
# AUDIO_SOURCE = r"C:\Users\loizi\PycharmProjects\lauzhack-2025\test_audio\podcast_sample.mp3"

# Option 3: BBC World Service live stream (for real-time testing)
# AUDIO_SOURCE = "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"

# Option 4: Any other local audio file (MP3, WAV, M4A, AAC, FLAC, OGG, etc.)
# AUDIO_SOURCE = r"C:\path\to\your\audio.wav"


async def stream_audio_to_deepgram():
    """
    Stream audio from a source (URL or file) to the server.
    FFmpeg converts to linear16 PCM format that Deepgram expects.
    """
    uri = "ws://localhost:8000/listen"

    # Check if source is a file
    is_file = not AUDIO_SOURCE.startswith("http://") and not AUDIO_SOURCE.startswith("https://")

    if is_file:
        source_path = Path(AUDIO_SOURCE)
        if not source_path.exists():
            print(f"❌ Audio file not found: {AUDIO_SOURCE}")
            print(f"\nPlease:")
            print(f"1. Create folder: test_audio")
            print(f"2. Place your MP3 file there as: podcast_sample.mp3")
            print(f"   OR update AUDIO_SOURCE in the script")
            return

        print(f"📁 Audio file: {source_path.name}")
        print(f"   Size: {source_path.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print(f"🌐 Streaming from: {AUDIO_SOURCE}")

    print(f"\nConnecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to server")

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

    print(f"✓ FFmpeg found")
    print()

    # Stream the configured audio source
    await stream_audio_to_deepgram()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✓ Stopped by user")
