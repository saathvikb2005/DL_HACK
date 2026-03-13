/**
 * Avatar Animation System
 * Dynamic expressions, gestures, and procedural animations
 */

export class AvatarAnimator {
  constructor(vrm) {
    this.vrm = vrm;
    this.currentEmotion = "neutral";
    this.emotionIntensity = 0;
    this.targetIntensity = 0;
    
    // Animation state
    this.idleTime = 0;
    this.breathingPhase = 0;
    this.gestureQueue = [];
    this.currentGesture = null;
    this.gestureTime = 0;
    
    // Procedural movement
    this.headSway = { x: 0, y: 0, z: 0 };
    this.bodyLean = 0;
    this.shoulderTilt = 0;
    
    // Expression blending
    this.expressionWeights = {
      happy: 0,
      angry: 0,
      sad: 0,
      relaxed: 0,
      surprised: 0,
      neutral: 1,
    };
    
    this.targetExpressions = { ...this.expressionWeights };
  }

  /**
   * Set the avatar's emotional state
   * @param {string} emotion - happy, concerned, urgent, calm, surprised
   * @param {number} intensity - 0 to 1
   */
  setEmotion(emotion, intensity = 0.7) {
    this.currentEmotion = emotion;
    this.targetIntensity = intensity;
    
    // Map emotion to VRM expressions
    const expressionMap = {
      happy: { happy: 1, relaxed: 0.3 },
      concerned: { sad: 0.6, relaxed: -0.2 },
      urgent: { angry: 0.4, surprised: 0.5 },
      calm: { relaxed: 0.8, happy: 0.2 },
      surprised: { surprised: 1, happy: 0.1 },
      neutral: { neutral: 1 },
      thinking: { neutral: 0.7, relaxed: 0.3 },
    };
    
    // Reset all to 0
    for (const key in this.targetExpressions) {
      this.targetExpressions[key] = 0;
    }
    
    // Apply new expression
    const expr = expressionMap[emotion] || expressionMap.neutral;
    for (const key in expr) {
      if (this.targetExpressions.hasOwnProperty(key)) {
        this.targetExpressions[key] = expr[key] * intensity;
      }
    }
  }

  /**
   * Add a gesture to the animation queue
   */
  addGesture(gestureName) {
    this.gestureQueue.push(gestureName);
  }

  /**
   * Perform a specific gesture animation
   */
  performGesture(gestureName) {
    const gestures = {
      nod: () => this._animateNod(),
      shake: () => this._animateShake(),
      shrug: () => this._animateShrug(),
      wave: () => this._animateWave(),
      pointForward: () => this._animatePointForward(),
      handToChest: () => this._animateHandToChest(),
      openArms: () => this._animateOpenArms(),
      thumbsUp: () => this._animateThumbsUp(),
    };
    
    const gesture = gestures[gestureName];
    if (gesture) {
      this.currentGesture = { name: gestureName, fn: gesture, duration: 2.0 };
      this.gestureTime = 0;
    }
  }

  /**
   * Update animations each frame
   */
  update(deltaTime) {
    if (!this.vrm) return;
    
    this.idleTime += deltaTime;
    this.breathingPhase += deltaTime;
    
    // Blend expressions smoothly
    this._updateExpressions(deltaTime);
    
    // Procedural idle animations
    this._updateIdleMovement(deltaTime);
    
    // Process gesture queue
    this._updateGestures(deltaTime);
    
    // Apply VRM updates
    this.vrm.update(deltaTime);
  }

  /**
   * Smooth expression blending
   */
  _updateExpressions(deltaTime) {
    const blendSpeed = 3.0;
    
    for (const key in this.expressionWeights) {
      const target = this.targetExpressions[key] || 0;
      const current = this.expressionWeights[key];
      const diff = target - current;
      
      this.expressionWeights[key] += diff * blendSpeed * deltaTime;
      
      // Apply to VRM (handle case where expression might not exist)
      try {
        this.vrm.expressionManager?.setValue(key, Math.max(0, this.expressionWeights[key]));
      } catch (e) {
        // Expression not available in this VRM model
      }
    }
    
    // Smooth emotion intensity blending
    const intensityDiff = this.targetIntensity - this.emotionIntensity;
    this.emotionIntensity += intensityDiff * blendSpeed * deltaTime;
  }

  /**
   * Procedural idle movement - breathing, subtle sway
   */
  _updateIdleMovement(deltaTime) {
    // Breathing animation
    const breathCycle = Math.sin(this.breathingPhase * 0.3);
    const chestExpansion = breathCycle * 0.02;
    
    // Natural head sway
    const swaySpeed = 0.4;
    const swayAmount = 0.08;
    this.headSway.y = Math.sin(this.idleTime * swaySpeed) * swayAmount;
    this.headSway.x = Math.sin(this.idleTime * swaySpeed * 0.7) * swayAmount * 0.5;
    this.headSway.z = Math.cos(this.idleTime * swaySpeed * 0.5) * swayAmount * 0.3;
    
    // Apply to VRM scene
    if (this.currentGesture === null) {
      // Only apply idle movement when not gesturing
      this.vrm.scene.rotation.y = this.headSway.y;
      this.vrm.scene.rotation.x = this.headSway.x * 0.5;
    }
    
    // Micro-adjustments for realism
    const microShift = Math.sin(this.idleTime * 1.2) * 0.01;
    this.vrm.scene.position.y = microShift;
  }

