"""
PitLane AI — Go-Kart Video Analysis FiftyOne Plugin
Powered by Twelve Labs (Marengo + Pegasus) + Groq LLaMA
"""

import os
import json
from dotenv import load_dotenv
import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
TWELVELABS_API_KEY = os.environ.get("TWELVELABS_API_KEY", "")
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY", "")

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
    video_id = None
    for field in ("twelvelabs_video_id", "tl_video_id"):
        try:
            video_id = sample.get_field(field)
            if video_id:
                break
        except AttributeError:
            continue
    if not video_id:
        raise ValueError(
            "No Twelve Labs video ID on this sample. "
            "Re-run dataset.py to sync with your Twelve Labs index."
        )
    return video_id


def _fmt_time(seconds):
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


# ---------------------------------------------------------------------------
# Operator 1 — Find Lap Errors (Pankhuri)
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
                "### Racing Line\n"
                "| Time | Error | Impact |\n"
                "|------|-------|--------|\n"
                "| MM:SS | error name | one-line impact |\n\n"
                "### Braking\n"
                "| Time | Error | Impact |\n"
                "|------|-------|--------|\n"
                "| MM:SS | error name | one-line impact |\n\n"
                "### Throttle & Traction\n"
                "| Time | Error | Impact |\n"
                "|------|-------|--------|\n"
                "| MM:SS | error name | one-line impact |\n\n"
                "### Car Control\n"
                "| Time | Error | Impact |\n"
                "|------|-------|--------|\n"
                "| MM:SS | error name | one-line impact |\n\n"
                "Only include categories that have errors. End with: **Total errors found: N**"
            ),
        )

        ctx.set_progress(1.0, label="Done")
        md = f"## Lap Error Analysis\n\n{result.data}"
        return {"errors": md}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("errors", label="Lap Errors", view=types.MarkdownView(read_only=True))
        return types.Property(outputs)


# ---------------------------------------------------------------------------
# Operator 2 — Find Best Moments (Pankhuri)
# ---------------------------------------------------------------------------

BEST_MOMENT_QUERIES = [
    ("kart hitting apex smoothly on corner entry",   "Smooth Apex"),
    ("smooth throttle acceleration out of corner",   "Clean Acceleration"),
    ("kart at full speed on straight",               "Fast Straight"),
    ("optimal racing line through corner",           "Perfect Racing Line"),
    ("controlled progressive braking before turn",   "Smooth Braking"),
    ("impressive fast exciting driving moment",      "Impressive Moment"),
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
        client   = _get_client()
        index_id = _get_index_id()
        total    = len(BEST_MOMENT_QUERIES)

        # Build video_id → sample map (supports both field names)
        vid_to_sample = {}
        for s in ctx.dataset:
            for field in ("twelvelabs_video_id", "tl_video_id"):
                try:
                    vid = s.get_field(field)
                    if vid:
                        vid_to_sample[vid] = s
                        break
                except AttributeError:
                    continue

        clips_by_vid = {vid: [] for vid in vid_to_sample}

        for i, (query, category) in enumerate(BEST_MOMENT_QUERIES):
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
                        "start":    clip.start,
                        "end":      clip.end,
                        "rank":     clip.rank,
                    })

        ctx.set_progress(0.9, label="Saving clips to timeline...")

        summary_rows = []
        for vid_id, clips in clips_by_vid.items():
            if not clips:
                continue
            sample = vid_to_sample[vid_id]
            fps = 30.0
            if sample.metadata and hasattr(sample.metadata, "frame_rate"):
                fps = sample.metadata.frame_rate or 30.0

            detections = []
            for c in clips:
                sf = max(1, int(c["start"] * fps))
                ef = max(sf + 1, int(c["end"] * fps))
                detections.append(fo.TemporalDetection(
                    label=c["category"],
                    support=[sf, ef],
                ))
                summary_rows.append({**c, "video_id": vid_id})

            sample["best_moments"] = fo.TemporalDetections(detections=detections)
            sample.save()

        ctx.set_progress(1.0, label="Done")
        ctx.trigger("reload_dataset")

        if not summary_rows:
            md = "## Best Moments\n\n_No highlights found._"
        else:
            summary_rows.sort(key=lambda c: c["start"])
            rows = "\n".join(
                f"| {_fmt_time(c['start'])} - {_fmt_time(c['end'])} | {c['category']} | #{c['rank']} |"
                for c in summary_rows
            )
            md = (
                f"## Best Moments — {len(summary_rows)} clip(s) saved to timeline\n\n"
                f"| Timestamp | Category | Rank |\n"
                f"|-----------|----------|------|\n"
                f"{rows}\n\n"
                f"_Clips are now visible as colored segments on the video timeline._"
            )

        return {"highlights": md}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("highlights", label="Best Moments", view=types.MarkdownView(read_only=True))
        return types.Property(outputs)


# ---------------------------------------------------------------------------
# Operator 3 — Ask Anything (Pankhuri)
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
            description="e.g. 'Was my racing line through Turn 3 correct?'",
            required=True,
        )
        return types.Property(inputs)

    def execute(self, ctx):
        question = ctx.params.get("question", "")
        video_id = _get_video_id(ctx)
        client   = _get_client()

        ctx.set_progress(0.3, label="Asking Pegasus...")
        result = client.analyze(
            video_id=video_id,
            prompt=(
                f"You are an expert go-kart race engineer. Answer this question: {question}\n\n"
                "Format your response in markdown using EXACTLY this structure:\n\n"
                "### Verdict\n"
                "One bold sentence direct answer.\n\n"
                "### Key Moments\n"
                "| Time | Observation |\n"
                "|------|-------------|\n"
                "| MM:SS | what is happening |\n\n"
                "### Recommendation\n"
                "One or two sentences on what to do differently.\n\n"
                "Be concise, specific, and use racing terminology."
            ),
        )

        ctx.set_progress(1.0, label="Done")
        md = f"## {question}\n\n{result.data}"
        return {"answer": md}

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("answer", label="Answer", view=types.MarkdownView(read_only=True))
        return types.Property(outputs)


