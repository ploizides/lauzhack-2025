# Demo Setup Guide

Quick guide for setting up the podcast demo.

## Prerequisites Checklist

- [x] Server running (`python main.py`)
- [x] FFmpeg installed at `C:\Users\loizi\PycharmProjects\ffmpeg`
- [x] Deepgram API key in `.env`
- [x] Together.ai API key in `.env`
- [ ] Podcast MP3 file ready

## Step-by-Step Demo Setup

### 1. Prepare Your Podcast File

```bash
# Create the test_audio folder (if not exists)
# Already created!

# Copy your podcast file to the folder
# Name it: podcast_sample.wav (or podcast_sample.mp3)
```

**Where to place it:**
```
lauzhack-2025/
  └── test_audio/
      └── podcast_sample.wav  ← Your WAV file here
      └── podcast_sample.mp3  ← Or your MP3 file here
```

### 2. Configure Audio Source

The script is already configured to use WAV files by default:

```python
# In test_audio_client.py (line 20)
AUDIO_SOURCE = r"C:\Users\loizi\PycharmProjects\lauzhack-2025\test_audio\podcast_sample.wav"
```

**To use MP3 instead:**
- Comment out line 20
- Uncomment line 23 in `test_audio_client.py`

**To use a different file:**
- Edit line 20 in `test_audio_client.py`
- Update the path to your WAV/MP3 file

**To use live stream instead:**
- Comment out line 20
- Uncomment line 26 (BBC World Service)

### 3. Start the Server

```bash
python main.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
2025-11-22 - INFO - Starting Real-Time Podcast AI Assistant
2025-11-22 - INFO - Fact queue processor started
```

### 4. Run the Demo

```bash
python test_audio_client.py
```

**Expected output:**
```
Real-Time Podcast AI Assistant - Audio Test Client
==================================================

✓ FFmpeg found

📁 Audio file: podcast_sample.wav
   Size: 3.45 MB

Connecting to ws://localhost:8000/listen...
✓ Connected to server
✓ Streaming audio data to server...
==================================================
Listening for transcriptions (Press Ctrl+C to stop)...
==================================================

🎤 FINAL [0.95] Welcome to today's podcast...
```

### 5. Watch the Magic Happen

You'll see:

1. **Real-time transcriptions** with confidence scores
   ```
   🎤 FINAL [0.95] The text that was spoken
   ```

2. **Topic updates** when conversation shifts
   ```
   📊 Topic Update: Artificial Intelligence (Total: 1)
   ```

3. **Fact checks queued** for verification
   ```
   🔍 Fact check queued: ChatGPT was released in November 2022...
   ```

### 6. Check Results

While the demo runs, open another terminal:

```bash
# View statistics
curl http://localhost:8000/stats

# View topic timeline
curl http://localhost:8000/topics

# View fact-check results
curl http://localhost:8000/facts
```

## Demo Flow

```
1. Audio File (MP3)
   ↓
2. FFmpeg converts to PCM
   ↓
3. Streams to Server
   ↓
4. Deepgram transcribes
   ↓
5. Topic Engine analyzes (every 5 sentences)
   ↓
6. Fact Engine verifies claims (rate-limited)
   ↓
7. Results displayed in real-time
```

## Stopping the Demo

Press `Ctrl+C` in the test client terminal

The server will continue running (stop with `Ctrl+C` there too)

## Demo Tips

### For Best Results

1. **Use a 2-5 minute podcast clip**
   - Long enough to show topic transitions
   - Short enough for attention span

2. **Choose content-rich podcasts**
   - News interviews (lots of facts to check)
   - Tech discussions (shows topic drift)
   - Avoid music-only or single-topic rambles

3. **Prepare your talking points**
   - "See how it transcribes in real-time"
   - "Notice the topic detection when subjects change"
   - "Watch fact-checking queue factual claims"
   - "Check the REST API for accumulated results"

### During the Demo

**Point out:**
- ✅ Real-time transcription with confidence scores
- ✅ Dual-loop architecture (fast/slow processing)
- ✅ Non-blocking async design
- ✅ Topic graph building with NetworkX
- ✅ Fact verification with source links

**Show the code:**
- `main.py` - Async WebSocket handling
- `topic_engine.py` - Semantic drift detection
- `fact_engine.py` - 3-step verification pipeline

**Show the results:**
- Terminal output (live transcriptions)
- Browser: `http://localhost:8000/topics`
- Browser: `http://localhost:8000/facts`

## Troubleshooting Demo Issues

### Audio file not found
```bash
# Check the file exists
ls test_audio/podcast_sample.wav

# Or use absolute path in test_audio_client.py
```

### No transcriptions appearing
1. Check Deepgram API key is valid
2. Ensure file contains speech (not silence/music)
3. Look at server logs for errors

### Slow processing
- First transcription has ~2-3 sec delay (normal)
- Large files take longer to process
- Consider using a shorter clip

### FFmpeg errors
- Ensure FFmpeg path is correct
- Check file isn't corrupted
- Try a different audio file

## Quick Reset

To reset between demos:

```bash
# Stop server (Ctrl+C)
# Restart server
python main.py

# State is cleared on restart
```

## Alternative: Live Stream Demo

Want to show it working with live audio?

**Edit `test_audio_client.py` line 20:**

```python
# Comment out local file
# AUDIO_SOURCE = r"...\test_audio\podcast_sample.mp3"

# Uncomment live stream
AUDIO_SOURCE = "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"
```

This will stream BBC World Service live radio - always has speech, great for demos!

## Demo Options

### Option A: WAV File Streaming (RECOMMENDED - No FFmpeg!)

Perfect for your 20-minute podcast demo:

1. ✅ Place WAV file at: `test_data/audio.wav`
2. ✅ Start server: `python main.py`
3. ✅ Run demo: `python test_wav_stream.py`
4. ✅ Watch real-time transcription + topic + fact-checking
5. ✅ Show results: `http://localhost:8000/topics` and `/facts`

**See:** `WAV_STREAMING_GUIDE.md` for details

### Option B: With FFmpeg (MP3/Other Formats)

1. ✅ Install FFmpeg (see `FFMPEG_INSTALLATION.md`)
2. ✅ Place file in: `test_audio/podcast_sample.mp3`
3. ✅ Start server: `python main.py`
4. ✅ Run demo: `python test_audio_client.py`

You're ready for the hackathon demo! 🎉
