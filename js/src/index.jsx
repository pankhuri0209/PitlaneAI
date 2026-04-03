import { registerComponent, PluginComponentTypes } from "@fiftyone/plugins";
import { useState, useEffect } from "react";

const API = "http://localhost:8000";

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const S = {
  panel: {
    width: "100%",
    height: "100%",
    overflowY: "auto",
    backgroundColor: "#0f0f0f",
    color: "#f0f0f0",
    fontFamily: "'Inter', sans-serif",
    boxSizing: "border-box",
    padding: "24px",
  },
  title: {
    fontSize: "22px",
    fontWeight: "700",
    marginBottom: "4px",
    color: "#ffffff",
  },
  subtitle: {
    fontSize: "13px",
    color: "#888",
    marginBottom: "20px",
  },
  label: {
    display: "block",
    fontSize: "11px",
    fontWeight: "600",
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    color: "#888",
    marginBottom: "6px",
  },
  select: {
    width: "100%",
    padding: "10px 14px",
    borderRadius: "8px",
    backgroundColor: "#1c1c1c",
    color: "#f0f0f0",
    border: "1px solid rgba(255,255,255,0.1)",
    fontSize: "13px",
    fontWeight: "500",
    marginBottom: "16px",
    outline: "none",
    cursor: "pointer",
  },
  card: {
    backgroundColor: "#1c1c1c",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: "12px",
    padding: "16px",
    marginBottom: "12px",
  },
  cardHeader: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "12px",
    marginBottom: "10px",
  },
  cardTitle: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#ffffff",
    margin: 0,
  },
  cardDesc: {
    fontSize: "12px",
    color: "#888",
    margin: "4px 0 0 0",
  },
  runBtn: {
    padding: "8px 16px",
    borderRadius: "8px",
    backgroundColor: "#00C851",
    color: "#000",
    fontWeight: "700",
    fontSize: "13px",
    border: "none",
    cursor: "pointer",
    flexShrink: 0,
    whiteSpace: "nowrap",
  },
  runBtnDisabled: {
    padding: "8px 16px",
    borderRadius: "8px",
    backgroundColor: "#00C851",
    color: "#000",
    fontWeight: "700",
    fontSize: "13px",
    border: "none",
    cursor: "not-allowed",
    flexShrink: 0,
    whiteSpace: "nowrap",
    opacity: 0.4,
  },
  input: {
    width: "100%",
    padding: "8px 12px",
    borderRadius: "8px",
    backgroundColor: "rgba(255,255,255,0.05)",
    color: "#f0f0f0",
    border: "1px solid rgba(255,255,255,0.08)",
    fontSize: "12px",
    outline: "none",
    boxSizing: "border-box",
  },
  spinner: {
    display: "inline-block",
    width: "18px",
    height: "18px",
    border: "2px solid #00C851",
    borderTopColor: "transparent",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
    marginRight: "8px",
    verticalAlign: "middle",
  },
  loadingBox: {
    backgroundColor: "#1c1c1c",
    borderRadius: "12px",
    padding: "20px",
    textAlign: "center",
    fontSize: "13px",
    color: "#888",
    marginTop: "12px",
  },
  resultBox: {
    backgroundColor: "#1c1c1c",
    borderRadius: "12px",
    padding: "20px",
    marginTop: "12px",
    fontSize: "13px",
    lineHeight: "1.7",
    overflowX: "auto",
  },
  error: {
    backgroundColor: "rgba(255,60,60,0.1)",
    border: "1px solid rgba(255,60,60,0.3)",
    color: "#ff6b6b",
    borderRadius: "8px",
    padding: "12px",
    fontSize: "13px",
    marginBottom: "12px",
  },
  timestamp: {
    display: "inline-block",
    backgroundColor: "rgba(0,200,81,0.15)",
    color: "#00C851",
    fontWeight: "600",
    fontSize: "12px",
    padding: "1px 6px",
    borderRadius: "4px",
    cursor: "pointer",
    border: "1px solid rgba(0,200,81,0.3)",
    fontFamily: "monospace",
  },
};

// ---------------------------------------------------------------------------
// Markdown renderer with clickable timestamps
// ---------------------------------------------------------------------------

