/**
 * Professional Speech System
 * Integrates both server-side TTS (Coqui + Rhubarb) and fallback Web Speech API
 */

import { AdvancedLipSync } from "./advanced_lipsync.js";

export class ProfessionalSpeech {
  constructor() {
    this.isSpeaking = false;
    this.speechQueue = [];
    this.isProcessingQueue = false;
    this.audioUnlocked = false;
    this.useServerTTS = true; // Try server TTS first
    
    // Callbacks
    this.onSpeechStart = null;
    this.onSpeechEnd = null;
    this.onSpeechError = null;
    
    // Emotion-based voice parameters
    this.emotionVoiceParams = {
      happy: { rate: 1.1, pitch: 1.15, volume: 1.0 },
      concerned: { rate: 0.95, pitch: 0.9, volume: 0.95 },
      urgent: { rate: 1.2, pitch: 1.05, volume: 1.0 },
      calm: { rate: 0.9, pitch: 1.0, volume: 0.9 },
      surprised: { rate: 1.15, pitch: 1.2, volume: 1.0 },
      neutral: { rate: 1.0, pitch: 1.0, volume: 1.0 },
      thinking: { rate: 0.85, pitch: 0.95, volume: 0.85 },
    };
    
    // Chrome workaround for Web Speech API
    this._keepAliveInterval = null;
    this._initKeepAlive();
    
    // Voice loading for fallback
    this._loadVoices();
    
    // Current audio playback
    this.currentAudio = null;
  }

  /**
   * Initialize audio unlock mechanism
   */
  setupAudioUnlock(overlayElement) {
    const unlockAudio = () => {
      if (this.audioUnlocked) return;
      this.audioUnlocked = true;

      // Trigger a silent utterance to unlock
      const silence = new SpeechSynthesisUtterance("");
      silence.volume = 0;
      speechSynthesis.speak(silence);

      overlayElement?.classList.add("hidden");
      console.log("🔊 Audio unlocked");

      // Process any queued speech
      this.processQueue();
    };

    overlayElement?.addEventListener("click", unlockAudio);
    document.addEventListener("click", unlockAudio, { once: true });
    document.addEventListener("keydown", unlockAudio, { once: true });
  }

  /**
   * Queue speech with emotion context
   * @param {string} text - Text to speak
   * @param {string} emotion - Emotion type
   * @param {number} priority - Higher priority speaks sooner
   * @param {Object} lipSyncController - Advanced lip sync instance (optional)
   */
  speak(text, emotion = "neutral", priority = 0, lipSyncController = null) {
    this.speechQueue.push({ text, emotion, priority, lipSyncController });
    
    // Sort by priority (higher first)
    this.speechQueue.sort((a, b) => b.priority - a.priority);
    
    this.processQueue();
  }

  /**
   * Process speech queue
   */
  async processQueue() {
    if (this.isProcessingQueue || this.speechQueue.length === 0) return;
    if (!this.audioUnlocked) {
      console.log("⏳ Audio not unlocked yet, speech queued");
      return;
    }

    this.isProcessingQueue = true;
    const { text, emotion, lipSyncController } = this.speechQueue.shift();
    const controllers = this._normalizeControllers(lipSyncController);

    try {
      // Try server-side TTS first (with visemes)
      if (this.useServerTTS && controllers.advanced) {
        const success = await this._speakWithServerTTS(text, emotion, controllers.advanced);
        if (success) {
          this.isProcessingQueue = false;
          this.processQueue();
          return;
        }
        // Fall through to Web Speech API
        console.log("⚠️ Server TTS failed, using Web Speech API");
      }
      
      // Fallback to Web Speech API
      await this._speakWithWebAPI(text, emotion, controllers.fallback || controllers.advanced);
      
    } catch (error) {
      console.error("Speech processing error:", error);
      if (this.onSpeechError) this.onSpeechError(error);
    }
    
    this.isProcessingQueue = false;
    this.processQueue();
  }

