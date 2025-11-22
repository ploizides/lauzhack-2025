# Test Audio Files

Place your podcast audio files here for testing.

## Quick Start

1. **Add your podcast audio file** to this folder (WAV, MP3, etc.)
2. **Rename it to:** `podcast_sample.wav` (or `podcast_sample.mp3`)
3. **Run the test:**
   ```bash
   python test_audio_client.py
   ```

## Using a Different Filename

If you want to use a different filename, edit `test_audio_client.py`:

```python
# Change this line:
AUDIO_SOURCE = r"C:\Users\loizi\PycharmProjects\lauzhack-2025\test_audio\podcast_sample.wav"

# To:
AUDIO_SOURCE = r"C:\Users\loizi\PycharmProjects\lauzhack-2025\test_audio\your_file.wav"
# Or:
AUDIO_SOURCE = r"C:\Users\loizi\PycharmProjects\lauzhack-2025\test_audio\your_file.mp3"
```

## Supported Audio Formats

FFmpeg will automatically convert any audio format:
- MP3
- WAV
- M4A
- AAC
- OGG
- FLAC
- etc.

## Recommended Test Podcasts

For best results, use podcasts with:
- ✅ Clear speech
- ✅ English language
- ✅ Factual content (news, interviews, discussions)
- ✅ 2-10 minute duration (for demo)

**Why?** This helps demonstrate:
- Transcription quality
- Topic detection (semantic drift between subjects)
- Fact-checking (verifiable claims)

## Download Sample Podcasts

You can download short podcast clips from:
- **NPR Podcasts**: https://www.npr.org/podcasts
- **BBC World Service**: https://www.bbc.co.uk/sounds/podcasts
- **TED Talks Audio**: https://www.ted.com/talks
- **YouTube to MP3** converters for podcast clips

## File Size

- Small file (< 5 MB): Fast processing, good for quick demos
- Medium file (5-20 MB): ~5-15 minutes, shows topic transitions
- Large file (> 20 MB): Longer sessions, more comprehensive testing

## What Happens During Processing

1. **FFmpeg** converts your MP3 to linear16 PCM (16kHz mono)
2. **Audio streams** to the server in ~80ms chunks
3. **Deepgram** transcribes in real-time
4. **Topic Engine** detects semantic drift every 5 sentences
5. **Fact Engine** queues factual claims for verification

## Example Output

```
📁 Audio file: podcast_sample.mp3
   Size: 3.45 MB

Connecting to ws://localhost:8000/listen...
✓ Connected to server
✓ Streaming audio data to server...
==================================================
Listening for transcriptions (Press Ctrl+C to stop)...
==================================================

🎤 FINAL [0.95] Welcome to today's podcast about artificial intelligence
🎤 FINAL [0.91] We're discussing the latest developments in large language models
🎤 FINAL [0.93] ChatGPT was released by OpenAI in November 2022

📊 Topic Update: Artificial Intelligence (Total: 1)

🔍 Fact check queued: ChatGPT was released by OpenAI in November 2022...
```

## Troubleshooting

**File not found error?**
- Check the file is in this folder
- Check the filename matches exactly
- Use absolute path if needed

**No transcriptions?**
- Ensure file contains speech (not music only)
- Check audio isn't corrupted
- Try a different podcast file

**Slow processing?**
- Large files take longer
- First transcription may have ~2-3 second delay
- This is normal for streaming processing