function ResultPanel({ markdown, onSeek }) {
  const lines = markdown.split("\n");

  function renderLine(line, i) {
    if (line.startsWith("## ")) {
      return (
        <div key={i} style={{ fontSize: "16px", fontWeight: "700", color: "#fff", margin: "16px 0 8px" }}>
          {line.slice(3)}
        </div>
      );
    }
    if (line.startsWith("### ")) {
      return (
        <div key={i} style={{ fontSize: "13px", fontWeight: "600", color: "#00C851", margin: "12px 0 6px" }}>
          {line.slice(4)}
        </div>
      );
    }
    if (line.match(/^\|[-\s|]+\|$/)) return null; // separator row
    if (line.startsWith("|")) {
      const cells = line.split("|").filter((c) => c.trim());
      return (
        <div key={i} style={{ display: "grid", gridTemplateColumns: `repeat(${cells.length}, 1fr)`, gap: "8px", padding: "6px 0", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          {cells.map((c, j) => (
            <span key={j} style={{ fontSize: "12px", color: j === 0 ? "#00C851" : "#aaa", paddingLeft: "4px" }}>
              {renderInline(c.trim(), onSeek)}
            </span>
          ))}
        </div>
      );
    }
    if (line.startsWith("**") && line.endsWith("**")) {
      return <div key={i} style={{ fontWeight: "600", margin: "8px 0", color: "#fff" }}>{line.slice(2, -2)}</div>;
    }
    if (line.trim() === "") return <div key={i} style={{ height: "6px" }} />;
    if (line.startsWith("_") && line.endsWith("_")) {
      return <div key={i} style={{ fontStyle: "italic", color: "#666", fontSize: "12px" }}>{line.slice(1, -1)}</div>;
    }
    if (line.match(/^\d+\.\s/)) {
      return <div key={i} style={{ color: "#ccc", margin: "4px 0", paddingLeft: "8px" }}>{renderInline(line, onSeek)}</div>;
    }
    if (line.startsWith("- ")) {
      return <div key={i} style={{ color: "#ccc", margin: "3px 0", paddingLeft: "12px" }}>• {renderInline(line.slice(2), onSeek)}</div>;
    }
    return <div key={i} style={{ color: "#aaa" }}>{renderInline(line, onSeek)}</div>;
  }

  return <div style={S.resultBox}>{lines.map(renderLine)}</div>;
}

// Render inline text — makes MM:SS timestamps clickable
function renderInline(text, onSeek) {
  const parts = [];
  const regex = /\b(\d{1,2}):(\d{2})\b/g;
  let last = 0;
  let match;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    const mins = parseInt(match[1]);
    const secs = parseInt(match[2]);
    const totalSecs = mins * 60 + secs;
    const ts = match[0];
    parts.push(
      <span
        key={match.index}
        style={S.timestamp}
        title={`Jump to ${ts}`}
        onClick={() => onSeek && onSeek(totalSecs)}
      >
        {ts}
      </span>
    );
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length === 1 && typeof parts[0] === "string" ? parts[0] : parts;
}

// ---------------------------------------------------------------------------
// Main panel component
// ---------------------------------------------------------------------------

function PitLanePanel() {
  const [videos, setVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState("");
  const [activeOp, setActiveOp] = useState("");
  const [errorTypes, setErrorTypes] = useState("all driving errors");
  const [question, setQuestion] = useState("");
  const [focus, setFocus] = useState("Full Analysis");
  const [fetchError, setFetchError] = useState("");
  const [seekMsg, setSeekMsg] = useState("");

  useEffect(() => {
    fetch(`${API}/videos`)
      .then((r) => r.json())
      .then((d) => {
        setVideos(d.videos || []);
        if (d.videos?.length) setSelectedVideo(d.videos[0].id);
      })
      .catch(() =>
        setFetchError("Cannot reach backend. Run: uvicorn backend.main:app --port 8000")
      );
  }, []);

  // Inject CSS animation for spinner
  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  async function clearHistory() {
    setLoading(true);
    setResult("");
    setActiveOp("clear");
    try {
      const res = await fetch(`${API}/clear-history`, { method: "POST" });
      const data = await res.json();
      setResult(data.result || "All analysis history cleared.");
    } catch (e) {
      setResult("Error clearing history. Is backend running?");
    }
    setLoading(false);
  }

  async function run(op) {
    if (!selectedVideo || loading) return;
    setActiveOp(op);
    setLoading(true);
    setResult("");
    setSeekMsg("");
    try {
      let res;
      if (op === "errors") {
        res = await fetch(`${API}/analyze/errors`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ video_id: selectedVideo, error_types: errorTypes }),
        });
      } else if (op === "moments") {
        res = await fetch(`${API}/analyze/best-moments`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ video_id: selectedVideo }),
        });
      } else if (op === "ask") {
        res = await fetch(`${API}/analyze/ask`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ video_id: selectedVideo, question }),
        });
      } else {
        res = await fetch(`${API}/analyze/coaching-report`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ video_id: selectedVideo, focus }),
        });
      }
      const data = await res.json();
      setResult(data.result || data.detail || "No result returned.");
    } catch (e) {
      setResult("Error contacting backend. Is uvicorn running on port 8000?");
    }
    setLoading(false);
  }

  function handleSeek(seconds) {
    // Show a seek message — FiftyOne JS panel API for video seeking
    // uses the fo-video player's global event system
    try {
      const event = new CustomEvent("pitlane-seek", { detail: { seconds } });
      window.dispatchEvent(event);
    } catch (_) {}
    const m = String(Math.floor(seconds / 60)).padStart(2, "0");
    const s = String(seconds % 60).padStart(2, "0");
    setSeekMsg(`Seek to ${m}:${s} — click that timestamp in the FiftyOne video timeline`);
  }

  const selectedFilename = videos.find((v) => v.id === selectedVideo)?.filename || "";

  return (
    <div style={S.panel}>
      <div style={S.title}>PitLane AI</div>
      <div style={S.subtitle}>Go-kart lap analysis powered by Twelve Labs + Groq</div>

      {fetchError && <div style={S.error}>{fetchError}</div>}

      {/* Clear History */}
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "12px" }}>
        <button
          onClick={clearHistory}
          disabled={loading}
          style={{ padding: "6px 14px", borderRadius: "6px", backgroundColor: "rgba(255,60,60,0.15)", color: "#ff6b6b", border: "1px solid rgba(255,60,60,0.3)", fontSize: "12px", fontWeight: "600", cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.5 : 1 }}
        >
          Clear All Analyses
        </button>
      </div>

      {/* Video selector */}
      <label style={S.label}>Select Video</label>
      <select
        value={selectedVideo}
        onChange={(e) => { setSelectedVideo(e.target.value); setResult(""); }}
        style={S.select}
      >
        {videos.map((v) => (
          <option key={v.id} value={v.id}>{v.filename}</option>
        ))}
      </select>

      {/* Op 1 — Find Lap Errors */}
      <div style={S.card}>
        <div style={S.cardHeader}>
          <div>
            <div style={S.cardTitle}>Find Lap Errors</div>
            <div style={S.cardDesc}>Detect every driving mistake with timestamps</div>
          </div>
          <button
            style={loading && activeOp === "errors" || !selectedVideo ? S.runBtnDisabled : S.runBtn}
            disabled={loading || !selectedVideo}
            onClick={() => run("errors")}
          >
            {loading && activeOp === "errors" ? "Analyzing..." : "Run"}
          </button>
        </div>
        <input
          value={errorTypes}
          onChange={(e) => setErrorTypes(e.target.value)}
          placeholder="Error types (e.g. missed apex, late braking)"
          style={S.input}
        />
      </div>

      {/* Op 2 — Find Best Moments */}
      <div style={S.card}>
        <div style={S.cardHeader}>
          <div>
            <div style={S.cardTitle}>Find Best Moments</div>
            <div style={S.cardDesc}>Highlight top driving moments across 6 categories</div>
          </div>
          <button
            style={loading && activeOp === "moments" || !selectedVideo ? S.runBtnDisabled : S.runBtn}
            disabled={loading || !selectedVideo}
            onClick={() => run("moments")}
          >
            {loading && activeOp === "moments" ? "Searching..." : "Run"}
          </button>
        </div>
      </div>

      {/* Op 3 — Ask About Lap */}
      <div style={S.card}>
        <div style={S.cardHeader}>
          <div>
            <div style={S.cardTitle}>Ask About This Lap</div>
            <div style={S.cardDesc}>Ask any question and get a timestamped answer</div>
          </div>
          <button
            style={loading && activeOp === "ask" || !selectedVideo || !question.trim() ? S.runBtnDisabled : S.runBtn}
            disabled={loading || !selectedVideo || !question.trim()}
            onClick={() => run("ask")}
          >
            {loading && activeOp === "ask" ? "Asking..." : "Ask"}
          </button>
        </div>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Was my racing line through Turn 3 correct?"
          style={S.input}
          onKeyDown={(e) => e.key === "Enter" && run("ask")}
        />
      </div>

      {/* Op 4 — Generate Coaching Report */}
      <div style={S.card}>
        <div style={S.cardHeader}>
          <div>
            <div style={S.cardTitle}>Generate Coaching Report</div>
            <div style={S.cardDesc}>Full telemetry report with scores — takes 30–60s</div>
          </div>
          <button
            style={loading && activeOp === "report" || !selectedVideo ? S.runBtnDisabled : S.runBtn}
            disabled={loading || !selectedVideo}
            onClick={() => run("report")}
          >
            {loading && activeOp === "report" ? "Generating..." : "Run"}
          </button>
        </div>
        <select
          value={focus}
          onChange={(e) => setFocus(e.target.value)}
          style={{ ...S.input, cursor: "pointer" }}
        >
          <option>Full Analysis</option>
          <option>Racing Line Only</option>
          <option>Braking Only</option>
          <option>Throttle &amp; Exit Only</option>
        </select>
      </div>

      {/* Loading */}
      {loading && (
        <div style={S.loadingBox}>
          <span style={S.spinner} />
          AI is analyzing your lap...
        </div>
      )}

      {/* Seek hint */}
      {seekMsg && !loading && (
        <div style={{ backgroundColor: "rgba(0,200,81,0.08)", border: "1px solid rgba(0,200,81,0.25)", color: "#00C851", borderRadius: "8px", padding: "10px 14px", fontSize: "12px", marginTop: "10px" }}>
          {seekMsg}
        </div>
      )}

      {/* Result */}
      {result && !loading && (
        <ResultPanel markdown={result} onSeek={handleSeek} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Register panel with FiftyOne
// ---------------------------------------------------------------------------

registerComponent({
  name: "PitLanePanel",
  label: "PitLane AI",
  component: PitLanePanel,
  type: PluginComponentTypes.Panel,
  activator: () => true,
});
