"""
Advanced TTS Service with Coqui TTS
====================================
Generates speech audio from text with professional quality.

Installation:
    pip install TTS
    
For Rhubarb Lip Sync:
    Download from: https://github.com/DanielSWolf/rhubarb-lip-sync/releases
    Place rhubarb.exe in avatar_system/tools/
"""

import os
import json
import subprocess
import hashlib
import shutil
import sys
from pathlib import Path
from typing import Optional, Tuple, List

COQUI_MODEL_NAME = "tts_models/en/ljspeech/tacotron2-DDC"


def _detect_tts_executable() -> Optional[str]:
    """Resolve Coqui CLI executable path from env or PATH."""
    env_exe = os.getenv("COQUI_TTS_EXE")
    if env_exe and os.path.exists(env_exe):
        return env_exe

    # Check near current Python executable (venv Scripts dir on Windows).
    py_dir = Path(sys.executable).resolve().parent
    for candidate in (py_dir / "tts.exe", py_dir / "tts"):
        if candidate.exists():
            return str(candidate)

    return shutil.which("tts")


COQUI_AVAILABLE = _detect_tts_executable() is not None
if not COQUI_AVAILABLE:
    print("⚠️  Coqui CLI not found. Install coqui-tts and ensure 'tts' is on PATH.")


class AdvancedTTSService:
    """
    Professional TTS service with lip-sync data generation.
    """
    
    def __init__(self, cache_dir: str = "avatar_system/audio_cache"):
        self.base_dir = Path(__file__).resolve().parent
        self.cache_dir = Path(cache_dir)
        if not self.cache_dir.is_absolute():
            # Resolve relative to avatar_system directory so launcher cwd does not matter.
            self.cache_dir = (self.base_dir / self.cache_dir.name)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Rhubarb executable path
        self.rhubarb_path = self.base_dir / "tools" / "rhubarb.exe"
        self.tts_exe = _detect_tts_executable()
    
    def _get_cache_path(self, text: str, emotion: str = "neutral") -> Tuple[Path, Path]:
        """
        Generate cache file paths for audio and viseme data.
        Returns: (audio_path, viseme_path)
        """
        # Create hash of text + emotion
        content = f"{text}_{emotion}"
        text_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        
        audio_path = self.cache_dir / f"{text_hash}.wav"
        viseme_path = self.cache_dir / f"{text_hash}_visemes.json"
        
        return audio_path, viseme_path
    
    def generate_speech(self, text: str, emotion: str = "neutral") -> Optional[Path]:
        """
        Generate speech from text.
        Returns: Path to wav file or None
        """
        audio_path, _ = self._get_cache_path(text, emotion)
        
        # Check cache
        if audio_path.exists():
            print(f"📦 Using cached audio: {audio_path.name}")
            return audio_path
        
        if not self.tts_exe:
            print("❌ Coqui CLI not available")
            return None
        
        try:
            print(f"🎤 Generating speech: '{text[:50]}...'")
            result = subprocess.run(
                [
                    self.tts_exe,
                    "--text",
                    text,
                    "--model_name",
                    COQUI_MODEL_NAME,
                    "--out_path",
                    str(audio_path),
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode != 0:
                err = (result.stderr or result.stdout or "Unknown Coqui CLI error").strip()
                print(f"❌ Coqui generation failed: {err}")
                return None
            print(f"✅ Audio generated: {audio_path.name}")
            return audio_path
            
        except Exception as e:
            print(f"❌ TTS generation failed: {e}")
            return None
    
    def generate_visemes(self, audio_path: Path) -> Optional[List[dict]]:
        """
        Generate viseme data from audio using Rhubarb Lip Sync.
        Returns: List of viseme cues or None
        """
        if not audio_path.exists():
            print(f"❌ Audio file not found: {audio_path}")
            return None
        
        _, viseme_path = self._get_cache_path("", "")
        viseme_path = audio_path.with_suffix(".json").with_name(f"{audio_path.stem}_visemes.json")
        
        # Check cache
        if viseme_path.exists():
            print(f"📦 Using cached visemes: {viseme_path.name}")
            with open(viseme_path, 'r') as f:
                data = json.load(f)
                return data.get('mouthCues', [])
        
        # Check if Rhubarb is available
        if not self.rhubarb_path.exists():
            print(f"⚠️  Rhubarb not found at {self.rhubarb_path}")
            print("📥 Download from: https://github.com/DanielSWolf/rhubarb-lip-sync/releases")
            return self._generate_fallback_visemes(audio_path)
        
        # Generate visemes
        try:
            print(f"👄 Generating visemes with Rhubarb...")
            result = subprocess.run(
                [str(self.rhubarb_path), str(audio_path), "-f", "json", "-o", str(viseme_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"✅ Visemes generated: {viseme_path.name}")
                with open(viseme_path, 'r') as f:
                    data = json.load(f)
                    return data.get('mouthCues', [])
            else:
                print(f"❌ Rhubarb failed: {result.stderr}")
                return self._generate_fallback_visemes(audio_path)
                
        except Exception as e:
            print(f"❌ Viseme generation failed: {e}")
            return self._generate_fallback_visemes(audio_path)
    
    def _generate_fallback_visemes(self, audio_path: Path) -> List[dict]:
        """
        Generate simple viseme timeline when Rhubarb is not available.
        Uses basic phoneme estimation from text.
        """
        print("⚠️  Using fallback viseme generation (less accurate)")
        
        # Estimate duration from file size (very rough)
        import wave
        try:
            with wave.open(str(audio_path), 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
        except:
            duration = 2.0  # default
        
        # Create simple viseme timeline
        viseme_sequence = ["X", "A", "B", "C", "D", "E", "F", "X"]
        cues = []
        
        segment_duration = duration / len(viseme_sequence)
        
        for i, viseme in enumerate(viseme_sequence):
            cues.append({
                "start": i * segment_duration,
                "end": (i + 1) * segment_duration,
                "value": viseme
            })
        
        return cues
    
    def generate_speech_with_visemes(self, text: str, emotion: str = "neutral") -> Optional[dict]:
        """
        Complete pipeline: Text → Speech → Visemes
        Returns: {audio_url, visemes, duration} or None
        """
        # Generate speech
        audio_path = self.generate_speech(text, emotion)
        if not audio_path:
            return None
        
        # Generate visemes
        visemes = self.generate_visemes(audio_path)
        if not visemes:
            return None
        
        # Calculate duration
        duration = visemes[-1]['end'] if visemes else 0
        
        # Return relative URL for frontend
        audio_url = f"/audio_cache/{audio_path.name}"
        
        return {
            "audio_url": audio_url,
            "visemes": visemes,
            "duration": duration,
            "text": text,
            "emotion": emotion
        }


# Singleton instance
_tts_service: Optional[AdvancedTTSService] = None


def get_tts_service() -> AdvancedTTSService:
    """Get or create TTS service singleton."""
    global _tts_service
    if _tts_service is None:
        _tts_service = AdvancedTTSService()
    return _tts_service
