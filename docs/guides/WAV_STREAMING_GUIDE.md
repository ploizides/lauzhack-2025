# WAV File Streaming Guide

Stream your 20-minute podcast WAV file directly to the server - **No FFmpeg needed!**

## Quick Start

1. **Verify your WAV file:**
   ```bash
   python test_wav_stream.py --test
   ```

2. **Start the server:**
   ```bash
   python main.py
   ```

3. **Stream the WAV file:**
   ```bash
   python test_wav_stream.py
   ```

## File Location

The script is configured for:
```
C:\Users\loizi\PycharmProjects\lauzhack-2025\test_data\audio.wav
```

**To use a different file**, edit `test_wav_stream.py` line 17:
```python
WAV_FILE_PATH = r"C:\path\to\your\file.wav"
```

## How It Works

### Chunked Streaming (Simulates Live Audio)

The script reads your 20-minute WAV file and streams it in **100ms chunks**:

```
WAV File (20 minutes)
  ↓
Read 100ms chunk
  ↓
Send to WebSocket
  ↓
Wait 100ms (simulate real-time)
  ↓
Repeat until complete
```

This simulates a live audio stream, perfect for demos!

### What You'll See

```
====================================================================
Real-Time Podcast AI Assistant - WAV Stream Test
====================================================================

📁 File: audio.wav
   Size: 32.50 MB
   Duration: 20.0 minutes (1200.0 seconds)
   Format: 1 channel(s), 16-bit, 16000Hz

✅ WAV format is optimal for Deepgram (mono, 16-bit, 16kHz)

Streaming in 100ms chunks (simulating real-time)
====================================================================

Connecting to ws://localhost:8000/listen...
✓ Connected to server

🎙️  Starting audio stream...
====================================================================
Transcriptions will appear below:
====================================================================

🎤 FINAL [0.95] Welcome to today's podcast about artificial intelligence
⏸️  PARTIAL [0.82] We're discussing the latest
🎤 FINAL [0.91] We're discussing the latest developments in AI

[Progress: 10.0% | Audio time: 120.0s | Elapsed: 122.5s]

📊 TOPIC UPDATE: Artificial Intelligence (Total topics: 1)

🔍 Fact check queued: ChatGPT was released by OpenAI in November 2022...

🎤 FINAL [0.93] The model has been trained on vast amounts of data
```

## Configuration

### Chunk Duration

Change how often audio chunks are sent (line 20):
```python
CHUNK_DURATION_MS = 100  # Send every 100ms

# Faster demo (less realistic):
CHUNK_DURATION_MS = 50   # Send every 50ms

# Slower (more conservative):
CHUNK_DURATION_MS = 200  # Send every 200ms
```

**Note:** The script automatically sleeps between chunks to simulate real-time, so a 20-minute file will take ~20 minutes to stream.

### Speed Up for Testing

To stream faster (not real-time), reduce the sleep time in line 183:
```python
# Original (real-time):
await asyncio.sleep(CHUNK_DURATION_MS / 1000.0)

# Faster (2x speed):
await asyncio.sleep(CHUNK_DURATION_MS / 2000.0)

# No delay (as fast as possible):
# await asyncio.sleep(0.01)  # Minimal delay
```

## WAV Format Requirements

### Optimal Format (Best Results)
- **Channels:** 1 (mono)
- **Bit depth:** 16-bit
- **Sample rate:** 16000 Hz (16kHz)

### Compatible Formats
- **Channels:** 1-2 (mono or stereo)
- **Bit depth:** 16-bit or 24-bit
- **Sample rate:** 8000Hz - 48000Hz

Deepgram will automatically convert non-optimal formats.

## Checking Your WAV File

### Quick Validation

```bash
python test_wav_stream.py --test
```