  /**
   * Speak using server-side TTS (Coqui + Rhubarb)
   */
  async _speakWithServerTTS(text, emotion, lipSyncController) {
    try {
      console.log(`🎤 Server TTS: "${text.substring(0, 50)}..."`);
      
      // Fetch TTS with visemes
      const result = await AdvancedLipSync.fetchTTS(text, emotion);
      
      if (!result) {
        return false;
      }

      const { audio, visemes, duration } = result;
      
      // Load visemes into lip sync controller
      if (lipSyncController && visemes) {
        lipSyncController.loadVisemes(visemes);
      }

      this.currentAudio = audio;
      this.isSpeaking = true;

      // Callback
      if (this.onSpeechStart) {
        this.onSpeechStart(text, emotion);
      }

      // Play audio and start lip sync
      if (lipSyncController) {
        lipSyncController.startWithAudio(audio);
      } else {
        audio.play();
      }

      // Wait for audio to finish
      await new Promise((resolve, reject) => {
        audio.onended = () => {
          this.isSpeaking = false;
          this.currentAudio = null;
          if (this.onSpeechEnd) this.onSpeechEnd();
          resolve();
        };
        
        audio.onerror = (e) => {
          this.isSpeaking = false;
          this.currentAudio = null;
          reject(e);
        };
      });

      return true;
      
    } catch (error) {
      console.error("Server TTS error:", error);
      return false;
    }
  }

  /**
   * Speak using Web Speech API (fallback)
   */
  async _speakWithWebAPI(text, emotion, lipSyncController) {
    return new Promise((resolve) => {
      speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      
      // Apply emotion-based parameters
      const params = this.emotionVoiceParams[emotion] || this.emotionVoiceParams.neutral;
      utterance.rate = params.rate;
      utterance.pitch = params.pitch;
      utterance.volume = params.volume;

      // Select voice
      const voices = speechSynthesis.getVoices();
      if (voices.length > 0) {
        const preferred =
          voices.find((v) => v.lang.startsWith("en") && v.localService) ||
          voices.find((v) => v.lang.startsWith("en")) ||
          voices[0];
        if (preferred) utterance.voice = preferred;
      }

      utterance.onstart = () => {
        this.isSpeaking = true;
        if (this.onSpeechStart) this.onSpeechStart(text, emotion);
        
        // Start basic lip sync if available
        if (lipSyncController && lipSyncController.startSpeaking) {
          lipSyncController.startSpeaking(text, emotion, utterance.rate);
        }
      };

      // Word/char boundary timing improves fallback mouth sync substantially.
      utterance.onboundary = (event) => {
        if (!lipSyncController || !lipSyncController.handleBoundary) return;
        lipSyncController.handleBoundary(event.charIndex, event.elapsedTime);
      };

      utterance.onend = () => {
        this.isSpeaking = false;
        if (this.onSpeechEnd) this.onSpeechEnd();
        
        // Stop basic lip sync
        if (lipSyncController && lipSyncController.stopSpeaking) {
          lipSyncController.stopSpeaking();
        }
        
        resolve();
      };

      utterance.onerror = (e) => {
        console.warn("Web Speech API error:", e.error);
        this.isSpeaking = false;
        if (this.onSpeechError) this.onSpeechError(e);
        resolve();
      };

      speechSynthesis.speak(utterance);
    });
  }

  _normalizeControllers(lipSyncController) {
    if (!lipSyncController) return { advanced: null, fallback: null };

    // New form: { advanced, fallback }
    if (lipSyncController.advanced || lipSyncController.fallback) {
      return {
        advanced: lipSyncController.advanced || null,
        fallback: lipSyncController.fallback || null,
      };
    }

    // Backward compatibility for legacy single controller usage.
    return {
      advanced: lipSyncController.startWithAudio ? lipSyncController : null,
      fallback: lipSyncController.startSpeaking ? lipSyncController : null,
    };
  }

  /**
   * Stop current speech and clear queue
   */
  stopSpeaking() {
    // Stop server TTS audio
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    
    // Stop Web Speech API
    speechSynthesis.cancel();
    
    this.speechQueue = [];
    this.isSpeaking = false;
    this.isProcessingQueue = false;
  }

  /**
   * Chrome workaround: keep speech synthesis alive
   */
  _initKeepAlive() {
    this._keepAliveInterval = setInterval(() => {
      if (speechSynthesis.speaking && !this.currentAudio) {
        speechSynthesis.pause();
        speechSynthesis.resume();
      }
    }, 10000);
  }

  /**
   * Load voices (async in Chrome)
   */
  _loadVoices() {
    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = () => {
        const voices = speechSynthesis.getVoices();
        console.log(`🎤 Web Speech API voices loaded: ${voices.length}`);
      };
    }
  }

  /**
   * Cleanup
   */
  destroy() {
    if (this._keepAliveInterval) {
      clearInterval(this._keepAliveInterval);
    }
    this.stopSpeaking();
  }
}
