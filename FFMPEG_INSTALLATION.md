# FFmpeg Installation Guide

FFmpeg is required to convert audio to the format Deepgram expects.

## Quick Install (Windows)

### Option 1: Download Pre-built Binaries (Easiest)

1. **Download FFmpeg:**
   - Visit: https://www.gyan.dev/ffmpeg/builds/
   - Download: **ffmpeg-release-essentials.zip** (smallest, recommended)
   - Or download: **ffmpeg-release-full.zip** (includes extra features)

2. **Extract:**
   ```
   Extract the ZIP to: C:\ffmpeg
   ```

3. **Verify structure:**
   ```
   C:\ffmpeg\
     └── bin\
         ├── ffmpeg.exe   ← This is what we need
         ├── ffplay.exe
         └── ffprobe.exe
   ```

4. **Test it:**
   ```bash
   C:\ffmpeg\bin\ffmpeg.exe -version
   ```

   Should output FFmpeg version info.

5. **Update the script:**
   The script is already configured to use `C:\ffmpeg\bin\ffmpeg.exe`

   If you extracted to a different location, edit `test_audio_client.py` line 16:
   ```python
   FFMPEG_PATH = r"C:\your\path\to\ffmpeg.exe"
   ```

### Option 2: Install with Chocolatey

If you have Chocolatey installed:

```bash
choco install ffmpeg
```

Then update `test_audio_client.py`:
```python
FFMPEG_PATH = "ffmpeg"  # Will use system PATH
```

### Option 3: Add to System PATH (Optional)

After downloading, you can add FFmpeg to your system PATH:

1. Press `Win + X` → System
2. Advanced system settings → Environment Variables
3. Under System Variables, find `Path`
4. Click Edit → New
5. Add: `C:\ffmpeg\bin`
6. Click OK on all dialogs
7. Restart terminal

Then update `test_audio_client.py`:
```python
FFMPEG_PATH = "ffmpeg"  # Will use system PATH
```

## Verification

Run this to verify FFmpeg is working:

```bash
# If installed to C:\ffmpeg
C:\ffmpeg\bin\ffmpeg.exe -version

# If added to PATH
ffmpeg -version
```

Expected output:
```
ffmpeg version N-xxxxx-xxx
built with gcc x.x.x
configuration: ...
```

## What the Script Does with FFmpeg

The script uses FFmpeg to convert your audio files to the format Deepgram requires:

```
Input: Your podcast.mp3 (or .wav, .m4a, etc.)
   ↓
FFmpeg: Converts to linear16 PCM, 16kHz, mono
   ↓
Output: Raw audio bytes
   ↓
Server: Sends to Deepgram for transcription
```

**Command used internally:**
```bash
ffmpeg -i input.mp3 \
  -f s16le \        # 16-bit little-endian PCM
  -ar 16000 \       # 16kHz sample rate
  -ac 1 \           # Mono (1 channel)
  -                 # Output to stdout
```

## Troubleshooting

### "ffmpeg is not recognized as an internal or external command"

**Cause:** FFmpeg not in PATH and FFMPEG_PATH is set to just `"ffmpeg"`

**Fix:**
- Option A: Use full path in `test_audio_client.py`
- Option B: Add FFmpeg to system PATH (see Option 3 above)

### "Permission denied" or "Access denied"

**Cause:** Windows security blocking execution

**Fix:**
1. Right-click ffmpeg.exe → Properties
2. Check "Unblock" if present → Apply
3. Or run terminal as Administrator

### FFmpeg downloaded but script still can't find it

**Check:**
1. Verify file is at: `C:\ffmpeg\bin\ffmpeg.exe`
2. Check `test_audio_client.py` line 16 matches your path
3. Use absolute path (not relative)

### FFmpeg works but audio conversion fails

**Cause:** Corrupted audio file or unsupported format

**Fix:**
1. Try a different audio file
2. Ensure file isn't empty
3. Check FFmpeg supports the format:
   ```bash
   ffmpeg -formats
   ```

## Alternative Download Sources

If the above link doesn't work:

- **Official FFmpeg builds**: https://ffmpeg.org/download.html#build-windows
- **GitHub releases**: https://github.com/BtbN/FFmpeg-Builds/releases
- **Chocolatey package**: https://community.chocolatey.org/packages/ffmpeg

## After Installation

Once FFmpeg is installed, you can run:

```bash
python test_audio_client.py
```

You should see:
```
✓ FFmpeg found
```

Instead of the error message.
