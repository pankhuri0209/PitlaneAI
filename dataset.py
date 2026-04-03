import os
import subprocess
import webbrowser
import fiftyone as fo

URLS = [
    "https://www.youtube.com/watch?v=teMpvybRYms",
    "https://www.youtube.com/watch?v=UB6v9BMFkeY",
    "https://www.youtube.com/watch?v=AARTajBBPZw",
]
OUT = os.path.join(os.path.dirname(__file__), "kart_clips")
os.makedirs(OUT, exist_ok=True)

print("Downloading go-kart clips...")
for url in URLS:
    subprocess.run([
        "yt-dlp",
        "-f", "best[height<=720][ext=mp4]/best[height<=720]",
        "--merge-output-format", "mp4",
        "-o", os.path.join(OUT, "%(title)s.%(ext)s"),
        "--no-playlist",
        url,
    ])

mp4s = [os.path.join(OUT, f) for f in os.listdir(OUT) if f.endswith(".mp4")]
if not mp4s:
    print("No videos downloaded — check yt-dlp and the URLs.")
    exit(1)

if fo.dataset_exists("pitlane-ai"):
    fo.delete_dataset("pitlane-ai")

dataset = fo.Dataset(name="pitlane-ai", persistent=True)
dataset.add_samples([fo.Sample(filepath=f) for f in mp4s])
dataset.compute_metadata()
print(dataset)

session = fo.launch_app(dataset, auto=False)
chrome = "C:/Program Files/Google/Chrome/Application/chrome.exe %s"
webbrowser.get(chrome).open(f"http://localhost:{session.server_port}")
session.wait()