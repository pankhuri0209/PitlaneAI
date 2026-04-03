# 🏎️ PitLane AI — Your AI Race Engineer

> **Built at Voxel51 Hackathon · April 2026**
> Northeastern University · Team NUPitlane

PitLane AI brings professional-grade race engineering to every kart driver. Upload your onboard lap video, and let AI find your mistakes, highlight your best moments, and generate a full coaching report — in seconds.

---

## About

Most karting drivers never get real-time feedback on their laps. Hiring a race engineer is expensive. Watching back footage yourself is slow and subjective.

**PitLane AI** solves this. Powered by Twelve Labs' multimodal video AI (Pegasus), it watches your lap the way a race engineer would — frame by frame — and delivers structured, timestamped coaching you can act on immediately.

The project ships as two integrated surfaces:
- **FiftyOne Plugin** — run operators directly on your video dataset inside FiftyOne's UI
- **Web Application** — a standalone React + FastAPI app for browser-based analysis

---

## Features

### 🔴 Find Lap Errors
Pegasus watches your entire onboard lap and identifies every driving mistake with timestamps. Errors are grouped into four engineering categories:

| Category | Examples |
|---|---|
| Racing Line | Wide entry, missed apex, late turn-in |
| Braking | Missed braking point, threshold braking errors |
| Throttle & Traction | Early throttle, wheelspin, traction loss |
| Car Control | Oversteer, understeer, snap corrections |

You can filter by specific error type (e.g. `"missed apex, late braking"`) or run a full-lap scan.

---

### 🌟 Find Best Moments
Highlights your top driving moments across six categories so you can understand what you're doing right:

| Category | What It Finds |
|---|---|
| 🎯 Smooth Apex | Clean corner entry and apex hit |
| 🚀 Clean Acceleration | Precise, progressive throttle out of corners |
| ⚡ Fast Straight | Maximum speed sections |
| 📐 Perfect Racing Line | Optimal corner geometry |
| 🛑 Smooth Braking | Controlled, progressive braking zones |
| 🏆 Impressive Moment | Standout moments of skill or commitment |

---

### 💬 Ask About This Lap
Ask any free-form question about your lap and get a structured, timestamped answer from the AI:

> *"Was my racing line through Turn 3 correct?"*
> *"Where am I losing the most time?"*
> *"Was my braking consistent across all three laps?"*

Returns a verdict, key moments table, and a concrete recommendation.

---

### 📊 Generate Coaching Report
A full two-step AI pipeline (Pegasus → Groq LLaMA 70B) produces a professional coaching report:

- **Performance scores** for Racing Line, Braking, Throttle (1–10)
- **Sector-by-sector** breakdown with timestamps
- **Lap time loss estimates** in tenths of seconds
- **Top 3 priority improvements** with specific corners and what to change
- **Overall rating** with biggest strength and biggest weakness

Focus modes: Full Analysis · Racing Line Only · Braking Only · Throttle & Exit Only

---

## How It Works

```
Onboard Video
     │
     ▼
Twelve Labs (Pegasus)
  – Watches the entire lap
  – Understands racing context
  – Returns raw timestamped observations
     │
     ▼
Groq LLaMA-3.3-70B  ← (Coaching Report only)
  – Extracts structured scores (JSON)
  – Writes markdown coaching report
     │
     ▼
FiftyOne UI  /  React Web App
  – Renders results with timestamps
  – Structured markdown tables
  – Performance scorecards
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Video AI | [Twelve Labs](https://twelvelabs.io) — Pegasus (analyze) + Marengo (search) |
| Dataset & Plugin UI | [Voxel51 FiftyOne](https://voxel51.com) |
| LLM Coaching | [Groq](https://groq.com) — LLaMA 3.3 70B Versatile |
| Backend API | [FastAPI](https://fastapi.tiangolo.com) + Uvicorn |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Package Management | pip + npm |

---

## Project Structure

```
PitlaneAI/
├── __init__.py              # FiftyOne plugin operators
├── fiftyone.yml             # Plugin manifest
├── dataset.py               # Downloads videos + creates FiftyOne dataset
├── .env                     # API keys (not committed)
├── backend/
│   └── main.py              # FastAPI backend (4 endpoints)
└── PitLane AI Web Application/
    └── src/app/
        ├── App.tsx
        └── components/
            ├── AnalyzePage.tsx   # Main analysis UI
            ├── HeroSection.tsx
            └── ...
