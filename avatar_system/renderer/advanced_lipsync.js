/**
 * Advanced Lip Sync System
 * Uses viseme timeline data from Rhubarb Lip Sync for accurate mouth animation
 * 
 * Rhubarb Visemes:
 * A - Open mouth (like "ah")
 * B - Lips together (p, b, m)
 * C - Rounded mouth (sh, ch)
 * D - Teeth visible (th, dh)
 * E - EE sound
 * F - Teeth on lip (f, v)
 * G - Soft tongue (k, g, ng)
 * H - Tongue up (n, l, d, t, s, z)
 * X - Rest/silence
 */

export class AdvancedLipSync {
  constructor(vrm) {
    this.vrm = vrm;
    this.visemeTimeline = [];
    this.currentViseme = "X";
    this.isPlaying = false;
    this.startTime = 0;
    this.audioElement = null;
    
    // Viseme to VRM blendshape mapping
    this.visemeToBlendshape = {
      A: { aa: 1.0, oh: 0.3 },           // Open wide
      B: { closed: 1.0 },                 // Lips closed
      C: { oh: 0.8, ou: 0.6 },           // Rounded
      D: { ih: 0.7, ee: 0.3 },           // Teeth
      E: { ee: 1.0 },                     // EE sound
      F: { narrow: 1.0 },                 // F/V sound
      G: { aa: 0.5, oh: 0.5 },           // Soft
      H: { ih: 0.8, aa: 0.2 },           // Tongue up
      X: { neutral: 0.2 },                // Rest position
    };
    
    // Available VRM mouth shapes
    this.mouthShapes = ["aa", "ih", "ou", "ee", "oh"];
  }

  /**
   * Load viseme timeline data
   * @param {Array} visemes - Array of {start, end, value} objects from Rhubarb
   */
  loadVisemes(visemes) {
    this.visemeTimeline = visemes || [];
    console.log(`📊 Loaded ${this.visemeTimeline.length} viseme cues`);
  }

  /**
   * Start lip sync playback with audio
   * @param {HTMLAudioElement} audioElement - Audio element to sync with
   */
  startWithAudio(audioElement) {
    this.audioElement = audioElement;
    this.isPlaying = true;
    this.startTime = performance.now();
    
    // Sync with audio time
    if (this.audioElement) {
      this.audioElement.play();
      
      this.audioElement.addEventListener("ended", () => {
        this.stop();
      });
    }
    
    console.log("🎬 Lip sync started");
  }

  /**
   * Stop lip sync
   */
  stop() {
    this.isPlaying = false;
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement.currentTime = 0;
    }
    this._resetMouth();
    console.log("⏹️ Lip sync stopped");
  }

  /**
   * Update lip sync each frame
   * @param {number} deltaTime - Time since last frame
   */
  update(deltaTime) {
    if (!this.vrm || !this.isPlaying) {
      return;
    }

    // Get current playback time from audio
    let currentTime;
    if (this.audioElement) {
      currentTime = this.audioElement.currentTime;
    } else {
      currentTime = (performance.now() - this.startTime) / 1000;
    }

    // Find current viseme
    const currentViseme = this._getVisemeAtTime(currentTime);
    
    if (currentViseme !== this.currentViseme) {
      this.currentViseme = currentViseme;
      this._applyViseme(currentViseme);
    }

    // Check if finished
    if (this.visemeTimeline.length > 0) {
      const lastCue = this.visemeTimeline[this.visemeTimeline.length - 1];
      if (currentTime > lastCue.end) {
        this.stop();
      }
    }
  }

  /**
   * Get the viseme that should be active at given time
   * @param {number} time - Time in seconds
   * @returns {string} Viseme code (A-H, X)
   */
  _getVisemeAtTime(time) {
    for (const cue of this.visemeTimeline) {
      if (time >= cue.start && time < cue.end) {
        return cue.value;
      }
    }
    return "X"; // Default to rest position
  }

  /**
   * Apply a viseme to the VRM avatar
   * @param {string} viseme - Viseme code
   */
  _applyViseme(viseme) {
    if (!this.vrm) return;

    // Reset all mouth shapes
    this._resetMouth();

    // Get blendshape mapping for this viseme
    const blendshapes = this.visemeToBlendshape[viseme] || this.visemeToBlendshape.X;

    // Apply blendshapes
    for (const [shape, weight] of Object.entries(blendshapes)) {
      this._setBlendshape(shape, weight);
    }
  }

  /**
   * Set a specific blendshape weight
   * @param {string} shapeName - Name of the blendshape
   * @param {number} weight - Weight 0-1
   */
  _setBlendshape(shapeName, weight) {
    try {
      // Try VRM expression manager first
      if (this.vrm.expressionManager) {
        this.vrm.expressionManager.setValue(shapeName, weight);
        return;
      }

      // Fallback: try morph targets directly
      this.vrm.scene.traverse((obj) => {
        if (obj.morphTargetInfluences && obj.morphTargetDictionary) {
          const index = obj.morphTargetDictionary[shapeName];
          if (index !== undefined) {
            obj.morphTargetInfluences[index] = weight;
          }
        }
      });
    } catch (e) {
      // Blendshape not available, ignore
    }
  }

  /**
   * Reset all mouth shapes to neutral
   */
  _resetMouth() {
    for (const shape of this.mouthShapes) {
      this._setBlendshape(shape, 0);
    }
    
    // Also reset common blendshapes
    this._setBlendshape("closed", 0);
    this._setBlendshape("narrow", 0);
    this._setBlendshape("neutral", 0);
  }

  /**
   * Create audio element from URL
   * @param {string} audioUrl - URL to audio file
   * @returns {HTMLAudioElement}
   */
  static createAudioElement(audioUrl) {
    const audio = new Audio(audioUrl);
    audio.crossOrigin = "anonymous";
    return audio;
  }

  /**
   * Fetch TTS with visemes from server
   * @param {string} text - Text to synthesize
   * @param {string} emotion - Emotion for TTS
   * @returns {Promise<{audio, visemes, duration}>}
   */
  static async fetchTTS(text, emotion = "neutral") {
    try {
      const response = await fetch("http://localhost:8765/api/tts/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text, emotion }),
      });

      if (!response.ok) {
        throw new Error(`TTS request failed: ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        console.error("TTS error:", data.error);
        return null;
      }

      // Create audio element
      const audioUrl = `http://localhost:8765${data.audio_url}`;
      const audio = AdvancedLipSync.createAudioElement(audioUrl);

      return {
        audio,
        visemes: data.visemes,
        duration: data.duration,
        text: data.text,
      };
    } catch (error) {
      console.error("Failed to fetch TTS:", error);
      return null;
    }
  }
}
