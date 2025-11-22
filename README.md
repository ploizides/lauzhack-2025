# Real-Time Podcast AI Assistant

An AI-powered assistant for live podcast transcription, topic tracking, and real-time fact-checking.

## Features

- **Live Transcription**: Real-time audio transcription using Deepgram Flux
- **Topic Tracking**: Automatic semantic drift detection and conversation timeline
- **Fact Checking**: 3-step verification pipeline (Detect → Search → Verify)
- **Dual-Loop Architecture**: Fast loop for topics, slow loop for fact-checking
- **WebSocket API**: Real-time communication with minimal latency

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client (Audio Stream)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Server                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Deepgram (Transcription)                   │ │
│  └──────────────┬─────────────────────────────────────────┘ │
│                 │                                             │
│     ┌───────────▼──────────┐       ┌────────────────────┐   │
│     │   FAST LOOP          │       │   SLOW LOOP         │   │
│     │   Topic Tracker      │       │   Fact Checker      │   │
│     │   (NetworkX Graph)   │       │   (3-Step Pipeline) │   │
│     └──────────────────────┘       └────────────────────┘   │
│                                                               │
│              State Manager (Central State)                   │
└─────────────────────────────────────────────────────────────┘
```

## Installation

1. **Clone the repository**:
   ```bash
   cd lauzhack-2025
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```
   DEEPGRAM_API_KEY=your_deepgram_key
   TOGETHER_API_KEY=your_together_ai_key
   HUGGINGFACE_API_KEY=your_hf_key  # Optional
   ```

4. **Verify setup** (optional but recommended):
   ```bash
   python verify_setup.py
   ```

## Usage

### Start the Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

### API Endpoints

- `GET /` - Health check
- `GET /stats` - System statistics
- `GET /topics` - Topic timeline
- `GET /facts` - Recent fact-check results
- `WebSocket /listen` - Main audio streaming endpoint
- `WebSocket /facts/stream` - Real-time fact results stream

### WebSocket Client Example

```python
import asyncio
import websockets
import pyaudio

async def stream_audio():
    uri = "ws://localhost:8000/listen"

    async with websockets.connect(uri) as websocket:
        # Configure audio
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8000
        )

        # Stream audio
        while True:
            data = stream.read(8000)
            await websocket.send(data)

            # Receive transcription
            response = await websocket.recv()
            print(response)

asyncio.run(stream_audio())
```

## Configuration

Edit `config.py` or set environment variables:

- `FACT_CHECK_RATE_LIMIT`: Seconds between fact checks (default: 10)
- `TOPIC_UPDATE_THRESHOLD`: Sentences before topic update (default: 5)
- `TOGETHER_MODEL`: LLM model to use (default: Llama-3.1-70B)

## Project Structure

```
lauzhack-2025/
├── main.py              # FastAPI server & WebSocket endpoints
├── config.py            # Configuration & prompts
├── state_manager.py     # Central state management
├── topic_engine.py      # Topic tracking & semantic drift
├── fact_engine.py       # 3-step fact-checking pipeline
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── README.md           # This file
```

## How It Works

### Fast Loop (Topic Tracking)

1. Partial transcripts arrive continuously
2. Every 5 finalized sentences → extract topic using LLM
3. Compare with current topic using embeddings
4. If semantic drift detected → create new topic node
5. Update NetworkX graph with topic timeline

### Slow Loop (Fact Checking)

1. **Detect**: LLM determines if sentence contains factual claim
2. **Search**: DuckDuckGo finds evidence (with source links)
3. **Verify**: LLM compares claim vs evidence
4. Rate-limited to 1 check per 10 seconds (configurable)
5. Results stored and streamed to clients

## Development

### Testing

```bash
# Run the server in development mode
python main.py

# In another terminal, test the API
curl http://localhost:8000/stats
```

### TODO Improvements

- [ ] Replace mock embeddings with sentence-transformers
- [ ] Add speaker diarization
- [ ] Implement conversation export
- [ ] Add authentication
- [ ] Create web UI
- [ ] Add database persistence
- [ ] Implement caching for LLM responses

## Tech Stack

- **Framework**: FastAPI 0.115.0
- **Audio**: Deepgram SDK 5.3.0
- **LLM**: Together.ai 1.3.4 (Llama-3.1-70B)
- **Search**: DuckDuckGo Search 8.1.1
- **Graph**: NetworkX 3.4.2
- **Async**: Python asyncio
- **Python**: 3.8+ required

## License

MIT License - Built for LauzHack 2025

## Troubleshooting

**Issue**: Deepgram connection fails
- Check API key in `.env`
- Ensure audio format is PCM 16kHz mono

**Issue**: Rate limiting on search
- Increase `FACT_CHECK_RATE_LIMIT` in `.env`
- Reduce `SEARCH_CONFIG.max_results` in `config.py`

**Issue**: LLM responses fail to parse
- Check Together.ai API key
- Verify model availability
- Check logs for JSON parsing errors

## Contributing

This is a hackathon MVP. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
