# Demo Commands - Quick Reference

## For Your 20-Minute WAV Demo

### Setup (One Time)

1. Place your WAV file:
   ```
   C:\Users\loizi\PycharmProjects\lauzhack-2025\test_data\audio.wav
   ```

2. Verify API keys in `.env`:
   ```
   DEEPGRAM_API_KEY=your_key
   TOGETHER_API_KEY=your_key
   ```

### Run Demo (Every Time)

**Terminal 1: Start Server**
```bash
python main.py
```

**Terminal 2: Stream Audio**
```bash
python test_wav_stream.py
```

**Browser: Open These URLs**
- http://localhost:8000/stats
- http://localhost:8000/topics
- http://localhost:8000/facts

That's it! 🎉

---

## File Purpose Summary

| File | Purpose | Needed for Demo? |
|------|---------|------------------|
| `main.py` | Server | ✅ YES |
| `test_wav_stream.py` | Stream WAV file | ✅ YES |
| `test_client.py` | Test API endpoints only | ❌ Optional |
| `test_audio_client.py` | FFmpeg-based streaming | ❌ No (use WAV instead) |

## What You'll See

### In Terminal 2 (test_wav_stream.py)
```
🎤 FINAL [0.95] Welcome to today's podcast...
📊 TOPIC UPDATE: Artificial Intelligence
🔍 Fact check queued: ChatGPT was released...
```

### In Browser
- `/stats` - Live statistics
- `/topics` - Topic timeline
- `/facts` - Verified claims with sources

## Stop Demo

Press `Ctrl+C` in both terminals

---

## Troubleshooting

**Server won't start?**
- Check port 8000 is free
- Verify API keys in `.env`

**No audio streaming?**
- Verify file exists at `test_data/audio.wav`
- Run: `python test_wav_stream.py --test`

**No transcriptions?**
- Check Deepgram API key
- Look at server logs in Terminal 1
