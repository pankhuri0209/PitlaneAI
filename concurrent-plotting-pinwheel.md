# PitLane AI — Go-Kart Coaching Plugin (Hackathon Plan)

> *"Your AI race engineer — for every driver, not just F1."*

**Event:** Voxel51 Video Understanding Hackathon — Northeastern University, April 3, 2026
**Submission deadline:** 5 PM today

---

## What We're Building

A **FiftyOne plugin** that uses Twelve Labs AI to coach go-kart drivers by analyzing onboard lap videos. Upload race footage → AI finds your mistakes, highlights your best moments, answers your questions, and gives you a full coaching breakdown — all in plain English.

---

## The AI Stack

| Tool | Type | Role |
|---|---|---|
| **Twelve Labs Marengo 3.0** | Multimodal video embedding model | Semantic video search — find moments that *look like* a description |
| **Twelve Labs Pegasus 1.2** | Video-language generation model | Watch video + answer questions / generate coaching text |
| **FiftyOne** | ML dataset visualization framework | UI layer — shows videos, timeline clips, sidebar fields |

---

## 4 Operators + Team Split

| # | Operator | What it does | Model | Owner |
|---|---|---|---|---|
| 1 | **Find Lap Errors** 🟢 | Auto-detects driving mistakes — missed apex, wide exit, early braking, wheel spin. Each error type gets a different color on the video timeline. | Marengo | Pankhuri (Easy) |
| 2 | **Find Best Moments** 🟢 | Highlights the best driving moments — smooth apexes, clean acceleration, fast corners. Color-coded on the timeline. | Marengo | Aditya (Easy) |
| 3 | **Ask About Lap** 🔴 | Ask any question about a lap in plain English. Pegasus watches the video and answers with timestamps. | Pegasus | Pankhuri (Hard) |
| 4 | **Generate Coaching Report** 🔴 | Full structured lap breakdown: racing line, braking, throttle, top 3 improvements with timestamps. | Pegasus | Aditya (Hard) |

---

## End-to-End Workflow

```
1. Load data
   python dataset.py
   → Downloads 3 go-kart onboard videos via yt-dlp
   → Creates FiftyOne dataset "pitlane-ai"

2. Index videos (one-time, ~2 min/video)
   python index_videos.py
   → Uploads videos to Twelve Labs index (Marengo + Pegasus)
   → Each video gets a tl_video_id stored in FiftyOne

3. Install plugin
   fiftyone plugins download C:/Users/.../voxel51

4. Open FiftyOne App
   → Run operators via \ (backslash) menu

5. Demo flow
   a. Find Lap Errors    → colored error clips on timeline
   b. Find Best Moments  → colored highlight clips on timeline
   c. Ask About Lap      → "Where did I brake too early?"
   d. Coaching Report    → full AI lap breakdown in sidebar
```

---

## Market Opportunity

| Segment | Size |
|---|---|
| Global karting market | $1.82B (2025) → $3.14B (2034), 6.2% CAGR |
| North America | $620M, 844 facilities |
| Elite junior spend | $10,000+ per race |
| K1 Speed (market leader) | $101M revenue — **no AI coaching product** |

**Gap:** Existing tools (AiM, VBOX, MyRaceLab) are telemetry-only — they show data but can't watch video and explain *why* you're slow. PitLane AI is the first natural language video coaching tool for karting.

---

## Technical Setup

**Team API key:** `tlk_1W11H001JQ0G232JBK18Q3AR7J7W`
**Team index ID:** `69cfea5921ee25d04843f78e`

```bash
pip install fiftyone twelvelabs python-dotenv yt-dlp
# Add TWELVELABS_API_KEY to .env
python dataset.py       # download videos
python index_videos.py  # index to Twelve Labs
fiftyone plugins download .
```

---

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Plugin — 4 operators |
| `fiftyone.yml` | Plugin manifest |
| `dataset.py` | Download videos + build FiftyOne dataset |
| `index_videos.py` | Upload videos to Twelve Labs index |
| `test_index.py` | Verify index access |
| `kart_clips/` | 3 go-kart onboard videos |
| `README.md` | Submission documentation |

---

## Submission Checklist

- [ ] Op 1: Find Lap Errors working (Pankhuri)
- [ ] Op 2: Find Best Moments working (Aditya)
- [ ] Op 3: Ask About Lap working (Pankhuri)
- [ ] Op 4: Generate Coaching Report working (Aditya)
- [ ] README updated with demo screenshots
- [ ] Final push to GitHub by 5 PM
