# Quick Start Guide

## Setup (5 minutes)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```env
   DEEPGRAM_API_KEY=your_key_here
   TOGETHER_API_KEY=your_key_here
   ```

3. **Start the server**:
   ```bash
   python main.py
   ```

## Test Without Audio

Run the test client to simulate a podcast conversation:

```bash
python test_client.py
```

This will:
- ✓ Test API endpoints
- ✓ Simulate transcript events
- ✓ Trigger topic detection
- ✓ Queue fact checks

## View Results

### REST API
```bash
# System stats
curl http://localhost:8000/stats

# Topic timeline
curl http://localhost:8000/topics

# Fact-check results (with source links)
curl http://localhost:8000/facts
```

### WebSocket (Real-time)
Connect to `ws://localhost:8000/listen` and send audio bytes.

## Key Files

- `config.py` → Prompts and settings
- `main.py` → Server entry point
- `state_manager.py` → Central state
- `topic_engine.py` → Fast Loop
- `fact_engine.py` → Slow Loop

## Adjust Configuration

Edit `config.py`:
- `FACT_CHECK_RATE_LIMIT`: Change rate limiting
- `TOPIC_UPDATE_THRESHOLD`: Sensitivity of topic detection
- LLM prompts: Customize detection and verification

## Monitoring

Server logs show:
- Transcript events (PARTIAL/FINAL)
- Topic shifts
- Fact check results
- API calls

## Common Issues

**"Failed to connect to Deepgram"**
→ Check `DEEPGRAM_API_KEY` in `.env`

**"Rate limit exceeded"**
→ Increase `FACT_CHECK_RATE_LIMIT` in `.env`

**"JSON parsing error"**
→ LLM response format issue - check Together.ai API key

## Next Steps

1. Integrate with real audio source (microphone, file, stream)
2. Replace mock embeddings in `topic_engine.py:get_embedding()`
3. Build frontend UI
4. Add database for persistence
5. Implement user authentication

## Architecture at a Glance

```
Audio → Deepgram → Transcript
                      ↓
         ┌────────────┴────────────┐
         ↓                         ↓
    FAST LOOP                 SLOW LOOP
  Topic Tracking           Fact Checking
  (Every 5 sentences)      (Rate limited)
         ↓                         ↓
   NetworkX Graph          Verification Results
                           (with source links)
```

Happy hacking! 🚀
