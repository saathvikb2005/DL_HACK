# S.ATHVA
### Smart Assistant for Thriving, Health, Vitality & Awareness

> 🚧 **Status:** Active Development (Ongoing)

S.ATHVA is an AI-powered desktop wellness companion designed to promote healthier work habits through real-time computer vision, AI assistance, and personalized wellness guidance.

Unlike traditional chatbots, S.ATHVA continuously monitors user wellness using computer vision and provides proactive recommendations to reduce digital fatigue, improve posture, and encourage healthier productivity.

---

# Vision

S.ATHVA aims to become an intelligent wellness companion capable of:

- 👁️ Monitoring eye health in real time
- 🧍 Detecting posture issues
- 🤖 Providing AI-powered assistance
- 📊 Tracking productivity patterns
- ❤️ Delivering personalized wellness insights
- 🎯 Encouraging healthier work habits

---

# Current Development Status

## Completed

- Authentication System
- JWT Security
- User Management
- Angular Dashboard
- Electron Desktop Shell
- FastAPI Backend
- MySQL Integration
- Avatar Chat
- Conversation Persistence
- Webcam Infrastructure
- MediaPipe Integration
- Face Landmark Detection
- Eye Landmark Detection
- Blink Detection
- Eye Health Event System

---

## Currently Under Development

### M01 – Eye Health

Current Progress

- Eye Landmark Mapping
- EAR Calculation
- Blink Detection
- Blink Rate
- Session Tracking
- Eye Health Indicators
- Long Stare Detection
- Screen Exposure Monitoring
- Recommendation Events

Upcoming

- Eye Recovery Sessions
- 20-20-20 Rule
- Adaptive Thresholds
- Calibration Improvements

---

## Planned Modules

### M02 – Posture Monitoring

- Neck Alignment
- Shoulder Alignment
- Spine Analysis
- Posture Events
- Stretch Recommendations

---

### M03 – Stress Monitoring

- Daily Mood Check
- Journal Analysis
- Sentiment Analysis
- Stress Indicators

---

### M04 – Productivity Monitoring

- Focus Sessions
- Work Duration
- Break Tracking
- Productivity Analytics

---

### M05 – Wellness Intelligence

- Physical Wellness
- Mental Wellness
- Work Wellness
- Personalized Wellness Insights

---

### M06 – Reports & Analytics

- Daily Reports
- Weekly Reports
- Monthly Reports
- Trend Analysis

---

### Future

- Electron Overlay Assistant
- Live2D Avatar
- Voice Assistant
- Cross-Application Wellness Notifications

---

# Architecture

```
                    S.ATHVA

        Angular Frontend
                │
         Electron Desktop
                │
          FastAPI Backend
                │
        ┌───────────────┐
        │               │
      MySQL        Gemini API
        │
        └───────────────┐
                        │
               OpenCV + MediaPipe
                        │
      Face • Eyes • Pose Detection
                        │
          Wellness Intelligence
```

---

# Technology Stack

## Frontend

- Angular
- TypeScript
- SCSS
- Bootstrap

## Desktop

- Electron

## Backend

- FastAPI
- Python

## Database

- MySQL

## AI

- Google Gemini API

## Computer Vision

- MediaPipe
- OpenCV

## Authentication

- JWT
- Passlib

---

# Folder Structure

```
SATHVA/

frontend/
│
├── angular-dashboard/
└── electron-shell/

backend/
│
├── app/
│   ├── api/
│   ├── database/
│   ├── models/
│   ├── services/
│   └── websocket/

docs/

assets/

overlay/ (Future)
```

---

# Features

## Dashboard

- Wellness Overview
- Session Summary
- Recent Alerts
- Quick Actions

---

## Avatar

- AI Chat
- Conversation History
- Context Awareness

---

## Eye Health

- Webcam Feed
- Blink Detection
- EAR Monitoring
- Long Stare Detection
- Eye Health Events
- Recommendations

---

## Posture

*(In Progress)*

---

## Stress

*(Planned)*

---

## Productivity

*(Planned)*

---

## Reports

*(Planned)*

---

# Current Milestones

| Phase | Status |
|---------|--------|
| Phase 0 – Foundation | ✅ Complete |
| Phase 1 – Avatar Foundation | ✅ Complete |
| Phase 2 – Wellness Infrastructure | ✅ Complete |
| M01 – Eye Health | 🚧 In Progress |
| M02 – Posture | ⏳ Planned |
| M03 – Stress | ⏳ Planned |
| M04 – Productivity | ⏳ Planned |
| Wellness Engine | ⏳ Planned |

---

# Installation

## Backend

```bash
cd backend

python -m venv .venv

pip install -r requirements.txt

uvicorn app.main:app --reload
```

---

## Frontend

```bash
cd frontend/angular-dashboard

npm install

ng serve
```

---

## Electron

```bash
cd frontend/electron-shell

npm install

npm run electron
```

---

# Future Roadmap

- Advanced Eye Health Analytics
- Posture Monitoring
- Stress Detection
- Productivity Intelligence
- Wellness Intelligence Engine
- Fatigue Detection
- Recovery Coach
- Voice Interaction
- Live2D Desktop Companion
- Cross-platform Support

---

# Screenshots

> 🚧 Screenshots will be added as the project progresses.

- Dashboard
- Avatar Chat
- Eye Health
- Reports

---

# Development Philosophy

S.ATHVA follows a modular architecture where each wellness module is independently developed, validated, and integrated into a centralized AI wellness ecosystem.

The project prioritizes:

- Scalability
- Maintainability
- Modular Design
- AI-assisted Wellness
- Real-time Computer Vision
- Clean Architecture

---

# License

This project is currently under active development for educational and research purposes.

---

⭐ If you find this project interesting, consider starring the repository and following its progress.
