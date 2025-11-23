# Migration Notes - Deepgram SDK 5.3.0

## Changes from 3.x to 5.x with v2 API

The code has been updated to be compatible with Deepgram SDK 5.3.0 using the v2 API endpoint.

### Key API Changes

1. **Client Initialization**
   ```python
   # Old (3.x)
   config = DeepgramClientOptions(options={"keepalive": "true"})
   deepgram = DeepgramClient(api_key, config)
   dg_connection = deepgram.listen.asynclive.v("1")

   # New (5.x with v2 API)
   from deepgram import AsyncDeepgramClient
   deepgram = AsyncDeepgramClient(api_key=api_key)
   dg_connection = await deepgram.listen.v2.connect(
       model="nova-2",
       encoding="linear16",
       sample_rate="16000"
   )
   ```

2. **Import Changes**
   ```python
   # Old
   from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions

   # New
   from deepgram import AsyncDeepgramClient
   from deepgram.core.events import EventType
   ```

3. **Event Handler Changes**
   ```python
   # Old
   dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

   # New
   dg_connection.on(EventType.MESSAGE, on_message)
   dg_connection.on(EventType.OPEN, on_open)
   dg_connection.on(EventType.ERROR, on_error)
   dg_connection.on(EventType.CLOSE, on_close)
   ```

4. **Starting Connection**
   ```python
   # Old
   await dg_connection.start(options)

   # New
   # Options passed in connect(), start_listening() begins receiving
   await dg_connection.start_listening()
   ```

5. **Sending Audio**
   ```python
   # Old
   dg_connection.send(audio_bytes)

   # New
   await dg_connection._send(audio_bytes)  # Now async
   ```

### Testing

The updated code maintains the same functionality:
- ✓ Live transcription via WebSocket
- ✓ Event handlers (on_message, on_error, on_close)
- ✓ Async/await pattern
- ✓ Audio streaming support

### Version Compatibility

- **Deepgram SDK**: 5.3.0 (was 3.8.3)
- **DuckDuckGo Search**: 8.1.1 (was 7.0.0)
- **Python**: 3.8+ required
- **FastAPI**: 0.115.0 (unchanged)
- **Together**: 1.3.4 (unchanged)

### Installation

```bash
pip install -r requirements.txt
```

No code changes needed in your application - just update dependencies!

## Verified Features

- [x] WebSocket connection
- [x] Live transcription
- [x] Event handling
- [x] Async operations
- [x] Error handling

## Notes

The Deepgram SDK 5.x series is the current stable release and includes:
- Better async support
- Simplified configuration
- Improved error handling
- More consistent API

For full SDK documentation, visit: https://developers.deepgram.com/docs/python-sdk
