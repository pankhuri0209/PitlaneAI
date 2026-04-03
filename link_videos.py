"""
link_videos.py
===============
Links already-indexed Twelve Labs videos to FiftyOne samples.
Run this instead of index_videos.py if you already uploaded videos manually.

Run: python link_videos.py
"""

import os
from dotenv import load_dotenv
from twelvelabs import TwelveLabs
import fiftyone as fo

load_dotenv()

INDEX_ID     = "69cfea5921ee25d04843f78e"
DATASET_NAME = "pitlane-ai"

client = TwelveLabs(api_key=os.environ["TWELVELABS_API_KEY"])

print(f"Fetching videos from index {INDEX_ID}...")
tl_videos = list(client.indexes.videos.list(INDEX_ID))
print(f"Found {len(tl_videos)} video(s) in Twelve Labs:\n")
for v in tl_videos:
    fname = getattr(v, "filename", None) or getattr(v, "system_metadata", {})
    print(f"  - id: {v.id} | metadata: {str(fname).encode('ascii', errors='replace').decode('ascii')}")

# Load FiftyOne dataset
dataset = fo.load_dataset(DATASET_NAME)
print(f"\nFiftyOne dataset has {len(dataset)} sample(s):")
for s in dataset:
    print(f"  - {os.path.basename(s.filepath).encode('ascii', errors='replace').decode('ascii')}")

# Match by filename
print("\nLinking...")
linked = 0
for sample in dataset:
    sample_name = os.path.basename(sample.filepath).lower().strip()

    for v in tl_videos:
        # Try to match by filename from metadata
        tl_name = ""
        if hasattr(v, "system_metadata") and v.system_metadata:
            tl_name = getattr(v.system_metadata, "filename", "") or ""
        if not tl_name and hasattr(v, "filename"):
            tl_name = v.filename or ""

        tl_name = os.path.basename(tl_name).lower().strip()

        if sample_name == tl_name or sample_name in tl_name or tl_name in sample_name:
            sample["tl_video_id"] = v.id
            sample["tl_index_id"] = INDEX_ID
            sample.save()
            print(f"  OK Linked: {sample_name.encode('ascii','replace').decode('ascii')} -> {v.id}")
            linked += 1
            break
    else:
        print(f"  NO MATCH: {sample_name.encode('ascii','replace').decode('ascii')}")

print(f"\nDone — {linked}/{len(dataset)} samples linked.")
print("You can now run Find Best Moments in the FiftyOne App.")
