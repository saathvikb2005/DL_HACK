# Team Phase Execution Plan

## Intelligent Telecall Conversation Analysis System (MERN + AI)

This document defines a **very detailed phase-wise development,
collaboration, Git workflow, and integration strategy** for building the
**Intelligent Telecall Conversation Analysis System**.

The system analyzes telecall recordings to detect:

-   Speech transcription
-   Sentiment
-   Intent
-   Suspicious conversation patterns
-   Analytics insights

The system will be built using a **MERN + AI architecture**:

  Layer           Technology
  --------------- ---------------------------------
  Frontend        React.js
  Backend         Node.js + Express
  Database        MongoDB
  AI Processing   Python (Whisper + Transformers)
  Integration     REST APIs
  Visualization   Chart.js / Recharts

------------------------------------------------------------------------

# Team Members

  Member     Role
  ---------- --------------------------------
  Saathvik   AI & Machine Learning Lead
  Vijitha    Backend & API Development Lead
  Thushika   Frontend & Visualization Lead

------------------------------------------------------------------------

# Repository Branch Strategy

Repository branches:

main -- production stable\
development -- integrated testing\
saathvik-ai -- AI development\
vijitha-backend -- backend development\
thushika-frontend -- frontend development

------------------------------------------------------------------------

# Phase 0 --- Project Initialization

## Goal

Create the **entire repository structure, environments, and base
infrastructure**.

------------------------------------------------------------------------

## Saathvik Responsibilities (AI Setup)

Tasks:

1.  Create AI service directory

```{=html}
<!-- -->
```
    ai-service/
       speech/
       nlp/
       models/
       datasets/
       utils/

2.  Create Python virtual environment

```{=html}
<!-- -->
```
    python -m venv venv
    source venv/bin/activate

3.  Install AI dependencies

```{=html}
<!-- -->
```
    pip install torch transformers openai-whisper pandas numpy scikit-learn fastapi uvicorn

4.  Create base AI server

Example:

``` python
from fastapi import FastAPI
app = FastAPI()

@app.get("/ai-health")
def health():
    return {"status": "AI running"}
```

------------------------------------------------------------------------

## Vijitha Responsibilities (Backend Setup)

Create backend service.

    backend/
       controllers/
       routes/
       models/
       services/
       config/
       server.js

Install packages

    npm init -y
    npm install express mongoose multer cors axios dotenv

Create server.js

``` javascript
const express = require("express")
const app = express()

app.get("/", (req,res)=>{
 res.send("Backend running")
})

app.listen(5000)
```

------------------------------------------------------------------------

## Thushika Responsibilities (Frontend Setup)

Create React app

    npx create-react-app frontend

Folder structure

    frontend/src/
       components/
       pages/
       services/
       hooks/

Create initial pages

-   Home
-   Upload Page
-   Dashboard Page

------------------------------------------------------------------------

## Phase 0 Integration

Integration steps:

1.  Pull latest code

```{=html}
<!-- -->
```
    git pull origin development

2.  Merge branches

```{=html}
<!-- -->
```
    git checkout development
    git merge saathvik-ai
    git merge vijitha-backend
    git merge thushika-frontend

3.  Test:

-   backend runs
-   frontend loads
-   ai service runs

------------------------------------------------------------------------

# Phase 1 --- Database & Dataset Preparation

## Goal

Prepare data infrastructure and datasets.

------------------------------------------------------------------------

## Saathvik

Download datasets:

Speech:

-   Mozilla Common Voice

Sentiment:

-   GoEmotions
-   Sentiment140

Fraud:

-   ScamCall dataset
-   Jigsaw Toxic Comment dataset

Create preprocessing scripts

    ai-service/utils/data_cleaning.py

Tasks:

-   remove noise
-   normalize text
-   create labeled examples

------------------------------------------------------------------------

## Vijitha

Setup MongoDB.

Install

    npm install mongoose

Create schema

    CallSchema
    {
     audioUrl,
     transcript,
     analysis,
     createdAt
    }

------------------------------------------------------------------------

## Thushika

Create **dataset preview UI**

Components

    DatasetViewer.jsx
    TranscriptSample.jsx

------------------------------------------------------------------------

## Integration

Workflow

Dataset → MongoDB → API → React display

------------------------------------------------------------------------

# Phase 2 --- Speech to Text

## Goal

Convert audio calls into transcripts.

------------------------------------------------------------------------

## Saathvik

Implement Whisper transcription

    ai-service/speech/transcriber.py

Example

``` python
import whisper
model = whisper.load_model("base")

def transcribe(audio):
    result = model.transcribe(audio)
    return result["text"]
```

------------------------------------------------------------------------

## Vijitha

Create endpoints

    POST /api/upload
    POST /api/transcribe

Use multer

``` javascript
const multer = require("multer")
```

Call AI service via axios

------------------------------------------------------------------------

## Thushika

Create components

    AudioUpload.jsx
    TranscriptViewer.jsx

Upload audio → backend → transcript

------------------------------------------------------------------------

## Integration Test

Flow

React Upload → Node API → Python AI → transcript → UI

------------------------------------------------------------------------

# Phase 3 --- NLP Analysis

## Goal

Analyze transcripts.

Modules

-   Sentiment detection
-   Intent detection
-   Suspicious detection

------------------------------------------------------------------------

## Saathvik

Create NLP modules

    ai-service/nlp/
       sentiment.py
       intent.py
       suspicious.py

Example

``` python
from transformers import pipeline
sentiment = pipeline("sentiment-analysis")
```

------------------------------------------------------------------------

## Vijitha

Create endpoint

    POST /api/analyze

Pipeline

Transcript → AI → store results → MongoDB

------------------------------------------------------------------------

## Thushika

Create transcript highlight UI

Color scheme

Green -- Positive\
Yellow -- Neutral\
Red -- Negative\
Purple -- Suspicious

------------------------------------------------------------------------

## Integration

Transcript → analyze API → result → React UI

------------------------------------------------------------------------

# Phase 4 --- Analytics Dashboard

## Goal

Provide insights.

------------------------------------------------------------------------

## Saathvik

Compute metrics

-   sentiment distribution
-   suspicious call frequency

------------------------------------------------------------------------

## Vijitha

Create analytics endpoint

    GET /api/analytics

Return

    {
     positiveCalls,
     negativeCalls,
     suspiciousCalls
    }

------------------------------------------------------------------------

## Thushika

Build dashboard

Charts

-   sentiment pie chart
-   suspicious detection bar chart
-   call activity graph

Libraries

    recharts
    chart.js

------------------------------------------------------------------------

# Phase 5 --- System Optimization

## Saathvik

-   optimize model inference
-   add batching

## Vijitha

-   optimize API performance
-   add caching

## Thushika

-   improve UI responsiveness

------------------------------------------------------------------------

# Phase 6 --- Testing

Testing levels

AI

-   transcription accuracy
-   sentiment accuracy

Backend

-   API reliability

Frontend

-   UI flow

------------------------------------------------------------------------

# Phase 7 --- Deployment

Backend

-   Node server on cloud

Frontend

-   Vercel

AI

-   Python service on GPU instance

Database

-   MongoDB Atlas

------------------------------------------------------------------------

# Final System Pipeline

Audio Upload ↓ Speech to Text ↓ Transcript ↓ NLP Analysis ↓ Suspicious
Detection ↓ MongoDB Storage ↓ Dashboard Visualization

------------------------------------------------------------------------

# Final Deliverables

The system will provide

-   telecall transcription
-   sentiment classification
-   intent detection
-   suspicious alerts
-   highlighted transcripts
-   analytics dashboard
