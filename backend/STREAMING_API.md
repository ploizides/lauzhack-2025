# Streaming API Documentation

Server-side audio streaming API for MVP demo. Processes a hardcoded audio file and provides results via JSON file and REST endpoints.

## Overview

This API allows you to:
1. Start processing a pre-recorded audio file server-side
2. Monitor processing progress in real-time
3. Access results incrementally as they're generated
4. Stop processing at any time

## Architecture

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │
       │ HTTP REST API
       │
┌──────▼──────────────────────────────────────────┐
│              FastAPI Backend                     │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │      StreamProcessor                    │    │
│  │  - Reads hardcoded WAV file            │    │
│  │  - Streams to Deepgram                 │    │
│  │  - Processes transcripts, topics, facts│    │
│  │  - Writes to stream_output.json        │    │
│  └────────────────────────────────────────┘    │
│                                                  │
└──────────────────────────────────────────────────┘
       │
       │ Writes to
       ▼
┌─────────────────┐
│stream_output.json│  ← Frontend can read this file
└─────────────────┘    or use /api/stream/results
```

## API Endpoints

### POST /api/stream/start

Start streaming the hardcoded audio file.

**Request:**
```bash
curl -X POST http://localhost:8000/api/stream/start
```

**Response:**
```json
{
  "status": "started",
  "file": "/path/to/audio/file.wav"
}
```

**Behavior:**
- Starts processing audio in chunks (100ms intervals)
- Simulates real-time streaming
- Runs transcription, topic detection, and fact-checking
- Writes results incrementally to `stream_output.json`

### POST /api/stream/stop

Stop the current streaming session.

**Request:**
```bash
curl -X POST http://localhost:8000/api/stream/stop
```

**Response:**
```json
{
  "status": "stopped"
}
```

### GET /api/stream/status

Get current streaming status.

**Request:**
```bash
curl http://localhost:8000/api/stream/status
```

**Response:**
```json
{
  "is_streaming": true,
  "status": "streaming",
  "progress": 45.2,
  "file": "/path/to/LexNuclear.wav",
  "transcripts_count": 150,
  "topics_count": 5,
  "fact_checks_count": 12
}
```

### GET /api/stream/results

Get complete current results.

**Request:**
```bash
curl http://localhost:8000/api/stream/results
```

**Response:**
```json
{
  "status": "streaming",
  "started_at": "2025-11-23T10:30:00",
  "progress": 45.2,
  "transcripts": [
    {
      "text": "Hello world",
      "is_final": true,
      "confidence": 0.95,
      "timestamp": "2025-11-23T10:30:05"
    }
  ],
  "topics": [
    {
      "topic_id": "node_0",
      "topic": "Introduction to AI",
      "total_topics": 1,
      "timestamp": "2025-11-23T10:30:10"
    }
  ],
  "fact_checks": [
    {
      "claim": "The Earth revolves around the Sun",
      "verdict": "SUPPORTED",
      "confidence": 0.98,
      "explanation": "...",
      "key_facts": [...],
      "sources": [...],
      "timestamp": "2025-11-23T10:30:15"
    }
  ],
  "metadata": {
    "filename": "LexNuclear.wav",
    "channels": 2,
    "sample_width": 16,
    "framerate": 48000,
    "total_frames": 14400000,
    "duration_seconds": 300.0
  }
}
```

## Output File

Results are written to `backend/stream_output.json` incrementally. This file is updated:
- When new transcript segments arrive (every ~100ms)
- When new topics are detected
- When fact-checks complete
- Progress updates every 5%

## Usage Example

### Starting a Stream

```bash
# 1. Start the stream
curl -X POST http://localhost:8000/api/stream/start

# 2. Check status periodically
curl http://localhost:8000/api/stream/status

# 3. Get results (or read stream_output.json directly)
curl http://localhost:8000/api/stream/results
```

### For Frontend Integration

**Option 1: Poll the API**
```javascript
// Start stream
await fetch('http://localhost:8000/api/stream/start', { method: 'POST' });

// Poll for updates every second
const interval = setInterval(async () => {
  const response = await fetch('http://localhost:8000/api/stream/results');
  const data = await response.json();

  // Update UI with data
  updateUI(data);

  // Stop polling when complete
  if (data.status === 'complete') {
    clearInterval(interval);
  }
}, 1000);
```

**Option 2: Read the JSON file directly**
```javascript
// If serving the JSON file statically
const interval = setInterval(async () => {
  const response = await fetch('/stream_output.json');
  const data = await response.json();
  updateUI(data);
}, 1000);
```

## Configuration

Hardcoded audio file location:
```python
# backend/app/services/stream_processor.py
DEFAULT_AUDIO_FILE = Path(__file__).parent.parent.parent / "tests" / "test_data" / "LexNuclear.wav"
```

Streaming parameters (same as test_wav_stream.py):
```python
CHUNK_DURATION_MS = 100  # Send chunks every 100ms
```

## Processing Flow

1. **Audio Chunking**: Reads WAV file in 100ms chunks
2. **Deepgram Transcription**: Sends chunks to Deepgram API
3. **Transcript Processing**:
   - Partial transcripts → stored temporarily
   - Final transcripts → added to results, triggers topic/fact processing
4. **Topic Detection**: Every N sentences, extracts topics
5. **Fact Checking**: Queued for background processing, results monitored
6. **JSON Writing**: Updates file after each significant event

## Code Reuse

This implementation **reuses code** from:
- `backend/app/api/main.py` - WebSocket endpoint logic
- `backend/tests/test_wav_stream.py` - Audio streaming logic
- Existing engines (topic_engine, fact_engine) unchanged

This ensures:
- Consistency with proven working code
- Easy to merge future improvements
- Minimal code duplication

## Differences from WebSocket Endpoint

| Aspect | WebSocket `/listen` | Streaming API |
|--------|-------------------|---------------|
| Client | External (test script) | Server-side |
| Audio Source | Uploaded/streamed | Hardcoded file |
| Output | WebSocket messages | JSON file + REST API |
| Use Case | Live recording | MVP demo |

## Future Improvements

- [ ] Support custom audio file selection
- [ ] Add WebSocket for real-time updates (instead of polling)
- [ ] Add pause/resume functionality
- [ ] Support multiple concurrent streams
- [ ] Add audio playback synchronization timestamps

## Troubleshooting

**Stream won't start:**
- Check audio file exists at the hardcoded path
- Verify Deepgram API key is configured
- Check backend logs for errors

**Results not updating:**
- Verify `stream_output.json` is being written
- Check file permissions
- Monitor backend logs for processing errors

**Fact-checks not appearing:**
- Fact-checking runs in background and may take time
- Monitor `/api/stream/status` for fact_checks_count
- Check that fact_engine background task is running
