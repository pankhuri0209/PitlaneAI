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
                f"Identify every driving error, focusing on: {error_types}. "
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

        ctx.set_progress(1.0, label="Done")
        md = f"## 🏁 Lap Error Analysis\n\n{result.data}"
        return {"errors": md}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str(
            "errors",
            label="Lap Errors",
            view=types.MarkdownView(read_only=True),
        )
        return types.Property(outputs)


# ---------------------------------------------------------------------------
# Operator 2 — Find Best Moments (Marengo)
# ---------------------------------------------------------------------------

BEST_MOMENT_QUERIES = [
    ("kart hitting apex smoothly on corner entry",       "🎯", "Smooth Apex"),
    ("smooth throttle acceleration out of corner",       "🚀", "Clean Acceleration"),
    ("kart at full speed on straight",                   "⚡", "Fast Straight"),
    ("optimal racing line through corner",               "📐", "Perfect Racing Line"),
    ("controlled progressive braking before turn",       "🛑", "Smooth Braking"),
    ("impressive fast exciting driving moment",          "🏆", "Impressive Moment"),
]

class FindBestMoments(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="find_best_moments",
            label="Find Best Moments",
            description="Highlight the best driving moments in this lap using Marengo",
        )

    def resolve_input(self, ctx):
        inputs = types.Object()
        inputs.float(
            "threshold",
            label="Confidence threshold (0-1)",
            description="Lower = more results, Higher = only strong matches",
            default=0.5,
            required=False,
        )
        return types.Property(inputs)

    def execute(self, ctx):
        import fiftyone as fo

        client = _get_client()
        index_id = _get_index_id()
        total = len(BEST_MOMENT_QUERIES)

        # Build a map: twelvelabs_video_id -> FiftyOne sample
        vid_to_sample = {
            s["twelvelabs_video_id"]: s
            for s in ctx.dataset
            if s.get_field("twelvelabs_video_id")
        }

        # Collect clips per video_id
        clips_by_vid = {vid: [] for vid in vid_to_sample}

        for i, (query, icon, category) in enumerate(BEST_MOMENT_QUERIES):
            ctx.set_progress((i + 1) / total * 0.85, label=f"Searching: {category}...")
            results = client.search.query(
                index_id=index_id,
                query_text=query,
                search_options=["visual"],
            )
            for clip in results:
                if clip.video_id in clips_by_vid:
                    clips_by_vid[clip.video_id].append({
                        "category": category,
                        "start": clip.start,
                        "end": clip.end,
                        "rank": clip.rank,
                    })

        ctx.set_progress(0.9, label="Saving clips to timeline...")

        # Save TemporalDetections onto each sample
        summary_rows = []
        for vid_id, clips in clips_by_vid.items():
            if not clips:
                continue
            sample = vid_to_sample[vid_id]
            fps = sample.get_field("metadata.frame_rate") or 30.0

            detections = []
            for c in clips:
                start_frame = max(1, int(c["start"] * fps))
                end_frame   = max(start_frame + 1, int(c["end"] * fps))
                detections.append(fo.TemporalDetection(
                    label=c["category"],
                    support=[start_frame, end_frame],
                ))
                summary_rows.append({**c, "video_id": vid_id})

            sample["best_moments"] = fo.TemporalDetections(detections=detections)
            sample.save()

        ctx.set_progress(1.0, label="Done")
        ctx.trigger("reload_dataset")

        if not summary_rows:
            md = "## 🌟 Best Moments\n\n_No highlights found._"
        else:
            summary_rows.sort(key=lambda c: c["start"])
            rows = "\n".join(
                f"| {_fmt_time(c['start'])} – {_fmt_time(c['end'])} "
                f"| {c['category']} "
                f"| #{c['rank']} |"
                for c in summary_rows
            )
            md = (
                f"## 🌟 Best Moments — {len(summary_rows)} clip(s) saved to timeline\n\n"
                f"| Timestamp | Category | Rank |\n"
                f"|-----------|----------|------|\n"
                f"{rows}\n\n"
                f"_Clips are now visible as colored segments on the video timeline._"
            )

        return {"highlights": md}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str(
            "highlights",
            label="Best Moments",
            view=types.MarkdownView(read_only=True),
        )
        return types.Property(outputs)


def _fmt_time(seconds):
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


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
                f"You are an expert go-kart race engineer. Answer this question: {question}\n\n"
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

        ctx.set_progress(1.0, label="Done")
        md = f"## 💬 {question}\n\n{result.data}"
        return {"answer": md}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str(
            "answer",
            label="Answer",
            view=types.MarkdownView(read_only=True),
        )
        return types.Property(outputs)


# ---------------------------------------------------------------------------
# Register operators
# ---------------------------------------------------------------------------

def register(plugin):
    plugin.register(FindLapErrors)
    plugin.register(FindBestMoments)
    plugin.register(AskAnything)
