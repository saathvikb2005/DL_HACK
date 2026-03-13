"""
FastAPI Server for Real-Time Work Pattern Analysis
Monitors typing behavior and recommends breaks
WITH REAL-TIME MONITORING INTEGRATION
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import json
import asyncio
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="Work Pattern Analysis API - Real-Time Edition",
    description="Real-time work pattern monitoring with automatic data collection",
    version="2.0.0"
)

# CORS middleware
# Production: Set ALLOWED_ORIGINS env var to specific domains
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model on startup
@app.on_event("startup")
async def startup_event():
    """Server startup"""
    print("\n" + "="*60)
    print("🚀 Starting Work Pattern Analysis API")
    print("="*60)
    try:
        from integrated_monitor import get_monitor
        monitor = get_monitor()
        monitor.start_background()
        print("✓ Integrated monitor started inside API process")
    except Exception as e:
        print(f"⚠ Could not start integrated monitor: {e}")
    print("✓ API ready")
    print("="*60 + "\n")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Work Pattern Analysis API - Real-Time Edition",
        "version": "2.0.0",
        "endpoints": {
            "realtime": "/api/v1/realtime-status",
            "stream": "/api/v1/stream",
            "health": "/api/health",
            "docs": "/api/docs"
        },
        "description": "Real-time typing behavior analysis with automatic monitoring"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        from integrated_monitor import get_monitor
        monitor = get_monitor()
        return {
            "status": "healthy",
            "monitor_active": monitor.running,
            "calibrated": not monitor.calibration_mode
        }
    except:
        return {
            "status": "healthy",
            "monitor_active": False,
            "message": "Start integrated_monitor.py for real-time data"
        }

@app.get("/api/v1/realtime-status")
async def get_realtime_status():
    """
    Get current real-time monitoring status
    
    **Returns**:
    - Current metrics from background monitor
    - Live analysis results
    - Session information
    - No manual input required!
    """
    try:
        from integrated_monitor import get_monitor
        monitor = get_monitor()
        
        status = monitor.get_current_status()
        
        if not status['metrics']:
            return {
                "status": "waiting",
                "message": "Start typing to see real-time data!",
                "calibrated": status['session_info']['calibrated']
            }
        
        return {
            "status": "active",
            "timestamp": datetime.now().isoformat(),
            "current_metrics": status['metrics'],
            "current_analysis": status['analysis'],
            "session_info": status['session_info']
        }
    except Exception as e:
        return {
            "status": "monitor_not_running",
            "message": "Start integrated_monitor.py to enable real-time data",
            "error": str(e)
        }

@app.get("/api/v1/stream")
async def stream_realtime():
    """
    Server-Sent Events stream for real-time updates
    
    **Usage**:
    - Open in browser to see live stream
    - Updates every 5 seconds
    - Shows typing speed, fatigue level, etc.
    """
    async def event_generator():
        from integrated_monitor import get_monitor
        monitor = get_monitor()
        
        while True:
            try:
                status = monitor.get_current_status()
                
                if status['metrics']:
                    data = {
                        'timestamp': datetime.now().isoformat(),
                        'typing_speed': status['metrics'].get('typing_speed', 0),
                        'fatigue_level': status['analysis'].get('fatigue_level', 'Unknown'),
                        'fatigue_score': status['analysis'].get('fatigue_score', 0),
                        'work_duration': status['session_info'].get('session_duration', 0)
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                else:
                    yield f"data: {json.dumps({'status': 'waiting'})}\n\n"
                
                await asyncio.sleep(5)
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(5)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )
