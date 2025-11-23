# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-Time Podcast AI Assistant - An event-driven system for live audio transcription with semantic topic tracking and fact-checking. Built for LauzHack 2025 hackathon.

## Running the Application

```bash
# Start the server (default: http://localhost:8000)
python main.py

# Test without audio (simulates transcript events)
python test_client.py

# Verify installation and configuration
python verify_setup.py
```

## Environment Setup

Required API keys in `.env`:
- `DEEPGRAM_API_KEY` - Live transcription service
- `TOGETHER_API_KEY` - LLM for claim detection and verification
- `HUGGINGFACE_API_KEY` - Optional

Copy from template: `cp .env.example .env`

## Architecture: Dual-Loop Event System

The application uses two async loops that run independently without blocking:

### Fast Loop (Topic Tracking)
- **Trigger**: Every 5 finalized sentences (configurable via `TOPIC_UPDATE_THRESHOLD`)
- **Function**: `topic_engine.update_topic_tree()`
- **Process**: Extract topic → Compare embeddings → Detect semantic drift → Update NetworkX graph
- **Non-blocking**: Uses `asyncio.create_task()` in `main.py:180`

### Slow Loop (Fact Checking)
- **Trigger**: Every finalized sentence, rate-limited to 10s intervals
- **Background worker**: `fact_engine.process_fact_queue()` (started in lifespan)
- **Pipeline**: Detect claim (LLM) → Search evidence (DuckDuckGo) → Verify (LLM)
- **Non-blocking**: Queued via `asyncio.Queue`, processed asynchronously

### Critical: Non-Blocking Design
Both loops use `asyncio.create_task()` to prevent blocking the WebSocket heartbeat. The fact queue runs as a background task started in the FastAPI lifespan manager.

## Central State Management

**`state_manager.py`** contains a singleton `StateManager` instance that ALL modules access:

```python
from state_manager import state  # Global singleton
```

Key state components:
- **`transcript_buffer`**: Deque of recent TranscriptSegment objects (max 100)
- **`topic_tree`**: NetworkX DiGraph tracking conversation flow
- **`fact_queue`**: asyncio.Queue for pending fact checks
- **`finalized_sentences`**: Accumulator for topic updates (cleared when threshold reached)
- **`fact_results`**: List of FactCheckResult with evidence sources

State mutation happens in:
- `main.py` - Adds transcript segments, queues fact checks
- `topic_engine.py` - Updates topic tree
- `fact_engine.py` - Adds fact results

## LLM Prompt Engineering

All prompts are in `config.py` and expect **JSON responses**. The code handles markdown code blocks:

```python
if content.startswith("```"):
    content = content.split("```")[1]
    if content.startswith("json"):
        content = content[4:]
```

When modifying prompts:
- Maintain the JSON schema in the prompt
- Update corresponding parsing code if schema changes
- Test with Together.ai's Llama-3.1-70B-Instruct-Turbo

Prompts:
- `CLAIM_DETECTION_PROMPT` - Returns `{is_claim, claim_text, reason}`
- `CLAIM_VERIFICATION_PROMPT` - Returns `{verdict, confidence, explanation, key_facts}`
- `TOPIC_EXTRACTION_PROMPT` - Returns `{topic, keywords}`

## Deepgram SDK 5.x Integration

**Important**: This uses Deepgram SDK 5.3.0 with the v2 API (NOT v1). Key differences:

```python
# Correct for 5.x with v2 API
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType

deepgram = AsyncDeepgramClient(api_key=settings.deepgram_api_key)
dg_connection = await deepgram.listen.v2.connect(
    model="nova-2",
    encoding="linear16",
    sample_rate="16000"
)

# Event handlers use EventType (not LiveTranscriptionEvents)
dg_connection.on(EventType.OPEN, on_open)
dg_connection.on(EventType.MESSAGE, on_message)
dg_connection.on(EventType.ERROR, on_error)
dg_connection.on(EventType.CLOSE, on_close)

# Start listening
await dg_connection.start_listening()

# Send audio
await dg_connection._send(audio_bytes)
```

Message objects received in event handlers have these attributes:
- `message.transcript` - The transcribed text
- `message.is_final` - Boolean indicating if transcription is final
- `message.words` - List of word objects with `.word` and `.confidence` attributes

## Embedding System (Currently Mock)

`topic_engine.py:get_embedding()` uses a **mock implementation** (simple hashing). To upgrade:

1. Install: `pip install sentence-transformers`
2. Replace in `topic_engine.py`:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(self, text: str) -> np.ndarray:
    if text in self.embedding_cache:
        return self.embedding_cache[text]
    embedding = model.encode(text)
    self.embedding_cache[text] = embedding
    return np.array(embedding)
```

## Configuration Tuning

Adjust in `config.py` or `.env`:

- **`FACT_CHECK_RATE_LIMIT`**: Seconds between fact checks (prevents search API rate limiting)
- **`TOPIC_UPDATE_THRESHOLD`**: Sentences before topic analysis (balances responsiveness vs. LLM cost)
- **`TOPIC_CONFIG['similarity_threshold']`**: Cosine similarity threshold for topic drift (0.0-1.0, lower = more sensitive)
- **`SEARCH_CONFIG['max_results']`**: DuckDuckGo results per claim (balance thoroughness vs. speed)

## Testing Strategy

**Without audio** (recommended for development):
```python
# test_client.py sends mock transcript events
python test_client.py
```

**With real audio**:
- Client must send PCM audio bytes (16kHz mono recommended) to WebSocket `/listen`
- Server forwards to Deepgram and returns transcript events

**Check endpoints**:
```bash
curl http://localhost:8000/stats      # System metrics
curl http://localhost:8000/topics     # Topic timeline
curl http://localhost:8000/facts      # Fact results with sources
```

## Code Organization Principles

- **No business logic in `main.py`**: It only orchestrates WebSocket/HTTP and calls engines
- **Engines are stateless**: All state mutations go through `state_manager.py`
- **Async everywhere**: All I/O operations (LLM, search, Deepgram) use async/await
- **Global singletons**: `state`, `topic_engine`, `fact_engine` are imported and shared

## Known Limitations (MVP)

- Mock embeddings (use real model for production)
- No database persistence (state lost on restart)
- No authentication on endpoints
- Rate limiting is time-based only (no token bucket)
- Evidence sources tracked but not displayed in UI (no UI exists yet)

## Adding New Features

**New LLM operation**:
1. Add prompt to `config.py`
2. Create async function in appropriate engine
3. Use `loop.run_in_executor()` for sync Together.ai calls
4. Handle JSON parsing with markdown block stripping

**New API endpoint**:
1. Add route in `main.py` (use `@app.get()` or `@app.websocket()`)
2. Access state via `state.get_stats()` or similar
3. Return JSONResponse for REST, send_json for WebSocket

**Modify loops**:
- Fast Loop threshold: Change `settings.topic_update_threshold`
- Slow Loop rate: Change `settings.fact_check_rate_limit`
- Add logic in `main.py` event handlers or engine processors
