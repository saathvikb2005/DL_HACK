/**
 * Enhanced Speech System
 * Dynamic TTS with emotion-aware voice parameters
 */

export class EnhancedSpeech {
  constructor() {
    this.isSpeaking = false;
    this.speechQueue = [];
    this.isProcessingQueue = false;
    this.audioUnlocked = false;
    
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
    
    // Chrome workaround for pausing
    this._keepAliveInterval = null;
    this._initKeepAlive();
    
    // Voice loading
    this._loadVoices();
  }

  /**
   * Initialize audio unlock mechanism
   */
  setupAudioUnlock(overlayElement) {
    const unlockAudio = () => {
      if (this.audioUnlocked) return;
      this.audioUnlocked = true;

      // Trigger a silent utterance to unlock speech engine
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
   * @param {string} emotion - Emotion type (happy, urgent, calm, etc.)
   * @param {number} priority - Higher priority speaks sooner (default: 0)
   */
  speak(text, emotion = "neutral", priority = 0) {
    this.speechQueue.push({ text, emotion, priority });
    
    // Sort by priority (higher first)
    this.speechQueue.sort((a, b) => b.priority - a.priority);
    
    this.processQueue();
  }

  /**
   * Process speech queue
   */
  processQueue() {
    if (this.isProcessingQueue || this.speechQueue.length === 0) return;
    if (!this.audioUnlocked) {
      console.log("⏳ Audio not unlocked yet, speech queued");
      return;
    }

    this.isProcessingQueue = true;
    const { text, emotion } = this.speechQueue.shift();

    // Cancel any stuck utterances
    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Apply emotion-based voice parameters
    const params = this.emotionVoiceParams[emotion] || this.emotionVoiceParams.neutral;
    utterance.rate = params.rate;
    utterance.pitch = params.pitch;
    utterance.volume = params.volume;

    // Select best voice
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
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      if (this.onSpeechEnd) this.onSpeechEnd();
      this.isProcessingQueue = false;
      this.processQueue(); // Process next in queue
    };

    utterance.onerror = (e) => {
      console.warn("Speech error:", e.error);
      this.isSpeaking = false;
      if (this.onSpeechError) this.onSpeechError(e);
      this.isProcessingQueue = false;
      this.processQueue();
    };

    speechSynthesis.speak(utterance);
  }

  /**
   * Stop current speech and clear queue
   */
  stopSpeaking() {
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
      if (speechSynthesis.speaking) {
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
        console.log(`🎤 Voices loaded: ${voices.length}`);
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
