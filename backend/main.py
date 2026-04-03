"""
PitLane AI — FastAPI Backend
Wraps the three FiftyOne plugin operators as HTTP endpoints.
No FiftyOne dependency. Uses the Twelve Labs Python SDK directly.
"""

import os
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
