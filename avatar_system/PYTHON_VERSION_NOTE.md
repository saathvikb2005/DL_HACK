# Python Version Compatibility Note

## Current Python Version
**Python 3.13.4** detected

## TTS Compatibility Issue

Coqui TTS currently requires **Python <3.12**

Your options:

### Option 1: Use Web Speech API (No Installation Required) ✅
The system is **already configured** to work with Web Speech API as a fallback!

**What you get:**
- ✅ Browser-based TTS (works immediately)
- ✅ Emotion-aware voice parameters
- ✅ Basic phoneme-based lip sync
- ✅ All avatar animations and gestures
- ⚠️ Less accurate lip sync (no Rhubarb)

**To use:** Just run the avatar - it's ready!

### Option 2: Install Python 3.11 (For Professional TTS)

If you want the best quality TTS with Rhubarb lip sync:

1. Install Python 3.11 from: https://www.python.org/downloads/
2. Create a virtual environment with Python 3.11
3. Install TTS: `pip install TTS`
4. Download Rhubarb from: https://github.com/DanielSWolf/rhubarb-lip-sync/releases

### Option 3: Use Alternative TTS Services

Replace Coqui TTS with:
- **Google Cloud TTS** (cloud-based, very high quality)
- **Azure Neural TTS** (cloud-based, emotion support)
- **ElevenLabs** (best quality, requires API key)
- **gTTS** (simple, no dependencies)

---

## Current System Status

### ✅ What Works NOW (No Installation)
- Avatar rendering with Three.js
- Web Speech API TTS
- Dynamic facial expressions (7 emotions)
- Gesture animations (8 types)
- Basic lip sync (phoneme-based)
- Chat interaction
- Health event notifications
- Emotion-aware speech

### ⏳ What Needs Python 3.11
- Coqui TTS (professional quality)
- Rhubarb Lip Sync (frame-perfect visemes)
- Audio caching

---

## Quick Start (Works Right Now!)

```bash
# Start the system (Web Speech API mode)
cd avatar_system
python orchestrator.py  # Terminal 1
npm run dev            # Terminal 2
```

Open http://localhost:5173 and click to unlock audio!

The avatar will speak using your browser's built-in TTS voices.

---

## Testing Current System

```javascript
// In browser console:
window.avatarSpeak("Hello! This uses Web Speech API", "happy");
window.avatarSpeak("This is urgent!", "urgent", 2);
```

Both will work perfectly with the current setup!

---

##Future Upgrade Path

When you're ready for professional TTS:

1. Create Python 3.11 environment
2. Install TTS
3. Download Rhubarb
4. System automatically uses better quality

The code is already written and ready - it will automatically switch to professional TTS when available!
