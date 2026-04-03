"""
index_videos.py
================
Uploads all videos in kart_clips/ to your existing Twelve Labs index.
Saves video IDs to video_ids.json for use by test_search.py and test_coaching.py

Run: python index_videos.py
"""

import os
import json
from dotenv import load_dotenv
from twelvelabs import TwelveLabs

load_dotenv()

INDEX_ID   = "69cfea5921ee25d04843f78e"
CLIPS_DIR  = os.path.join(os.path.dirname(__file__), "kart_clips")
IDS_FILE   = os.path.join(os.path.dirname(__file__), "video_ids.json")

client = TwelveLabs(api_key=os.environ["TWELVELABS_API_KEY"])

mp4_files = [
    os.path.join(CLIPS_DIR, f)
    for f in os.listdir(CLIPS_DIR)
    if f.lower().endswith(".mp4")
]

if not mp4_files:
    print("No MP4 files found in kart_clips/")
    exit(1)

# Load existing IDs if any
if os.path.exists(IDS_FILE):
    with open(IDS_FILE) as f:
        video_ids = json.load(f)
else:
    video_ids = {}

print(f"Uploading {len(mp4_files)} video(s) to index {INDEX_ID}...\n")

for filepath in mp4_files:
    name = os.path.basename(filepath)

    if name in video_ids:
        print(f"  ✓ Already indexed: {name} → {video_ids[name]}")
        continue

    print(f"  ↑ Uploading: {name}")
    task = client.tasks.create(index_id=INDEX_ID, video_file=filepath)

    print(f"    Waiting for indexing to complete...")
    task.wait_for_done(sleep_interval=5)

    if task.status == "ready":
        video_ids[name] = task.video_id
        print(f"    ✓ Done → video_id: {task.video_id}")
    else:
        print(f"    ✗ Failed: {task.status}")

# Save IDs for other scripts
with open(IDS_FILE, "w") as f:
    json.dump(video_ids, f, indent=2)

print(f"\nAll done. Video IDs saved to video_ids.json")
print(json.dumps(video_ids, indent=2))
