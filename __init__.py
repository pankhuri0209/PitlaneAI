"""
PitLane AI — Go-Kart Video Analysis FiftyOne Plugin
Powered by Twelve Labs (Marengo + Pegasus)
"""

import os
from dotenv import load_dotenv
import fiftyone.operators as foo
import fiftyone.operators.types as types

load_dotenv()
TWELVELABS_API_KEY = os.environ.get("TWELVELABS_API_KEY", "")

_index_id_cache = None


def _get_client():
    from twelvelabs import TwelveLabs
    return TwelveLabs(api_key=TWELVELABS_API_KEY)


def _get_index_id():
    global _index_id_cache
    if _index_id_cache:
        return _index_id_cache
    client = _get_client()
    indexes = list(client.indexes.list())
    if not indexes:
        raise RuntimeError("No indexes found for this API key.")
    _index_id_cache = indexes[0].id
    return _index_id_cache


def _get_video_id(ctx):
    """Get the Twelve Labs video_id from the current sample."""
    sample = ctx.dataset[ctx.current_sample]
    video_id = sample.get_field("twelvelabs_video_id")
    if not video_id:
        raise ValueError(
            "No 'twelvelabs_video_id' on this sample. "
            "Re-run dataset.py to sync with your Twelve Labs index."
        )
    return video_id


# ---------------------------------------------------------------------------
# Operator 1 — Find Lap Errors (Pegasus)
# ---------------------------------------------------------------------------

class FindLapErrors(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="find_lap_errors",
            label="Find Lap Errors",
            description="Detect every driving mistake in this lap with timestamps using Pegasus",
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str(
            "error_types",
            label="Error types to look for (optional)",
            description="e.g. 'missed apex, late braking, understeer, wheelspin, wide exit'",
            default="all driving errors",
            required=False,
        )
        return types.Property(inputs)

    def execute(self, ctx):
        error_types = ctx.params.get("error_types", "all driving errors")
        video_id = _get_video_id(ctx)
        client = _get_client()

        ctx.set_progress(0.3, label="Scanning for errors with Pegasus...")
        result = client.analyze(
            video_id=video_id,
            prompt=(
                "You are an expert go-kart race engineer reviewing onboard lap footage. "
                f"Identify every driving error in this video, focusing on: {error_types}. "
                "For each error found, output exactly this format:\n"
                "- [MM:SS] ERROR TYPE: one-sentence description of what went wrong and why it costs time.\n\n"
                "Errors to detect: missed apex, early apex, late braking, early braking, "
                "understeer, oversteer, wheelspin on exit, poor throttle application, "
                "wide entry, wide exit, wrong racing line, late turn-in, early turn-in. "
                "List every error ordered by timestamp. Be specific and concise."
            ),
        )

        ctx.set_progress(1.0, label="Done")
        return {"errors": result.data}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("errors", label="Lap Errors")
        return types.Property(outputs)


# ---------------------------------------------------------------------------
# Operator 2 — Technique Search (Marengo)
# ---------------------------------------------------------------------------

class TechniqueSearch(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="technique_search",
            label="Search Driving Technique",
            description="Find specific moments using Marengo semantic search across all indexed videos",
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str(
            "query",
            label="Search query",
            description="e.g. 'understeer', 'late apex', 'early braking', 'wheel spin'",
            required=True,
        )
        inputs.float(
            "threshold",
            label="Confidence threshold (0-1)",
            default=0.5,
            required=False,
        )
        return types.Property(inputs)

    def execute(self, ctx):
        query = ctx.params.get("query", "")
        threshold = ctx.params.get("threshold", 0.5)
        client = _get_client()

        ctx.set_progress(0.3, label=f"Searching for '{query}'...")
        results = client.search.query(
            index_id=_get_index_id(),
            query_text=query,
            options=["visual", "audio"],
            threshold=threshold,
        )

        clips = []
        for page in results:
            for clip in page.data:
                clips.append({
                    "start": round(clip.start, 2),
                    "end": round(clip.end, 2),
                    "score": round(clip.score, 3),
                    "video_id": clip.video_id,
                })

        ctx.set_progress(1.0, label="Done")
        return {
            "query": query,
            "clip_count": len(clips),
            "clips": str(clips),
        }

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("query", label="Query")
        outputs.int("clip_count", label="Clips found")
        outputs.str("clips", label="Matched clips (start/end seconds + score)")
        return types.Property(outputs)


# ---------------------------------------------------------------------------
# Operator 3 — Ask Anything (Pegasus QA)
# ---------------------------------------------------------------------------

class AskAnything(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="ask_anything",
            label="Ask About This Lap",
            description="Ask any question about this lap video using Pegasus",
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.str(
            "question",
            label="Your question",
            description="e.g. 'Was my racing line through Turn 3 correct?' or 'Where am I losing the most time?'",
            required=True,
        )
        return types.Property(inputs)

    def execute(self, ctx):
        question = ctx.params.get("question", "")
        video_id = _get_video_id(ctx)
        client = _get_client()

        ctx.set_progress(0.3, label="Asking Pegasus...")
        result = client.analyze(
            video_id=video_id,
            prompt=(
                f"You are an expert go-kart race engineer. "
                f"Answer this question about the lap video with specific timestamps where relevant: {question}"
            ),
        )

        ctx.set_progress(1.0, label="Done")
        return {"answer": result.data}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("answer", label="Answer")
        return types.Property(outputs)


# ---------------------------------------------------------------------------
# Register operators
# ---------------------------------------------------------------------------

def register(plugin):
    plugin.register(FindLapErrors)
    plugin.register(TechniqueSearch)
    plugin.register(AskAnything)