**Output:**
```
====================================================================
WAV File Validation
====================================================================

✓ File: audio.wav
  Size: 32.50 MB
  Duration: 20.0 minutes
  Channels: 1
  Sample width: 16-bit
  Sample rate: 16000Hz
  Total frames: 19,200,000

✅ Format: Perfect for Deepgram!

Ready to stream!
```

### Using Python Directly

```python
import wave

with wave.open('audio.wav', 'rb') as wav:
    print(f"Channels: {wav.getnchannels()}")
    print(f"Sample width: {wav.getsampwidth()} bytes")
    print(f"Framerate: {wav.getframerate()} Hz")
    print(f"Frames: {wav.getnframes()}")
```

## Demo Tips for Hackathon

### Prepare Your Demo

1. **Test first** with `--test` flag to verify format
2. **Start server** well before demo
3. **Have endpoints ready** in browser tabs:
   - http://localhost:8000/topics
   - http://localhost:8000/facts
   - http://localhost:8000/stats

### During the Demo

**Show the terminal output:**
- Real-time transcriptions appearing
- Topic updates when conversation shifts
- Fact checks being queued
- Progress indicators

**Show the browser:**
- `/topics` - Visual topic timeline
- `/facts` - Verified claims with sources
- `/stats` - System statistics

**Explain the architecture:**
- "20-minute podcast streaming in real-time chunks"
- "Dual-loop: Fast topic detection, slow fact-checking"
- "Non-blocking async design"
- "No FFmpeg needed - direct WAV streaming"

### Handle Questions

**"Why is it slow?"**
- "We're simulating real-time - 20 min audio takes 20 min"
- "This shows it works like a live podcast"
- "Can speed up by reducing sleep time"

**"Can it handle live audio?"**
- "Yes! Connect to microphone or streaming URL"
- "This demo uses a file to ensure consistent results"

**"What formats does it support?"**
- "WAV files directly, no conversion needed"
- "Other formats via FFmpeg (MP3, M4A, etc.)"

## Stopping the Demo

Press `Ctrl+C` in the terminal running `test_wav_stream.py`

The script will gracefully stop and show final statistics.

## Troubleshooting

### File not found
```bash
# Check file exists
ls "C:\Users\loizi\PycharmProjects\lauzhack-2025\test_data\audio.wav"

# Update path in test_wav_stream.py if needed
```

### No transcriptions appearing
1. Verify WAV file has audio (not silent)
2. Check Deepgram API key in `.env`
3. Check server logs for errors
4. Try `--test` mode to validate file

### Connection errors
1. Ensure server is running (`python main.py`)
2. Check server is on port 8000
3. Look for errors in server console

### Slow performance
- Large WAV files take time to stream
- This is intentional (simulates real-time)
- Can speed up by modifying sleep duration

## Advanced Usage

### Stream Only First N Minutes

Edit the streaming loop to stop early:

```python
# Add this after line 177
max_seconds = 300  # Only stream 5 minutes (300 seconds)
if frames_sent > max_seconds * wav_file.getframerate():
    print(f"\n✓ Reached {max_seconds}s limit, stopping...")
    break
```

### Stream Specific Section

```python
# Skip to 5 minutes into the audio
wav_file.setpos(int(5 * 60 * wav_file.getframerate()))

# Then start streaming
```

### Faster Streaming for Testing

```python
# Change line 183 to stream at 2x speed:
await asyncio.sleep(CHUNK_DURATION_MS / 2000.0)

# Or 4x speed:
await asyncio.sleep(CHUNK_DURATION_MS / 4000.0)
```

## Summary

✅ No FFmpeg required
✅ Direct WAV file streaming
✅ Simulates real-time audio
✅ Perfect for 20-minute demo
✅ Shows full pipeline in action
✅ Easy to run and understand

**Demo Command:**
```bash
# Terminal 1
python main.py

# Terminal 2
python test_wav_stream.py

# Browser
http://localhost:8000/topics
http://localhost:8000/facts
```

You're ready for the hackathon! 🎉
