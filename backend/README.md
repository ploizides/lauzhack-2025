# Backend - Real-Time Podcast AI Assistant

FastAPI-based backend for real-time podcast transcription, topic tracking, and fact-checking.

## Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── main.py          # FastAPI app and WebSocket endpoints
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py        # Configuration and settings
│   │   ├── state_manager.py # Global state management
│   │   └── __init__.py
│   ├── engines/
│   │   ├── fact_engine.py   # Fact-checking pipeline
│   │   ├── topic_engine.py  # Topic detection and tracking
│   │   └── __init__.py
│   └── utils/
│       ├── logger_util.py   # Logging utilities
│       └── __init__.py
├── tests/
│   ├── test_wav_stream.py   # WAV streaming test client
│   ├── test_audio/          # Test audio files
│   └── test_data/           # Test data files
├── logs/                     # Application logs
├── run.py                    # Entry point to run the server
├── __main__.py              # Allow running as module
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create from .env.example)
└── .env.example             # Example environment variables
```

## Installation

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   - `DEEPGRAM_API_KEY`: Your Deepgram API key
   - `TOGETHER_API_KEY`: Your Together AI API key

## Running the Server

### Method 1: Using run.py
```bash
python run.py
```

### Method 2: As a module
```bash
python -m backend
```

### Method 3: Using uvicorn directly
```bash
uvicorn backend.app.api.main:app --host 0.0.0.0 --port 8765 --reload
```

The server will start on `http://localhost:8765`

## API Endpoints

### WebSocket Endpoint
- **URL**: `ws://localhost:8765/ws`
- **Protocol**: Audio streaming + JSON messages

#### Client → Server Messages
1. **Audio Frames**: Raw audio bytes (16kHz, 16-bit, mono PCM)
2. **Control Messages**: JSON objects for control

#### Server → Client Messages
1. **Transcript Updates**: Real-time transcription results
2. **Topic Updates**: Topic tree changes
3. **Fact Check Results**: Verification results

### HTTP Endpoints
- `GET /`: Root endpoint with API info
- `GET /health`: Health check endpoint

## Testing

### WAV File Streaming Test
Tests the WebSocket connection by streaming a WAV file:

```bash
cd backend/tests
python test_wav_stream.py
```

Make sure the backend server is running before starting the test.

## Configuration

Key configuration options in `.env`:

- `FACT_CHECK_RATE_LIMIT`: Seconds between fact checks (default: 10)
- `TOPIC_UPDATE_THRESHOLD`: Sentences before topic update (default: 15)
- `TOGETHER_MODEL`: LLM model to use (default: Meta-Llama-3.1-70B-Instruct-Turbo)

## Architecture

### Three-Loop System

1. **Fast Loop (WebSocket)**: Real-time transcription
2. **Medium Loop (Topic Engine)**: Topic detection every N sentences
3. **Slow Loop (Fact Engine)**: Background fact-checking queue

### State Management
Global state is managed in `state_manager.py`:
- Transcript buffer (circular buffer)
- Topic tree (NetworkX graph)
- Fact-checking queue and results

## Development

### Adding New Features

1. **New API Endpoint**: Add to `app/api/main.py`
2. **New Configuration**: Add to `app/core/config.py`
3. **New Engine**: Create in `app/engines/`
4. **New Utility**: Add to `app/utils/`

### Logging
Logs are written to `backend/logs/` directory. Use the `debug_logger` from `utils/logger_util.py` for debug logging.

## Troubleshooting

### Import Errors
Make sure you're running from the project root and that the project root is in your PYTHONPATH.

### API Key Errors
Verify your `.env` file has valid API keys for Deepgram and Together AI.

### WebSocket Connection Issues
- Check that the server is running on port 8765
- Verify firewall settings
- Check server logs in `backend/logs/`

## Dependencies

Main dependencies:
- FastAPI: Web framework
- Uvicorn: ASGI server
- Deepgram SDK: Audio transcription
- Together AI: LLM inference
- NetworkX: Graph operations for topic tree
- DuckDuckGo Search: Web search for fact-checking

See `requirements.txt` for complete list.
