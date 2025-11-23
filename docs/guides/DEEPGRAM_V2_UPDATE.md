# Deepgram SDK v2 API Update

## Summary of Changes

The code has been updated to use Deepgram SDK 5.3.0 with the **v2 API endpoint** based on the official Deepgram Flux documentation.

## What Changed

### 1. Imports
```python
# Before
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# After
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
```

### 2. Client Initialization
```python
# Before
deepgram = DeepgramClient(settings.deepgram_api_key)
dg_connection = deepgram.listen.live.v("1")

# After
deepgram = AsyncDeepgramClient(api_key=settings.deepgram_api_key)
dg_connection = await deepgram.listen.v2.connect(
    model="nova-2",
    encoding="linear16",
    sample_rate="16000"
)
```

**Key Points:**
- Use `AsyncDeepgramClient` instead of `DeepgramClient`
- Use `v2.connect()` instead of `live.v("1")`
- Pass model and audio format parameters directly to `connect()`

### 3. Event Handlers
```python
# Before
dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
dg_connection.on(LiveTranscriptionEvents.Error, on_error)
dg_connection.on(LiveTranscriptionEvents.Close, on_close)

# After
dg_connection.on(EventType.OPEN, on_open)
dg_connection.on(EventType.MESSAGE, on_message)
dg_connection.on(EventType.ERROR, on_error)
dg_connection.on(EventType.CLOSE, on_close)
```

**Key Points:**
- Use `EventType` enum instead of `LiveTranscriptionEvents`
- Add `EventType.OPEN` handler
- `EventType.MESSAGE` replaces `LiveTranscriptionEvents.Transcript`

### 4. Message Structure
```python
# Event handler receives message object
def on_message(message):
    if hasattr(message, 'transcript') and message.transcript:
        text = message.transcript
        is_final = getattr(message, 'is_final', True)

        # Get confidence from words
        if hasattr(message, 'words') and message.words:
            confidence = sum(w.confidence for w in message.words) / len(message.words)
```

**Message Attributes:**
- `message.transcript` - Transcribed text
- `message.is_final` - Boolean for final transcription
- `message.words` - List with `.word` and `.confidence` attributes

### 5. Starting the Connection
```python
# Before
await dg_connection.start(options)

# After
listen_task = asyncio.create_task(dg_connection.start_listening())
```

**Key Points:**
- No separate `start()` call needed
- Use `start_listening()` to begin receiving transcriptions
- Run as async task to avoid blocking

### 6. Sending Audio
```python
# Before
dg_connection.send(audio_bytes)

# After
await dg_connection._send(audio_bytes)
```

**Key Points:**
- Method is now async (requires `await`)
- Uses `_send()` internal method for v2 API

### 7. Cleanup
```python
# Before
await dg_connection.finish()

# After
listen_task.cancel()
try:
    await listen_task
except asyncio.CancelledError:
    pass
```

## Files Modified

1. **main.py** - Complete Deepgram integration rewrite
2. **CLAUDE.md** - Updated Deepgram SDK documentation
3. **MIGRATION_NOTES.md** - Detailed API migration guide
4. **DEEPGRAM_V2_UPDATE.md** - This file

## Testing

The application should now work with:
```bash
python main.py
```

**Note:** You must have `DEEPGRAM_API_KEY` set in your `.env` file.

## Supported Models

With v2 API, you can use:
- `nova-2` (default in code)
- `flux-general-en` (for Flux model with turn detection)

To use Flux, change the model parameter:
```python
dg_connection = await deepgram.listen.v2.connect(
    model="flux-general-en",  # Instead of nova-2
    encoding="linear16",
    sample_rate="16000"
)
```

## Audio Format Requirements

The v2 API requires explicit audio format specification:
- **Encoding**: `linear16` (16-bit PCM)
- **Sample Rate**: `16000` (16kHz recommended)
- **Channels**: Mono (1 channel)

For other formats, see Deepgram documentation.

## References

- [Deepgram Flux Quickstart](https://developers.deepgram.com/docs/flux/quickstart)
- [Deepgram Python SDK](https://github.com/deepgram/deepgram-python-sdk)

## Troubleshooting

**Error: Cannot import 'LiveTranscriptionEvents'**
- ✓ Fixed - Use `EventType` instead

**Error: Connection requires v2 endpoint**
- ✓ Fixed - Using `listen.v2.connect()`

**Error: send() is not async**
- ✓ Fixed - Using `await _send()`

All issues resolved in this update! ✅
