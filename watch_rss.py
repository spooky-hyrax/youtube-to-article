import feedparser
import subprocess
import os
import json
from datetime import datetime

CHANNEL_ID = "UCB8tiE8u0fKTHkBMTFx09yA"  # Siderolabs
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
SEEN_FILE = "seen_videos.json"

# Load already-processed videos
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen = json.load(f)
else:
    seen = []

# Parse RSS feed
feed = feedparser.parse(RSS_URL)

new_count = 0
for entry in feed.entries:
    video_id = entry.yt_videoid
    if video_id in seen:
        continue

    print(f"New video found: {entry.title}")
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Run pipeline
    subprocess.run(["python3.11", "pipeline.py", url])

    # Mark as seen
    seen.append(video_id)
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

    new_count += 1

if new_count == 0:
    print(f"No new videos. Checked at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
