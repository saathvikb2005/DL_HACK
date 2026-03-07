"""
Wellness Orchestrator — Central Hub
====================================
Connects all monitoring modules to the avatar via WebSocket.

Architecture:
    Eye_care  ─────┐
    Posture   ─────┤
    Workpattern ───┼──→  Orchestrator (FastAPI + WebSocket)  ──→  Avatar (Browser)
    Air Quality ───┤
    AI Chat   ─────┘

Endpoints:
    POST /api/event          — Monitoring modules push events here
    POST /api/chat           — User sends chat messages
    GET  /api/status         — System health dashboard
    WS   /ws                 — Avatar connects here for real-time updates
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("orchestrator")

# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Wellness Orchestrator",
    description="Central hub connecting health monitors to the AI avatar",
    version="1.0.0",
)

# CORS: Use specific origins from environment or default to localhost
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── State ────────────────────────────────────────────────────────────────────

connected_avatars: list[WebSocket] = []
event_history: list[dict] = []
module_status: dict[str, dict] = {}

# Debug: latest camera frame (JPEG bytes)
_debug_frame: bytes = b""
_debug_frame_ts: float = 0.0

# SSE subscribers for debug events
_debug_event_queues: list[asyncio.Queue] = []

# Cooldowns: prevent the same event from spamming the avatar
cooldowns: dict[str, float] = {}
COOLDOWN_SECONDS = {
    "LOW_BLINK_RATE": 120,
    "CONTINUOUS_STARE": 60,
    "LONG_SCREEN_TIME": 300,
    "BAD_POSTURE": 90,
    "HIGH_FATIGUE": 180,
    "LONG_SESSION": 300,
    "POOR_AIR_QUALITY": 600,
    "AQI_REPORT": 14400,     # 4 hours
    "HYDRATE": 1800,
    "TAKE_BREAK": 300,
    "EYE_STRAIN": 120,
    "HIGH_STRESS": 300,
    "HIGH_DISEASE_RISK": 600,
    "WORK_STATUS": 1800,     # 30 min
}

# ── Event → Friendly Message Mapping ────────────────────────────────────────

EVENT_MESSAGES = {
    "LOW_BLINK_RATE": [
        "Hey, your blink rate is a bit low. Try blinking slowly a few times.",
        "Looks like your eyes are getting dry. Let's do a few slow blinks.",
        "You've been staring for a while. Close your eyes for 3 seconds and relax.",
    ],
    "CONTINUOUS_STARE": [
        "You haven't blinked in a while. Take a micro-break right now.",
        "Your eyes need a rest. Close them for 15 seconds and breathe deeply.",
    ],
    "LONG_SCREEN_TIME": [
        "You've been at the screen for too long. Follow the 20-20-20 rule.",
        "Time for an eye break! Look at something 20 feet away for 20 seconds.",
    ],
    "BAD_POSTURE": [
        "Your posture needs attention.",
    ],
    "HIGH_FATIGUE": [
        "You seem tired. Consider taking a short break.",
        "Your typing pattern suggests fatigue. A 5-minute stretch would help.",
        "Looks like your energy is dropping. How about a quick walk?",
    ],
    "LONG_SESSION": [
        "You've been working for a while. Time for a stretch.",
        "Great focus! But your body needs movement. Stand up for a minute.",
    ],
    "POOR_AIR_QUALITY": [
        "The air quality around you isn't great. Consider opening a window.",
        "Air quality is poor right now. Fresh air would help you concentrate.",
    ],
    "TAKE_BREAK": [
        "It's time for a break. Stand up and move around.",
        "You've earned a break. Step away for a few minutes.",
    ],
    "HYDRATE": [
        "Remember to drink some water!",
        "Stay hydrated! Take a sip of water.",
    ],
    "EYE_STRAIN": [
        "Your eyes may be strained. Look away from the screen for a bit.",
    ],
    "HIGH_STRESS": [
        "Your stress levels seem elevated. Try some deep breathing.",
        "Let's pause for a moment. Take 3 slow, deep breaths.",
    ],
    "HIGH_DISEASE_RISK": [
        "Your health risk assessment shows some elevated scores. Consider reviewing your lifestyle habits.",
        "Some of your health indicators need attention. Regular exercise and a balanced diet can help.",
    ],
    "AQI_REPORT": [
        "Here's your air quality update.",
        "Time for an air quality check.",
    ],
    "WORK_STATUS": [
        "Here's a quick update on your work session.",
    ],
}

import random

# ── Posture issue → specific advice mapping ──────────────────────────────────

_POSTURE_ISSUE_TIPS = {
    "Forward Head": [
        "Your head is too far forward. Tuck your chin in and align your ears over your shoulders.",
        "I see forward head posture. Pull your head back gently, like making a double chin.",
        "Your neck is craning forward. Imagine a string pulling the top of your head toward the ceiling.",
    ],
    "Uneven Shoulders": [
        "Your shoulders are uneven. Drop both shoulders down and level them out.",
        "One shoulder is higher than the other. Relax both shoulders and shake them out.",
        "I notice your shoulders are tilted. Roll them back and let them settle evenly.",
    ],
    "Slouching": [
        "You're slouching. Sit up tall and press your lower back into the chair.",
        "Your spine is curved forward. Straighten up and engage your core.",
        "I see slouching. Imagine stacking your vertebrae one on top of another.",
    ],
    "Rounded Shoulders": [
        "Your shoulders are rounded forward. Open your chest and squeeze your shoulder blades together.",
        "I notice rounded shoulders. Pull them back and down away from your ears.",
        "Your shoulders are hunching forward. Try a quick doorway chest stretch.",
    ],
}

_POSTURE_SEVERITY = {
    "critical": [
        "Your posture needs immediate correction!",
        "Please fix your posture right now.",
    ],
    "bad": [
        "Your posture isn't great.",
        "Time to adjust your sitting position.",
    ],
    "moderate": [
        "Your posture could be a little better.",
        "A small posture adjustment would help.",
    ],
}


def _build_posture_message(score: int, issues: list) -> str:
    """Build a specific posture message from the actual score and detected issues."""
    if score < 30:
        severity = "critical"
    elif score < 50:
        severity = "bad"
    else:
        severity = "moderate"

    intro = random.choice(_POSTURE_SEVERITY[severity])

    if issues:
        # Pick the advice for one specific issue (rotate through them)
        issue = random.choice(issues)
        tips = _POSTURE_ISSUE_TIPS.get(issue, [f"You have {issue.lower()}."])
        detail = random.choice(tips)
        return f"{intro} {detail} Posture score: {score}%."
    else:
        return f"{intro} Posture score: {score}%."


def get_friendly_message(event_type: str, context: Optional[dict] = None) -> str:
    """Pick a random friendly message for the event, optionally with context."""
    messages = EVENT_MESSAGES.get(event_type)
    if not messages:
        return f"Health alert: {event_type.replace('_', ' ').lower()}"
    msg = random.choice(messages)
    
    # ── Special handling for BAD_POSTURE: build message from actual issues ──
    if event_type == "BAD_POSTURE" and context:
        score = context.get("posture_score", 0)
        issues = context.get("issues", [])
        return _build_posture_message(score, issues)
    
    # ── Special handling for POOR_AIR_QUALITY: use dynamic recommended_action ──
    if event_type == "POOR_AIR_QUALITY" and context:
        aqi = context.get("aqi")
        city = context.get("city", "your area")
        category = context.get("category", "")
        severity = context.get("severity", "")
        recommended_action = context.get("recommended_action", "")
        
        if aqi and recommended_action:
            # Safely format AQI as numeric value
            try:
                numeric_aqi = float(aqi)
                aqi_str = f"{numeric_aqi:.0f}"
            except (ValueError, TypeError):
                aqi_str = str(aqi)  # Use as-is if not numeric
            
            # Build comprehensive AQI message with context
            msg = f"Air quality in {city} is {severity if severity else category}. The AQI is {aqi_str}. {recommended_action}"
            return msg
        elif aqi:
            # Safely format AQI
            try:
                numeric_aqi = float(aqi)
                aqi_str = f"{numeric_aqi:.0f}"
            except (ValueError, TypeError):
                aqi_str = str(aqi)
            
            msg += f" Current AQI: {aqi_str} in {city}."
            if category:
                msg += f" Category: {category}."
            return msg

    if context:
        # Append context info if available
        if "blink_rate" in context:
            msg += f" Your current blink rate is {context['blink_rate']}/min."
        if "work_duration" in context:
            msg += f" You've been working for {context['work_duration']} minutes."
        if "aqi" in context:
            msg += f" Current AQI: {context['aqi']}."
        if "city" in context:
            msg += f" Location: {context['city']}."
        if "risk_level" in context and "heart" in context:
            msg += f" Risk level: {context['risk_level']}."
        if "stress_score" in context:
            msg += f" Stress score: {context['stress_score']}/100."
        if "aqi_value" in context:
            msg += f" The current AQI is {context['aqi_value']}, which is {context.get('aqi_category', 'unknown')}."
            city = context.get('city', '')
            if city:
                msg += f" Location: {city}."
        if "typing_speed" in context:
            msg += f" Typing speed: {context['typing_speed']} WPM."
        if "session_duration" in context:
            msg += f" Session duration: {context['session_duration']} minutes."
        if "fatigue_level" in context:
            msg += f" Fatigue level: {context['fatigue_level']}."
    return msg


def is_on_cooldown(event_type: str) -> bool:
    """Check if this event type is still cooling down."""
    last_time = cooldowns.get(event_type, 0)
    cd = COOLDOWN_SECONDS.get(event_type, 60)
    return (time.time() - last_time) < cd


# ── Schemas ──────────────────────────────────────────────────────────────────


class EventPayload(BaseModel):
    event_type: str
    source: str  # "eye_care", "posture", "workpattern", etc.
    context: Optional[dict] = None


class ChatPayload(BaseModel):
    message: str


# ── WebSocket: Avatar connection ─────────────────────────────────────────────


async def broadcast_to_avatars(payload: dict):
    """Send a JSON message to all connected avatar clients."""
    dead = []
    for ws in connected_avatars:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_avatars.remove(ws)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_avatars.append(ws)
    logger.info("Avatar connected. Total: %d", len(connected_avatars))

    # Send current status on connect
    await ws.send_json({
        "type": "welcome",
        "message": "Connected to Wellness Orchestrator",
        "modules": list(module_status.keys()),
    })

    try:
        while True:
            # Listen for messages from avatar (e.g. user chat)
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "chat":
                    await handle_chat_from_avatar(msg.get("message", ""), ws)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        # Safely remove websocket only if present
        if ws in connected_avatars:
            connected_avatars.remove(ws)
        logger.info("Avatar disconnected. Total: %d", len(connected_avatars))


# ── REST: Event endpoint (modules push events here) ─────────────────────────


@app.post("/api/event")
async def receive_event(payload: EventPayload):
    """Monitoring modules call this to report health events."""

    event_type = payload.event_type.upper()

    # Update module status
    module_status[payload.source] = {
        "last_event": event_type,
        "last_time": datetime.now().isoformat(),
    }

    # Cooldown check
    if is_on_cooldown(event_type):
        return {"status": "cooldown", "event": event_type}

    cooldowns[event_type] = time.time()

    # Get friendly message
    message = get_friendly_message(event_type, payload.context)

    # Store in history
    record = {
        "event": event_type,
        "source": payload.source,
        "message": message,
        "time": datetime.now().isoformat(),
    }
    event_history.append(record)
    if len(event_history) > 200:
        event_history.pop(0)

    logger.info("[%s] %s → %s", payload.source, event_type, message)

    # Broadcast to avatar
    await broadcast_to_avatars({
        "type": "speak",
        "event": event_type,
        "message": message,
        "source": payload.source,
    })

    # Push to debug SSE stream
    await _push_debug_event(record)

    return {"status": "delivered", "event": event_type, "message": message}


# ── REST: Chat endpoint ─────────────────────────────────────────────────────


async def handle_chat_from_avatar(user_message: str, ws: WebSocket):
    """Handle chat input from the avatar UI."""
    response = generate_chat_response(user_message)
    await ws.send_json({
        "type": "speak",
        "event": "CHAT_RESPONSE",
        "message": response,
        "source": "ai",
    })


@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    """REST endpoint for chat — also broadcasts to avatar."""
    response = generate_chat_response(payload.message)

    await broadcast_to_avatars({
        "type": "speak",
        "event": "CHAT_RESPONSE",
        "message": response,
        "source": "ai",
    })

    return {"response": response}


def generate_chat_response(user_message: str) -> str:
    """
    Simple rule-based chat for now.
    Replace with LLM integration (OpenAI, local model, etc.) for production.
    """
    msg = user_message.lower().strip()

    # Status queries
    if any(w in msg for w in ["how long", "working", "session", "time"]):
        if module_status.get("workpattern"):
            return "I've been tracking your session. Check the work pattern monitor for detailed stats."
        return "I don't have session data right now. Make sure the work pattern monitor is running."

    # Emotional support
    if any(w in msg for w in ["tired", "exhausted", "sleepy"]):
        return "I can tell you're tired. Take a 5-minute break, stretch, and grab some water. You'll feel better."

    if any(w in msg for w in ["stressed", "anxious", "overwhelmed"]):
        return "Take a deep breath. In for 4 seconds, hold for 4, out for 4. Repeat 3 times. It really helps."

    if any(w in msg for w in ["frustrated", "stuck", "bug", "error"]):
        return "Debugging is tough. Sometimes stepping away for 2 minutes gives you a fresh perspective. Try it."

    if any(w in msg for w in ["bored", "unmotivated"]):
        return "Try switching tasks for a bit, or set a small achievable goal. Momentum builds motivation."

    # Health queries
    if any(w in msg for w in ["eyes", "blink", "strain"]):
        return "Your eyes need regular breaks. Try the 20-20-20 rule: every 20 minutes, look at something 20 feet away for 20 seconds."

    if any(w in msg for w in ["posture", "back", "sitting"]):
        return "Good posture tip: feet flat, back straight, screen at eye level. Roll your shoulders back right now."

    if any(w in msg for w in ["break", "rest", "pause"]):
        return "Great idea! Stand up, stretch your arms above your head, and walk around for 2 minutes."

    # Greetings
    if any(w in msg for w in ["hello", "hi", "hey"]):
        return "Hey! I'm your wellness companion. I'm watching out for your health while you code."

    if any(w in msg for w in ["thanks", "thank you"]):
        return "You're welcome! I'm here whenever you need me."

    if any(w in msg for w in ["who are you", "what are you"]):
        return "I'm your AI wellness companion. I monitor your health while you work and remind you to take care of yourself."

    # Default
    return "I'm here to help you stay healthy while coding. Ask me about breaks, posture, eye care, or just chat."


# ── REST: Status dashboard ───────────────────────────────────────────────────


@app.get("/api/status")
async def system_status():
    """Overall system health and connected modules."""
    return {
        "avatar_connected": len(connected_avatars) > 0,
        "avatar_count": len(connected_avatars),
        "modules": module_status,
        "recent_events": event_history[-10:],
        "uptime": datetime.now().isoformat(),
    }


@app.get("/api/history")
async def event_history_endpoint():
    """Return full event history."""
    return {"events": event_history}


# ── Debug endpoints (video + event stream) ──────────────────────────────────


@app.post("/api/debug/frame")
async def upload_debug_frame(request: Request):
    """Combined monitor POSTs JPEG frames here."""
    global _debug_frame, _debug_frame_ts
    
    # Validate Content-Type
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("image/jpeg"):
        raise HTTPException(status_code=415, detail="Only image/jpeg content type is supported")
    
    # Enforce max body size (5MB)
    MAX_FRAME_SIZE = 5 * 1024 * 1024
    body = await request.body()
    if len(body) > MAX_FRAME_SIZE:
        raise HTTPException(status_code=413, detail="Frame size exceeds 5MB limit")
    
    _debug_frame = body
    _debug_frame_ts = time.time()
    return {"status": "ok"}


@app.get("/api/debug/frame")
async def get_debug_frame():
    """Return latest camera frame as JPEG image."""
    if not _debug_frame:
        return Response(status_code=204)
    return Response(content=_debug_frame, media_type="image/jpeg")


async def _debug_event_generator():
    """SSE generator that yields debug events."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    _debug_event_queues.append(queue)
    try:
        while True:
            data = await queue.get()
            yield f"data: {json.dumps(data)}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        if queue in _debug_event_queues:
            _debug_event_queues.remove(queue)


