"""
PitLane AI — Unified Go-Kart Coaching Hub
Single operator with menu-driven flow: choose an analysis, run it, return to menu.
"""

import os
import re
import json
from dotenv import load_dotenv
import fiftyone as fo
import fiftyone.operators as foo
import fiftyone.operators.types as types

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(_PLUGIN_DIR, "..", ".env"))
TWELVELABS_API_KEY = os.environ.get("TWELVELABS_API_KEY", "")
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY", "")

_index_id_cache = None

# Analysis fields managed by this plugin (used by Clear All Analyses)
_ANALYSIS_FIELDS = ["lap_errors", "best_moments", "ask_moments", "coaching_moments"]

BEST_MOMENT_QUERIES = [
    ("kart hitting apex smoothly on corner entry",  "Smooth Apex"),
    ("smooth throttle acceleration out of corner",  "Clean Acceleration"),
    ("kart at full speed on straight",              "Fast Straight"),
    ("optimal racing line through corner",          "Perfect Racing Line"),
    ("controlled progressive braking before turn",  "Smooth Braking"),
    ("impressive fast exciting driving moment",     "Impressive Moment"),
]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

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
        raise ValueError("No Twelve Labs video ID on this sample.")
    return video_id


def _get_fps(sample):
    if sample.metadata and hasattr(sample.metadata, "frame_rate"):
        return sample.metadata.frame_rate or 30.0
    return 30.0


def _fmt_time(seconds):
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


def _parse_clips_from_markdown(text, fps, clip_duration=7):
    """Parse MM:SS timestamps from markdown and return TemporalDetection list."""
    detections = []
    current_label = "Moment"
    seen = set()
    for line in text.splitlines():
        header = re.match(r"^#{1,3}\s+(.+)", line)
        if header:
            raw = header.group(1).strip()
            current_label = re.sub(r"[^\w\s&-]", "", raw).strip()
            continue
        for m, s in re.findall(r"\b(\d{1,2}):(\d{2})\b", line):
            start_sec = int(m) * 60 + int(s)
            key = (current_label, start_sec)
            if key in seen:
                continue
            seen.add(key)
            sf = max(1, int(start_sec * fps))
            ef = max(sf + 1, int((start_sec + clip_duration) * fps))
            detections.append(fo.TemporalDetection(label=current_label, support=[sf, ef]))
    return detections


def _save_timeline_clips(ctx, text, field_name, fps, clip_duration=7):
    sample = ctx.dataset[ctx.current_sample]
    detections = _parse_clips_from_markdown(text, fps, clip_duration)
    if detections:
        sample[field_name] = fo.TemporalDetections(detections=detections)
        sample.save()
        ctx.trigger("reload_dataset")
    return len(detections)


# ---------------------------------------------------------------------------
# Unified Operator — PitLane AI Hub
# ---------------------------------------------------------------------------

