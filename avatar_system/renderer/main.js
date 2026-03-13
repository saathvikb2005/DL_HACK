import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRM } from "@pixiv/three-vrm";

// ── State ───────────────────────────────────────────────────────────────────

let currentVrm;
let blinkTimer = 0;
let idleTime = 0;
let isSpeaking = false;
let speechQueue = [];
let isProcessingQueue = false;

// ── DOM Elements ────────────────────────────────────────────────────────────

const speechBubble = document.getElementById("speechBubble");
const eventLog = document.getElementById("eventLog");
const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const chatSend = document.getElementById("chatSend");
const indOrch = document.getElementById("indOrch");
// Validate critical DOM elements
if (!speechBubble || !eventLog || !chatMessages || !chatInput || !chatSend || !indOrch) {
  console.error("Critical DOM elements missing. Cannot initialize avatar.");
  throw new Error("Required DOM elements not found");
}
// ── Three.js Scene ──────────────────────────────────────────────────────────

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a2e);

const camera = new THREE.PerspectiveCamera(
  35,
  window.innerWidth / window.innerHeight,
  0.1,
  1000
);
camera.position.set(0, 1.4, 3);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);

const mainLight = new THREE.DirectionalLight(0xffffff, 0.8);
mainLight.position.set(1, 2, 3);
scene.add(mainLight);

const fillLight = new THREE.DirectionalLight(0x8888ff, 0.3);
fillLight.position.set(-2, 1, -1);
scene.add(fillLight);

// ── VRM Loader ──────────────────────────────────────────────────────────────

const loader = new GLTFLoader();
loader.register((parser) => new VRMLoaderPlugin(parser));

loader.load(
  "/avatar_models/saathvik.vrm",
  (gltf) => {
    currentVrm = gltf.userData.vrm;
    scene.add(currentVrm.scene);
    currentVrm.scene.rotation.y = 0;
    console.log("Avatar loaded");
    addChatMessage("system", "Avatar loaded. Connecting to orchestrator...");
    connectWebSocket();
  },
  (progress) => {
    // Guard against division by zero
    const total = progress.total || 1;
    const pct = (100 * progress.loaded / total).toFixed(0);
    console.log(`Loading: ${pct}%`);
  },
  (error) => {
    console.error("Avatar load error:", error);
    addChatMessage("system", "Failed to load avatar model.");
  }
);

// ── Lip Sync ────────────────────────────────────────────────────────────────

const mouthShapes = ["aa", "ih", "ou", "ee", "oh"];
let mouthIndex = 0;
let mouthCycleTimer = 0;

function updateLipSync(deltaTime) {
  if (!currentVrm) return;

  if (isSpeaking) {
    mouthCycleTimer += deltaTime;
    if (mouthCycleTimer > 0.1) {
      mouthCycleTimer = 0;
      mouthIndex = (mouthIndex + 1) % mouthShapes.length;
    }
    const value = Math.abs(Math.sin(Date.now() * 0.015));
    for (const s of mouthShapes) currentVrm.expressionManager.setValue(s, 0);
    currentVrm.expressionManager.setValue(mouthShapes[mouthIndex], value);
  } else {
    for (const s of mouthShapes) currentVrm.expressionManager.setValue(s, 0);
  }
}

// ── Animation Loop ──────────────────────────────────────────────────────────

const clock = new THREE.Clock();

function animate() {
  requestAnimationFrame(animate);
  const dt = clock.getDelta();

  if (currentVrm) {
    currentVrm.update(dt);
    currentVrm.lookAt.target = camera;

    // Lip sync
    updateLipSync(dt);

    // Idle head movement
    idleTime += dt;
    currentVrm.scene.rotation.y = Math.sin(idleTime * 0.5) * 0.15;

    // Blink
    blinkTimer += dt;
    const blinkCycle = blinkTimer % 4;
    currentVrm.expressionManager.setValue("blink", blinkCycle < 0.15 ? 1 : 0);
  }

  renderer.render(scene, camera);
}
animate();

// ── Audio Activation ────────────────────────────────────────────────────────

let audioUnlocked = false;
const audioOverlay = document.getElementById("audioOverlay");

