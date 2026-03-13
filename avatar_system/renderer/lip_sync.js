/**
 * Dynamic Lip Sync System
 * Fallback lip-sync for Web Speech API mode.
 * Uses boundary events when available and smooth viseme blending.
 */

export class LipSyncController {
  constructor(vrm) {
    this.vrm = vrm;
    this.isSpeaking = false;
    this.currentTarget = { aa: 0, ih: 0, ou: 0, ee: 0, oh: 0 };
    this.currentWeights = { aa: 0, ih: 0, ou: 0, ee: 0, oh: 0 };
    this.pendingTimeline = [];
    this.timelineIndex = 0;
    this.elapsed = 0;
    this.blendSpeed = 16.0;
    this.currentWord = "";
    
    // VRM mouth shapes
    this.mouthShapes = ["aa", "ih", "ou", "ee", "oh"];
    this.lastText = "";
    this.wordRanges = [];
  }

  /**
   * Start fallback lip sync if boundary events are unavailable.
   * Builds a coarse timeline from text.
   */
  startSpeaking(text, emotion = "neutral", speechRate = 1.0) {
    this.isSpeaking = true;
    this.elapsed = 0;
    this.lastText = text || "";
    this.wordRanges = this._buildWordRanges(this.lastText);
    this.pendingTimeline = this._buildEstimatedTimeline(this.lastText, speechRate);
    this.timelineIndex = 0;
  }

  /**
   * Called by SpeechSynthesis on word/char boundaries.
   * Provides tighter timing than fixed-step phoneme loops.
   */
  handleBoundary(charIndex, elapsedTime = null) {
    if (!this.isSpeaking || !this.lastText) return;

    // If elapsed time is provided, sync internal clock.
    if (typeof elapsedTime === "number" && Number.isFinite(elapsedTime)) {
      this.elapsed = elapsedTime;
      this._consumeTimeline(this.elapsed);
    }

    const word = this._wordAtCharIndex(charIndex);
    if (!word) return;

    this.currentWord = word;
    const target = this._weightsFromWord(word);
    this._setTarget(target);
  }

  /**
   * Stop speaking
   */
  stopSpeaking() {
    this.isSpeaking = false;
    this.pendingTimeline = [];
    this.timelineIndex = 0;
    this.lastText = "";
    this._closeMouth();
  }

  /**
   * Update lip sync each frame
   */
  update(deltaTime, speechRate = 1.0) {
    if (!this.vrm) return;

    if (this.isSpeaking) {
      this.elapsed += deltaTime;
      this._consumeTimeline(this.elapsed);
      this._applySmoothedTarget(deltaTime);
    } else {
      this._setTarget({ aa: 0, ih: 0, ou: 0, ee: 0, oh: 0 });
      this._applySmoothedTarget(deltaTime);
    }
  }

  /**
   * Consume estimated cue timeline according to elapsed audio time.
   */
  _consumeTimeline(elapsed) {
    while (this.timelineIndex < this.pendingTimeline.length) {
      const cue = this.pendingTimeline[this.timelineIndex];
      if (elapsed < cue.start) break;
      if (elapsed >= cue.start && elapsed <= cue.end) {
        this._setTarget(cue.weights);
        break;
      }
      if (elapsed > cue.end) {
        this.timelineIndex += 1;
        continue;
      }
    }
  }

  /**
   * Smoothly move current weights toward target weights.
   */
  _applySmoothedTarget(deltaTime) {
    const k = Math.min(1, this.blendSpeed * deltaTime);
    for (const shape of this.mouthShapes) {
      const target = this.currentTarget[shape] || 0;
      const current = this.currentWeights[shape] || 0;
      const next = current + (target - current) * k;
      this.currentWeights[shape] = next;
      try {
        this.vrm.expressionManager?.setValue(shape, Math.max(0, Math.min(1, next)));
      } catch (_) {
        // Ignore unsupported expressions in specific VRM models.
      }
    }
  }

  /**
   * Set desired mouth-shape target.
   */
  _setTarget(weights) {
    this.currentTarget = {
      aa: weights.aa || 0,
      ih: weights.ih || 0,
      ou: weights.ou || 0,
      ee: weights.ee || 0,
      oh: weights.oh || 0,
    };
  }

  _weightsFromWord(word) {
    const w = (word || "").toLowerCase();
    const has = (chars) => chars.some((c) => w.includes(c));

    // Weighted co-articulation by vowel presence.
    const weights = { aa: 0.15, ih: 0.1, ou: 0.08, ee: 0.1, oh: 0.1 };

    if (has(["a"])) weights.aa += 0.55;
    if (has(["e", "y"])) weights.ee += 0.55;
    if (has(["i"])) weights.ih += 0.55;
    if (has(["o"])) weights.oh += 0.55;
    if (has(["u", "w"])) weights.ou += 0.5;

    // Consonant classes to shape the lips.
    if (has(["m", "p", "b"])) {
      weights.aa *= 0.35;
      weights.oh *= 0.35;
      weights.ou *= 0.4;
    }
    if (has(["f", "v"])) {
      weights.ee += 0.2;
      weights.ih += 0.2;
    }
    if (has(["s", "z", "t", "d", "n", "l"])) {
      weights.ih += 0.12;
    }

    // Normalize to <= 1.0 with slight dynamics.
    const max = Math.max(...Object.values(weights), 1);
    const scale = max > 1 ? 1 / max : 1;
    const pulse = 0.9 + Math.sin(Date.now() * 0.018) * 0.08;
    return {
      aa: Math.min(1, weights.aa * scale * pulse),
      ih: Math.min(1, weights.ih * scale * pulse),
      ou: Math.min(1, weights.ou * scale * pulse),
      ee: Math.min(1, weights.ee * scale * pulse),
      oh: Math.min(1, weights.oh * scale * pulse),
    };
  }

  _buildEstimatedTimeline(text, speechRate) {
    const words = (text || "").trim().split(/\s+/).filter(Boolean);
    const timeline = [];
    let t = 0;

    const baseWord = 0.16 / Math.max(0.7, speechRate);
    const charWeight = 0.018 / Math.max(0.7, speechRate);

    for (const word of words) {
      const dur = Math.min(0.42, Math.max(0.09, baseWord + word.length * charWeight));
      const start = t;
      const end = t + dur;
      timeline.push({ start, end, weights: this._weightsFromWord(word) });
      t = end;

      // Short closure cue between words.
      const gap = 0.04;
      timeline.push({ start: t, end: t + gap, weights: { aa: 0.06, ih: 0.05, ou: 0.04, ee: 0.05, oh: 0.05 } });
      t += gap;
    }

    return timeline;
  }

  _buildWordRanges(text) {
    const ranges = [];
    const re = /[A-Za-z']+/g;
    let m;
    while ((m = re.exec(text || "")) !== null) {
      ranges.push({ start: m.index, end: m.index + m[0].length, word: m[0] });
    }
    return ranges;
  }

  _wordAtCharIndex(charIndex) {
    if (!Number.isFinite(charIndex)) return "";
    for (const r of this.wordRanges) {
      if (charIndex >= r.start && charIndex < r.end) {
        return r.word;
      }
    }
    return "";
  }

  /**
   * Close mouth (neutral position)
   */
  _closeMouth() {
    this.currentTarget = { aa: 0, ih: 0, ou: 0, ee: 0, oh: 0 };
  }
}