  /**
   * Process and execute gestures
   */
  _updateGestures(deltaTime) {
    // Start next gesture if none is playing
    if (!this.currentGesture && this.gestureQueue.length > 0) {
      const nextGesture = this.gestureQueue.shift();
      this.performGesture(nextGesture);
    }
    
    // Execute current gesture
    if (this.currentGesture) {
      this.gestureTime += deltaTime;
      this.currentGesture.fn(this.gestureTime, this.currentGesture.duration);
      
      // Gesture complete
      if (this.gestureTime >= this.currentGesture.duration) {
        this.currentGesture = null;
        this.gestureTime = 0;
        // Reset to idle pose
        this._resetPose();
      }
    }
  }

  /**
   * Gesture: Nod head (affirmative)
   */
  _animateNod() {
    const t = this.gestureTime;
    const nodProgress = Math.min(t / 0.6, 1);
    const nodAngle = Math.sin(nodProgress * Math.PI * 2) * 0.3;
    this.vrm.scene.rotation.x = nodAngle;
  }

  /**
   * Gesture: Shake head (negative)
   */
  _animateShake() {
    const t = this.gestureTime;
    const shakeProgress = Math.min(t / 0.8, 1);
    const shakeAngle = Math.sin(shakeProgress * Math.PI * 3) * 0.25;
    this.vrm.scene.rotation.y = shakeAngle;
  }

  /**
   * Gesture: Shrug shoulders
   */
  _animateShrug() {
    const t = this.gestureTime;
    const progress = Math.min(t / 1.0, 1);
    const shrug = Math.sin(progress * Math.PI) * 0.15;
    
    // Approximate shoulder lift with body tilt
    this.vrm.scene.position.y = shrug * 0.1;
  }

  /**
   * Gesture: Wave hand
   */
  _animateWave() {
    const t = this.gestureTime;
    const waveProgress = Math.min(t / 1.5, 1);
    
    // Create a waving motion with body lean
    const wave = Math.sin(waveProgress * Math.PI * 2.5) * 0.2;
    this.vrm.scene.rotation.z = wave * 0.3;
  }

  /**
   * Gesture: Point forward (emphasis)
   */
  _animatePointForward() {
    const t = this.gestureTime;
    const progress = Math.min(t / 1.0, 1);
    
    // Lean forward slightly
    const lean = Math.sin(progress * Math.PI) * 0.15;
    this.vrm.scene.position.z = -lean * 0.2;
    this.vrm.scene.rotation.x = -lean * 0.3;
  }

  /**
   * Gesture: Hand to chest (sincerity)
   */
  _animateHandToChest() {
    const t = this.gestureTime;
    const progress = Math.min(t / 1.2, 1);
    
    // Slight bow
    const bow = Math.sin(progress * Math.PI) * 0.1;
    this.vrm.scene.rotation.x = bow * 0.5;
  }

  /**
   * Gesture: Open arms (welcoming)
   */
  _animateOpenArms() {
    const t = this.gestureTime;
    const progress = Math.min(t / 1.5, 1);
    
    // Spread pose (simulated with slight back lean)
    const openness = Math.sin(progress * Math.PI) * 0.1;
    this.vrm.scene.rotation.x = -openness * 0.3;
    this.vrm.scene.position.y = openness * 0.05;
  }

  /**
   * Gesture: Thumbs up (approval)
   */
  _animateThumbsUp() {
    const t = this.gestureTime;
    const progress = Math.min(t / 1.0, 1);
    
    // Quick upward motion
    const thumbsUp = Math.sin(progress * Math.PI) * 0.15;
    this.vrm.scene.position.y = thumbsUp * 0.1;
    this.vrm.scene.rotation.z = thumbsUp * 0.2;
  }

  /**
   * Reset to neutral pose
   */
  _resetPose() {
    const resetSpeed = 2.0;
    // Smooth reset is handled in idle movement
    // Just ensure we're not stuck
    this.vrm.scene.rotation.x = 0;
    this.vrm.scene.rotation.z = 0;
    this.vrm.scene.position.z = 0;
    this.vrm.scene.position.y = 0;
  }
  
  /**
   * React to user interaction (click, message sent, etc)
   */
  reactToInteraction(interactionType = "acknowledge") {
    const reactions = {
      acknowledge: () => {
        this.setEmotion("happy", 0.6);
        this.addGesture("nod");
      },
      greeting: () => {
        this.setEmotion("happy", 0.8);
        this.addGesture("wave");
      },
      concern: () => {
        this.setEmotion("concerned", 0.7);
        this.addGesture("handToChest");
      },
      urgent: () => {
        this.setEmotion("urgent", 0.9);
        this.addGesture("pointForward");
      },
      positive: () => {
        this.setEmotion("happy", 0.9);
        this.addGesture("thumbsUp");
      },
      thinking: () => {
        this.setEmotion("thinking", 0.6);
        this.addGesture("shrug");
      },
    };
    
    const reaction = reactions[interactionType];
    if (reaction) reaction();
  }
}