function unlockAudio() {
  if (audioUnlocked) return;
  audioUnlocked = true;

  // Trigger a silent utterance to unlock the speech engine
  const silence = new SpeechSynthesisUtterance("");
  silence.volume = 0;
  speechSynthesis.speak(silence);

  audioOverlay.classList.add("hidden");
  console.log("Audio unlocked");

  // If anything was queued before unlock, start processing
  processQueue();
}

audioOverlay.addEventListener("click", unlockAudio);
// Also unlock on any click/keydown anywhere on the page
document.addEventListener("click", unlockAudio, { once: true });
document.addEventListener("keydown", unlockAudio, { once: true });

// ── Speech Engine ───────────────────────────────────────────────────────────

function avatarSpeak(text) {
  speechQueue.push(text);
  processQueue();
}

function processQueue() {
  if (isProcessingQueue || speechQueue.length === 0) return;
  if (!audioUnlocked) return; // Wait until user has clicked
  isProcessingQueue = true;

  const text = speechQueue.shift();

  // Chrome fix: cancel any stuck pending utterances
  speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1;
  utterance.pitch = 1;

  // Pick a voice (prefer English), handle empty voices array
  const voices = speechSynthesis.getVoices();
  if (voices.length > 0) {
    const preferred = voices.find(v => v.lang.startsWith("en") && v.localService)
      || voices.find(v => v.lang.startsWith("en"))
      || voices[0];
    if (preferred) utterance.voice = preferred;
  } else {
    // Voices not loaded yet - register listener for retry
    console.warn("No voices available, speech may use default");
  }

  utterance.onstart = () => {
    isSpeaking = true;
    speechBubble.innerText = text;
    speechBubble.style.display = "block";
  };

  utterance.onend = () => {
    isSpeaking = false;
    speechBubble.style.display = "none";
    isProcessingQueue = false;
    processQueue(); // Next in queue
  };

  utterance.onerror = (e) => {
    console.warn("Speech error:", e.error);
    isSpeaking = false;
    speechBubble.style.display = "none";
    isProcessingQueue = false;
    processQueue();
  };

  speechSynthesis.speak(utterance);
}

// Ensure voices are loaded (Chrome loads them async)
if (speechSynthesis.onvoiceschanged !== undefined) {
  speechSynthesis.onvoiceschanged = () => {
    console.log("Voices loaded:", speechSynthesis.getVoices().length);
  };
}

// Chrome workaround: speech synthesis pauses after ~15s of continuous speech.
// Periodically resume it to keep it alive.
setInterval(() => {
  if (speechSynthesis.speaking) {
    speechSynthesis.pause();
    speechSynthesis.resume();
  }
}, 10000);

// ── WebSocket Connection to Orchestrator ────────────────────────────────────

let ws = null;
let reconnectTimer = null;

function connectWebSocket() {
  // Prevent overlapping connections (check both OPEN and CONNECTING)
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

  ws = new WebSocket("ws://localhost:8765/ws");

  ws.onopen = () => {
    console.log("Connected to orchestrator");
    indOrch.className = "indicator green";
    addChatMessage("system", "Connected to Wellness Hub");
    if (reconnectTimer) {
      clearInterval(reconnectTimer);
      reconnectTimer = null;
    }
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    } catch (e) {
      console.error("Bad message from server:", e);
    }
  };

  ws.onclose = () => {
    console.log("Disconnected from orchestrator");
    indOrch.className = "indicator red";
    // Auto-reconnect every 5 seconds
    if (!reconnectTimer) {
      reconnectTimer = setInterval(connectWebSocket, 5000);
    }
  };

  ws.onerror = () => {
    indOrch.className = "indicator red";
  };
}

function handleServerMessage(data) {
  switch (data.type) {
    case "speak":
      avatarSpeak(data.message);
      addChatMessage("assistant", data.message);
      logEvent(data.event, data.source);
      updateModuleIndicator(data.source);
      break;

    case "welcome":
      addChatMessage("system", data.message);
      break;

    case "status":
      // Future: update status pills
      break;
  }
}

function sendChatToServer(message) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "chat", message }));
  } else {
    // Fallback: direct HTTP
    fetch("http://localhost:8765/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.response) {
          avatarSpeak(data.response);
          addChatMessage("assistant", data.response);
        }
      })
      .catch(() => {
        addChatMessage("system", "Cannot reach the orchestrator. Is it running?");
      });
  }
}

// ── Chat UI ─────────────────────────────────────────────────────────────────

function addChatMessage(role, text) {
  const el = document.createElement("div");
  el.className = `chat-msg ${role}`;
  el.textContent = text;
  chatMessages.appendChild(el);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatSend.addEventListener("click", sendChat);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendChat();
});

function sendChat() {
  const text = chatInput.value.trim();
  if (!text) return;

  addChatMessage("user", text);
  chatInput.value = "";
  sendChatToServer(text);
}

// ── Event Log ───────────────────────────────────────────────────────────────

function logEvent(eventType, source) {
  eventLog.style.display = "block";
  const entry = document.createElement("div");
  const time = new Date().toLocaleTimeString();
  entry.textContent = `[${time}] ${source || "?"} → ${eventType}`;
  eventLog.appendChild(entry);
  eventLog.scrollTop = eventLog.scrollHeight;

  // Auto-hide after 30 seconds of no events
  clearTimeout(logEvent._hideTimer);
  logEvent._hideTimer = setTimeout(() => {
    eventLog.style.display = "none";
  }, 30000);
}

// ── Module Status Indicators ────────────────────────────────────────────────

const indicatorTimeouts = {};  // Track timeouts by element ID to prevent stacking

function updateModuleIndicator(source) {
  const map = {
    eye_care: "indEye",
    posture: "indPosture",
    workpattern: "indWork",
    air_quality: "indAir",
    vijitha: "indVijitha",
  };
  const elId = map[source];
  if (elId) {
    const el = document.getElementById(elId);
    if (!el) return;
    
    el.className = "indicator green";
    
    // Clear any existing timeout for this indicator
    if (indicatorTimeouts[elId]) {
      clearTimeout(indicatorTimeouts[elId]);
    }
    
    // Set new timeout and store it
    indicatorTimeouts[elId] = setTimeout(() => {
      el.className = "indicator gray";
      delete indicatorTimeouts[elId];  // Clean up
    }, 120000);
  }
}

// ── Resize Handler ──────────────────────────────────────────────────────────

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ── Expose Globally (for console testing) ───────────────────────────────────

window.avatarSpeak = avatarSpeak;

// ── Debug Panel ─────────────────────────────────────────────────────────────

const debugToggle = document.getElementById("debugToggle");
const debugPanel = document.getElementById("debugPanel");
const debugVideo = document.getElementById("debugVideo");
const debugEventLog = document.getElementById("debugEventLog");
const audioCanvas = document.getElementById("audioCanvas");

let debugActive = false;
let videoRefreshInterval = null;
let debugSSE = null;
let audioCtx = null;
let analyser = null;
let audioAnimFrame = null;

debugToggle.addEventListener("click", () => {
  debugActive = !debugActive;
  debugToggle.classList.toggle("active", debugActive);
  debugPanel.classList.toggle("hidden", !debugActive);
  debugPanel.classList.toggle("visible", debugActive);

  if (debugActive) {
    startDebugVideo();
    startDebugSSE();
    startAudioVis();
  } else {
    stopDebugVideo();
    stopDebugSSE();
    stopAudioVis();
  }
});

function startDebugVideo() {
  // Refresh the <img> every 200ms with the latest frame
  const refresh = () => {
    debugVideo.src = "http://localhost:8765/api/debug/frame?" + Date.now();
  };
  refresh();
  videoRefreshInterval = setInterval(refresh, 200);
}

function stopDebugVideo() {
  if (videoRefreshInterval) {
    clearInterval(videoRefreshInterval);
    videoRefreshInterval = null;
  }
  debugVideo.src = "";
}

