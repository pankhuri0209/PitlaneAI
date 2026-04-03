"""
PitLane AI — FastAPI Backend
Wraps the three FiftyOne plugin operators as HTTP endpoints.
No FiftyOne dependency. Uses the Twelve Labs Python SDK directly.
"""

import os
import json
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
TWELVELABS_API_KEY = os.environ.get("TWELVELABS_API_KEY", "")
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY", "")

# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------

app = FastAPI(title="PitLane AI Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Twelve Labs client + index cache
# ---------------------------------------------------------------------------

_index_id_cache: Optional[str] = None


def _get_client():
    from twelvelabs import TwelveLabs
    if not TWELVELABS_API_KEY:
        raise HTTPException(status_code=500, detail="TWELVELABS_API_KEY not set.")
    return TwelveLabs(api_key=TWELVELABS_API_KEY)


def _get_index_id() -> str:
    global _index_id_cache
    if _index_id_cache:
        return _index_id_cache
    indexes = list(_get_client().indexes.list())
    if not indexes:
        raise HTTPException(status_code=500, detail="No Twelve Labs indexes found.")
    _index_id_cache = indexes[0].id
    return _index_id_cache


# ---------------------------------------------------------------------------
# Shared constants (verbatim from __init__.py)
# ---------------------------------------------------------------------------

BEST_MOMENT_QUERIES = [
    ("kart hitting apex smoothly on corner entry",  "🎯", "Smooth Apex"),
    ("smooth throttle acceleration out of corner",  "🚀", "Clean Acceleration"),
    ("kart at full speed on straight",              "⚡", "Fast Straight"),
    ("optimal racing line through corner",          "📐", "Perfect Racing Line"),
    ("controlled progressive braking before turn",  "🛑", "Smooth Braking"),
    ("impressive fast exciting driving moment",     "🏆", "Impressive Moment"),
]


def _fmt_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ErrorsRequest(BaseModel):
    video_id: str
    error_types: Optional[str] = "all driving errors"


class BestMomentsRequest(BaseModel):
    video_id: str


class AskRequest(BaseModel):
    video_id: str
    question: str


class CoachingReportRequest(BaseModel):
    video_id: str
    focus: Optional[str] = "Full Analysis"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/videos")
def list_videos():
    """List all videos from the Twelve Labs index."""
    try:
        client = _get_client()
        index_id = _get_index_id()
        raw = list(client.indexes.videos.list(index_id))
        videos = []
        for v in raw:
            video = client.indexes.videos.retrieve(index_id, v.id)
            filename = getattr(video, "filename", None) or f"{v.id}.mp4"
            videos.append({"id": v.id, "filename": filename})
        return {"videos": videos}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/errors")
def analyze_errors(body: ErrorsRequest):
    """Find lap errors using Pegasus."""
    try:
        client = _get_client()
        result = client.analyze(
            video_id=body.video_id,
            prompt=(
                "You are an expert go-kart race engineer reviewing onboard lap footage. "
                f"Identify every driving error, focusing on: {body.error_types}. "
                "Group errors into these categories: Racing Line, Braking, Throttle & Traction, Car Control.\n\n"
                "Output ONLY the following markdown, no extra text:\n\n"
                "### 🔴 Racing Line\n"
                "| Time | Error | Impact |\n"
                "|------|-------|--------|\n"
                "| MM:SS | error name | one-line impact |\n\n"
                "### 🟡 Braking\n"
                "| Time | Error | Impact |\n"
                "|------|-------|--------|\n"
                "| MM:SS | error name | one-line impact |\n\n"
                "### 🟠 Throttle & Traction\n"
                "| Time | Error | Impact |\n"
                "|------|-------|--------|\n"
                "| MM:SS | error name | one-line impact |\n\n"
                "### 🔵 Car Control\n"
                "| Time | Error | Impact |\n"
                "|------|-------|--------|\n"
                "| MM:SS | error name | one-line impact |\n\n"
                "Only include categories that have errors. End with: **Total errors found: N**"
            ),
        )
        return {"result": f"## 🏁 Lap Error Analysis\n\n{result.data}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/best-moments")
def analyze_best_moments(body: BestMomentsRequest):
    """Find best driving moments using Marengo semantic search."""
    try:
        client = _get_client()
        index_id = _get_index_id()
        rows = []

        for query, _icon, category in BEST_MOMENT_QUERIES:
            results = client.search.query(
                index_id=index_id,
                query_text=query,
                search_options=["visual"],
            )
            for clip in results:
                if clip.video_id == body.video_id:
                    rows.append({
                        "category": category,
                        "start": clip.start,
                        "end": clip.end,
                        "rank": clip.rank,
                    })

        if not rows:
            md = "## 🌟 Best Moments\n\n_No highlights found._"
        else:
            rows.sort(key=lambda c: c["start"])
            table = "\n".join(
                f"| {_fmt_time(c['start'])} – {_fmt_time(c['end'])} | {c['category']} | #{c['rank']} |"
                for c in rows
            )
            md = (
                f"## 🌟 Best Moments — {len(rows)} clip(s) found\n\n"
                f"| Timestamp | Category | Rank |\n"
                f"|-----------|----------|------|\n"
                f"{table}\n"
            )

        return {"result": md}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/ask")
def analyze_ask(body: AskRequest):
    """Ask anything about the lap using Pegasus."""
    try:
        client = _get_client()
        result = client.analyze(
            video_id=body.video_id,
            prompt=(
                f"You are an expert go-kart race engineer. Answer this question: {body.question}\n\n"
                "Format your response in markdown using EXACTLY this structure:\n\n"
                "### ✅ Verdict\n"
                "One bold sentence direct answer (yes/no + why).\n\n"
                "### 📍 Key Moments\n"
                "| Time | Observation |\n"
                "|------|-------------|\n"
                "| MM:SS | what is happening at this timestamp |\n\n"
                "### 💡 Recommendation\n"
                "One or two sentences on what to do differently or keep doing.\n\n"
                "Be concise, specific, and use racing terminology."
            ),
        )
        return {"result": f"## 💬 {body.question}\n\n{result.data}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/coaching-report")
def analyze_coaching_report(body: CoachingReportRequest):
    """Generate a full coaching report using Pegasus + Groq LLaMA (two-step pipeline)."""
    try:
        from groq import Groq

        if not GROQ_API_KEY:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY not set.")

        tl_client   = _get_client()
        groq_client = Groq(api_key=GROQ_API_KEY)

        focus_instruction = {
            "Full Analysis":        "Cover racing line, braking, throttle, and car control.",
            "Racing Line Only":     "Focus only on racing line and corner entry/exit.",
            "Braking Only":         "Focus only on braking points, trail braking, and stopping distances.",
            "Throttle & Exit Only": "Focus only on throttle application, wheelspin, and corner exits.",
        }.get(body.focus or "Full Analysis", "Cover racing line, braking, throttle, and car control.")

        # Step 1: Pegasus watches the full lap
        pegasus_result = tl_client.analyze(
            video_id=body.video_id,
            prompt=(
                "Watch this entire go-kart onboard lap carefully. "
                f"{focus_instruction} "
                "Describe in detail everything you observe every 30 seconds with timestamps (MM:SS). "
                "Be raw, factual, and detailed — this will be reviewed by a race engineer."
            ),
        )
        raw_observations = pegasus_result.data

        # Step 2: Groq extracts structured scores
        scores_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a data analyst. Extract numerical scores from lap observations. Respond with valid JSON only.",
                },
                {
                    "role": "user",
                    "content": (
                        f"From these go-kart lap observations, extract performance scores.\n\n"
                        f"{raw_observations}\n\n"
                        "Return JSON in exactly this format:\n"
                        '{"segments":[{"time":"0:00","racing_line":7,"braking":6,"throttle":8}],'
                        '"overall":{"racing_line":7,"braking":6,"throttle":8,"consistency":7}}'
                        "\nScore each metric 1-10. JSON only, no extra text."
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=800,
        )

        try:
            scores_text = scores_response.choices[0].message.content.strip()
            if "```" in scores_text:
                scores_text = scores_text.split("```")[1].lstrip("json").strip()
            scores_data = json.loads(scores_text)
            segments = scores_data.get("segments", [])
            overall  = scores_data.get("overall", {})
        except Exception:
            segments = []
            overall  = {"racing_line": 6, "braking": 6, "throttle": 6, "consistency": 6}

        rl = overall.get("racing_line", "?")
        br = overall.get("braking", "?")
        th = overall.get("throttle", "?")

        # Step 3: Groq writes the coaching report
        report_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional karting race engineer with 20 years experience. "
                        "Write precise, actionable coaching reports — data-driven, specific, no fluff."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Raw lap observations:\n{raw_observations}\n\n"
                        f"Performance scores by segment: {json.dumps(segments)}\n"
                        f"Overall scores: {json.dumps(overall)}\n\n"
                        f"Write a professional coaching report:\n\n"
                        f"## PERFORMANCE SUMMARY\n"
                        f"2-3 sentences overall assessment.\n\n"
                        f"## RACING LINE  (score: {rl}/10)\n"
                        f"- Specific observations with timestamps\n\n"
                        f"## BRAKING POINTS  (score: {br}/10)\n"
                        f"- Specific observations with timestamps\n\n"
                        f"## THROTTLE & EXIT SPEED  (score: {th}/10)\n"
                        f"- Specific observations with timestamps\n\n"
                        f"## LAP TIME LOSSES\n"
                        f"Estimate time lost per sector in tenths of seconds.\n\n"
                        f"## TOP 3 PRIORITY IMPROVEMENTS\n"
                        f"1. [Specific corner + timestamp + what to do differently]\n"
                        f"2.\n"
                        f"3.\n\n"
                        f"## OVERALL RATING: X/10\n"
                        f"Biggest strength: ...\n"
                        f"Biggest weakness: ..."
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=1200,
        )
        report = report_response.choices[0].message.content

        return {
            "result": report,
            "segments": segments,
            "overall": overall,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
