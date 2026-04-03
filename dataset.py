import os
import subprocess

# Must be set BEFORE importing fiftyone
os.environ["FIFTYONE_PLUGINS_DIR"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import fiftyone as fo
from dotenv import load_dotenv
from twelvelabs import TwelveLabs

load_dotenv()
client = TwelveLabs(api_key=os.environ["TWELVELABS_API_KEY"])

# Find the first index
indexes = list(client.indexes.list())
if not indexes:
    print("No indexes found for this API key.")
    exit(1)
INDEX_ID = indexes[0].id
print(f"Using index: {getattr(indexes[0], 'name', INDEX_ID)} ({INDEX_ID})")

# Fetch videos with their HLS URLs
print("Fetching videos from Twelve Labs...")
tl_videos = list(client.indexes.videos.list(INDEX_ID))
if not tl_videos:
    print("No videos found in the index.")
    exit(1)

# Download HLS streams as MP4 files
DOWNLOADS = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS, exist_ok=True)

samples = []
for v in tl_videos:
    video = client.indexes.videos.retrieve(INDEX_ID, v.id)
    filename = getattr(video, "filename", None) or f"{v.id}.mp4"
    # Ensure .mp4 extension
    base = os.path.splitext(filename)[0]
    local_path = os.path.join(DOWNLOADS, f"{base}.mp4")

    hls = getattr(video, "hls", None)
    hls_url = getattr(hls, "video_url", None) if hls else None

    if not hls_url:
        print(f"  SKIP {filename} — no stream URL")
        continue

    if os.path.exists(local_path):
        print(f"  Already downloaded: {os.path.basename(local_path)}")
    else:
        print(f"  Downloading: {filename}...")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", hls_url,
            "-c", "copy",
            local_path
        ], check=True)
        print(f"  Saved: {os.path.basename(local_path)}")

    s = fo.Sample(filepath=local_path)
    s["twelvelabs_video_id"] = v.id
    s["twelvelabs_filename"] = filename
    samples.append(s)

if not samples:
    print("No videos downloaded.")
    exit(1)

if fo.dataset_exists("pitlane-ai"):
    fo.delete_dataset("pitlane-ai")

dataset = fo.Dataset(name="pitlane-ai", persistent=True)
dataset.add_samples(samples)
dataset.compute_metadata()
print(f"\nLoaded {len(samples)} video(s) into FiftyOne.")

session = fo.launch_app(dataset)
session.wait()
