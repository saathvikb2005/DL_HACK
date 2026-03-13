# Run All Modules In Debug Mode

This guide is for checking every module with visible output, including camera windows where applicable.

## What Debug Mode Means

`MASTER_LAUNCHER.py --all --debug` does the following:

- Starts the orchestrator with visible logs.
- Starts the avatar frontend with visible Vite logs.
- Starts Eye Care with webcam preview enabled.
- Starts Posture Detection with its normal camera window.
- Starts the Workpattern monitor and API together in one process.
- Starts the Air Quality API.
- Starts the Vijitha API.

## Recommended Start

From the project root:

```powershell
cd D:\DL_HACK
d:\DL_HACK\.venv\Scripts\python.exe MASTER_LAUNCHER.py --all --debug
```

## What You Should See

- Orchestrator logs in the terminal.
- Avatar UI started by Vite, usually on `http://localhost:5173` or the next free port.
- Eye Care webcam window.
- Posture Detection webcam window.
- Workpattern console updates.
- Air Quality API startup logs.
- Vijitha API startup logs.

## Camera-Based Modules

These modules should show live visual output in debug mode:

- Eye Care
- Posture Detection

These modules do not use camera windows:

- Workpattern
- Air Quality
- Vijitha
- Orchestrator
- Avatar UI

## Quick Health Checks

Open another terminal and run:

```powershell
Invoke-RestMethod http://localhost:8765/api/status | ConvertTo-Json -Depth 4
Invoke-RestMethod http://localhost:8001/api/health | ConvertTo-Json -Depth 4
Invoke-RestMethod http://localhost:8002/health | ConvertTo-Json -Depth 4
Invoke-RestMethod http://localhost:8000/health | ConvertTo-Json -Depth 4
```

## Trigger A Live Avatar Message

Once the avatar page is open, send:

```powershell
$body = '{"message":"hi"}'
Invoke-RestMethod -Method Post -Uri "http://localhost:8765/api/chat" -ContentType "application/json" -Body $body
```

## If You Want To Run Modules Manually

### Orchestrator

```powershell
cd D:\DL_HACK
D:\DL_HACK\.venv311\Scripts\python.exe avatar_system\orchestrator.py
```

### Avatar UI

```powershell
cd D:\DL_HACK\avatar_system
npm run dev
```

### Eye Care With Camera Preview

```powershell
cd D:\DL_HACK\Eye_care
d:\DL_HACK\.venv\Scripts\python.exe main.py
```

### Posture Detection With Camera Preview

```powershell
cd D:\DL_HACK\posture_detection
d:\DL_HACK\.venv\Scripts\python.exe posture_detection.py
```

### Workpattern Monitor + API

Recommended:

```powershell
cd D:\DL_HACK\workpattern
d:\DL_HACK\.venv\Scripts\python.exe main.py
```

Optional standalone monitor-only mode:

```powershell
cd D:\DL_HACK\workpattern
d:\DL_HACK\.venv\Scripts\python.exe integrated_monitor.py
```

### Air Quality API

```powershell
cd D:\DL_HACK\Air_quality_risk_pred
d:\DL_HACK\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

### Vijitha API

```powershell
cd D:\DL_HACK\vijitha
d:\DL_HACK\.venv\Scripts\python.exe main.py
```

## Notes

- The orchestrator serves avatar speech, event routing, websocket updates, and TTS.
- The avatar frontend may open on `5174` if `5173` is already in use.
- The avatar needs one click in the browser before audio playback is allowed.
- If webcam modules fail, first check camera permissions and whether another app is already using the camera.

## Stop Everything

Press `Ctrl+C` in the launcher terminal.