function startDebugSSE() {
  debugSSE = new EventSource("http://localhost:8765/api/debug/events");
  debugSSE.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      const entry = document.createElement("div");
      entry.className = "debug-event-entry";
      
      // Safely create elements with textContent to prevent XSS
      const timeSpan = document.createElement("span");
      timeSpan.className = "ev-time";
      timeSpan.textContent = data.time ? new Date(data.time).toLocaleTimeString() : "";
      
      const sourceSpan = document.createElement("span");
      sourceSpan.className = "ev-source";
      sourceSpan.textContent = `[${data.source || "?"}]`;
      
      const typeSpan = document.createElement("span");
      typeSpan.className = "ev-type";
      typeSpan.textContent = data.event || "";
      
      const msgSpan = document.createElement("span");
      msgSpan.className = "ev-msg";
      msgSpan.textContent = (data.message || "").substring(0, 80);
      
      entry.appendChild(timeSpan);
      entry.appendChild(document.createTextNode(" "));
      entry.appendChild(sourceSpan);
      entry.appendChild(document.createTextNode(" "));
      entry.appendChild(typeSpan);
      entry.appendChild(document.createTextNode(" "));
      entry.appendChild(msgSpan);
      
      debugEventLog.appendChild(entry);
      debugEventLog.scrollTop = debugEventLog.scrollHeight;
      // Keep max 50 entries
      while (debugEventLog.children.length > 50) {
        debugEventLog.removeChild(debugEventLog.firstChild);
      }
    } catch (_) {}
  };
}

function stopDebugSSE() {
  if (debugSSE) {
    debugSSE.close();
    debugSSE = null;
  }
}

function startAudioVis() {
  // Capture browser audio output (speech synthesis) for waveform
  try {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;

    // Create a media stream from the audio destination
    if (audioCtx.createMediaStreamDestination) {
      const dest = audioCtx.createMediaStreamDestination();
      // Connect the destination to analyze system audio if possible
      analyser.connect(dest);
    }

    // For speech synthesis, we visualize using the analyser with no real input
    // so draw a flat line that animates when speaking
    const canvasCtx = audioCanvas.getContext("2d");
    const bufLen = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufLen);

    function draw() {
      audioAnimFrame = requestAnimationFrame(draw);
      const w = audioCanvas.width = audioCanvas.offsetWidth;
      const h = audioCanvas.height = audioCanvas.offsetHeight;
      canvasCtx.clearRect(0, 0, w, h);

      // If avatar is speaking, draw animated waveform; else flat line
      if (isSpeaking) {
        canvasCtx.lineWidth = 2;
        canvasCtx.strokeStyle = "#4caf50";
        canvasCtx.beginPath();
        const sliceW = w / 60;
        for (let i = 0; i < 60; i++) {
          const v = Math.sin(Date.now() * 0.01 + i * 0.5) * (h * 0.35) *
            (0.3 + 0.7 * Math.abs(Math.sin(Date.now() * 0.003 + i * 0.2)));
          const y = h / 2 + v;
          if (i === 0) canvasCtx.moveTo(0, y);
          else canvasCtx.lineTo(i * sliceW, y);
        }
        canvasCtx.stroke();

        // Glow effect
        canvasCtx.lineWidth = 4;
        canvasCtx.strokeStyle = "rgba(76, 175, 80, 0.2)";
        canvasCtx.stroke();
      } else {
        canvasCtx.lineWidth = 1;
        canvasCtx.strokeStyle = "#333";
        canvasCtx.beginPath();
        canvasCtx.moveTo(0, h / 2);
        // Subtle noise line
        for (let i = 0; i < w; i += 4) {
          canvasCtx.lineTo(i, h / 2 + (Math.random() - 0.5) * 3);
        }
        canvasCtx.stroke();
      }
    }
    draw();
  } catch (e) {
    console.warn("Audio visualization not available:", e);
  }
}

function stopAudioVis() {
  if (audioAnimFrame) {
    cancelAnimationFrame(audioAnimFrame);
    audioAnimFrame = null;
  }
  if (audioCtx) {
    audioCtx.close().catch(() => {});
    audioCtx = null;
    analyser = null;
  }
}

// ── Initial greeting on first click (browser TTS policy) ────────────────────

window.addEventListener("click", () => {
  avatarSpeak("Hello Saathvik. Your wellness companion is ready.");
}, { once: true });