class PitLaneAI(foo.Operator):
    @property
    def config(self):
        return foo.OperatorConfig(
            name="pitlane_ai",
            label="PitLane AI",
            description="Go-kart coaching hub — choose an analysis and get instant AI feedback",
        )

    # ── Inputs: menu dropdown + dynamic per-operation fields ────────────────

    def resolve_input(self, ctx):
        inputs = types.Object()

        # Phase 1: Operation selector
        choices = types.Choices()
        choices.add_choice("find_lap_errors",   label="Find Lap Errors")
        choices.add_choice("find_best_moments", label="Find Best Moments")
        choices.add_choice("ask_anything",      label="Ask About This Lap")
        choices.add_choice("coaching_report",   label="Generate Coaching Report")
        choices.add_choice("clear_history",     label="Clear All Analyses")

        inputs.enum(
            "operation",
            values=choices.values(),
            label="Choose Analysis",
            description="Select which analysis to run on this lap",
            view=choices,
        )

        # Phase 2: Operation-specific inputs (appear after selection)
        op = ctx.params.get("operation")

        if op == "find_lap_errors":
            inputs.view("notice", view=types.Notice(
                label="Pegasus will scan the full lap and save every error as a clip on the timeline."
            ))

        elif op == "find_best_moments":
            inputs.view("notice", view=types.Notice(
                label="Marengo will search all videos for 6 categories of best moments and save them to the timeline."
            ))

        elif op == "ask_anything":
            inputs.str(
                "question",
                label="Your question",
                description="e.g. 'Was my racing line through Turn 3 correct?'",
                required=True,
            )

        elif op == "coaching_report":
            inputs.view("notice", view=types.Notice(
                label="Takes 30-60 seconds. Pegasus analyzes the full lap, then Groq LLaMA writes a report with performance graphs."
            ))
            inputs.enum(
                "focus",
                values=["Full Analysis", "Racing Line Only", "Braking Only", "Throttle & Exit Only"],
                label="Analysis Focus",
                default="Full Analysis",
                view=types.DropdownView(),
            )

        elif op == "clear_history":
            inputs.view("notice", view=types.Notice(
                label="This will clear all analysis results (lap errors, best moments, ask moments, coaching moments) from every video in the dataset."
            ))

        return types.Property(inputs)

    # ── Execute: route to the chosen analysis ───────────────────────────────

    def execute(self, ctx):
        op = ctx.params.get("operation")
        if op == "find_lap_errors":   return self._find_lap_errors(ctx)
        if op == "find_best_moments": return self._find_best_moments(ctx)
        if op == "ask_anything":      return self._ask_anything(ctx)
        if op == "coaching_report":   return self._coaching_report(ctx)
        if op == "clear_history":     return self._clear_history(ctx)
        return {"result": "_No operation selected._"}

    # ── Outputs: dynamic based on chosen operation ───────────────────────────

    def resolve_output(self, ctx):
        outputs = types.Object()
        op = ctx.params.get("operation")

        if op == "find_lap_errors":
            outputs.str("errors", label="Lap Errors",
                        view=types.MarkdownView(read_only=True))

        elif op == "find_best_moments":
            outputs.str("highlights", label="Best Moments",
                        view=types.MarkdownView(read_only=True))

        elif op == "ask_anything":
            outputs.str("answer", label="Answer",
                        view=types.MarkdownView(read_only=True))

        elif op == "coaching_report":
            outputs.str("report", label="Coaching Report",
                        view=types.MarkdownView(read_only=True))
            outputs.plot("line_chart",  label="Performance Over Lap")
            outputs.plot("radar_chart", label="Driver Skill Radar")

        elif op == "clear_history":
            outputs.str("status", label="Result",
                        view=types.MarkdownView(read_only=True))

        else:
            outputs.str("result", label="Result",
                        view=types.MarkdownView(read_only=True))

        return types.Property(outputs)

    # ── Private: Find Lap Errors ─────────────────────────────────────────────

    def _find_lap_errors(self, ctx):
        video_id = _get_video_id(ctx)
        client   = _get_client()
        sample   = ctx.dataset[ctx.current_sample]
        fps      = _get_fps(sample)

        ctx.set_progress(0.3, label="Scanning for errors with Pegasus...")
        result = client.analyze(
            video_id=video_id,
            prompt=(
                "You are an expert go-kart race engineer reviewing onboard lap footage. "
                "Identify every driving error. "
                "Group errors into: Racing Line, Braking, Throttle & Traction, Car Control.\n\n"
                "Output ONLY markdown:\n\n"
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
                "Only include categories with errors. End with: **Total errors found: N**"
            ),
        )

        ctx.set_progress(0.9, label="Saving error clips to timeline...")
        n = _save_timeline_clips(ctx, result.data, "lap_errors", fps)

        ctx.set_progress(1.0, label="Done")
        return {"errors": f"## Lap Error Analysis — {n} clip(s) on timeline\n\n{result.data}\n\n_Error clips visible on video timeline._"}

    # ── Private: Find Best Moments ───────────────────────────────────────────

    def _find_best_moments(self, ctx):
        client   = _get_client()
        index_id = _get_index_id()
        total    = len(BEST_MOMENT_QUERIES)

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
                        "start": clip.start,
                        "end":   clip.end,
                        "rank":  clip.rank,
                    })

        ctx.set_progress(0.9, label="Saving clips to timeline...")
        summary_rows = []
        for vid_id, clips in clips_by_vid.items():
            if not clips:
                continue
            sample = vid_to_sample[vid_id]
            fps = _get_fps(sample)
            detections = []
            for c in clips:
                sf = max(1, int(c["start"] * fps))
                ef = max(sf + 1, int(c["end"] * fps))
                detections.append(fo.TemporalDetection(label=c["category"], support=[sf, ef]))
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
                f"_Clips visible as colored segments on the video timeline._"
            )
        return {"highlights": md}

    # ── Private: Ask Anything ────────────────────────────────────────────────

    def _ask_anything(self, ctx):
        question = ctx.params.get("question", "")
        video_id = _get_video_id(ctx)
        client   = _get_client()
        sample   = ctx.dataset[ctx.current_sample]
        fps      = _get_fps(sample)

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

        ctx.set_progress(0.85, label="Saving timestamps to timeline...")
        n = _save_timeline_clips(ctx, result.data, "ask_moments", fps)

        ctx.set_progress(1.0, label="Done")
        return {"answer": f"## {question}\n\n{result.data}\n\n_Saved {n} timestamp clip(s) to timeline._"}

    # ── Private: Generate Coaching Report ────────────────────────────────────

    def _coaching_report(self, ctx):
        from groq import Groq

        focus       = ctx.params.get("focus", "Full Analysis")
        video_id    = _get_video_id(ctx)
        tl_client   = _get_client()
        groq_client = Groq(api_key=GROQ_API_KEY)
        sample      = ctx.dataset[ctx.current_sample]
        fps         = _get_fps(sample)

        focus_instruction = {
            "Full Analysis":        "Cover racing line, braking, throttle, and car control.",
            "Racing Line Only":     "Focus only on racing line and corner entry/exit.",
            "Braking Only":         "Focus only on braking points, trail braking, and stopping distances.",
            "Throttle & Exit Only": "Focus only on throttle application, wheelspin, and corner exits.",
        }.get(focus, "Cover racing line, braking, throttle, and car control.")

        ctx.set_progress(0.15, label="Step 1/3 — Pegasus analyzing lap footage...")
        pegasus_result = tl_client.analyze(
            video_id=video_id,
            prompt=(
                "Watch this entire go-kart onboard lap carefully. "
                f"{focus_instruction} "
                "Describe everything you observe every 30 seconds with timestamps (MM:SS). "
                "Be raw, factual, and detailed."
            ),
        )
        raw_observations = pegasus_result.data

        ctx.set_progress(0.45, label="Step 2/3 — Extracting performance scores...")
        scores_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a data analyst. Extract numerical scores from lap observations. Respond with valid JSON only."},
                {"role": "user", "content": (
                    f"From these go-kart lap observations, extract performance scores.\n\n"
                    f"{raw_observations}\n\n"
                    "Return JSON in exactly this format:\n"
                    '{"segments":[{"time":"0:00","racing_line":7,"braking":6,"throttle":8}],'
                    '"overall":{"racing_line":7,"braking":6,"throttle":8,"consistency":7}}'
                    "\nScore each metric 1-10. JSON only, no extra text."
                )},
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

        ctx.set_progress(0.7, label="Step 3/3 — Writing coaching report...")
        report_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional karting race engineer with 20 years experience. Write precise, actionable coaching reports."},
                {"role": "user", "content": (
                    f"Raw lap observations:\n{raw_observations}\n\n"
                    f"Performance scores by segment: {json.dumps(segments)}\n"
                    f"Overall scores: {json.dumps(overall)}\n\n"
                    f"Write a professional coaching report:\n\n"
                    f"## PERFORMANCE SUMMARY\n2-3 sentences overall assessment.\n\n"
                    f"## RACING LINE  (score: {rl}/10)\n- Specific observations with timestamps\n\n"
                    f"## BRAKING POINTS  (score: {br}/10)\n- Specific observations with timestamps\n\n"
                    f"## THROTTLE & EXIT SPEED  (score: {th}/10)\n- Specific observations with timestamps\n\n"
                    f"## LAP TIME LOSSES\nEstimate time lost per sector in tenths of seconds.\n\n"
                    f"## TOP 3 PRIORITY IMPROVEMENTS\n1. [Specific corner + timestamp + what to do differently]\n2.\n3.\n\n"
                    f"## OVERALL RATING: X/10\nBiggest strength: ...\nBiggest weakness: ..."
                )},
            ],
            temperature=0.3,
            max_tokens=1200,
        )
        report = report_response.choices[0].message.content

        ctx.set_progress(0.9, label="Saving timestamps to timeline...")
        n = _save_timeline_clips(ctx, report, "coaching_moments", fps)

        times = [s.get("time", f"{i*30}s") for i, s in enumerate(segments)]
        line_chart = {
            "data": [
                {"x": times, "y": [s.get("racing_line", 5) for s in segments], "type": "scatter", "mode": "lines+markers", "name": "Racing Line", "line": {"color": "#00C851", "width": 3}},
                {"x": times, "y": [s.get("braking", 5) for s in segments],     "type": "scatter", "mode": "lines+markers", "name": "Braking",      "line": {"color": "#FF4444", "width": 3}},
                {"x": times, "y": [s.get("throttle", 5) for s in segments],    "type": "scatter", "mode": "lines+markers", "name": "Throttle",     "line": {"color": "#FFBB33", "width": 3}},
            ],
            "layout": {"title": "Performance Over Lap", "xaxis": {"title": "Timestamp"}, "yaxis": {"title": "Score (1-10)", "range": [0, 10]}, "height": 350, "paper_bgcolor": "#1a1a1a", "plot_bgcolor": "#1a1a1a", "font": {"color": "white"}},
        }
        radar_chart = {
            "data": [{"type": "scatterpolar", "r": [overall.get("racing_line", 5), overall.get("braking", 5), overall.get("throttle", 5), overall.get("consistency", 5), overall.get("racing_line", 5)], "theta": ["Racing Line", "Braking", "Throttle", "Consistency", "Racing Line"], "fill": "toself", "fillcolor": "rgba(0,200,81,0.3)", "line": {"color": "#00C851"}, "name": "Driver Profile"}],
            "layout": {"title": "Driver Skill Radar", "polar": {"radialaxis": {"range": [0, 10], "color": "white"}, "angularaxis": {"color": "white"}, "bgcolor": "#1a1a1a"}, "height": 350, "paper_bgcolor": "#1a1a1a", "font": {"color": "white"}},
        }

        ctx.set_progress(1.0, label="Done!")
        return {
            "report":      report + f"\n\n_Saved {n} timestamp clip(s) to timeline._",
            "line_chart":  line_chart,
            "radar_chart": radar_chart,
        }

    # ── Private: Clear All Analyses ──────────────────────────────────────────

    def _clear_history(self, ctx):
        cleared = 0
        for sample in ctx.dataset:
            changed = False
            for field in _ANALYSIS_FIELDS:
                try:
                    if sample.get_field(field) is not None:
                        sample[field] = None
                        changed = True
                except Exception:
                    pass
            if changed:
                sample.save()
                cleared += 1
        ctx.trigger("reload_dataset")
        return {"status": f"## Cleared\n\nRemoved all analysis data from {cleared} video(s). Timeline clips have been cleared."}


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

def register(plugin):
    plugin.register(PitLaneAI)