@app.get("/api/debug/events")
async def debug_event_stream():
    """Server-Sent Events stream for debug panel."""
    return StreamingResponse(
        _debug_event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _push_debug_event(event_data: dict):
    """Push an event to all SSE subscribers (non-blocking)."""
    dead = []
    for q in _debug_event_queues:
        try:
            q.put_nowait(event_data)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _debug_event_queues.remove(q)


@app.get("/")
async def root():
    return {
        "name": "Wellness Orchestrator",
        "version": "1.0.0",
        "description": "Central hub for the AI Wellness Companion",
        "endpoints": {
            "POST /api/event": "Modules push health events",
            "POST /api/chat": "User chat input",
            "GET /api/status": "System status dashboard",
            "GET /api/history": "Event history",
            "WS /ws": "Avatar WebSocket connection",
            "POST /api/debug/frame": "Upload camera frame (JPEG)",
            "GET /api/debug/frame": "Get latest camera frame",
            "GET /api/debug/events": "SSE stream for debug events",
        },
    }


# ── Background Scheduler: Periodic AQI & Work Status ────────────────────────

AQI_CITY = "Hyderabad"            # Fallback city; auto-detected on startup
AQI_INTERVAL = 4 * 3600           # every 4 hours
WORK_POLL_INTERVAL = 5 * 60       # every 5 minutes

_scheduler_tasks: list[asyncio.Task] = []


async def _detect_city() -> str:
    """Auto-detect city from IP geolocation."""
    global AQI_CITY
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("http://ip-api.com/json/?fields=status,city,regionName,country")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success" and data.get("city"):
                    AQI_CITY = data["city"]
                    logger.info("Location detected: %s, %s, %s",
                                data["city"], data.get("regionName", ""), data.get("country", ""))
                    return AQI_CITY
    except Exception as e:
        logger.warning("Location detection failed (%s), using fallback: %s", e, AQI_CITY)
    return AQI_CITY


async def _internal_push(event_type: str, source: str, context: dict):
    """Push an event internally (same logic as /api/event)."""
    if is_on_cooldown(event_type):
        return

    cooldowns[event_type] = time.time()
    message = get_friendly_message(event_type, context)

    module_status[source] = {
        "last_event": event_type,
        "last_time": datetime.now().isoformat(),
    }

    record = {
        "event": event_type,
        "source": source,
        "message": message,
        "time": datetime.now().isoformat(),
    }
    event_history.append(record)
    if len(event_history) > 200:
        event_history.pop(0)

    logger.info("[%s] %s → %s", source, event_type, message)

    await broadcast_to_avatars({
        "type": "speak",
        "event": event_type,
        "message": message,
        "source": source,
    })
    await _push_debug_event(record)


def _aqi_category(aqi: int) -> str:
    """Map AQI number to category string."""
    if aqi <= 50: return "Good"
    if aqi <= 100: return "Moderate"
    if aqi <= 150: return "Unhealthy for sensitive groups"
    if aqi <= 200: return "Unhealthy"
    if aqi <= 300: return "Very Unhealthy"
    return "Hazardous"


async def _poll_aqi():
    """Fetch AQI from the Air Quality module and announce."""
    await asyncio.sleep(30)  # wait for AQI service to start
    await _detect_city()     # auto-detect location from IP
    logger.info("AQI scheduler started (city=%s, interval=%ds)", AQI_CITY, AQI_INTERVAL)

    while True:
        aqi_val = None
        city_name = AQI_CITY

        # Try 1: local AQI prediction service
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    "http://localhost:8002/api/v1/predict/city",
                    json={"city": AQI_CITY},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    aqi_val = data.get("current_aqi", 0)
        except Exception:
            pass

        # Try 2: WAQI public API directly (use env var for token)
        if aqi_val is None:
            waqi_token = os.getenv("WAQI_TOKEN", "demo")  # Use env var or fallback to demo
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(
                        f"https://api.waqi.info/feed/{AQI_CITY}/?token={waqi_token}"
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("status") == "ok":
                            aqi_val = data["data"].get("aqi", 0)
                            city_name = data["data"].get("city", {}).get("name", AQI_CITY)
                        else:
                            logger.warning("WAQI API returned non-ok status: %s", data.get("data"))
                    else:
                        logger.warning("WAQI API HTTP error: %s", resp.status_code)
            except httpx.RequestError as e:
                logger.error("WAQI API request failed: %s", e)
            except (KeyError, ValueError) as e:
                logger.error("WAQI API response parsing failed: %s", e)

        # Try 3: WAQI geo-based lookup using detected coords
        if aqi_val is None:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    geo_resp = await client.get(
                        "http://ip-api.com/json/?fields=lat,lon"
                    )
                    if geo_resp.status_code == 200:
                        geo = geo_resp.json()
                        lat, lon = geo.get("lat"), geo.get("lon")
                        if lat and lon:
                            resp = await client.get(
                                f"https://api.waqi.info/feed/geo:{lat};{lon}/?token=demo"
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                if data.get("status") == "ok":
                                    aqi_val = data["data"].get("aqi", 0)
                                    city_name = data["data"].get("city", {}).get("name", AQI_CITY)
            except Exception as e:
                logger.debug("AQI geo-lookup failed: %s", e)

        if aqi_val is not None:
            category = _aqi_category(int(aqi_val))
            await _internal_push("AQI_REPORT", "air_quality", {
                "aqi_value": int(aqi_val),
                "aqi_category": category,
                "city": city_name,
            })
            if int(aqi_val) > 100:
                await _internal_push("POOR_AIR_QUALITY", "air_quality", {
                    "aqi": int(aqi_val),
                    "city": city_name,
                    "risk_level": category,
                })
        else:
            logger.warning("AQI: Could not fetch data for %s from any source", AQI_CITY)

        await asyncio.sleep(AQI_INTERVAL)


async def _poll_workpattern():
    """Fetch work status from the workpattern module and announce if interesting."""
    await asyncio.sleep(60)  # wait for workpattern to start
    logger.info("Work pattern poller started (interval=%ds)", WORK_POLL_INTERVAL)

    while True:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get("http://localhost:8001/api/v1/realtime-status")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "active":
                        analysis = data.get("current_analysis", {})
                        metrics = data.get("current_metrics", {})
                        session = data.get("session_info", {})

                        fatigue_level = analysis.get("fatigue_level", "Low")
                        fatigue_score = analysis.get("fatigue_score", 0)
                        typing_speed = metrics.get("typing_speed", 0)
                        duration = round(session.get("session_duration", 0))

                        # Push work status update
                        if duration >= 30:
                            await _internal_push("WORK_STATUS", "workpattern", {
                                "typing_speed": round(typing_speed),
                                "fatigue_level": fatigue_level,
                                "session_duration": duration,
                            })

                        # Push fatigue warning if high
                        if fatigue_score >= 70 or analysis.get("break_needed"):
                            await _internal_push("HIGH_FATIGUE", "workpattern", {
                                "fatigue_score": fatigue_score,
                                "work_duration": duration,
                            })
        except Exception as e:
            logger.debug("Workpattern poll failed: %s", e)

        await asyncio.sleep(WORK_POLL_INTERVAL)


@app.on_event("startup")
async def _start_schedulers():
    """Launch background pollers on app startup."""
    _scheduler_tasks.append(asyncio.create_task(_poll_aqi()))
    _scheduler_tasks.append(asyncio.create_task(_poll_workpattern()))
    logger.info("Background schedulers started (AQI every 4h, Work every 5m)")


@app.on_event("shutdown")
async def _stop_schedulers():
    """Cancel background tasks on shutdown."""
    for t in _scheduler_tasks:
        t.cancel()


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("  Wellness Orchestrator -- Starting")
    print("=" * 60)
    print("  POST /api/event    -> Modules push events")
    print("  POST /api/chat     -> User chat")
    print("  GET  /api/status   -> System dashboard")
    print("  WS   /ws           -> Avatar connection")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8765)