```

---

## Running Locally

### Prerequisites

- Python 3.9+
- Node.js 18+
- ffmpeg (`brew install ffmpeg` on macOS)
- API keys for [Twelve Labs](https://twelvelabs.io), [Groq](https://groq.com)

### 1. Clone & configure

```bash
git clone https://github.com/pankhuri0209/NUPitlane-PitlaneAI.git
cd NUPitlane-PitlaneAI/PitlaneAI
```

Create a `.env` file in the root:

```env
TWELVELABS_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

### 2. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fiftyone twelvelabs fastapi uvicorn python-dotenv groq
```

### 3. Load the FiftyOne dataset

Upload your onboard lap videos to [Twelve Labs Playground](https://playground.twelvelabs.io), then:

```bash
python dataset.py
```

This downloads the indexed videos as MP4s into `downloads/` and creates a FiftyOne dataset called `kart_laps`.

### 4. Install the FiftyOne plugin

```bash
mkdir -p ~/fiftyone/__plugins__/pitlane-ai
cp __init__.py fiftyone.yml ~/fiftyone/__plugins__/pitlane-ai/
```

Then launch FiftyOne:

```bash
python -c "import fiftyone as fo; fo.launch_app(fo.load_dataset('kart_laps'))"
```

Open `http://localhost:5151` → press \` to open the operator panel → search for `find_lap_errors`, `find_best_moments`, or `ask_anything`.

### 5. Start the FastAPI backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 6. Start the React web app

```bash
cd "PitLane AI Web Application"
npm install
npm run dev
```

Open `http://localhost:5173` — select a video, choose an operator, and get instant AI coaching.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/videos` | List all indexed videos |
| POST | `/analyze/errors` | Find lap errors |
| POST | `/analyze/best-moments` | Find best driving moments |
| POST | `/analyze/ask` | Ask any question about the lap |
| POST | `/analyze/coaching-report` | Generate full coaching report |

---

## Use Cases

**Recreational Karting**
Drivers who race for fun but want to improve. PitLane AI gives them the same feedback a paid coach would, at zero cost per analysis.

**Competitive Junior Drivers**
Junior drivers in arrive-and-drive championships or rental kart series can review every lap between sessions and arrive at the next race with a concrete improvement plan.

**Karting Academies & Coaches**
Coaches can load an entire session's worth of onboard footage, run batch analysis, and prepare timestamped debrief notes for multiple drivers simultaneously — dramatically reducing post-session review time.

**Track Day Organizers**
Track operators can offer AI-powered lap review as a premium add-on service, providing participants with a coaching report after their session without needing a human engineer on site.

---

## Limitations & Notes

- Twelve Labs free tier: **50 analyze requests / day**. The 429 rate limit error is surfaced gracefully in the UI.
- Best results with clear, well-lit onboard footage where the road and driving line are visible.
- Coaching Report takes **30–60 seconds** due to the two-step Pegasus → Groq pipeline.

---

## Team

Built by **Northeastern University** students at the Voxel51 Hackathon, April 2026.

- [Pankhuri](https://github.com/pankhuri0209)
- Aditya Gulati
- Pridhi Balhara

---

## Feedback

Found a bug or have a feature request? [Open an issue on GitHub](https://github.com/pankhuri0209/NUPitlane-PitlaneAI/issues) or reach out directly.

---

*PitLane AI — because every driver deserves a race engineer.*
