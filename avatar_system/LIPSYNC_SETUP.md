# Professional Avatar Lip Sync Setup

## Installation Guide

### Step 1: Install Coqui TTS

```bash
pip install TTS
```

This installs the professional Text-to-Speech engine that generates high-quality audio.

#### Verify Installation
```python
python -c "from TTS.api import TTS; print('✅ Coqui TTS installed')"
```

### Step 2: Download Rhubarb Lip Sync

1. **Download** from: https://github.com/DanielSWolf/rhubarb-lip-sync/releases
2. **Extract** the executable
3. **Place** `rhubarb.exe` in: `avatar_system/tools/rhubarb.exe`

#### For Windows:
```powershell
# Create tools directory
New-Item -ItemType Directory -Force -Path "avatar_system\tools"

# Download and extract manually from GitHub releases
# Then move rhubarb.exe to avatar_system/tools/
```

#### Verify Installation
```bash
avatar_system\tools\rhubarb.exe --version
```

Expected output: `Rhubarb Lip Sync version X.X.X`

---

## System Architecture

```
User Input
    ↓
Text Generation
    ↓
Coqui TTS (Server)
    ↓
speech.wav
    ↓
Rhubarb Lip Sync
    ↓
visemes.json
    ↓
Three.js Avatar (Client)
    ↓
Professional Talking Avatar
```

---

## Features

### ✅ What's Implemented

1. **Coqui TTS Integration**
   - High-quality speech synthesis
   - Emotion-aware voice parameters
   - Audio caching (no re-generation)

2. **Rhubarb Lip Sync**
   - Phoneme-to-viseme conversion
   - Precise mouth shape timeline
   - Frame-accurate synchronization

3. **Professional Speech System**
   - Server-side TTS (best quality)
   - Web Speech API fallback
   - Priority queue management
   - Emotion integration

4. **Advanced Lip Sync**
   - 9 viseme types (A-H, X)
   - VRM blendshape mapping
   - Audio-synchronized playback
   - Fallback phoneme system

---

## API Endpoints

### Generate TTS with Visemes

**POST** `/api/tts/generate`

**Request:**
```json
{
  "text": "Hello, how are you?",
  "emotion": "happy"
}
```

**Response:**
```json
{
  "audio_url": "/audio_cache/abc123.wav",
  "visemes": [
    {"start": 0.0, "end": 0.12, "value": "X"},
    {"start": 0.12, "end": 0.25, "value": "A"},
    {"start": 0.25, "end": 0.40, "value": "B"}
  ],
  "duration": 2.5,
  "text": "Hello, how are you?",
  "emotion": "happy"
}
```

---

## Frontend Usage

### Basic Usage

```javascript
// Speak with professional TTS
window.avatarSpeak("Hello there!", "happy", 1);
```

### Advanced Usage

```javascript
// Direct TTS + viseme fetch
const result = await AdvancedLipSync.fetchTTS(
  "Your wellness is important",
  "calm"
);

if (result) {
  advancedLipSync.loadVisemes(result.visemes);
  advancedLipSync.startWithAudio(result.audio);
}
```

---

## Viseme Reference

| Viseme | Mouth Shape | Example Sounds |
|--------|-------------|----------------|
| A | Wide open | ah, bat |
| B | Lips together | p, b, m |
| C | Rounded | sh, ch |
| D | Teeth visible | th, dh |
| E | EE sound | see, beat |
| F | Teeth on lip | f, v |
| G | Soft tongue | k, g, ng |
| H | Tongue up | n, l, d, t, s, z |
| X | Rest/silence | (silence) |

---

## Fallback Behavior

The system automatically falls back to simpler methods if components are missing:

1. **Server TTS available + Rhubarb available** → Best quality
2. **Server TTS available + No Rhubarb** → Good quality (estimated visemes)
3. **No Server TTS** → Web Speech API (basic phoneme sync)

---

## Troubleshooting

### TTS Not Working

```bash
# Check if TTS is installed
pip list | grep TTS

# Reinstall if needed
pip install --upgrade TTS
```

### Rhubarb Not Found

```
⚠️ Rhubarb not found at avatar_system/tools/rhubarb.exe
📥 Download from: https://github.com/DanielSWolf/rhubarb-lip-sync/releases
```

**Solution:** Download and place in correct directory

### Audio Not Playing

1. **Click anywhere** on the page to unlock audio
2. Check browser console for errors
3. Verify `audio_cache` directory is served correctly

### Lip Sync Out of Sync

- This usually means Rhubarb isn't installed
- System falls back to estimated visemes (less accurate)
- Install Rhubarb for frame-perfect sync

---

## Performance

### Audio Cache

- Generated audio files are cached in `avatar_system/audio_cache/`
- Same text + emotion = instant playback (no regeneration)
- Clear cache periodically if disk space is limited

### Model Loading

- First TTS generation loads the model (5-10 seconds)
- Subsequent generations are fast (~1-2 seconds)
- Model stays in memory during session

---

## Development Tips

### Test the TTS Service Directly

```python
from avatar_system.tts_service import get_tts_service

tts = get_tts_service()
result = tts.generate_speech_with_visemes(
    "This is a test",
    emotion="neutral"
)

print(f"Audio: {result['audio_url']}")
print(f"Visemes: {len(result['visemes'])} cues")
print(f"Duration: {result['duration']:.2f}s")
```

### Monitor Viseme Timeline

Open browser console and check logs:
```
📊 Loaded 45 viseme cues
🎬 Lip sync started
⏹️ Lip sync stopped
```

### Debug Viseme Data

```javascript
// In browser console
console.log(advancedLipSync.visemeTimeline);
```

---

## Production Deployment

For production, consider:

1. **Faster TTS Models**
   - Use `tts_models/en/ljspeech/speedy-speech` for lower latency
   - Or use cloud TTS (Google, Azure, AWS)

2. **Pre-generate Common Phrases**
   - Cache frequent messages
   - Reduce server load

3. **Audio Compression**
   - Convert to MP3 for smaller file sizes
   - Trade quality for bandwidth

4. **CDN Distribution**
   - Serve audio files from CDN
   - Reduce server bandwidth

---

## Next Steps

- ✅ Basic TTS + Lip Sync working
- ⬜ Add emotion-specific TTS models
- ⬜ Implement streaming TTS (real-time)
- ⬜ Add voice cloning
- ⬜ Integrate with LLM for AI conversations

---

## Credits

- **Coqui TTS**: https://github.com/coqui-ai/TTS
- **Rhubarb Lip Sync**: https://github.com/DanielSWolf/rhubarb-lip-sync
- **Three.js**: https://threejs.org/
- **VRM**: https://github.com/pixiv/three-vrm