# ---------------------------------------------------------------------------
# Operator 4 — Generate Coaching Report (Aditya)
# Pegasus watches the lap → Groq LLaMA writes a telemetry-style report + graphs
# ---------------------------------------------------------------------------

class GenerateCoachingReport(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="generate_coaching_report",
            label="Generate Coaching Report",
            description=(
                "Two-step AI coaching: Pegasus watches the full lap, "
                "then Groq LLaMA 3.3 writes a professional telemetry report with performance graphs."
            ),
        )

    def execute(self, ctx):
        from groq import Groq

        ctx.set_progress(0.05, label="Loading video...")
        video_id    = _get_video_id(ctx)
        tl_client   = _get_client()
        groq_client = Groq(api_key=GROQ_API_KEY)

        # ── Step 1: Pegasus watches the full lap ──────────────────────────
        ctx.set_progress(0.15, label="Step 1/3 — Pegasus analyzing lap footage...")
        pegasus_result = tl_client.analyze(
            video_id=video_id,
            prompt=(
                "Watch this entire go-kart onboard lap carefully. "
                "Describe in detail everything you observe about the driver's technique every 30 seconds. "
                "For each segment cover: racing line (correct/wide/tight), "
                "braking points (early/late/correct), throttle application (smooth/wheelspin/early), "
                "and any notable mistakes or impressive moments. "
                "Include specific timestamps (MM:SS). Be raw, factual, and detailed."
            ),
        )
        raw_observations = pegasus_result.data
        print(f"[PitLane AI] Pegasus: {raw_observations[:200]}...")

        # ── Step 2: Groq extracts structured scores per segment ───────────
        ctx.set_progress(0.45, label="Step 2/3 — Extracting performance scores...")
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
                        "Return JSON in exactly this format (one segment per 30 seconds):\n"
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
        except Exception as e:
            print(f"[PitLane AI] Score parse error: {e}")
            segments = []
            overall  = {"racing_line": 6, "braking": 6, "throttle": 6, "consistency": 6}

        rl = overall.get("racing_line", "?")
        br = overall.get("braking", "?")
        th = overall.get("throttle", "?")

        # ── Step 3: Groq writes the coaching report ───────────────────────
        ctx.set_progress(0.7, label="Step 3/3 — Writing coaching report...")
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

        # ── Build Plotly charts ───────────────────────────────────────────
        times = [s.get("time", f"{i*30}s") for i, s in enumerate(segments)]

        line_chart = {
            "data": [
                {"x": times, "y": [s.get("racing_line", 5) for s in segments],
                 "type": "scatter", "mode": "lines+markers", "name": "Racing Line",
                 "line": {"color": "#00C851", "width": 3}},
                {"x": times, "y": [s.get("braking", 5) for s in segments],
                 "type": "scatter", "mode": "lines+markers", "name": "Braking",
                 "line": {"color": "#FF4444", "width": 3}},
                {"x": times, "y": [s.get("throttle", 5) for s in segments],
                 "type": "scatter", "mode": "lines+markers", "name": "Throttle",
                 "line": {"color": "#FFBB33", "width": 3}},
            ],
            "layout": {
                "title": "Performance Over Lap",
                "xaxis": {"title": "Timestamp"},
                "yaxis": {"title": "Score (1-10)", "range": [0, 10]},
                "height": 350,
                "paper_bgcolor": "#1a1a1a",
                "plot_bgcolor": "#1a1a1a",
                "font": {"color": "white"},
            },
        }

        radar_chart = {
            "data": [{
                "type": "scatterpolar",
                "r": [
                    overall.get("racing_line", 5),
                    overall.get("braking", 5),
                    overall.get("throttle", 5),
                    overall.get("consistency", 5),
                    overall.get("racing_line", 5),
                ],
                "theta": ["Racing Line", "Braking", "Throttle", "Consistency", "Racing Line"],
                "fill": "toself",
                "fillcolor": "rgba(0, 200, 81, 0.3)",
                "line": {"color": "#00C851"},
                "name": "Driver Profile",
            }],
            "layout": {
                "title": "Driver Skill Radar",
                "polar": {
                    "radialaxis": {"range": [0, 10], "color": "white"},
                    "angularaxis": {"color": "white"},
                    "bgcolor": "#1a1a1a",
                },
                "height": 350,
                "paper_bgcolor": "#1a1a1a",
                "font": {"color": "white"},
            },
        }

        ctx.set_progress(1.0, label="Done!")
        return {
            "report":      report,
            "line_chart":  line_chart,
            "radar_chart": radar_chart,
        }

    def resolve_output(self, ctx):
        outputs = types.Object()
        outputs.str("report", label="Coaching Report", view=types.MarkdownView(read_only=True))
        outputs.plot("line_chart",  label="Performance Over Lap")
        outputs.plot("radar_chart", label="Driver Skill Radar")
        return types.Property(outputs)


# ---------------------------------------------------------------------------
# Register all operators
# ---------------------------------------------------------------------------

def register(plugin):
    plugin.register(FindLapErrors)
    plugin.register(FindBestMoments)
    plugin.register(AskAnything)
    plugin.register(GenerateCoachingReport)
