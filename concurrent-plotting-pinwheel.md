# Plan: PitLane AI — Go-Kart Video Analysis FiftyOne Plugin (Hackathon)

## Context
Hackathon April 3 using Twelve Labs (Marengo + Pegasus) + FiftyOne.
Build a FiftyOne plugin targeting go-karting coaches and competitive drivers.
Use case: upload onboard/trackside video → AI analyzes racing line, tire behavior, corner technique.

---

## Market Opportunity (why go-karting, not F1)

| Segment | Size | Key Insight |
|---------|------|-------------|
| Global karting market | $1.82B (2025) → $3.14B (2034) | 6.2% CAGR |
| North America alone | $620M | 34% of global market |
| US tracks | 844 facilities, 164 commercial | Fragmented, no dominant AI tool |
| Youth segment | 32.5% of revenue, 7.1% CAGR | Fastest growing |
| US Kid Kart 2025 | 12,500+ new participants | Record high |
| Elite junior spend | $10,000+ per race | Will pay for edge |
| K1 Speed (leader) | $101M revenue, 107 locations | No AI coaching product |

**Gap:** Existing tools (AiM, VBOX, MyRaceLab) are telemetry-only — no natural language video QA.
**Opportunity:** Parents spending $10K+/race will pay for AI coaching. K1 Speed has no analysis product.

---

## Startup Pitch: PitLane AI

**Tagline:** *"Your AI race engineer — for every driver, not just F1."*

**Target customers:**
1. Competitive youth karting parents ($10K+/race budget)
2. Go-kart coaching academies (K1 Speed, Andretti, independents)
3. Semi-pro drivers in Rotax MAX, IAME series (7,500+ global participants)

**Core value prop:** Upload your onboard lap video → ask in plain English:
- *"Was my racing line through Turn 3 correct?"*
- *"Show me where I'm losing time compared to my best lap"*
- *"Is there tire graining visible on the rear left?"*
- *"When did I brake too early?"*

---

## Plugin Features (3 operators for hackathon)

### Operator 1 — AI Coaching Report (Pegasus + Claude)
Input: onboard lap video
Output: structured coaching report with timestamps

Pegasus analyzes: racing line, braking points, throttle application, vision, consistency
Claude converts analysis into: 3 ranked improvements with WHY + HOW TO FIX

```
"Your main time loss is Turn 3 (0:42s) — early apex entry forces wide exit.
 Try trail braking 2 meters deeper. This alone could save 0.3s per lap."
```

### Operator 2 — Technique Search (Marengo)
Input: search query
Output: video clips matching the query highlighted in FiftyOne timeline
```
"Find all moments of understeer" → highlights 3 clips at exact timestamps
"Find all early braking points" → shows every corner where driver braked too early
```

### Operator 3 — Ask Anything (Pegasus QA)
Input: natural language question about the lap
Output: direct answer with timestamp
```
"Was my racing line through Turn 8 correct?" →
"At 1:23 you entered too tight, missing the apex by ~1 meter.
 You can see the kart running wide on exit losing drive."
```

---

## Demo Script for Hackathon

1. Open FiftyOne with a go-kart onboard lap loaded
2. Click **"Ask about this lap"** → type *"Was my racing line optimal?"*
3. Pegasus responds with timestamped analysis
4. Click **"Find understeer moments"** → Marengo highlights clips in timeline
5. Click **"Generate coaching summary"** → full lap breakdown appears in sidebar

---

## Files to Create

```
pitlane-ai/
├── fiftyone.yml       # plugin metadata
├── __init__.py        # 3 operators using Twelve Labs SDK
├── README.md          # demo screenshots + usage
└── sample_lap.mp4     # demo video (download from YouTube)
```

---

## Setup Needed Tonight
```bash
pip install fiftyone twelvelabs huggingface_hub yt-dlp
# set TWELVELABS_API_KEY
# download a go-kart onboard lap from YouTube with yt-dlp
# index the video via Twelve Labs API
```

---

## Submission Checklist
- [ ] Dependencies installed + API key set
- [ ] Go-kart onboard video downloaded + indexed in Twelve Labs
- [ ] fiftyone.yml + __init__.py + README.md created
- [ ] At least Operator 1 (Lap QA) working end-to-end
- [ ] First GitHub push by 3PM
- [ ] Final push by 5PM
