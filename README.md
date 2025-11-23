# Real-Time Podcast AI Assistant

A real-time AI assistant for podcast transcription, topic tracking, fact-checking, and intelligent image search. Built with FastAPI, Deepgram, and Together.ai.

## Features

### 🎙️ Real-Time Audio Processing
- **Live Transcription**: Deepgram Nova-3 for WebSocket-based speech-to-text
- **Streaming Architecture**: Non-blocking async processing with multiple update loops

### 📊 Topic Tracking
- **Semantic Analysis**: Automatic topic detection and extraction
- **Topic Tree**: NetworkX-based DAG tracking conversation flow
- **Smart Images**: Context-aware image search decoupled from topic updates

### ✓ Fact-Checking Pipeline
- **Claim Selection**: LLM-powered batched claim detection with strict filtering
- **Web Search**: DuckDuckGo integration with URL filtering and SafeSearch
- **Verification**: 3-step pipeline (Detect → Search → Verify)

### ⚡ Multi-Loop Architecture
- **Fast Loop** (2 sentences ~32s): Image updates
- **Medium Loop** (3 sentences ~48s): Topic updates  
- **Slow Loop** (5 sentences ~80s): Claim selection and fact-checking

## Project Structure

```
lauzhack-2025/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── main.py              # FastAPI app & WebSocket endpoint
│   │   ├── core/
│   │   │   ├── config.py            # Settings, prompts, configuration
│   │   │   └── state_manager.py     # Centralized state management
│   │   ├── engines/
│   │   │   ├── fact_engine.py       # Fact-checking pipeline
│   │   │   └── topic_engine.py      # Topic extraction & image search
│   │   ├── services/
│   │   │   └── stream_processor.py  # File-based streaming for testing
│   │   └── utils/
│   │       └── logger_util.py       # Logging utilities
│   ├── tests/
│   │   ├── test_audio/
│   │   │   └── LexNuclear.wav       # Test audio file
│   │   └── test_wav_stream.py       # Streaming test client
│   ├── .env.example                  # Environment template
│   ├── run.py                        # Server entry point
│   └── requirements.txt              # Python dependencies
├── env/                              # Virtual environment
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11
- API Keys:
  - [Deepgram](https://deepgram.com/) (speech-to-text)
  - [Together.ai](https://together.ai/) (LLM inference)

### Installation

1. **Clone and navigate to project:**
   ```bash
   cd /path/to/lauzhack-2025
   ```

2. **Activate virtual environment:**
   ```bash
   source env/bin/activate
   ```

3. **Install dependencies** (if needed):
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Configure API keys:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env and add your API keys:
   # DEEPGRAM_API_KEY=your_key_here
   # TOGETHER_API_KEY=your_key_here
   ```

### Running the Server

```bash
# From project root with venv activated
python backend/run.py
```

Server runs on **http://localhost:8000**

### Testing with Audio File

```bash
# Terminal 1: Start server
source env/bin/activate
python backend/run.py

# Terminal 2: Stream test audio
cd backend/tests
python test_wav_stream.py
```

### API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /api/stream/start` - Start server-side streaming (for testing)
- `WS /ws` - WebSocket endpoint for real-time audio streaming

## Configuration

### Timing Thresholds (`backend/app/core/config.py`)

Based on Deepgram's ~16 seconds per "final sentence":

```python
topic_update_threshold: int = 3        # 5 sentences
claim_selection_batch_size: int = 5    # 10 sentences
max_claims_per_batch: int = 2          # Max claims per batch
```

### LLM Configuration

```python
together_model: str = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
```

### Search Configuration

```python
SEARCH_CONFIG = {
    "max_results": 5,
    "safesearch": "strict",    # Filters inappropriate content
    "region": "wt-wt"          # Worldwide
}
```

## Architecture

### State Management
- **Centralized State**: `StateManager` class handles all application state
- **Transcript Buffer**: Deque of recent segments
- **Topic Tree**: NetworkX DiGraph tracking conversation flow
- **Fact Queue**: Async queue for fact-checking tasks

### WebSocket Flow

1. **Client connects** → Deepgram WebSocket established
2. **Audio chunks sent** → Real-time transcription
3. **Transcript received** → Added to state buffer
4. **Multi-loop processing**:
   
   - Topic updates (every 5 sentences)
   - Claim selection (every 10 sentences)
5. **Results streamed** → Client receives updates via WebSocket

### Fact-Checking Pipeline

```
Sentences → Batch Selection → Search Query Generation → 
Web Search (filtered) → Evidence Verification → Result
```

## Key Features

### Strict Claim Filtering
The claim selection prompt filters out:
- Opinions and subjective statements
- Vague claims without specifics
- Hypotheticals and predictions
- Questions and greetings
- Incomplete fragments

### URL Filtering
Blocks inappropriate domains from search results:
- Adult content sites
- Gambling/casino sites
- Other inappropriate content

### Decoupled Image Updates
Images update independently from topics for better visual engagement:
- Uses current topic + keywords + recent context
- More frequent than topic changes
- Better user experience

## Development

### Log Analysis

Monitor real-time operations:
```bash
# Watch server output for:
🖼️  Image search triggered
📊 Topic tree updated
✅ Claim selected
🔍 Search query generated
```

### Output File

Server-side streaming creates `stream_output.json` with all events for analysis.

## Troubleshooting

**Port already in use:**
```bash
lsof -ti:8765 | xargs kill -9
```

**Missing dependencies:**
```bash
source env/bin/activate
pip install -r backend/requirements.txt
```

**API key errors:**
Check `backend/.env` file has valid keys.

## License

See [LICENSE](LICENSE) file for details.

## Credits

Created for LauzHack 2025.
