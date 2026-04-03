import os
import subprocess
import fiftyone as fo

URLS = [
    "https://www.youtube.com/watch?v=teMpvybRYms",
    "https://www.youtube.com/watch?v=UB6v9BMFkeY",
    "https://www.youtube.com/watch?v=AARTajBBPZw",
]
OUT = os.path.join(os.path.dirname(__file__), "kart_clips")
os.makedirs(OUT, exist_ok=True)

# Only download if videos don't already exist
existing = [f for f in os.listdir(OUT) if f.endswith(".mp4")] if os.path.exists(OUT) else []
if not existing:
    print("Downloading go-kart clips (first time only)...")
    for url in URLS:
        subprocess.run([
            "yt-dlp",
            "-f", "best[height<=720][ext=mp4]/best[height<=720]",
            "--merge-output-format", "mp4",
            "-o", os.path.join(OUT, "%(title)s.%(ext)s"),
            "--no-playlist",
            url,
        ])
else:
    print(f"Videos already downloaded ({len(existing)} files) — skipping.")

mp4s = [os.path.join(OUT, f) for f in os.listdir(OUT) if f.endswith(".mp4")]
if not mp4s:
    print("No videos found — check kart_clips/ folder.")
    exit(1)

# Load existing dataset or create new one
if fo.dataset_exists("pitlane-ai"):
    print("Dataset already exists — loading it.")
    dataset = fo.load_dataset("pitlane-ai")
else:
    dataset = fo.Dataset(name="pitlane-ai", persistent=True)
    dataset.add_samples([fo.Sample(filepath=f) for f in mp4s])
    dataset.compute_metadata()
print(dataset)

session = fo.launch_app(dataset, auto=False)
print(f"App running at http://localhost:{session.server_port}")
session.wait()